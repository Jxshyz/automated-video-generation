import os
import requests
import subprocess
from dotenv import load_dotenv

# Load API key from credentials.env
load_dotenv('./credentials.env')
api_key = os.getenv("HEYGEN_API_KEY")

# Google Drive Direct URLs for the audio files
first_audio_url = 'https://drive.google.com/uc?id=1cCWo0K28CB-0AMI2Lp0Tozk9bwc_4S-e&export=download'
second_audio_url = 'https://drive.google.com/uc?id=1a9d6kqV2-F1PVu398toBpUiR8ORDz9wc&export=download'
third_audio_url = 'https://drive.google.com/uc?id=1cCUU3T00gY564OtDtn4kpoSTiuY4w7Ym&export=download'

video_output_path_1 = './data/avatar_part1.mp4'
import os
import requests
import subprocess
from dotenv import load_dotenv

# Load API key from credentials.env
load_dotenv('./credentials.env')
api_key = os.getenv("HEYGEN_API_KEY")

# Google Drive Direct URLs for the audio files
first_audio_url = 'https://drive.google.com/uc?id=1cCWo0K28CB-0AMI2Lp0Tozk9bwc_4S-e&export=download'
second_audio_url = 'https://drive.google.com/uc?id=1a9d6kqV2-F1PVu398toBpUiR8ORDz9wc&export=download'
third_audio_url = 'https://drive.google.com/uc?id=1cCUU3T00gY564OtDtn4kpoSTiuY4w7Ym&export=download'

video_output_path_1 = './data/avatar_part1.mp4'
video_output_path_2 = './data/avatar_part2.mp4'
video_output_path_3 = './data/avatar_part3.mp4'
final_video_path = './data/final_avatar_video.mp4'

# Function to generate avatar video using HeyGen API
def create_avatar_video(audio_url, video_output_path, avatar_id):
    print(f"Sending API request for avatar video generation with audio URL: {audio_url}")
    
    url = "https://api.heygen.com/v2/video/generate"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }

    # Prepare the API request payload
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,  # Use the selected avatar ID here
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "audio",
                    "input_audio": audio_url  # Use the hosted audio URL here
                },
                "background": {
                    "type": "transparent"
                }
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        }
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

# Function to check video status and download when ready
def download_video(video_id, video_output_path):
    print(f"Checking status for video_id: {video_id}")
    
    status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {
        "X-Api-Key": api_key
    }

    response = requests.get(status_url, headers=headers)
    print(f"Video status check response: {response.status_code}, {response.text}")

    if response.status_code == 200:
        video_info = response.json()["data"]
        status = video_info["status"]
        print(f"Video status: {status}")

        while status not in ["completed", "failed"]:
            print("Video is still processing...")
            response = requests.get(status_url, headers=headers)
            video_info = response.json()["data"]
            status = video_info["status"]
            print(f"Current status: {status}")

        if status == "completed":
            video_url = video_info["video_url"]
            print(f"Video is ready. Downloading from {video_url}...")
            video_data = requests.get(video_url).content
            with open(video_output_path, "wb") as f:
                f.write(video_data)
            print(f"Video saved to {video_output_path}")
        else:
            print(f"Video creation failed: {video_info['error']}")
    else:
        print(f"Error checking video status: {response.status_code}, {response.text}")

