import cv2
import numpy as np
import os
import subprocess

# Input and Output Paths
INPUT_VIDEO = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\avatar_video.mp4"
TEMP_VIDEO = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\temp_cropped.mp4"
OUTPUT_VIDEO = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\final_cropped_avatar.mp4"
AUDIO_FILE = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\original_audio.aac"

# Global variables for cropping
ref_point = []
cropping = False

def click_and_crop(event, x, y, flags, param):
    """ Mouse callback function to select the square crop area """
    global ref_point, cropping, frame

    if event == cv2.EVENT_LBUTTONDOWN:
        ref_point = [(x, y)]
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        ref_point.append((x, y))
        cropping = False

        # Draw a white rectangle on the preview frame
        preview = frame.copy()
        cv2.rectangle(preview, ref_point[0], ref_point[1], (255, 255, 255), 2)
        cv2.imshow("Select Crop Area", preview)

# Open the video and grab the first frame for selection
cap = cv2.VideoCapture(INPUT_VIDEO)
ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ Error: Couldn't read the video file!")
    exit()

cv2.imshow("Select Crop Area", frame)
cv2.setMouseCallback("Select Crop Area", click_and_crop)

print("🖱️ Select the area with your mouse (click and drag to define a square) and press 'Enter' when done.")
cv2.waitKey(0)
cv2.destroyAllWindows()

if len(ref_point) < 2:
    print("❌ No selection made. Exiting.")
    exit()

# Get crop dimensions
x1, y1 = ref_point[0]
x2, y2 = ref_point[1]
width = abs(x2 - x1)
height = abs(y2 - y1)

# ---- STEP 1: Crop Video ----
print("✂️ Cropping video...")
crop_cmd = [
    "ffmpeg", "-i", INPUT_VIDEO,
    "-vf", f"crop={width}:{height}:{min(x1, x2)}:{min(y1, y2)}",
    "-c:v", "libx264", "-c:a", "aac", "-y", TEMP_VIDEO
]
subprocess.run(crop_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"✅ Cropped video saved to {TEMP_VIDEO}")

# ---- STEP 2: Extract Original Audio ----
print("🔊 Extracting original audio...")
ffmpeg_extract_audio = [
    "ffmpeg", "-i", INPUT_VIDEO, "-vn", "-acodec", "copy", "-y", AUDIO_FILE
]
subprocess.run(ffmpeg_extract_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"✅ Extracted audio: {AUDIO_FILE}")

# ---- STEP 3: Merge Cropped Video with Audio ----
print("🎬 Merging cropped video with audio...")
ffmpeg_merge = [
    "ffmpeg", "-i", TEMP_VIDEO, "-i", AUDIO_FILE,
    "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental", "-y", OUTPUT_VIDEO
]
subprocess.run(ffmpeg_merge, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print(f"✅ Final cropped video with audio: {OUTPUT_VIDEO}")
