#!/usr/bin/env python3
"""
Простой скрипт для тестирования загрузки и обработки изображений
"""
import asyncio
import httpx
from PIL import Image
import io
import sys


async def create_test_image():
    """Создает тестовое изображение"""
    print("Создаем тестовое изображение...")
    
    # Создаем красивое тестовое изображение
    img = Image.new('RGB', (500, 400), color='lightblue')
    
    # Добавляем цветные полосы
    colors = [
        (255, 0, 0),    # красный
        (0, 255, 0),    # зеленый  
        (0, 0, 255),    # синий
        (255, 255, 0),  # желтый
        (255, 0, 255),  # фиолетовый
    ]
    
    stripe_width = 100
    for i, color in enumerate(colors):
        x_start = i * stripe_width
        x_end = min((i + 1) * stripe_width, 500)
        
        for x in range(x_start, x_end):
            for y in range(150, 250):
                if x < 500:  # проверка границ
                    img.putpixel((x, y), color)
    
    # Сохраняем в байты
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=90)
    img_bytes.seek(0)
    
    print(f"Создано изображение размером {len(img_bytes.getvalue())} байт")
    return img_bytes.getvalue()


async def check_health():
    """Проверяет здоровье API"""
    print("Проверяем состояние API...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get('http://localhost:8000/health', timeout=5.0)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"API здоров: {health_data}")
                return True
            else:
                print(f"API недоступен. Код: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        print("Убедитесь, что сервисы запущены: docker compose up --build")
        return False


async def upload_image():
    """Загружает изображение и отслеживает его обработку"""
    print("\nЗагружаем изображение...")
    
    # Создаем тестовое изображение
    image_data = await create_test_image()
    
    try:
        async with httpx.AsyncClient() as client:
            # Загружаем изображение
            files = {'file': ('test_colorful.jpg', image_data, 'image/jpeg')}
            response = await client.post(
                'http://localhost:8000/api/v1/images',
                files=files,
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"Ошибка загрузки: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return None
                
            result = response.json()
            task_id = result['task_id']
            print("Изображение загружено!")
            print(f"   Task ID: {task_id}")
            print(f"   Статус: {result['status']}")
            
            return task_id
            
    except Exception as e:
        print(f"Ошибка при загрузке: {e}")
        return None


async def check_processing_status(task_id):
    """Проверяет статус обработки изображения"""
    print(f"\nОтслеживаем обработку изображения {task_id}...")
    
    try:
        async with httpx.AsyncClient() as client:
            for attempt in range(15):  # Максимум 15 попыток (30 секунд)
                await asyncio.sleep(2)
                
                response = await client.get(
                    f'http://localhost:8000/api/v1/images/{task_id}',
                    timeout=5.0
                )
                
                if response.status_code != 200:
                    print(f"Ошибка проверки статуса: {response.status_code}")
                    continue
                    
                data = response.json()
                status = data['status']
                
                print(f"   Попытка {attempt + 1}: {status}")
                
                if status == 'DONE':
                    print("\nОбработка завершена успешно!")
                    
                    thumbnails = data.get('thumbnails', {})
                    print(f"Создано миниатюр: {len(thumbnails)}")
                    
                    for size, path in thumbnails.items():
                        print(f"   - {size}: {path}")
                    
                    print(f"\nСоздано: {data['created_at']}")
                    print(f"Обновлено: {data['updated_at']}")
                    
                    return True
                    
                elif status == 'ERROR':
                    error_msg = data.get('error_message', 'Неизвестная ошибка')
                    print(f"\nОшибка обработки: {error_msg}")
                    return False
            
            print("\nПревышено время ожидания")
            return False
            
    except Exception as e:
        print(f"Ошибка проверки статуса: {e}")
        return False


async def main():
    """Главная функция"""
    print("Тестируем сервис обработки изображений\n")
    
    # 1. Проверяем здоровье API
    if not await check_health():
        sys.exit(1)
    
    # 2. Загружаем изображение
    task_id = await upload_image()
    if not task_id:
        sys.exit(1)
    
    # 3. Отслеживаем обработку
    success = await check_processing_status(task_id)
    
    # 4. Результат
    if success:
        print("\nТест прошел успешно!")
        print("\nПолезные ссылки:")
        print("   - API: http://localhost:8000/")
        print("   - Документация: http://localhost:8000/docs")
        print("   - RabbitMQ: http://localhost:15672 (guest/guest)")
    else:
        print("\nТест не удался!")
        print("Проверьте логи: docker compose logs -f worker")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nТест прерван пользователем")
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")
        sys.exit(1)