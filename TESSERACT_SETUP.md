# Установка Tesseract OCR для Windows

Для полного функционала парсера документов необходимо установить Tesseract OCR.

## Скачивание и установка

1. **Скачайте Tesseract OCR для Windows:**
   - Перейдите на страницу: https://github.com/UB-Mannheim/tesseract/wiki
   - Скачайте последнюю версию для Windows (например, `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)

2. **Установите Tesseract:**
   - Запустите скачанный файл
   - Выберите "Additional language data" и установите:
     - Russian (rus)
     - English (eng)
   - Запомните путь установки (по умолчанию: `C:\Program Files\Tesseract-OCR`)

3. **Добавьте Tesseract в PATH:**
   - Откройте "Системные переменные среды"
   - Добавьте в PATH: `C:\Program Files\Tesseract-OCR`
   - Или создайте переменную `TESSDATA_PREFIX` со значением `C:\Program Files\Tesseract-OCR\tessdata`

## Проверка установки

Откройте командную строку и выполните:
```bash
tesseract --version
```

Должно вывести версию Tesseract.

## Настройка Python

После установки Tesseract, обновите `app.py` для указания пути к Tesseract:

```python
import pytesseract

# Добавьте эту строку после импорта pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Альтернативный способ (через conda)

Если у вас установлен Anaconda/Miniconda:

```bash
conda install -c conda-forge tesseract
```

## Тестирование

После установки перезапустите приложение:

```bash
python app.py
```

Теперь OCR будет работать для всех типов документов.
