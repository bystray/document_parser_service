# Локальное тестирование Document Parser Service

## Быстрый старт

### 1. Запуск приложения

```bash
# Установка зависимостей (если еще не установлены)
pip install fastapi uvicorn python-multipart pillow opencv-python-headless pytesseract passporteye pdf417decoder

# Запуск локальной версии (без Tesseract OCR)
python app_local.py

# Или запуск полной версии (требует Tesseract OCR)
python app.py
```

### 2. Проверка работы

Приложение будет доступно по адресу: `http://localhost:8000`

**Endpoints:**
- `GET /` - главная страница с информацией
- `GET /health` - проверка работоспособности
- `POST /parse` - парсинг документов
- `GET /docs` - интерактивная документация Swagger

### 3. Способы тестирования

#### A. Веб-интерфейс
Откройте в браузере:
- `http://localhost:8000/static/test_client.html` - тестовый клиент через веб-сервер
- Или откройте файл `test_client.html` напрямую из файловой системы

#### B. Командная строка
```bash
# Проверка health
python test_api.py

# Тестирование парсинга
python test_api.py path/to/image.jpg passport
python test_api.py path/to/image.jpg driver_license
python test_api.py path/to/image.jpg sts
```

#### C. curl/Postman
```bash
# Health check
curl http://localhost:8000/health

# Парсинг документа
curl -X POST "http://localhost:8000/parse" \
  -F "file=@document.jpg" \
  -F "doc_type=passport"
```

#### D. Swagger UI
Откройте `http://localhost:8000/docs` в браузере для интерактивного тестирования API.

## Поддерживаемые форматы

- **Изображения:** JPG, PNG, BMP, TIFF
- **Типы документов:**
  - `passport` - Паспорт РФ
  - `driver_license` - Водительское удостоверение
  - `sts` - СТС

## Методы распознавания

### Паспорт РФ
1. **PassportEye (MRZ)** - основной метод, высокая точность
2. **Tesseract OCR** - резервный метод (требует установки Tesseract)

### Водительское удостоверение
1. **PDF417 декодер** - основной метод для задней стороны
2. **Tesseract OCR** - резервный метод для лицевой стороны

### СТС
1. **PDF417 декодер** - основной метод для штрихкода
2. **Tesseract OCR** - резервный метод для текста

## Установка Tesseract OCR (опционально)

Для полного функционала установите Tesseract OCR:

1. Скачайте с https://github.com/UB-Mannheim/tesseract/wiki
2. Установите с поддержкой русского и английского языков
3. Добавьте в PATH: `C:\Program Files\Tesseract-OCR`
4. Перезапустите приложение

Подробная инструкция в файле `TESSERACT_SETUP.md`.

## Примеры ответов

### Успешный парсинг паспорта
```json
{
  "success": true,
  "document_type": "passport",
  "method": "mrz",
  "confidence": 98.5,
  "data": {
    "full_name": "ИВАНОВ ИВАН ИВАНОВИЧ",
    "passport_number": "123456789",
    "nationality": "RUS",
    "birth_date": "1990-01-01",
    "sex": "M",
    "expiry_date": "2030-01-01"
  }
}
```

### Ошибка распознавания
```json
{
  "success": false,
  "document_type": "passport",
  "method": "mrz_only",
  "confidence": 0,
  "data": {},
  "error": "MRZ не найден. Для полного функционала установите Tesseract OCR"
}
```

## Отладка

### Логи приложения
Приложение выводит логи в консоль. Обратите внимание на сообщения:
- `[MRZ] Failed: ...` - ошибки MRZ распознавания
- `[PDF417] Failed: ...` - ошибки PDF417 декодирования

### Проверка зависимостей
```bash
python -c "import cv2, numpy, PIL, passporteye, pdf417decoder; print('Все зависимости установлены')"
```

### Проверка Tesseract
```bash
tesseract --version
```

## Производительность

- **MRZ распознавание:** ~1-2 секунды
- **PDF417 декодирование:** ~0.5-1 секунда  
- **OCR fallback:** ~3-5 секунд
- **Память:** ~100-200 MB

## Ограничения локальной версии

- OCR отключен без Tesseract
- Нет масштабирования (только один процесс)
- Нет логирования в файлы
- Нет мониторинга

Для продакшена используйте развернутую версию на Railway.
