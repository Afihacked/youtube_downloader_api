FROM python:3.11-slim

ARG PORT
ENV PORT=${PORT}

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Menambahkan timeout-keep-alive di sini
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "600"]
