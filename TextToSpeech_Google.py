import requests
import os
import re
import sys
import base64
import subprocess
from dotenv import load_dotenv
from pydub import AudioSegment
from google.cloud import storage

# Load API key from .env file
load_dotenv("credentials.env")
GOOGLE_TTS_API_KEY = os.getenv("GOOGLE_TTS_API_KEY")
MAX_TTS_CHUNK_SIZE = 5000  # Google TTS API limit

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\buoyant-airport-451611-d4-0e7f2929f9e6.json"
storage_client = storage.Client()
bucket_name = "mein-uni-bucket-2025"
bucket = storage_client.get_bucket(bucket_name)

def read_text_file(file_path):
    """Reads and filters spoken text from the input file."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as file:
        raw_text = file.read()

    return filter_spoken_text(raw_text)

def filter_spoken_text(text):
    """Removes non-spoken content enclosed in (( ... ))."""
    return re.sub(r"\(\(.*?\)\)", "", text).strip()

def split_text(text, max_size=MAX_TTS_CHUNK_SIZE):
    """Splits text into chunks of max_size bytes."""
    chunks = []
    while len(text.encode("utf-8")) > max_size:
        split_index = text.rfind(".", 0, max_size)
        if split_index == -1:
            split_index = max_size  # If no period is found, force split
        chunks.append(text[:split_index + 1])
        text = text[split_index + 1:].lstrip()
    chunks.append(text)
    return chunks

def generate_speech(text_chunks, voice="en-GB-Standard-D", speed=1.0, format="MP3"):
    """Generates speech for text chunks using Google TTS API and saves audio files."""
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={GOOGLE_TTS_API_KEY}"
    headers = {"Content-Type": "application/json"}
    audio_files = []

    for i, chunk in enumerate(text_chunks):
        data = {
            "input": {"text": chunk},
            "voice": {"languageCode": "en-GB", "name": voice, "ssmlGender": "MALE"},
            "audioConfig": {"audioEncoding": format, "speakingRate": speed}
        }

        response = requests.post(url, headers=headers, json=data)
        print(f"🔍 API Response {i}: {response.status_code}")

        if response.status_code == 200:
            response_json = response.json()
            audio_content = response_json.get("audioContent")

            if not audio_content:
                print(f"❌ Error: No audio content received for chunk {i}")
                continue

            try:
                decoded_audio = base64.b64decode(audio_content, validate=True)
                file_ext = "ogg" if format == "OGG_OPUS" else "mp3"
                file_name = f"output_part_{i}.{file_ext}"

                with open(file_name, "wb") as f:
                    f.write(decoded_audio)

                print(f"✅ Chunk {i} saved as {file_name}")
                audio_files.append(file_name)

                # Test if chunk is valid
                validate_audio_file(file_name)

            except Exception as e:
                print(f"❌ Base64 decoding error for chunk {i}: {e}")
                continue

        else:
            print(f"❌ API Error {i}: {response.text}")
            return

    return merge_audio_files(audio_files, format)

def merge_audio_files(audio_files, format):
    """Merges multiple MP3 files into one using ffmpeg and uploads to GCS."""
    output_file = f"./data/output.{format.lower()}"
    output_blob_name = f"tts_output.{format.lower()}"  # Name in GCS

    if not audio_files:
        print("❌ No valid audio files to merge.")
        return None

    # Check if all chunk files exist before merging
    for file in audio_files:
        if not os.path.exists(file):
            print(f"❌ Missing chunk file: {file}. Merging will fail.")
            return None

    concat_list = "./data/concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for file in audio_files:
            absolute_path = os.path.abspath(file)
            print(f"✅ Adding file: {absolute_path}")
            f.write(f"file '{absolute_path}'\n")

    command = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", output_file, "-y"
    ]

    print("🔄 Merging files using ffmpeg...")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print(f"✅ Successfully merged into {output_file}")
    else:
        print(f"❌ ffmpeg merge failed. Falling back to pydub.\nError: {result.stderr.decode()}")
        merge_audio_files_pydub(audio_files, output_file)
        if not os.path.exists(output_file):
            return None

    # Upload to Google Cloud Storage
    blob = bucket.blob(output_blob_name)
    blob.upload_from_filename(output_file)
    print(f"✅ Uploaded {output_file} to GCS as {output_blob_name}")
    blob.make_public()  # Make it publicly accessible for HeyGen
    public_url = blob.public_url
    print(f"📎 Public URL: {public_url}")

    # Cleanup
    os.remove(concat_list)
    for file in audio_files:
        os.remove(file)
    if os.path.exists(output_file):
        os.remove(output_file)

    return public_url

def merge_audio_files_pydub(audio_files, output_file):
    """Fallback merging using pydub if ffmpeg fails."""
    print("🔄 Merging files using pydub...")
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=500)  # 0.5-second pause between parts

    for file in audio_files:
        if os.path.exists(file):
            combined += AudioSegment.from_file(file, format="mp3") + pause
            os.remove(file)
        else:
            print(f"❌ Skipping missing file: {file}")

    combined.export(output_file, format="mp3")
    print(f"✅ Successfully merged using pydub. File saved as {output_file}")

def validate_audio_file(file_path):
    """Checks if the MP3 or OGG file is valid and playable."""
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{file_path}' not found.")
        return

    file_size = os.path.getsize(file_path)
    print(f"📂 File Size: {file_size} bytes")

    if file_size == 0:
        print("❌ The audio file is empty.")
        return

    try:
        audio = AudioSegment.from_file(file_path)
        print(f"✅ Audio file is valid! Duration: {len(audio) / 1000:.2f} seconds")
    except Exception as e:
        print(f"❌ Invalid audio file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python google_tts_fixed.py <path_to_text_file> [MP3 or OGG_OPUS]")
        sys.exit(1)

    file_path = sys.argv[1]
    format = sys.argv[2] if len(sys.argv) > 2 else "MP3"  # Default to MP3

    text_content = read_text_file(file_path)

    if text_content:
        text_chunks = split_text(text_content)
        public_url = generate_speech(text_chunks, format=format)
        if public_url:
            print(f"🎉 Final audio URL: {public_url}")
        else:
            print("❌ Failed to generate or upload audio.")
    
    # Validate output file (optional, since it's uploaded and removed locally)
    # validate_audio_file(f"./data/output.{format.lower()}")