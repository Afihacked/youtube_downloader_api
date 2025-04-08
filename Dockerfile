FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Install dependencies
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# Jalankan FastAPI dengan Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
