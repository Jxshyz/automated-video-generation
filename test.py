import gdown

def download_audio_file_from_google_drive(file_url, output_filename):
    print(f"Attempting to download file from: {file_url}")
    
    try:
        gdown.download(file_url, output_filename, quiet=False)
        print(f"File successfully downloaded and saved as {output_filename}")
    except Exception as e:
        print(f"Error downloading file: {e}")

# Replace these with your Google Drive file links
file_url_1 = "https://drive.google.com/uc?id=1cCWo0K28CB-0AMI2Lp0Tozk9bwc_4S-e&export=download"
download_audio_file_from_google_drive(file_url_1, "audio_part1.wav")
