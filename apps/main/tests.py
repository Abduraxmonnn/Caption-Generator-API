# Django
from django.conf import settings

# Third-Part
import assemblyai as aai

ASSEMBLYAI_API_KEY = settings.ASSEMBLYAI_KEY
aai.settings.api_key = ASSEMBLYAI_API_KEY
asd = aai.Transcriber().transcribe('ae8cb66d-f47c-4996-8d4f-b30b33cd7f86.mp4')
sub = asd.export_subtitles_srt()


# Function to parse SRT content into list of dicts
def parse_srt(srt_content):
    lines = srt_content.strip().split("\n")
    subtitles = []

    for i in range(0, len(lines), 4):  # Each subtitle block has 4 lines
        if i + 3 < len(lines):
            time_info = lines[i + 1]
            content = lines[i + 2].strip()
            start_time, end_time = time_info.split(' --> ')

            # Convert times to seconds
            start_time_sec = convert_to_seconds(start_time)
            end_time_sec = convert_to_seconds(end_time)

            subtitles.append({
                "start_time": start_time_sec,
                "end_time": end_time_sec,
                "content": content
            })

    return subtitles


def convert_to_seconds(time_str):
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000


# Parse the subtitles and print the result
subtitles_list = parse_srt(sub)
for subtitle in subtitles_list:
    print(subtitle)

# Save the result as a JSON file (optional)
import json

with open('subtitles.json', 'w') as json_file:
    json.dump(subtitles_list, json_file, indent=4)
