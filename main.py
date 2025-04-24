from fastapi import FastAPI, Query, BackgroundTasks
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
def download_video(background_tasks: BackgroundTasks, url: str = Query(...), format: str = Query("mp4")):
    file_id = str(uuid.uuid4())
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    # Pengaturan untuk yt-dlp
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
        'socket_timeout': 3600,  # Timeout 1 jam untuk koneksi
        'noplaylist': True,  # Hindari mengunduh playlist besar (optional)
    }

    # Fungsi untuk mengunduh video di latar belakang
    def download_task():
        try:
            # Mengunduh video dengan yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Cari file hasil download (cocokkan ekstensi yang benar)
            for file in os.listdir(DOWNLOAD_DIR):
                if file.startswith(file_id) and file.endswith(f".{format}"):
                    filepath = os.path.join(DOWNLOAD_DIR, file)
                    # Kirim file ke user setelah selesai
                    return FileResponse(filepath, media_type="application/octet-stream", filename=file)

        except Exception as e:
            print(f"Gagal mengunduh: {str(e)}")
            return {"error": f"Gagal mengunduh: {str(e)}"}

    # Menambahkan tugas download ke latar belakang
    background_tasks.add_task(download_task)

    return {"message": "Download dimulai, tunggu beberapa saat untuk menerima file."}
