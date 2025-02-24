from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
import requests
import os
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Load API keys from .env file
load_dotenv("credentials.env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
D_ID_API_KEY = os.getenv("D_ID_API_KEY")  # Free AI avatar generator
GOOGLE_TTS_API_KEY = os.getenv("GOOGLE_TTS_API_KEY")  # Free text-to-speech
PICTORY_AI_KEY = os.getenv("PICTORY_AI_KEY")  # Free animated slide generator

app = FastAPI()

# Serve static files and HTML templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def render_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "video_url": None})

@app.post("/generate_video/")
def generate_video(
    request: Request,
    topic: str = Form(...),
    voice: str = Form(...),
    emotion: str = Form(...),
    speed: float = Form(...),
    length: int = Form(...),
    avatar_gender: str = Form(...),
    avatar_skin_color: str = Form(...),
    avatar_hair: str = Form(...),
    avatar_eyes: str = Form(...)
):
    """Generates a presentation-style video using free AI APIs"""

    # 1️⃣ OpenAI: Generate structured script
    openai_response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        json={
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "Generate a structured, engaging script for a video presentation with key points and summaries."},
                {"role": "user", "content": f"Create a presentation video script about {topic}."}
            ]
        }
    )
    script = openai_response.json()["choices"][0]["message"]["content"]

    # 2️⃣ Google Cloud Text-to-Speech (Free Alternative to ElevenLabs)
    google_tts_response = requests.post(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        headers={"Authorization": f"Bearer {GOOGLE_TTS_API_KEY}"},
        json={
            "input": {"text": script},
            "voice": {"languageCode": "en-US", "name": voice, "ssmlGender": "NEUTRAL"},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": speed}
        }
    )
    audio_url = google_tts_response.json().get("audioContent")

    # 3️⃣ D-ID API for AI Avatar (Free Alternative to Synthesia)
    d_id_response = requests.post(
        "https://api.d-id.com/talks",
        headers={"Authorization": f"Bearer {D_ID_API_KEY}"},
        json={
            "script": script,
            "voice_url": audio_url,
            "avatar": {
                "gender": avatar_gender,
                "skin_color": avatar_skin_color,
                "hair": avatar_hair,
                "eyes": avatar_eyes
            }
        }
    )
    avatar_video_url = d_id_response.json().get("result_url")

    # 4️⃣ Pictory AI for Animated Slides (Free Alternative to Runway ML)
    pictory_response = requests.post(
        "https://api.pictory.ai/v1/generate-video",
        headers={"Authorization": f"Bearer {PICTORY_AI_KEY}"},
        json={
            "topic": topic,
            "script": script,
            "style": "presentation",
            "duration": length
        }
    )
    animation_video_url = pictory_response.json().get("video_url")

    # 5️⃣ OpenShot for Final Video Editing (Free Alternative to DaVinci Resolve)
    import openshot_api  # You need to install and set up OpenShot API

    final_video_path = f"/home/user/videos/{topic}_presentation.mp4"
    openshot_api.create_project(final_video_path)
    openshot_api.add_clip(final_video_path, avatar_video_url)
    openshot_api.add_clip(final_video_path, animation_video_url)
    openshot_api.export_video(final_video_path)

    return templates.TemplateResponse("index.html", {"request": request, "video_url": final_video_path})
