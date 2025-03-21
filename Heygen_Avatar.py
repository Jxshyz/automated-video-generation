import os
import requests
import subprocess
import time
from dotenv import load_dotenv
from google.cloud import storage

# Load API key from .env file
load_dotenv("./credentials.env")
api_key = os.getenv("HEYGEN_API_KEY")
if not api_key:
    raise ValueError("HEYGEN_API_KEY not found in credentials.env")

# Google Cloud Storage setup
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\buoyant-airport-451611-d4-0e7f2929f9e6.json"
storage_client = storage.Client()
bucket_name = "mein-uni-bucket-2025"

# Publicly accessible URLs (no need for signed URLs anymore)
video_filenames = ["temp_part1.mp4", "temp_part2.mp4", "temp_part3.mp4"]
video_urls = [f"https://storage.googleapis.com/{bucket_name}/{filename}" for filename in video_filenames]
video_output_paths = [f"./data/{filename}" for filename in video_filenames]
final_video_path = "./data/avatar_video.mp4"

# HeyGen avatar settings
avatar_id = "Dexter_Doctor_Standing2_public"
background_color = "#000000"  # Black background

def create_avatar_video(audio_url, video_output_path):
    """ Sends a request to HeyGen API to create an avatar video. """
    print(f"🎥 Requesting HeyGen avatar generation with audio: {audio_url}")

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
                "background": {"type": "color", "value": background_color}
            }
        ],
        "dimension": {"width": 1280, "height": 720}
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Response: {response.status_code}, {response.text}")

    if response.status_code == 200:
        video_id = response.json()["data"]["video_id"]
        print(f"✅ Video created successfully with video_id: {video_id}")
        return video_id
    else:
        print(f"❌ Failed to create video: {response.status_code}, {response.text}")
        return None

def download_video(video_id, video_output_path):
    """ Checks the status and downloads the generated HeyGen video. """
    print(f"⏳ Checking status for video_id: {video_id}")
    status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {"X-Api-Key": api_key}

    while True:
        response = requests.get(status_url, headers=headers)
        if response.status_code == 200:
            video_info = response.json()["data"]
            status = video_info["status"]

            if status == "completed":
                video_url = video_info["video_url"]
                print(f"🎬 Video is ready. Downloading from {video_url}...")
                video_data = requests.get(video_url).content
                with open(video_output_path, "wb") as f:
                    f.write(video_data)
                print(f"✅ Video saved to {video_output_path}")
                return True
            elif status == "failed":
                print(f"❌ Video creation failed: {video_info.get('error', 'Unknown error')}")
                return False
            else:
                print("⌛ Still processing...")
                time.sleep(5)
        else:
            print(f"❌ Error checking video status: {response.status_code}, {response.text}")
            return False

def combine_videos(video_paths, output_path):
    """ Combines multiple video files into one final video. """
    if not all(os.path.exists(path) for path in video_paths):
        print("❌ One or more video files are missing. Aborting merge.")
        return False

    print("🔧 Combining video parts with FFmpeg...")
    command = ['ffmpeg'] + sum([['-i', path] for path in video_paths], []) + [
        '-filter_complex', f'concat=n={len(video_paths)}:v=1:a=1[outv][outa]',
        '-map', '[outv]', '-map', '[outa]',
        '-c:v', 'libx264', '-c:a', 'aac', '-y', output_path
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print(f"✅ Final video created: {output_path}")
        return True
    else:
        print(f"❌ FFmpeg error: {result.stderr.decode()}")
        return False

def process_and_generate():
    """ Main function to generate and merge avatar videos. """
    os.makedirs("./data", exist_ok=True)

    # Request HeyGen avatar videos
    video_ids = []
    for audio_url, video_path in zip(video_urls, video_output_paths):
        video_id = create_avatar_video(audio_url, video_path)
        if video_id:
            video_ids.append((video_id, video_path))

    # Download videos
    for video_id, video_path in video_ids:
        download_video(video_id, video_path)

    # Merge videos
    if video_ids and combine_videos(video_output_paths, final_video_path):
        print("🎉 Avatar video generation completed successfully!")
    else:
        print("❌ Avatar video generation failed.")

# Run the script
process_and_generate()