# Function to combine the three video parts using FFmpeg
def combine_videos():
    print("Combining video parts...")

    # Check if video part files exist before running FFmpeg
    if not os.path.exists(video_output_path_1):
        print(f"Error: {video_output_path_1} does not exist!")
        return
    if not os.path.exists(video_output_path_2):
        print(f"Error: {video_output_path_2} does not exist!")
        return
    if not os.path.exists(video_output_path_3):
        print(f"Error: {video_output_path_3} does not exist!")
        return

    command = [
        'ffmpeg', 
        '-i', video_output_path_1,  # First part video
        '-i', video_output_path_2,  # Second part video
        '-i', video_output_path_3,  # Third part video
        '-filter_complex', '[0:v][1:v][2:v]concat=n=3:v=1:a=0[outv]',  # Combine video
        '-map', '[outv]', 
        final_video_path
    ]
    
    # Run the FFmpeg command
    print(f"Running FFmpeg command: {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode == 0:
        print(f"Final video created successfully: {final_video_path}")
    else:
        print(f"Error while combining videos: {result.stderr.decode()}")

# Function to start the process
def process_and_generate():
    # Choose the avatar ID from the list
    avatar_id = "1733536264"  # Example: Javi (Intense)

    # Generate video for the first part
    video_id_1 = create_avatar_video(first_audio_url, video_output_path_1, avatar_id)
    if video_id_1:
        download_video(video_id_1, video_output_path_1)

    # Generate video for the second part
    video_id_2 = create_avatar_video(second_audio_url, video_output_path_2, avatar_id)
    if video_id_2:
        download_video(video_id_2, video_output_path_2)

    # Generate video for the third part
    video_id_3 = create_avatar_video(third_audio_url, video_output_path_3, avatar_id)
    if video_id_3:
        download_video(video_id_3, video_output_path_3)

    # Combine the video parts
    combine_videos()

# Start the audio processing and video generation
process_and_generate()
video_output_path_2 = './data/avatar_part2.mp4'
video_output_path_3 = './data/avatar_part3.mp4'
final_video_path = './data/final_avatar_video.mp4'

# Function to generate avatar video using HeyGen API
def create_avatar_video(audio_url, video_output_path, avatar_id):
    print(f"Sending API request for avatar video generation with audio URL: {audio_url}")
    
    url = "https://api.heygen.com/v2/video/generate"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }

    # Prepare the API request payload
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,  # Use the selected avatar ID here
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "audio",
                    "input_audio": audio_url  # Use the hosted audio URL here
                },
                "background": {
                    "type": "transparent"
                }
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        }
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

# Function to check video status and download when ready
def download_video(video_id, video_output_path):
    print(f"Checking status for video_id: {video_id}")
    
    status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {
        "X-Api-Key": api_key
    }

    response = requests.get(status_url, headers=headers)
    print(f"Video status check response: {response.status_code}, {response.text}")

    if response.status_code == 200:
        video_info = response.json()["data"]
        status = video_info["status"]
        print(f"Video status: {status}")

        while status not in ["completed", "failed"]:
            print("Video is still processing...")
            response = requests.get(status_url, headers=headers)
            video_info = response.json()["data"]
            status = video_info["status"]
            print(f"Current status: {status}")

        if status == "completed":
            video_url = video_info["video_url"]
            print(f"Video is ready. Downloading from {video_url}...")
            video_data = requests.get(video_url).content
            with open(video_output_path, "wb") as f:
                f.write(video_data)
            print(f"Video saved to {video_output_path}")
        else:
            print(f"Video creation failed: {video_info['error']}")
    else:
        print(f"Error checking video status: {response.status_code}, {response.text}")

# Function to combine the three video parts using FFmpeg
def combine_videos():
    print("Combining video parts...")
    command = [
        'ffmpeg', 
        '-i', video_output_path_1,  # First part video
        '-i', video_output_path_2,  # Second part video
        '-i', video_output_path_3,  # Third part video
        '-filter_complex', '[0:v][1:v][2:v]concat=n=3:v=1:a=0[outv]',  # Combine video
        '-map', '[outv]', 
        final_video_path
    ]
    
    # Run the FFmpeg command
    print(f"Running FFmpeg command: {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode == 0:
        print(f"Final video created successfully: {final_video_path}")
    else:
        print(f"Error while combining videos: {result.stderr.decode()}")

# Function to start the process
def process_and_generate():
    # Choose the avatar ID from the list
    avatar_id = "1733536264"  # Example: Javi (Intense)

    # Generate video for the first part
    video_id_1 = create_avatar_video(first_audio_url, video_output_path_1, avatar_id)
    if video_id_1:
        download_video(video_id_1, video_output_path_1)

    # Generate video for the second part
    video_id_2 = create_avatar_video(second_audio_url, video_output_path_2, avatar_id)
    if video_id_2:
        download_video(video_id_2, video_output_path_2)

    # Generate video for the third part
    video_id_3 = create_avatar_video(third_audio_url, video_output_path_3, avatar_id)
    if video_id_3:
        download_video(video_id_3, video_output_path_3)

    # Combine the video parts
    combine_videos()

# Start the audio processing and video generation
process_and_generate()
