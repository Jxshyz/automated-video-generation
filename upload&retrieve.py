import os

# Setze die Umgebungsvariable, wenn sie noch nicht gesetzt ist
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\eprot\\buoyant-airport-451611-d4-0e7f2929f9e6.json"

from google.cloud import storage

# Erstelle einen Storage-Client
storage_client = storage.Client()

print(storage_client.project)

# Der Name deines Buckets
bucket_name = "mein-uni-bucket-2025"

# Hole den Bucket
bucket = storage_client.get_bucket(bucket_name)

# Die Dateien, die du hochladen möchtest
files_to_upload = ["./data/audio_part1.wav", "./data/audio_part2.wav", "./data/audio_part3.wav"]

# Liste, um die URLs der hochgeladenen Dateien zu speichern
uploaded_file_urls = []

# Lade jede Datei in den Bucket hoch
for file_path in files_to_upload:
    # Extrahiere den Dateinamen aus dem Pfad
    file_name = os.path.basename(file_path)
    
    # Erstelle ein Blob (Dateiobjekt) im Bucket
    blob = bucket.blob(file_name)
    
    # Lade die Datei hoch
    blob.upload_from_filename(file_path)
    print(f"Datei {file_path} wurde erfolgreich hochgeladen.")
    
    # Erstelle die öffentlich zugängliche URL für die Datei
    blob_url = f"https://storage.googleapis.com/{bucket_name}/{file_name}"
    uploaded_file_urls.append(blob_url)

# Zeige die URLs der hochgeladenen Dateien
for url in uploaded_file_urls:
    print(f"Datei erreichbar unter: {url}")
