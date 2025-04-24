from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import yt_dlp
import uuid
import os
import shutil

app = FastAPI()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_PATH = shutil.which("ffmpeg")  # Lokasi ffmpeg

@app.get("/")
def root():
    return {"message": "YouTube Downloader API is running"}

@app.get("/download")
def download_video(url: str = Query(...), format: str = Query("mp4")):
    file_id = str(uuid.uuid4())
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    ydl_opts = {
        'outtmpl': outtmpl,
        'format': 'bestaudio/best' if format == "mp3" else 'bestvideo+bestaudio/best',
        'ffmpeg_location': FFMPEG_PATH,
        'merge_output_format': format,  # Paksa output ke .mp4
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format == "mp3" else []
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Cari file hasil download (cocokkan ekstensi yang benar)
        for file in os.listdir(DOWNLOAD_DIR):
            if file.startswith(file_id) and file.endswith(f".{format}"):
                filepath = os.path.join(DOWNLOAD_DIR, file)
                return FileResponse(filepath, media_type="application/octet-stream", filename=file)

        return {"error": f"File .{format} tidak ditemukan setelah download"}
    except Exception as e:
        return {"error": f"Gagal mengunduh: {str(e)}"}
