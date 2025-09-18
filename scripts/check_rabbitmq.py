#!/usr/bin/env python3
"""
Проверка состояния RabbitMQ и очередей
"""
import asyncio
import httpx


async def check_rabbitmq_health():
    """Проверяет состояние RabbitMQ"""
    print("Проверяем состояние RabbitMQ...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'http://localhost:15672/api/overview',
                auth=('guest', 'guest'),
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print("RabbitMQ работает:")
                print(f"   Версия: {data.get('rabbitmq_version', 'Unknown')}")
                print(f"   Узел: {data.get('node', 'Unknown')}")
                return True
            else:
                print(f"RabbitMQ недоступен. Код: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"Ошибка подключения к RabbitMQ: {e}")
        return False


async def check_queues():
    """Проверяет состояние очередей"""
    print("\nПроверяем очереди...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'http://localhost:15672/api/queues',
                auth=('guest', 'guest'),
                timeout=10.0
            )
            
            if response.status_code == 200:
                queues = response.json()
                
                if not queues:
                    print("Очередей не найдено")
                    return False
                
                print(f"Найдено очередей: {len(queues)}")
                
                for queue in queues:
                    name = queue.get('name', 'Unknown')
                    messages = queue.get('messages', 0)
                    consumers = queue.get('consumers', 0)
                    ready = queue.get('messages_ready', 0)
                    unacked = queue.get('messages_unacknowledged', 0)
                    
                    print(f"\nОчередь: {name}")
                    print(f"   Всего сообщений: {messages}")
                    print(f"   Готовых к обработке: {ready}")
                    print(f"   Обрабатывается: {unacked}")
                    print(f"   Потребителей: {consumers}")
                    
                    if name == 'images':
                        if consumers > 0:
                            print("   Worker подключен!")
                        else:
                            print("   Worker не подключен!")
                
                return True
            else:
                error_msg = f"Не удалось получить информацию об очередях: {response.status_code}"
                print(error_msg)
                return False
                
    except Exception as e:
        print(f"Ошибка проверки очередей: {e}")
        return False


async def check_connections():
    """Проверяет активные соединения"""
    print("\nПроверяем соединения...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'http://localhost:15672/api/connections',
                auth=('guest', 'guest'),
                timeout=10.0
            )
            
            if response.status_code == 200:
                connections = response.json()
                
                print(f"Активных соединений: {len(connections)}")
                
                for i, conn in enumerate(connections):
                    name = conn.get('name', f'connection-{i}')
                    user = conn.get('user', 'Unknown')
                    state = conn.get('state', 'Unknown')
                    channels = conn.get('channels', 0)
                    
                    print(f"\nСоединение: {name}")
                    print(f"   Пользователь: {user}")
                    print(f"   Состояние: {state}")
                    print(f"   Каналов: {channels}")
                
                return True
            else:
                error_msg = f"Не удалось получить информацию о соединениях: {response.status_code}"
                print(error_msg)
                return False
                
    except Exception as e:
        print(f"Ошибка проверки соединений: {e}")
        return False


async def main():
    """Главная функция"""
    print("Проверяем состояние RabbitMQ\n")
    
    # Проверяем здоровье RabbitMQ
    if not await check_rabbitmq_health():
        print("\nУбедитесь, что RabbitMQ запущен:")
        print("   docker compose up rabbit -d")
        return
    
    # Проверяем очереди
    await check_queues()
    
    # Проверяем соединения
    await check_connections()
    
    print("\nПолезные ссылки:")
    print("   RabbitMQ Management: http://localhost:15672")
    print("   Логин/Пароль: guest/guest")
    print("   API: http://localhost:15672/api/")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПроверка прервана")
    except Exception as e:
        print(f"\nОшибка: {e}")