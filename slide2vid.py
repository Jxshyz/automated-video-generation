import os
import re
import subprocess
from pdf2image import convert_from_path

# Paths
SLIDES_DIR = "./data/slides"
IMAGES_DIR = "./data/slides_images"
OUTPUT_VIDEO = "./data/final_slides_video.mp4"
SLIDES_LIST_FILE = os.path.join(IMAGES_DIR, "slides_list.txt")

# Video properties
FPS = 30  # Frames per second

# Correct slide durations (in seconds)
slide_durations = [
    23, 32, 20, 22, 18, 29, 18, 15, 26, 24, 18,
    13, 8, 24, 20, 17, 16, 17, 7  # Total: 367s
]

def extract_slide_number(filename):
    """Extract numerical slide number from filename."""
    match = re.search(r"slide_(\d+)", filename)
    return int(match.group(1)) if match else float('inf')

def convert_slides_to_images():
    """Convert PDF slides to images and use JPEGs directly."""
    slide_files = sorted(
        [f for f in os.listdir(SLIDES_DIR) if f.lower().endswith((".pdf", ".jpg", ".jpeg"))],
        key=lambda x: extract_slide_number(x)  # Sort numerically
    )

    print(f"📂 Found {len(slide_files)} slide files:")
    for f in slide_files:
        print(f"   - {f}")

    image_files = []
    for slide in slide_files:
        slide_path = os.path.join(SLIDES_DIR, slide)
        image_filename = os.path.join(IMAGES_DIR, f"{os.path.splitext(slide)[0]}.png")

        if slide.lower().endswith(".pdf"):
            if os.path.exists(image_filename):
                print(f"⏭️ Skipping already converted {slide}")
            else:
                images = convert_from_path(slide_path, dpi=300)
                images[0].save(image_filename, "PNG")
                print(f"📷 Converted {slide} -> {image_filename}")
        else:
            if not os.path.exists(image_filename):
                os.rename(slide_path, image_filename)
            print(f"🖼 Using existing JPEG: {slide}")

        image_files.append(os.path.abspath(image_filename))  # Store absolute path

    return image_files

def create_video_from_slides(image_files):
    """Create a video from slide images using FFmpeg."""
    num_slides = len(image_files)
    expected_slides = len(slide_durations)

    print(f"📊 Slides Detected: {num_slides}, Expected Durations: {expected_slides}")

    if num_slides != expected_slides:
        print(f"❌ ERROR: Found {num_slides} slides but expected {expected_slides}. Check missing files!")
        return False

    # Create FFmpeg input file
    with open(SLIDES_LIST_FILE, "w", encoding="utf-8") as f:
        for img, duration in zip(image_files, slide_durations):
            f.write(f"file '{img.replace(os.sep, '/')}'\n")
            f.write(f"duration {duration:.2f}\n")

    # Ensure last slide is displayed
    with open(SLIDES_LIST_FILE, "a", encoding="utf-8") as f:
        f.write(f"file '{image_files[-1].replace(os.sep, '/')}'\n")

    print(f"🎬 Creating video with FFmpeg (Total Duration: {sum(slide_durations)}s)...")

    # Run FFmpeg
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", SLIDES_LIST_FILE,
        "-vf", f"fps={FPS},format=yuv420p",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-y", OUTPUT_VIDEO
    ]

    result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print(f"✅ Successfully created video: {OUTPUT_VIDEO}")
        return True
    else:
        print(f"❌ FFmpeg error:\n{result.stderr.decode()}")
        return False

def main():
    """Main execution function."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    image_files = convert_slides_to_images()
    if image_files:
        create_video_from_slides(image_files)

if __name__ == "__main__":
    main()
