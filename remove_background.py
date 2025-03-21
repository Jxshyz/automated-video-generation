import cv2
import numpy as np
import subprocess
import os
import time
import glob
import shutil

# Input and Output Paths
INPUT_VIDEO = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\cropped_avatar.mp4"
TEMP_FRAMES_DIR = r"C:\temp_frames_transparent"  # Moved to a local path
OUTPUT_VIDEO = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\transparent_avatar_prores_5s.mov"
OUTPUT_VIDEO_WEBM = r"C:\Users\eprot\OneDrive - Hochschule Düsseldorf\Dokumente\Uni\6. Semester (NO)\CV and DL\automated-video-generation\data\transparent_avatar_5s.webm"

# Ensure temp frames directory exists
if os.path.exists(TEMP_FRAMES_DIR):
    shutil.rmtree(TEMP_FRAMES_DIR, ignore_errors=True)  # Clean up any existing directory
os.makedirs(TEMP_FRAMES_DIR, exist_ok=True)

# Check disk space
def check_disk_space(path):
    total, used, free = shutil.disk_usage(path)
    free_gb = free / (1024 ** 3)  # Convert to GB
    print(f"[+] Disk space check: {free_gb:.2f} GB free on drive containing {path}")
    return free_gb > 1  # Ensure at least 1 GB free

def make_background_transparent(input_path, temp_dir, output_path_prores, output_path_webm, duration_secs=5, color_to_remove=(0, 0, 0), threshold=20):
    """
    Process the first 'duration_secs' of a video to make the black background transparent.
    Saves frames as PNGs with alpha channel, then compiles them into ProRes and WebM videos.
    Args:
        input_path (str): Path to input video.
        temp_dir (str): Directory to save temporary frames.
        output_path_prores (str): Path to save ProRes output video.
        output_path_webm (str): Path to save WebM output video.
        duration_secs (int): Duration to process in seconds.
        color_to_remove (tuple): RGB color to remove (default: black #000000).
        threshold (int): Color matching threshold.
    """
    # Check disk space
    if not check_disk_space(temp_dir):
        print(f"❌ Error: Insufficient disk space on drive containing {temp_dir}.")
        return

    # Check if input video exists
    if not os.path.exists(input_path):
        print(f"❌ Error: Input video '{input_path}' not found.")
        return

    # Open the video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video '{input_path}'.")
        return

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate frames to process for the first 5 seconds
    frames_to_process = min(int(fps * duration_secs), total_frames)

    print(f"🎥 Processing first {duration_secs} seconds ({frames_to_process} frames) to make background transparent...")

    frame_idx = 0
    debug_frame_saved = False
    while cap.isOpened() and frame_idx < frames_to_process:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to RGB for accurate color detection (OpenCV uses BGR)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create a mask for the color to remove
        lower_bound = np.array([max(0, c - threshold) for c in color_to_remove])
        upper_bound = np.array([min(255, c + threshold) for c in color_to_remove])
        mask = cv2.inRange(frame_rgb, lower_bound, upper_bound)

        # Invert mask: 0 where we want transparency, 255 elsewhere
        mask = cv2.bitwise_not(mask)

        # Convert frame to RGBA (add alpha channel)
        frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

        # Set alpha channel based on mask
        frame_rgba[:, :, 3] = mask  # Alpha channel: 0 = transparent, 255 = opaque

        # Save frame as PNG (which supports transparency)
        frame_path = os.path.join(temp_dir, f"frame_{frame_idx:04d}.png")
        success = cv2.imwrite(frame_path, frame_rgba)
        if not success:
            print(f"❌ Failed to save frame {frame_path}. Check permissions or disk space.")
            break

        # Save one frame for debugging
        if not debug_frame_saved and frame_idx == 100:
            debug_frame_path = "debug_frame_transparent_5s.png"
            success = cv2.imwrite(debug_frame_path, frame_rgba)
            if success:
                print(f"[+] Saved debug frame to {debug_frame_path} for transparency check.")
            else:
                print(f"❌ Failed to save debug frame {debug_frame_path}.")
            debug_frame_saved = True

        frame_idx += 1
        if frame_idx % 50 == 0:
            print(f"[+] Processed {frame_idx}/{frames_to_process} frames...")

    # Release video capture
    cap.release()
    cv2.destroyAllWindows()

    print(f"[+] Processed {frame_idx} frames.")

    # Check if frames were saved
    saved_frames = glob.glob(os.path.join(temp_dir, "frame_*.png"))
    if not saved_frames:
        print(f"❌ Error: No frames were saved in {temp_dir}. Check permissions or disk space.")
        return
    print(f"[+] Found {len(saved_frames)} frames in {temp_dir}.")

    # Use FFmpeg to compile frames into a ProRes video with transparency
    try:
        ffmpeg_cmd = (
            f'ffmpeg -framerate {fps} -i "{temp_dir}\\frame_%04d.png" '
            f'-c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le -r {fps} "{output_path_prores}" -y'
        )
        result = subprocess.run(ffmpeg_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[+] Created ProRes MOV with transparent background: {output_path_prores}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error (ProRes):\n{e.stderr.decode()}")

    # Try WebM with VP9 as a fallback
    try:
        ffmpeg_cmd_webm = (
            f'ffmpeg -framerate {fps} -i "{temp_dir}\\frame_%04d.png" '
            f'-c:v libvpx-vp9 -pix_fmt yuva420p -r {fps} "{output_path_webm}" -y'
        )
        result = subprocess.run(ffmpeg_cmd_webm, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[+] Created WebM with transparent background: {output_path_webm}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error (WebM):\n{e.stderr.decode()}")

    # Cleanup temporary directory
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)
                print(f"[+] Cleaned up temporary directory: {temp_dir}")
            break
        except Exception as e:
            print(f"[!] Attempt {attempt + 1}/{max_attempts} to clean up {temp_dir} failed: {str(e)}")
            time.sleep(1)  # Wait 1 second before retrying
    else:
        print(f"[!] Failed to clean up {temp_dir} after {max_attempts} attempts. Please delete manually.")

if __name__ == "__main__":
    # Process the first 5 seconds of the cropped video to make the background transparent
    make_background_transparent(INPUT_VIDEO, TEMP_FRAMES_DIR, OUTPUT_VIDEO, OUTPUT_VIDEO_WEBM, duration_secs=5, color_to_remove=(0, 0, 0), threshold=20)

    print("\n[+] Video processing complete.")
    print("[+] Open 'debug_frame_transparent_5s.png' in an image editor (e.g., Photoshop, GIMP) to verify the background is transparent (checkered pattern).")
    print("[+] Test the ProRes output (transparent_avatar_prores_5s.mov) or WebM output (transparent_avatar_5s.webm) in a video editor that supports transparency (e.g., Adobe Premiere, DaVinci Resolve).")