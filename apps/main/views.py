# Python
import time
import uuid
import requests
import boto3
from botocore.exceptions import ClientError

# Django
from django.conf import settings

# Rest-Framework
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

# Project
from apps.main.models import Video, UploadedVideo, TranscribeResult
from apps.main.serializers import VideoSerializer, UploadedVideoSerializer, TranscribeResultSerializer

AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_SECRET_REGION = settings.AWS_REGION_NAME


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Save the user if authenticated; otherwise, save as None
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)


class UploadedVideoViewSet(viewsets.ModelViewSet):
    queryset = UploadedVideo.objects.all()
    serializer_class = UploadedVideoSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Extract the bucket name and object key from the request data
        serializer = UploadedVideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bucket_name = serializer.validated_data.get('bucket')
        obj_key = serializer.validated_data.get('obj_key')
        file_content = serializer.validated_data.get('file')

        if file_content is None:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Save the user if authenticated; otherwise, save as None
        user = self.request.user if self.request.user.is_authenticated else None

        # Check if all required fields are provided
        if bucket_name and obj_key and file_content:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=str(AWS_ACCESS_KEY_ID),
                aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY)
            )
            try:
                # Upload the file to S3
                extra_args = {'ContentType': 'video/mp4', 'ContentDisposition': 'inline'}  # Adjust as needed
                s3_client.upload_fileobj(file_content, bucket_name, obj_key, ExtraArgs=extra_args)
                # Save the UploadedVideo instance after successful upload
                UploadedVideo.objects.create(
                    user=user,
                    bucket=bucket_name,
                    obj_key=obj_key
                ).save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ClientError as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                return Response({'error': 'An error occurred while uploading to S3: ' + str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'error': 'Missing required fields: bucket, obj_key, or file.'},
                            status=status.HTTP_400_BAD_REQUEST)


class TranscribeResultViewSet(viewsets.ModelViewSet):
    queryset = TranscribeResult.objects.all()
    serializer_class = TranscribeResultSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        filename = serializer.validated_data.get('filename')
        user = request.user if request.user.is_authenticated else None

        s3_bucket = 'kiut-captions'
        s3_uri = f's3://{s3_bucket}/{filename}'

        transcribe_client = boto3.client(
            'transcribe',
            region_name=AWS_SECRET_REGION,
            aws_access_key_id=str(AWS_ACCESS_KEY_ID),
            aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY)
        )

        job_name = f'transcription-{str(uuid.uuid4())}'

        try:
            # Start the transcription job
            transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': s3_uri},
                MediaFormat='mp4',  # Adjust based on your video format
                LanguageCode='en-US'
            )

            # Poll for job completion
            while True:
                response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                status = response['TranscriptionJob']['TranscriptionJobStatus']

                if status in ['COMPLETED', 'FAILED']:
                    break
                time.sleep(5)  # Wait before checking again

            if status == 'COMPLETED':
                # Get the transcript file URL
                transcript_url = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                transcript_response = requests.get(transcript_url)
                transcript_data = transcript_response.json()

                # Print or log the transcript data to inspect it
                print("Transcript Data:", transcript_data)  # Debugging line

                # Check for the presence of items
                if 'results' in transcript_data and 'items' in transcript_data['results']:
                    segments = []
                    for item in transcript_data['results']['items']:
                        # Safely extract start_time, end_time, and content
                        try:
                            start_time = float(item['start_time'])
                            end_time = float(item['end_time'])
                            content = item['alternatives'][0]['content'] if item['alternatives'] else ''
                            segments.append({
                                'start_time': start_time,
                                'end_time': end_time,
                                'content': content
                            })
                        except KeyError as e:
                            print(f"KeyError: {str(e)} - Item: {item}")  # Log the error and item
                            continue  # Skip this item if there's a KeyError

                    if not segments:
                        return Response({'error': 'No transcription segments found.'},
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                else:
                    return Response({'error': 'Transcription results are not available.'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Save the result to the TranscribeResult model
                TranscribeResult.objects.create(
                    user=user,
                    uri=s3_uri,
                    redacted=False
                )

                # Generate a presigned URL for the video file
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=str(AWS_ACCESS_KEY_ID),
                    aws_secret_access_key=str(AWS_SECRET_ACCESS_KEY)
                )
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': s3_bucket, 'Key': filename},
                    ExpiresIn=3600  # URL expires in 1 hour
                )

                # Create a response that includes the job details and segments
                response_data = {
                    'job_name': job_name,
                    's3_uri': s3_uri,
                    'video_url': presigned_url,
                    'message': 'Transcription job completed successfully.',
                    'transcription_segments': segments
                }

                return Response(response_data, status=200)

            else:
                return Response({'error': 'Transcription job failed.'}, status=500)

        except ClientError as e:
            return Response({'error': str(e)}, status=500)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
