# server.py

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os

app = FastAPI()

# Define a directory to save the uploaded files
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Endpoint for file upload
@app.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_location = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return JSONResponse(content={"message": f"File uploaded successfully at {file_location}"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

# If running this script, the FastAPI server will start
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
