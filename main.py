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

# Path untuk file cookies (gunakan format Netscape: .txt, bukan JSON)
COOKIES_PATH = os.path.join(os.path.dirname(__file__), "cookies.txt")

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
        'merge_output_format': format,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format == "mp3" else [],
        'socket_timeout': 3600,
        'noplaylist': True,
        'cookiefile': COOKIES_PATH  # Pastikan file cookies.txt format Netscape
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for file in os.listdir(DOWNLOAD_DIR):
            if file.startswith(file_id) and file.endswith(f".{format}"):
                filepath = os.path.join(DOWNLOAD_DIR, file)
                return FileResponse(filepath, media_type="application/octet-stream", filename=file)

        return {"error": f"File .{format} tidak ditemukan setelah download"}
    except Exception as e:
        return {"error": f"Gagal mengunduh: {str(e)}"}
