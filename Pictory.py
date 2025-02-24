import re
import json
import os
from mutagen.mp3 import MP3

# Ask the user for file paths
script_file = input("Enter the path to your script file (e.g., script.txt): ").strip()
audio_file = input("Enter the path to your audio file (e.g., audio.mp3): ").strip()

# Define output paths
illustration_output_path = "./data/illustrations.json"
clean_script_output_path = "./data/clean_script.txt"

# Ensure the data directory exists
os.makedirs("./data", exist_ok=True)

# Read the script file
try:
    with open(script_file, "r", encoding="utf-8") as file:
        script_content = file.read()
except FileNotFoundError:
    print(f"Error: The file '{script_file}' was not found.")
    exit(1)

# Extract illustrations using regex
illustrations = re.findall(r"\(\( Illustration: (.*?) \)\)", script_content)

# Remove all illustration markers from script
clean_script = re.sub(r"\(\( Illustration: .*? \)\)", "", script_content)

# Get the length of the audio file in seconds
audio_duration = None
try:
    audio = MP3(audio_file)
    audio_duration = audio.info.length  # Length in seconds
except FileNotFoundError:
    print(f"Error: The file '{audio_file}' was not found.")
    exit(1)
except Exception as e:
    print(f"Could not determine audio duration: {e}")

# Save illustrations to JSON file in ./data/
illustration_output = {"illustrations": illustrations}
with open(illustration_output_path, "w", encoding="utf-8") as file:
    json.dump(illustration_output, file, indent=4)

# Save cleaned script for Pictory AI
with open(clean_script_output_path, "w", encoding="utf-8") as file:
    file.write(clean_script)

# Print extracted data
print(f"\nIllustrations saved to: {illustration_output_path}")
print(f"Clean script saved as: {clean_script_output_path}")

if audio_duration:
    print(f"Audio duration: {audio_duration:.2f} seconds")
else:
    print("Audio duration could not be determined.")
