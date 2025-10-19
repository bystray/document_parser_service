from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from passporteye import read_mrz
from pdf417decoder import PDF417Decoder
import pytesseract
from PIL import Image
import cv2
import numpy as np
import io
import re
from typing import Dict, Any, Optional

app = FastAPI(title="Document Parser API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Предобработка изображений =============
def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Предобработка:
    - Перевод в grayscale
    - Увеличение контрастности
    - Бинаризация (Otsu's method)
    - Deskew (выравнивание по горизонту)
    """
    img_np = np.array(image.convert('L'))  # Grayscale
    
    # Применяем адаптивную бинаризацию
    thresh = cv2.adaptiveThreshold(
        img_np, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Deskew (выравнивание)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        (h, w) = thresh.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(thresh, M, (w, h), 
                                 flags=cv2.INTER_CUBIC, 
                                 borderMode=cv2.BORDER_REPLICATE)
        return rotated
    
    return thresh

# ============= Парсинг паспорта =============
@app.post("/parse")
async def parse_document(
    file: UploadFile,
    doc_type: str = Form(...)
):
    """
    Универсальная точка входа для всех типов документов
    """
    try:
        # Читаем изображение
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Вызываем соответствующий парсер
        if doc_type == "passport":
            return await parse_passport(image)
        elif doc_type == "driver_license":
            return await parse_driver_license(image)
        elif doc_type == "sts":
            return await parse_sts(image)
        else:
            raise HTTPException(400, f"Unsupported doc_type: {doc_type}")
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "document_type": doc_type
        }

# ============= Паспорт РФ =============
async def parse_passport(image: Image.Image) -> Dict[str, Any]:
    """
    Паспорт:
    1. PassportEye (MRZ) — приоритет
    2. Tesseract OCR (ocrb) — fallback
    """
    result = {
        "success": False,
        "document_type": "passport",
        "method": "unknown",
        "confidence": 0,
        "data": {}
    }
    
    # Шаг 1: PassportEye (MRZ)
    try:
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        
        mrz = read_mrz(image_bytes)
        
        if mrz and mrz.valid_score > 0.8:
            mrz_data = mrz.to_dict()
            
            # Форматируем дату рождения
            birth_date = mrz_data.get('date_of_birth', '')
            if birth_date and len(birth_date) == 6:  # YYMMDD
                year = '19' + birth_date[:2] if int(birth_date[:2]) > 50 else '20' + birth_date[:2]
                birth_date = f"{year}-{birth_date[2:4]}-{birth_date[4:6]}"
            
            result.update({
                "success": True,
                "method": "mrz",
                "confidence": round(mrz_data.get('valid_score', 0) * 100, 1),
                "data": {
                    "full_name": f"{mrz_data.get('surname', '')} {mrz_data.get('names', '')}".strip(),
                    "passport_number": mrz_data.get('number', ''),
                    "nationality": mrz_data.get('nationality', ''),
                    "birth_date": birth_date,
                    "sex": mrz_data.get('sex', ''),
                    "expiry_date": mrz_data.get('expiration_date', ''),
                },
                "mrz_text": mrz_data.get('raw_text', '')
            })
            return result
    except Exception as e:
        print(f"[MRZ] Failed: {e}")
    
    # Шаг 2: Tesseract OCR (fallback)
    try:
        processed = preprocess_image(image)
        
        # Tesseract с OCRB шрифтом для MRZ-зоны
        custom_config = r'--oem 1 --psm 6 -l rus+eng'
        text = pytesseract.image_to_string(processed, config=custom_config)
        
        # Извлекаем данные регулярками
        passport_match = re.search(r'(\d{2}\s*\d{2})\s*№?\s*(\d{6})', text)
        name_match = re.search(r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)', text)
        
        result.update({
            "success": True,
            "method": "ocr",
            "confidence": 60,  # OCR менее точен
            "data": {
                "full_name": name_match.group(1) if name_match else None,
                "passport_series": passport_match.group(1).replace(' ', '') if passport_match else None,
                "passport_number": passport_match.group(2) if passport_match else None,
            },
            "raw_text": text
        })
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

# ============= Водительское удостоверение =============
async def parse_driver_license(image: Image.Image) -> Dict[str, Any]:
    """
    ВУ:
    1. PDF417 (задняя сторона) — приоритет
    2. Tesseract OCR (лицевая сторона) — fallback
    """
    result = {
        "success": False,
        "document_type": "driver_license",
        "method": "unknown",
        "confidence": 0,
        "data": {}
    }
    
    # Шаг 1: PDF417 декодер
    try:
        img_np = np.array(image)
        decoder = PDF417Decoder(img_np)
        
        if decoder.decode():
            barcode_data = decoder.barcode_data_index_to_string(0)
            
            # Парсим данные из штрихкода (формат РФ ВУ)
            lines = barcode_data.split('\n')
            
            result.update({
                "success": True,
                "method": "pdf417",
                "confidence": 98,
                "data": parse_driver_license_pdf417(lines),
                "raw_barcode": barcode_data
            })
            return result
    except Exception as e:
        print(f"[PDF417] Failed: {e}")
    
    # Шаг 2: OCR fallback
    try:
        processed = preprocess_image(image)
        text = pytesseract.image_to_string(processed, lang='rus+eng')
        
        # Извлекаем данные
        license_match = re.search(r'(\d{2}\s*[А-ЯA-Z]{2}\s*\d{6})', text)
        
        result.update({
            "success": True,
            "method": "ocr",
            "confidence": 50,
            "data": {
                "license_number": license_match.group(1).replace(' ', '') if license_match else None,
            },
            "raw_text": text
        })
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

def parse_driver_license_pdf417(lines: list) -> Dict[str, Any]:
    """
    Парсинг PDF417 штрихкода водительского удостоверения РФ
    """
    data = {}
    if len(lines) > 0: data["license_number"] = lines[0].strip()
    if len(lines) > 1: data["surname"] = lines[1].strip()
    if len(lines) > 2: data["name"] = lines[2].strip()
    if len(lines) > 3: data["patronymic"] = lines[3].strip()
    if len(lines) > 4: data["birth_date"] = lines[4].strip()
    if len(lines) > 5: data["issue_date"] = lines[5].strip()
    if len(lines) > 6: data["expiry_date"] = lines[6].strip()
    if len(lines) > 7: data["issuer_code"] = lines[7].strip()
    if len(lines) > 8: data["categories"] = lines[8].strip()
    
    return data

# ============= СТС =============
async def parse_sts(image: Image.Image) -> Dict[str, Any]:
    """
    СТС:
    1. PDF417 (штрихкод) — приоритет
    2. Tesseract OCR — fallback
    """
    result = {
        "success": False,
        "document_type": "sts",
        "method": "unknown",
        "confidence": 0,
        "data": {}
    }
    
    # Шаг 1: PDF417 декодер
    try:
        img_np = np.array(image)
        decoder = PDF417Decoder(img_np)
        
        if decoder.decode():
            barcode_data = decoder.barcode_data_index_to_string(0)
            
            result.update({
                "success": True,
                "method": "pdf417",
                "confidence": 98,
                "data": parse_sts_pdf417(barcode_data),
                "raw_barcode": barcode_data
            })
            return result
    except Exception as e:
        print(f"[PDF417] Failed: {e}")
    
    # Шаг 2: OCR fallback
    try:
        processed = preprocess_image(image)
        text = pytesseract.image_to_string(processed, lang='rus+eng')
        
        # Извлекаем данные
        reg_number_match = re.search(r'([АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3})', text, re.IGNORECASE)
        vin_match = re.search(r'VIN[:\s]*([A-HJ-NPR-Z0-9]{17})', text, re.IGNORECASE)
        
        result.update({
            "success": True,
            "method": "ocr",
            "confidence": 55,
            "data": {
                "registration_number": reg_number_match.group(1) if reg_number_match else None,
                "vin": vin_match.group(1) if vin_match else None,
            },
            "raw_text": text
        })
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

def parse_sts_pdf417(barcode_data: str) -> Dict[str, Any]:
    """
    Парсинг PDF417 штрихкода СТС
    """
    lines = barcode_data.split('\n')
    data = {}
    
    for line in lines:
        if 'VIN' in line:
            data['vin'] = line.split(':')[-1].strip()
        elif 'Госномер' in line or 'Рег' in line:
            match = re.search(r'([АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3})', line, re.IGNORECASE)
            if match:
                data['registration_number'] = match.group(1)
        elif 'Марка' in line:
            data['brand'] = line.split(':')[-1].strip()
        elif 'Модель' in line:
            data['model'] = line.split(':')[-1].strip()
        elif 'Год' in line:
            match = re.search(r'\d{4}', line)
            if match:
                data['year'] = match.group(0)
    
    return data

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "document-parser-v2"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
