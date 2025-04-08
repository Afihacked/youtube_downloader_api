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

    # Opsi untuk MP3
    if format == "mp3":
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': filepath,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ],
            'ffmpeg_location': '/usr/bin/ffmpeg',  # lokasi umum ffmpeg di image
        }
    else:
        # Opsi untuk video (mp4)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': filepath,
            'merge_output_format': 'mp4',
            'ffmpeg_location': '/usr/bin/ffmpeg',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return FileResponse(filepath, media_type="application/octet-stream", filename=filename)
    except Exception as e:
        return {"error": str(e)}
