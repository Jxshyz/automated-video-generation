import subprocess
import os

# Paths
SLIDES_VIDEO = "./data/final_slides_video.mp4"
AVATAR_VIDEO = "./data/final_cropped_avatar.mp4"
OUTPUT_VIDEO = "./data/final_combined_video.mp4"

# Avatar Overlay Settings
AVATAR_WIDTH = 800  # Doubled the width
AVATAR_HEIGHT = 490  # Kept the same height
X_POS = "5"  # Position from left (pixels)
Y_POS = "5"  # Slightly higher position from the top

# FFmpeg command to overlay avatar and control duration
ffmpeg_cmd = [
    "ffmpeg",
    "-i", SLIDES_VIDEO,  # Input: Slides video
    "-i", AVATAR_VIDEO,  # Input: Avatar video
    "-filter_complex",
    f"[1:v]scale={AVATAR_WIDTH}:{AVATAR_HEIGHT}[avatar];"
    f"[0:v][avatar] overlay={X_POS}:{Y_POS}:enable='lte(t,367)' [outv]",  # Avatar disappears after 367s
    "-map", "[outv]",  # Use the overlayed video
    "-map", "1:a",  # Use avatar's audio
    "-t", "367",  # Trim audio to match avatar duration
    "-c:v", "libx264",  # Video codec
    "-c:a", "aac",  # Audio codec
    "-y", OUTPUT_VIDEO  # Overwrite output file
]

# Run FFmpeg
print(f"🎬 Combining avatar and slides into {OUTPUT_VIDEO}...")
result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Check for errors
if result.returncode == 0:
    print(f"✅ Successfully created video: {OUTPUT_VIDEO}")
else:
    print(f"❌ FFmpeg error:\n{result.stderr.decode()}")
