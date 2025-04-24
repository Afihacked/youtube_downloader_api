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
        'merge_output_format': format,
        'socket_timeout': 3600,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if format == "mp3" else []
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info_dict)

            # Cek jika file sudah berubah menjadi .mp4/mp3
            if format == "mp4" and not final_filename.endswith(".mp4"):
                final_filename = os.path.splitext(final_filename)[0] + ".mp4"
            elif format == "mp3" and not final_filename.endswith(".mp3"):
                final_filename = os.path.splitext(final_filename)[0] + ".mp3"

        if os.path.exists(final_filename):
            return FileResponse(
                final_filename,
                media_type="application/octet-stream",
                filename=os.path.basename(final_filename)
            )
        else:
            return {"error": f"File hasil tidak ditemukan: {final_filename}"}
    except Exception as e:
        return {"error": f"Gagal mengunduh: {str(e)}"}
