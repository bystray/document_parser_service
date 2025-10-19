FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libgl1 \
    libglib2.0-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Скачиваем OCRB traineddata для MRZ
RUN wget -O /usr/share/tesseract-ocr/5/tessdata/ocrb.traineddata \
    https://github.com/Shreeshrii/tessdata_ocrb/raw/master/ocrb.traineddata

WORKDIR /app

# Устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY app.py .

EXPOSE 8000

# Запускаем через uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
