#!/usr/bin/env python3
"""
Полная диагностика сервиса обработки изображений
"""
import asyncio
import httpx
import subprocess
import sys


async def check_docker_containers():
    """Проверяет состояние Docker контейнеров"""
    print("Проверяем Docker контейнеры...")
    
    try:
        result = subprocess.run([
            'docker', 'compose', 'ps', '--format', 'table'
        ], capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Есть заголовок + строки
                print("Контейнеры запущены:")
                for line in lines[1:]:  # Пропускаем заголовок
                    if 'Up' in line:
                        service = line.split()[0].split('-')[-2]
                        print(f"   {service}: работает")
                    else:
                        service = line.split()[0].split('-')[-2]
                        print(f"   {service}: не работает")
                return True
            else:
                print("Контейнеры не запущены")
                return False
        else:
            print(f"Ошибка Docker: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Ошибка проверки Docker: {e}")
        return False


async def check_api_health():
    """Проверяет здоровье API"""
    print("\nПроверяем API...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Корневой endpoint
            root_response = await client.get('http://localhost:8000/', timeout=5.0)
            if root_response.status_code == 200:
                print("Корневой endpoint работает")
            else:
                print(f"Корневой endpoint: {root_response.status_code}")
            
            # Health check
            health_response = await client.get('http://localhost:8000/health', timeout=5.0)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print("Health check прошел:")
                print(f"   Статус: {health_data.get('status')}")
                print(f"   БД: {health_data.get('db')}")
                print(f"   RabbitMQ: {health_data.get('rabbitmq')}")
                return True
            else:
                print(f"Health check не прошел: {health_response.status_code}")
                return False
                
    except Exception as e:
        print(f"Ошибка API: {e}")
        return False


async def check_rabbitmq_brief():
    """Краткая проверка RabbitMQ"""
    print("\nПроверяем RabbitMQ...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'http://localhost:15672/api/queues',
                auth=('guest', 'guest'),
                timeout=5.0
            )
            
            if response.status_code == 200:
                queues = response.json()
                images_queue = next((q for q in queues if q['name'] == 'images'), None)
                
                if images_queue:
                    consumers = images_queue.get('consumers', 0)
                    messages = images_queue.get('messages', 0)
                    
                    print("Очередь 'images' найдена:")
                    print(f"   Worker'ов подключено: {consumers}")
                    print(f"   Сообщений в очереди: {messages}")
                    
                    if consumers > 0:
                        print("   Worker активен")
                        return True
                    else:
                        print("   Worker не подключен")
                        return False
                else:
                    print("Очередь 'images' не найдена")
                    return False
            else:
                print(f"RabbitMQ недоступен: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"Ошибка RabbitMQ: {e}")
        return False


async def check_storage():
    """Проверяет файловое хранилище"""
    print("\nПроверяем хранилище...")
    
    try:
        result = subprocess.run([
            'docker', 'compose', 'exec', '-T', 'worker', 
            'bash', '-c', 'ls -la /storage/'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Хранилище доступно:")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Пропускаем "total"
                if 'original' in line or 'thumbs' in line:
                    dir_name = line.split()[-1]
                    print(f"   {dir_name}")
            
            # Проверяем содержимое
            thumb_result = subprocess.run([
                'docker', 'compose', 'exec', '-T', 'worker',
                'bash', '-c', 'find /storage -name "*.jpg" | wc -l'
            ], capture_output=True, text=True)
            
            if thumb_result.returncode == 0:
                file_count = thumb_result.stdout.strip()
                print(f"   Файлов изображений: {file_count}")
            
            return True
        else:
            print(f"Хранилище недоступно: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Ошибка проверки хранилища: {e}")
        return False


def print_summary(api_ok, rabbitmq_ok, storage_ok, docker_ok):
    """Выводит итоговый отчет"""
    print("\n" + "="*50)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("="*50)
    
    total_checks = 4
    passed_checks = sum([api_ok, rabbitmq_ok, storage_ok, docker_ok])
    
    print(f"Пройдено проверок: {passed_checks}/{total_checks}")
    
    if passed_checks == total_checks:
        status_emoji = "ОК"
    elif passed_checks >= 2:
        status_emoji = "ЧАСТИЧНО"
    else:
        status_emoji = "ПРОБЛЕМЫ"
    
    print(f"Docker контейнеры: {'ОК' if docker_ok else 'ОШИБКА'}")
    print(f"API сервис: {'ОК' if api_ok else 'ОШИБКА'}")
    print(f"RabbitMQ + Worker: {'ОК' if rabbitmq_ok else 'ОШИБКА'}")
    print(f"Файловое хранилище: {'ОК' if storage_ok else 'ОШИБКА'}")
    
    print(f"\nОбщий статус: {status_emoji}")
    
    if passed_checks == total_checks:
        print("Система полностью функциональна!")
        print("\nМожно тестировать загрузку изображений:")
        print("   python test_upload.py")
    elif passed_checks >= 2:
        print("Система частично работает")
        print("\nРекомендации:")
        if not docker_ok:
            print("   - Перезапустите контейнеры: docker compose restart")
        if not api_ok:
            print("   - Проверьте логи API: docker compose logs api")
        if not rabbitmq_ok:
            print("   - Проверьте логи worker: docker compose logs worker")
        if not storage_ok:
            print("   - Проверьте volumes: docker volume ls")
    else:
        print("Система не работает!")
        print("\nПопробуйте:")
        print("   - Перезапустить: docker compose restart")
        print("   - Пересобрать: docker compose up --build")
        print("   - Проверить логи: docker compose logs")


async def main():
    """Главная функция полной диагностики"""
    print("ДИАГНОСТИКА СЕРВИСА ОБРАБОТКИ ИЗОБРАЖЕНИЙ")
    print("=" * 50)
    
    # Выполняем все проверки
    docker_ok = await check_docker_containers()
    api_ok = await check_api_health()
    rabbitmq_ok = await check_rabbitmq_brief()
    storage_ok = await check_storage()
    
    # Выводим итоги
    print_summary(api_ok, rabbitmq_ok, storage_ok, docker_ok)
    
    print("\nПолезные ссылки:")
    print("   API: http://localhost:8000/")
    print("   Документация: http://localhost:8000/docs")
    print("   RabbitMQ: http://localhost:15672 (guest/guest)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nДиагностика прервана")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        sys.exit(1)