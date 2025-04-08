# Menggunakan image dasar Python yang ringan
FROM python:3.11-slim

# Mengatur variabel lingkungan untuk mencegah buffer output
ENV PYTHONUNBUFFERED=1

# Memperbarui daftar paket dan menginstal ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Menetapkan direktori kerja
WORKDIR /app

# Menyalin file requirements.txt dan menginstal dependensi Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin semua file proyek ke dalam container
COPY . .

# Menjalankan aplikasi FastAPI menggunakan Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
