import os
import requests
import subprocess
import time
from datetime import timedelta
from dotenv import load_dotenv
from pydub import AudioSegment
from google.cloud import storage
from image_processing import remove_background

# Load API key from credentials.env
load_dotenv('./credentials.env')
api_key = os.getenv("HEYGEN_API_KEY")
if not api_key:
    raise ValueError("HEYGEN_API_KEY not found in credentials.env")

# Google Cloud Storage setup
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\buoyant-airport-451611-d4-0e7f2929f9e6.json"
storage_client = storage.Client()
bucket_name = "mein-uni-bucket-2025"
bucket = storage_client.get_bucket(bucket_name)

# Output paths
video_output_paths = ['./data/avatar_part1.mp4', './data/avatar_part2.mp4', './data/avatar_part3.mp4']
final_video_path = './data/final_avatar_video.mp4'
transparent_video_path = './data/final_avatar_transparent.mov'

def download_and_process_audio(gcs_url):
    local_mp3 = "./data/tts_output.mp3"
    blob = bucket.blob("tts_output.mp3")
    blob.download_to_filename(local_mp3)
    print(f"✅ Downloaded {gcs_url} to {local_mp3}")

    audio = AudioSegment.from_mp3(local_mp3)
    local_wav = "./data/tts_output.wav"
    audio.export(local_wav, format="wav")
    print(f"✅ Converted to {local_wav}")

    max_length_ms = 175 * 1000
    audio_parts = []
    for i, start in enumerate(range(0, len(audio), max_length_ms)):
        end = min(start + max_length_ms, len(audio))
        part = audio[start:end]
        part_file = f"./data/tts_part_{i}.wav"
        part.export(part_file, format="wav")
        audio_parts.append(part_file)
        print(f"✅ Split part {i}: {start/1000:.1f}s - {end/1000:.1f}s saved as {part_file}")

    uploaded_urls = []
    for part_file in audio_parts:
        blob_name = os.path.basename(part_file)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(part_file)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET"
        )
        uploaded_urls.append(signed_url)
        print(f"✅ Uploaded {part_file} to GCS with signed URL: {signed_url[:50]}...")

    os.remove(local_mp3)
    os.remove(local_wav)
    for part_file in audio_parts:
        os.remove(part_file)

    return uploaded_urls, audio_parts

def create_avatar_video(audio_url, video_output_path, avatar_id):
    print(f"Sending API request for avatar video generation with audio URL: {audio_url[:50]}...")
    url = "https://api.heygen.com/v2/video/generate"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    payload = {
        "video_inputs": [
            {
                "character": {"type": "avatar", "avatar_id": avatar_id, "avatar_style": "normal"},
                "voice": {"type": "audio", "audio_url": audio_url},
                "background": {"type": "color", "value": "#000000"}
            }
        ],
        "dimension": {"width": 1280, "height": 720}
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Received response from HeyGen API: {response.status_code}, {response.text}")
    
    if response.status_code == 200:
        video_id = response.json()["data"]["video_id"]
        print(f"Video created successfully with video_id: {video_id}")
        return video_id
    else:
        print(f"Failed to create video: {response.status_code}, {response.text}")
        return None

def download_video(video_id, video_output_path):
    print(f"Checking status for video_id: {video_id}")
    status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {"X-Api-Key": api_key}

    while True:
        response = requests.get(status_url, headers=headers)
        print(f"Video status check response: {response.status_code}, {response.text}")
        if response.status_code == 200:
            video_info = response.json()["data"]
            status = video_info["status"]
            print(f"Video status: {status}")
            if status == "completed":
                video_url = video_info["video_url"]
                print(f"Video is ready. Downloading from {video_url}...")
                video_data = requests.get(video_url).content
                with open(video_output_path, "wb") as f:
                    f.write(video_data)
                print(f"Video saved to {video_output_path}")
                break
            elif status == "failed":
                print(f"Video creation failed: {video_info['error']}")
                break
            else:
                print("Video is still processing...")
                time.sleep(5)
        else:
            print(f"Error checking video status: {response.status_code}, {response.text}")
            break

def combine_videos(video_paths):
    if not video_paths:
        print("❌ No videos to combine.")
        return False

    print("Combining video parts...")
    for path in video_paths:
        if not os.path.exists(path):
            print(f"Error: {path} does not exist!")
            return False

    filter_complex = "".join(f"[{i}:v][{i}:a]" for i in range(len(video_paths))) + f"concat=n={len(video_paths)}:v=1:a=1[outv][outa]"
    command = ['ffmpeg'] + sum([['-i', path] for path in video_paths], []) + [
        '-filter_complex', filter_complex,
        '-map', '[outv]',           # Map video output
        '-map', '[outa]',           # Map audio output
        '-c:v', 'libx264',          # Re-encode video
        '-c:a', 'aac',              # Re-encode audio
        '-y',                       # Overwrite output
        final_video_path
    ]
    
    print(f"Running FFmpeg command: {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode == 0:
        print(f"Final video created successfully: {final_video_path}")
        return True
    else:
        print(f"Error while combining videos: {result.stderr.decode()}")
        return False

def process_and_generate():
    os.makedirs("./data", exist_ok=True)
    gcs_url = "https://storage.googleapis.com/mein-uni-bucket-2025/tts_output.mp3"
    uploaded_urls, audio_parts = download_and_process_audio(gcs_url)

    avatar_id = "Dexter_Doctor_Standing2_public"
    video_ids = []
    for i, (audio_url, video_path) in enumerate(zip(uploaded_urls, video_output_paths[:len(uploaded_urls)])):
        video_id = create_avatar_video(audio_url, video_path, avatar_id)
        if video_id:
            video_ids.append((video_id, video_path))

    for video_id, video_path in video_ids:
        download_video(video_id, video_path)

    if video_ids and combine_videos([path for _, path in video_ids]):
        if remove_background(final_video_path, transparent_video_path):
            print("🎉 Video processing complete with transparent background!")
        else:
            print("❌ Failed to create transparent video.")
    else:
        print("❌ No videos generated or combined, skipping background removal.")

# Start the process
process_and_generate()