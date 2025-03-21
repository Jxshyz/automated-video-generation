import cv2
import numpy as np
import os
import subprocess

# Input and Output Paths
INPUT_VIDEO = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\avatar_video.mp4"
TEMP_VIDEO = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\temp_cropped_video.avi"
OUTPUT_VIDEO = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\cropped_avatar.mp4"
AUDIO_FILE = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\original_audio.aac"

# Global variables for cropping
ref_point = []
cropping = False

def click_and_crop(event, x, y, flags, param):
    global ref_point, cropping, frame

    if event == cv2.EVENT_LBUTTONDOWN:
        ref_point = [(x, y)]
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        ref_point.append((x, y))
        cropping = False

        # Draw white circle outline on a copy of the frame
        radius = int(((ref_point[1][0] - ref_point[0][0])**2 + (ref_point[1][1] - ref_point[0][1])**2) ** 0.5 / 2)
        center = ((ref_point[0][0] + ref_point[1][0]) // 2, (ref_point[0][1] + ref_point[1][1]) // 2)

        preview = frame.copy()
        cv2.circle(preview, center, radius, (255, 255, 255), 2)  # White outline, thickness=2
        cv2.imshow("Select Avatar Area", preview)


# Open the video and grab the first frame for selection
cap = cv2.VideoCapture(INPUT_VIDEO)
ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ Error: Couldn't read the video file!")
    exit()

cv2.imshow("Select Avatar Area", frame)
cv2.setMouseCallback("Select Avatar Area", click_and_crop)

print("🖱️ Select the area with your mouse (click and drag to define a circle) and press 'Enter' when done.")
cv2.waitKey(0)
cv2.destroyAllWindows()

if len(ref_point) < 2:
    print("❌ No selection made. Exiting.")
    exit()

# Calculate crop center and radius
x1, y1 = ref_point[0]
x2, y2 = ref_point[1]
radius = int(((x2 - x1)**2 + (y2 - y1)**2) ** 0.5 / 2)
center = ((x1 + x2) // 2, (y1 + y2) // 2)

# Reopen the video for processing
cap = cv2.VideoCapture(INPUT_VIDEO)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Initialize VideoWriter for direct output
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Use AVI because MP4 with OpenCV won't store audio
out = cv2.VideoWriter(TEMP_VIDEO, fourcc, fps, (frame_width, frame_height))

print(f"🎥 Processing {frame_count} frames directly to {TEMP_VIDEO}...")

frame_idx = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Create a circular mask with alpha channel
    mask = np.zeros_like(frame, dtype=np.uint8)
    cv2.circle(mask, center, radius, (255, 255, 255), -1)

    # Apply mask to keep only the circular area
    cropped = cv2.bitwise_and(frame, mask)

    # Write the frame directly to the output video
    out.write(cropped)

    frame_idx += 1
    if frame_idx % 50 == 0:
        print(f"[+] Processed {frame_idx}/{frame_count} frames...")

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()

print(f"✅ Successfully created circular cropped video: {TEMP_VIDEO}")

# ---- STEP 2: Extract Audio ----
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

print(f"✅ Final video with audio: {OUTPUT_VIDEO}")
