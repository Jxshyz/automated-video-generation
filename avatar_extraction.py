import os

# Define video URL and output directory
video_url = "https://www.youtube.com/watch?v=qrvK_KuIeJk"
output_dir = os.path.abspath("./data")
os.makedirs(output_dir, exist_ok=True)

# File paths
input_video = os.path.join(output_dir, "Hinton.mp4")
webm_video = os.path.join(output_dir, "Hinton.webm")  # If yt-dlp downloads WebM
merged_output = os.path.join(output_dir, "Hinton_merged.mp4")
final_output = os.path.join(output_dir, "Hinton.mp4")  # Final renamed output
temp_list = os.path.join(output_dir, "file_list.txt")

# If the wrong file exists, rename it
if os.path.exists(webm_video):
    os.rename(webm_video, input_video)
    print("🔄 Renamed WebM file to MP4")

# Download video if it doesn't exist
if not os.path.exists(input_video):
    print("🎥 Downloading video...")
    os.system(f'yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best" -o "{input_video}" {video_url}')

# Verify if the file was downloaded
if not os.path.exists(input_video):
    print("❌ Error: Video download failed. Exiting.")
    exit(1)

print("✅ Video downloaded successfully!")

# Define segments (start time in seconds, duration in seconds)
segments = [
    (4 * 60 + 18, 24),  # 4:18 - 4:42
    (6 * 60 + 58, 19),  # 6:58 - 7:17
    (9 * 60 + 26, 9),   # 9:26 - 9:35
]

# Extract segments
clip_files = []
for i, (start_time, duration) in enumerate(segments):
    clip_file = os.path.join(output_dir, f"clip_{i + 1}.mp4")
    clip_files.append(clip_file)
    
    # Ensure FFmpeg properly extracts segments
    print(f"✂ Extracting segment {i + 1}...")
    extract_cmd = f'ffmpeg -i "{input_video}" -ss {start_time} -t {duration} -c copy "{clip_file}"'
    
    os.system(extract_cmd)

# Verify if clips exist
for clip in clip_files:
    if not os.path.exists(clip):
        print(f"❌ Error: Clip {clip} was not created! Exiting.")
        exit(1)

print("✅ All clips extracted successfully!")

# Create a list for merging
with open(temp_list, "w", encoding="utf-8") as f:
    for clip in clip_files:
        f.write(f"file '{clip.replace('\\', '/')}'\n")

# Merge clips
print("🔄 Merging clips into final video...")
merge_status = os.system(f'ffmpeg -f concat -safe 0 -i "{temp_list}" -c copy "{merged_output}"')

if merge_status != 0:
    print("❌ Error: Merging failed! Exiting.")
    exit(1)

print("✅ Merging completed!")

# Cleanup unnecessary files
print("🗑 Deleting temporary files...")
for clip in clip_files:
    os.remove(clip)
os.remove(temp_list)
os.remove(input_video)  # Delete the original downloaded video

# Rename the merged file to "Hinton.mp4"
os.rename(merged_output, final_output)

print(f"✅ Final video saved as: {final_output}")
