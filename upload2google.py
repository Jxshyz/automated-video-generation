import os
import math
import subprocess
from pydub import AudioSegment
from google.cloud import storage

# File paths
MP3_FILE = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\output.mp3"
GCS_BUCKET_NAME = "mein-uni-bucket-2025"
GCS_CREDENTIALS = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\buoyant-airport-451611-d4-0e7f2929f9e6.json"

# Ensure Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS

# Convert MP3 to WAV in memory (without saving)
print("🔄 Converting MP3 to WAV in memory...")
audio = AudioSegment.from_mp3(MP3_FILE)

# Split into 3 parts (each max 2m 57s)
MAX_LENGTH_MS = 177 * 1000  # 2 minutes 57 seconds in milliseconds
num_parts = math.ceil(len(audio) / MAX_LENGTH_MS)
split_mp4_files = []

for i in range(num_parts):
    start_time = i * MAX_LENGTH_MS
    end_time = min((i + 1) * MAX_LENGTH_MS, len(audio))
    split_audio = audio[start_time:end_time]

    # Save temporary WAV file
    temp_wav = f"temp_part{i+1}.wav"
    split_audio.export(temp_wav, format="wav")

    # Convert to MP4 (audio-only)
    temp_mp4 = f"temp_part{i+1}.mp4"
    ffmpeg_mp4_command = f'ffmpeg -i "{temp_wav}" -c:a aac -b:a 192k -vn "{temp_mp4}" -y'
    subprocess.run(ffmpeg_mp4_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Delete temp WAV file
    os.remove(temp_wav)

    # Upload MP4 to Google Cloud Storage
    print(f"📤 Uploading {temp_mp4} to Google Cloud Storage...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(temp_mp4)
    blob.upload_from_filename(temp_mp4)

    print(f"✅ Uploaded: gs://{GCS_BUCKET_NAME}/{temp_mp4}")

    # Delete local MP4 file after upload
    os.remove(temp_mp4)

print("🎉 All MP4 files processed, uploaded to cloud, and deleted locally!")
