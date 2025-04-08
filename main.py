from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import yt_dlp
import uuid
import os

app = FastAPI()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "YouTube Downloader API is running"}

@app.get("/download")
def download_video(url: str = Query(...), format: str = Query("mp4")):
    filename = f"{uuid.uuid4()}.{format}"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if format == "mp3":
        # Download audio langsung tanpa ffmpeg
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [],  # ffmpeg akan kita hindari
        }
    else:
        # Untuk video biasa
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best',
            'postprocessors': []
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return FileResponse(filepath, media_type="application/octet-stream", filename=filename)
    except Exception as e:
        return {"error": str(e)}
