import requests
import os
import re
import sys
import base64
import subprocess
from dotenv import load_dotenv
from pydub import AudioSegment

# Load API key from .env file
load_dotenv("credentials.env")
GOOGLE_TTS_API_KEY = os.getenv("GOOGLE_TTS_API_KEY")
MAX_TTS_CHUNK_SIZE = 5000  # Google TTS API limit

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

    merge_audio_files(audio_files, format)

def merge_audio_files(audio_files, format):
    """Merges multiple MP3 files into one using ffmpeg. Falls back to pydub if ffmpeg fails."""
    output_file = f"./data/output.{format.lower()}"

    if not audio_files:
        print("❌ No valid audio files to merge.")
        return

    # Check if all chunk files exist before merging
    for file in audio_files:
        if not os.path.exists(file):
            print(f"❌ Missing chunk file: {file}. Merging will fail.")
            return

    concat_list = "./data/concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for file in audio_files:
            absolute_path = os.path.abspath(file)
            print(f"✅ Adding file: {absolute_path}")  # Debugging
            f.write(f"file '{absolute_path}'\n")  # Use absolute paths for ffmpeg

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

    # Cleanup
    os.remove(concat_list)
    for file in audio_files:
        os.remove(file)

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
        generate_speech(text_chunks, format=format)

    # Validate output file
    validate_audio_file(f"./data/output.{format.lower()}")
