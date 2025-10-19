# Document Parser Service

Универсальный парсер документов РФ (Паспорт / Водительское удостоверение / СТС) с использованием PassportEye (MRZ), pdf417decoder и Tesseract OCR.

## Поддерживаемые документы

- **Паспорт РФ**: PassportEye (MRZ) → Tesseract OCR (fallback)
- **Водительское удостоверение**: PDF417 декодер → Tesseract OCR (fallback)
- **СТС**: PDF417 декодер → Tesseract OCR (fallback)

## Деплой

### Railway.app (рекомендуется)

```bash
cd document_parser_service
railway login
railway init
railway up
```

После деплоя получите URL вида: `https://document-parser-production.up.railway.app`

### Google Cloud Run

```bash
gcloud run deploy document-parser \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 60s
```

### Render.com

1. Создайте новый Web Service
2. Подключите GitHub репозиторий
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT --workers 2`

### Docker (локально для тестирования)

```bash
docker build -t document-parser .
docker run -p 8000:8000 document-parser
```

URL: `http://localhost:8000`

## Настройка Supabase

После деплоя добавьте секрет в Supabase:

```
DOCUMENT_PARSER_SERVICE_URL=https://your-service-url.railway.app
```

## API

### POST /parse

**Параметры:**
- `file`: изображение документа
- `doc_type`: тип документа (`passport`, `driver_license`, `sts`)

**Ответ:**
```json
{
  "success": true,
  "document_type": "passport",
  "method": "mrz",
  "confidence": 98,
  "data": {
    "full_name": "IVANOV IVAN",
    "passport_number": "123456789",
    "birth_date": "1990-01-01",
    "nationality": "RUS"
  }
}
```

### GET /health

Проверка работоспособности сервиса.

## Точность распознавания

| Документ | Метод | Точность |
|----------|-------|----------|
| Паспорт РФ | MRZ (PassportEye) | ~98% |
| Паспорт РФ | OCR (fallback) | ~70% |
| ВУ РФ | PDF417 | ~95% |
| ВУ РФ | OCR (fallback) | ~50% |
| СТС | PDF417 | ~95% |
| СТС | OCR (fallback) | ~55% |
