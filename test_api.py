#!/usr/bin/env python3
"""
Простой скрипт для тестирования Document Parser API
"""

import requests
import json
import sys
import os

API_URL = "http://localhost:8000"

def test_health():
    """Тест health endpoint"""
    print("Проверка health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"Сервер работает: {data}")
            return True
        else:
            print(f"Ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return False

def test_parse(image_path, doc_type):
    """Тест парсинга документа"""
    print(f"Тестирование парсинга {doc_type}...")
    
    if not os.path.exists(image_path):
        print(f"Файл не найден: {image_path}")
        return False
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'doc_type': doc_type}
            
            response = requests.post(f"{API_URL}/parse", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Результат парсинга:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return True
            else:
                print(f"Ошибка: {response.status_code}")
                print(response.text)
                return False
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def main():
    print("Document Parser API Test")
    print("=" * 40)
    
    # Проверяем health
    if not test_health():
        print("\nСервер недоступен. Убедитесь, что приложение запущено:")
        print("   python app_local.py")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    
    # Если передан аргумент с путем к файлу
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        doc_type = sys.argv[2] if len(sys.argv) > 2 else "passport"
        
        test_parse(image_path, doc_type)
    else:
        print("Для тестирования парсинга передайте путь к изображению:")
        print("   python test_api.py path/to/image.jpg passport")
        print("   python test_api.py path/to/image.jpg driver_license")
        print("   python test_api.py path/to/image.jpg sts")
        
        print("\nИли откройте test_client.html в браузере для веб-интерфейса")

if __name__ == "__main__":
    main()
