from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import uuid
import os
import shutil
from datetime import datetime

app = FastAPI()

BASE_DOWNLOAD_DIR = "downloads"
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

LOG_FILE = "download_logs.txt"
FFMPEG_PATH = shutil.which("ffmpeg")
COOKIES_PATH = os.path.join(os.path.dirname(__file__), "cookies.txt")


def cleanup_dir(path: str):
    try:
        shutil.rmtree(path)
    except Exception as e:
        print(f"Gagal hapus folder: {path} | Error: {e}")


@app.get("/")
def root():
    return {"message": "Downloader API is running"}


@app.get("/download")
def download_video(
    background_tasks: BackgroundTasks,
    url: str = Query(...),
    format: str = Query("mp4"),
    start: str = Query(None),
    end: str = Query(None),
    index: int = Query(None, description="Index media untuk carousel (opsional)"),
):
    session_id = str(uuid.uuid4())
    download_dir = os.path.join(BASE_DOWNLOAD_DIR, session_id)
    os.makedirs(download_dir, exist_ok=True)

    outtmpl = os.path.join(download_dir, f"{session_id}.%(ext)s")
    download_sections = f"*{start}-{end}" if start and end else None
    is_instagram = "instagram.com" in url

    ydl_opts = {
        'outtmpl': outtmpl,
        'ffmpeg_location': FFMPEG_PATH,
        'socket_timeout': 3600,
        'noplaylist': True,
        'cookiefile': COOKIES_PATH
    }

    if format == "mp3":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['merge_output_format'] = format
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = format

    if is_instagram:
        ydl_opts['format'] = 'best'
        ydl_opts.pop('merge_output_format', None)
        ydl_opts.pop('postprocessors', None)

        if index is not None:
            ydl_opts['playlist_items'] = str(index + 1)

    if download_sections:
        ydl_opts['download_sections'] = download_sections

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for file in os.listdir(download_dir):
            if file.startswith(session_id):
                filepath = os.path.join(download_dir, file)

                with open(LOG_FILE, "a", encoding="utf-8") as log_file:
                    log_file.write(f"{datetime.now().isoformat()} | {url} | {format} | {file}\n")

                background_tasks.add_task(cleanup_dir, download_dir)

                return FileResponse(
                    filepath,
                    media_type="application/octet-stream",
                    filename=file,
                    background=background_tasks
                )

        return {"error": "File hasil download tidak ditemukan"}
    except Exception as e:
        shutil.rmtree(download_dir, ignore_errors=True)
        return {"error": f"Gagal mengunduh: {str(e)}"}


@app.get("/info")
def video_info(url: str = Query(...), format: str = Query("mp4")):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'simulate': True,
        'forcejson': True,
        'format': 'bestaudio/best' if format == "mp3" else 'bestvideo+bestaudio/best',
        'cookiefile': COOKIES_PATH
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Tidak diketahui')
            filesize = 0

            formats = info.get('formats', [])
            valid_formats = [
                f for f in formats
                if f.get('filesize') is not None or f.get('filesize_approx') is not None
            ]

            if valid_formats:
                best_format = max(
                    valid_formats,
                    key=lambda f: (f.get('filesize', 0) or f.get('filesize_approx', 0))
                )
                filesize = best_format.get('filesize') or best_format.get('filesize_approx', 0)

            return {
                "title": title,
                "filesize": filesize,
                "type": info.get('ext', 'unknown'),
                "uploader": info.get('uploader'),
                "thumbnail": info.get('thumbnail')
            }
    except Exception as e:
        return {"error": f"Gagal mengambil info video: {str(e)}"}


@app.get("/carousel-info")
def carousel_info(url: str = Query(...)):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'simulate': True,
        'cookiefile': COOKIES_PATH,
        'extract_flat': False,
        'forcejson': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            entries = info.get('entries', [])
            if not entries:
                return {"error": "Bukan carousel / tidak ada beberapa media"}

            media_list = []
            for i, item in enumerate(entries):
                media_list.append({
                    "index": i,
                    "title": item.get('title', f"Media {i+1}"),
                    "url": item.get('url'),
                    "thumbnail": item.get('thumbnail'),
                    "ext": item.get('ext', 'jpg')
                })

            return {
                "type": "carousel",
                "media_count": len(media_list),
                "media": media_list
            }

    except Exception as e:
        return {"error": f"Gagal mengambil info carousel: {str(e)}"}
        
        @app.get("/download-carousel")
def download_all_carousel(
    background_tasks: BackgroundTasks,
    url: str = Query(...)
):
    session_id = str(uuid.uuid4())
    download_dir = os.path.join(BASE_DOWNLOAD_DIR, session_id)
    os.makedirs(download_dir, exist_ok=True)

    outtmpl = os.path.join(download_dir, f"{session_id}_%(autonumber)03d.%(ext)s")

    ydl_opts = {
        'outtmpl': outtmpl,
        'ffmpeg_location': FFMPEG_PATH,
        'format': 'best',
        'cookiefile': COOKIES_PATH,
        'noplaylist': True,
        'force_keyframes_at_cuts': True,
        'playlistend': 100,  # Batas maksimal (biasanya carousel <10)
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        zip_name = f"{session_id}.zip"
        zip_path = os.path.join(BASE_DOWNLOAD_DIR, zip_name)
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', download_dir)

        with open(LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(f"{datetime.now().isoformat()} | {url} | carousel-zip | {zip_name}\n")

        background_tasks.add_task(cleanup_dir, download_dir)

        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=zip_name,
            background=background_tasks
        )
    except Exception as e:
        shutil.rmtree(download_dir, ignore_errors=True)
        return {"error": f"Gagal mengunduh carousel: {str(e)}"}