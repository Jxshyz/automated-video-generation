import subprocess
import os

def concatenate_videos(input_videos, output_video):
    """Concatenate multiple video files into one with sound."""
    # Check if all input files exist
    for video in input_videos:
        if not os.path.exists(video):
            print(f"❌ Input video {video} not found!")
            return False

    # Build FFmpeg command with video and audio
    filter_complex = "".join(f"[{i}:v][{i}:a]" for i in range(len(input_videos))) + f"concat=n={len(input_videos)}:v=1:a=1[outv][outa]"
    command = ['ffmpeg'] + sum([['-i', video] for video in input_videos], []) + [
        '-filter_complex', filter_complex,
        '-map', '[outv]',           # Map video output
        '-map', '[outa]',           # Map audio output
        '-c:v', 'libx264',          # Re-encode video
        '-c:a', 'aac',              # Re-encode audio
        '-y',                       # Overwrite output
        output_video
    ]

    print(f"Running FFmpeg command: {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print(f"✅ Successfully concatenated videos with sound: {output_video}")
        return True
    else:
        print(f"❌ Error during concatenation: {result.stderr.decode()}")
        return False

if __name__ == "__main__":
    # Input videos
    input_videos = [
        "./data/avatar_part1.mp4",
        "./data/avatar_part2.mp4",
        "./data/avatar_part3.mp4"
    ]
    output_video = "./data/final_avatar_video.mp4"

    # Run concatenation
    concatenate_videos(input_videos, output_video)