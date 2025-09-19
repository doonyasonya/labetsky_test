# Сервис асинхронной обработки изображений

[![CI](https://github.com/doonyasonya/labetsky_test/workflows/CI/badge.svg)](https://github.com/doonyasonya/labetsky_test/actions)
[![Deploy](https://github.com/doonyasonya/labetsky_test/workflows/Deploy/badge.svg)](https://github.com/doonyasonya/labetsky_test/actions)
[![Docker Image](https://img.shields.io/docker/image-size/doonyanikitin/image-processing-api/latest)](https://hub.docker.com/r/doonyanikitin/image-processing-api)
[![Docker Pulls](https://img.shields.io/docker/pulls/doonyanikitin/image-processing-api)](https://hub.docker.com/r/doonyanikitin/image-processing-api)

Backend-сервис для загрузки и асинхронной обработки изображений с автоматическим созданием миниатюр.

## Технологии

- **FastAPI** - современный веб-фреймворк для создания API
- **PostgreSQL** - база данных для хранения метаинформации об изображениях
- **RabbitMQ** - брокер сообщений для асинхронной обработки
- **Docker + Docker Compose** - контейнеризация и оркестрация сервисов
- **SQLAlchemy + Alembic** - ORM и миграции базы данных
- **Pillow** - обработка изображений и создание миниатюр

## Требования

- Python 3.12+
- Docker и Docker Compose
- Git
- Свободные порты: 8000, 5432, 5672, 15672

## Быстрый старт

1. **Клонирование репозитория:**
   ```bash
   git clone <repo-url>
   cd labetsky_test
   ```

2. **Запуск сервисов:**
   ```bash
   docker compose up --build
   ```

3. **Создание таблиц в БД:**
   ```bash
   docker compose exec api python -c "from app.models import Base; from sqlalchemy import create_engine; engine = create_engine('postgresql://user:password@db:5432/images_db'); Base.metadata.create_all(engine); print('Tables created')"
   ```

## Доступные интерфейсы

| Сервис | URL | Описание |
|--------|-----|----------|
| **API Root** | http://localhost:8000/ | Информация о сервисе |
| **API** | http://localhost:8000/api/v1 | Основной API сервиса |
| **Swagger UI** | http://localhost:8000/docs | Интерактивная документация API |
| **ReDoc** | http://localhost:8000/redoc | Альтернативная документация |
| **Health Check** | http://localhost:8000/health | Проверка состояния сервиса |
| **RabbitMQ Management** | http://localhost:15672 | Управление очередями (guest/guest) |
| **Просмотр изображений** | http://localhost:8000/api/v1/images/{id}/file | Просмотр файлов в браузере |
| **Скачивание изображений** | http://localhost:8000/api/v1/images/{id}/download | Скачивание файлов |

## API Endpoints

### Загрузка изображения
```http
POST /api/v1/images
Content-Type: multipart/form-data

Параметры:
- file: файл изображения (JPEG/PNG)

Ответ:
{
  "task_id": "uuid",
  "status": "PROCESSING"
}
```

### Получение информации об изображении
```http
GET /api/v1/images/{id}

Ответ:
{
  "id": "uuid",
  "status": "NEW|PROCESSING|DONE|ERROR",
  "original_url": "string",
  "thumbnails": {
    "100x100": "url",
    "300x300": "url",
    "1200x1200": "url"
  },
  "error_message": "string|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Просмотр файла изображения
```http
GET /api/v1/images/{id}/file?size={size}

Параметры:
- id: UUID изображения
- size (опционально): 100x100, 300x300, 1200x1200 или пусто для оригинала

Ответ:
- Файл изображения для просмотра в браузере (Content-Disposition: inline)
```

### Скачивание файла изображения
```http
GET /api/v1/images/{id}/download?size={size}

Параметры:
- id: UUID изображения
- size (опционально): 100x100, 300x300, 1200x1200 или пусто для оригинала

Ответ:
- Файл для скачивания (Content-Disposition: attachment)
- Имя файла: original_name_{size}.jpg или оригинальное имя
```

### Проверка здоровья сервиса
```http
GET /health

Ответ:
{
  "status": "healthy",
  "db": "connected",
  "rabbitmq": "connected"
}
```

## Полная проверка системы

Для полной проверки системы созданы специальные скрипты:

### Структура тестов

Тесты организованы по функциональности:
- [tests/test_api.py](file://d:\Dev\labetsky_test\tests\test_api.py) - Unit-тесты основных API эндпоинтов
- [tests/test_file_endpoints.py](file://d:\Dev\labetsky_test\tests\test_file_endpoints.py) - Unit-тесты файловых эндпоинтов (просмотр/скачивание)
- [tests/test_integration.py](file://d:\Dev\labetsky_test\tests\test_integration.py) - Интеграционные тесты полного жизненного цикла

### Скрипты тестирования и диагностики

Вспомогательные скрипты находятся в папке [scripts/](file://d:\Dev\labetsky_test\scripts\):
- [scripts/check_system.py](file://d:\Dev\labetsky_test\scripts\check_system.py) - Комплексная диагностика системы
- [scripts/check_rabbitmq.py](file://d:\Dev\labetsky_test\scripts\check_rabbitmq.py) - Проверка состояния RabbitMQ
- [scripts/test_upload.py](file://d:\Dev\labetsky_test\scripts\test_upload.py) - Тест загрузки изображений
- [scripts/check_ci.py](file://d:\Dev\labetsky_test\scripts\check_ci.py) - Проверка готовности CI/CD
- [scripts/monitor_ci.py](file://d:\Dev\labetsky_test\scripts\monitor_ci.py) - Мониторинг GitHub Actions
- [scripts/fix_ci_issues.py](file://d:\Dev\labetsky_test\scripts\fix_ci_issues.py) - Автоматическое исправление проблем

### 1. Общая диагностика
```bash
# Полная проверка всех компонентов
python scripts/check_system.py
```

Отобразит:
- Состояние Docker контейнеров
- Доступность API
- Состояние RabbitMQ и worker'ов
- Доступность файлового хранилища
- Итоговый отчет о состоянии системы

### 2. Тестирование загрузки изображений
```bash
# Полный тест загрузки и обработки с новыми эндпоинтами
python scripts/test_upload.py
```

Выполнит:
- Создание тестового изображения
- Проверку здоровья API
- Загрузку изображения через API
- Отслеживание процесса обработки
- Проверку создания миниатюр
- Тестирование просмотра файлов (оригинал и миниатюры)
- Тестирование скачивания файлов
- Проверку обработки ошибок
- Автоматическое открытие браузера с результатом

### 3. Проверка RabbitMQ
```bash
# Детальная проверка очередей и соединений
python scripts/check_rabbitmq.py
```

Покажет:
- Состояние RabbitMQ сервера
- Информацию о всех очередях
- Количество подключенных worker'ов
- Количество сообщений в очередях
- Активные соединения

### 4. Ручная проверка компонентов

#### Проверка контейнеров:
```bash
# Статус всех сервисов
docker compose ps

# Логи всех сервисов
docker compose logs -f

# Логи конкретного сервиса
docker compose logs api
docker compose logs worker
docker compose logs db
docker compose logs rabbit
```

#### Проверка API:
```bash
# Проверка корневого endpoint
curl http://localhost:8000/

# Проверка здоровья
curl http://localhost:8000/health

# Ожидаемые результаты:
# {"message":"Image Processing Service","version":"1.0.0",...}
# {"status":"healthy","db":"connected","rabbitmq":"connected"}
```

#### Проверка документации:
```bash
# Swagger UI доступен
curl -I http://localhost:8000/docs

# Должен вернуть: HTTP/1.1 200 OK
```

#### Проверка базы данных:
```bash
# Подключение к БД
docker compose exec db psql -U user -d images_db

# Проверка таблиц
\\dt

# Проверка данных
SELECT id, status, created_at FROM images ORDER BY created_at DESC LIMIT 5;

# Выход
\\q
```

#### Проверка файлового хранилища:
```bash
# Просмотр созданных файлов
docker compose exec worker bash -c "ls -la /storage/original/"
docker compose exec worker bash -c "ls -la /storage/thumbs/100x100/"
docker compose exec worker bash -c "ls -la /storage/thumbs/300x300/"
docker compose exec worker bash -c "ls -la /storage/thumbs/1200x1200/"

# Подсчет файлов
docker compose exec worker bash -c "find /storage -name '*.jpg' | wc -l"
```

### 5. Запуск автотестов
```bash
# Все тесты
docker compose exec api python -m pytest tests/ -v

# Тесты с покрытием
docker compose exec api python -m pytest tests/ --cov=app --cov-report=term-missing

# Ожидаемый результат: 3 passed
```

### 6. Проверка качества кода
```bash
# Линтинг
docker compose exec api flake8 app/ --max-line-length=88

# Типизация (если настроен mypy)
docker compose exec api mypy app/
```



#### Через Python:
```python
import httpx
from PIL import Image
import io

# Создаем тестовое изображение
img = Image.new('RGB', (200, 200), color='blue')
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)

# Загружаем
with httpx.Client() as client:
    files = {'file': ('test.jpg', img_bytes.getvalue(), 'image/jpeg')}
    response = client.post('http://localhost:8000/api/v1/images', files=files)
    result = response.json()
    task_id = result['task_id']
    print(f"Task ID: {task_id}")
    
    # Проверяем статус
    import time
    time.sleep(3)  # Ждем обработки
    status_response = client.get(f'http://localhost:8000/api/v1/images/{task_id}')
    print(status_response.json())
    
    # Просматриваем оригинал
    view_url = f'http://localhost:8000/api/v1/images/{task_id}/file'
    print(f"View original: {view_url}")
    
    # Просматриваем миниатюру
    thumb_url = f'http://localhost:8000/api/v1/images/{task_id}/file?size=300x300'
    print(f"View thumbnail: {thumb_url}")
    
    # Скачиваем миниатюру
    download_response = client.get(f'http://localhost:8000/api/v1/images/{task_id}/download?size=100x100')
    if download_response.status_code == 200:
        with open('downloaded_thumb.jpg', 'wb') as f:
            f.write(download_response.content)
        print("Thumbnail downloaded successfully")
```

### 7. Проверка RabbitMQ
```bash
# Проверка очередей через Management UI
open http://localhost:15672
# Логин: guest, Пароль: guest

# Или через API
curl -u guest:guest http://localhost:15672/api/queues
```

### 8. Проверка PostgreSQL
```bash
# Подключение к БД
docker compose exec db psql -U user -d images_db

# Проверка таблиц
\dt

# Проверка данных
SELECT id, status, created_at FROM images ORDER BY created_at DESC LIMIT 5;

# Выход
\q
```

### 9. Запуск автотестов
```bash
# Все тесты
docker compose exec api python -m pytest tests/ -v

# Только unit-тесты API
docker compose exec api python -m pytest tests/test_api.py -v

# Только тесты файловых эндпоинтов
docker compose exec api python -m pytest tests/test_file_endpoints.py -v

# Интеграционные тесты (требуют полностью запущенного сервиса)
docker compose exec api python -m pytest tests/test_integration.py -v -m integration

# Тесты с покрытием
docker compose exec api python -m pytest tests/ --cov=app --cov-report=term-missing

# Ожидаемый результат: 16+ passed
```

### 10. Проверка качества кода
```bash
# Линтинг
docker compose exec api flake8 app/ --max-line-length=88

# Типизация (если настроен mypy)
docker compose exec api mypy app/
```

### 11. Проверка файлового хранилища
```bash
# Просмотр созданных файлов
docker compose exec api ls -la /storage/original/
docker compose exec api ls -la /storage/thumbs/100x100/
docker compose exec api ls -la /storage/thumbs/300x300/
docker compose exec api ls -la /storage/thumbs/1200x1200/
```

## Локальная разработка

### Без Docker (для разработки):
```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск только БД и RabbitMQ через Docker
docker compose up db rabbit -d

# Создание таблиц
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/images_db \
RABBITMQ_URL=amqp://guest:guest@localhost:5672/ \
STORAGE_PATH=./storage \
alembic upgrade head

# Запуск API
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/images_db \
RABBITMQ_URL=amqp://guest:guest@localhost:5672/ \
STORAGE_PATH=./storage \
uvicorn app.main:app --reload

# Запуск worker (в другом терминале)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/images_db \
RABBITMQ_URL=amqp://guest:guest@localhost:5672/ \
STORAGE_PATH=./storage \
python app/workers/image_processor.py
```

## Решение проблем

### Порты заняты:
```bash
# Проверка занятых портов
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432
netstat -tulpn | grep :5672
netstat -tulpn | grep :15672

# Остановка всех контейнеров
docker compose down
```

### Проблемы с контейнерами:
```bash
# Полная пересборка
docker compose down -v
docker compose build --no-cache
docker compose up
```

### Проблемы с БД:
```bash
# Пересоздание БД
docker compose down -v
docker volume rm labetsky_test_postgres_data
docker compose up db -d
# Затем создать таблицы заново
```

### Очистка системы:
```bash
# Остановка и удаление всего
docker compose down -v --remove-orphans
docker system prune -f
```

## Мониторинг

- **Логи в реальном времени**: `docker compose logs -f`
- **Метрики RabbitMQ**: http://localhost:15672/#/queues
- **Статистика API**: Доступна через Swagger UI
- **Состояние БД**: Через `docker compose exec db psql -U user -d images_db`

## Архитектура

```mermaid
graph TB
    Client[Клиент] --> API[FastAPI API:8000]
    API --> DB[(PostgreSQL:5432)]
    API --> Queue[RabbitMQ:5672]
    Queue --> Worker[Image Worker]
    Worker --> Storage[File Storage]
    Worker --> DB
    
    subgraph "Docker Compose"
        API
        DB
        Queue
        Worker
        Storage
    end
```

## Примечания

- Поддерживаемые форматы: JPEG, PNG
- Размеры миниатюр: 100x100, 300x300, 1200x1200 пикселей
- Качество JPEG: 85% с оптимизацией
- Хранилище: локальная файловая система в Docker volume
- База данных: PostgreSQL с индексами на статус и дату создания
- Просмотр файлов: доступен после завершения обработки (статус "DONE")
- Скачивание: оригинальные и масштабированные версии с корректными именами файлов

## CI/CD

Проект настроен с GitHub Actions для автоматического тестирования и деплоя:

### Настройка GitHub Secrets

Для корректной работы CI/CD pipeline необходимо настроить следующие секреты в репозитории:

1. Перейдите на https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions
2. Добавьте следующие секреты:

   - **DOCKER_HUB_USERNAME** - ваш логин на Docker Hub (например: `doonyanikitin`)
   - **DOCKER_HUB_TOKEN** - токен доступа Docker Hub:
     - Перейдите на https://hub.docker.com/settings/security
     - Создайте новый Access Token с правом записи
     - Скопируйте токен и добавьте в секреты

### Статусы workflow

- **CI** - запускается при push в main/develop и PR в main
- **Deploy** - запускается при push в main или создании тега

### Проверки качества кода
- **Flake8** - линтинг кода с конфигурацией в `.flake8`
- **Автоматические тесты** - unit тесты с покрытием
- **Docker сборка** - проверка контейнеризации

### Тестовая среда
- **PostgreSQL 13** - база данных для тестов
- **RabbitMQ 3.11** - брокер сообщений
- **Миграции Alembic** - автоматическое создание схемы БД

### Локальное воспроизведение CI
```bash
# Проверка синтаксиса и критических ошибок
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Линтинг с предупреждениями
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

# Тесты с покрытием
pytest tests/test_api.py tests/test_file_endpoints.py -v --cov=app --cov-report=xml

# Сборка Docker образа
docker build -t image-processing-api .
```

### Мониторинг и решение проблем
```bash
# Проверка статуса GitHub Actions
python scripts/monitor_ci.py

# Полная проверка CI/CD
python scripts/check_ci.py

# Автоматическое исправление проблем
python scripts/fix_ci_issues.py
```

### Диагностика проблем с бейджами

Если бейджи показывают "invalid" или не обновляются:

1. **Проверьте статус workflow** в Actions на GitHub
2. **Убедитесь, что workflow выполнился хотя бы один раз** - бейджи появляются только после первого запуска
3. **Проверьте корректность названий workflow** в файлах `.github/workflows/`
4. **Для Docker Hub бейджей** убедитесь, что образ существует и доступен

**Команды для диагностики:**
```bash
# Проверка локальной Docker сборки
docker build -t image-processing-api .
docker run --rm image-processing-api python -c "import app.main; print('OK')"

# Проверка подключения к Docker Hub
echo $DOCKER_HUB_TOKEN | docker login --username $DOCKER_HUB_USERNAME --password-stdin

# Ручная сборка и push (если есть права)
docker build -t doonyanikitin/image-processing-api:latest .
docker push doonyanikitin/image-processing-api:latest
```

### Примечания по CI/CD

**Нормальное поведение:**
- GitHub Actions автоматически очищает контейнеры и сети после выполнения
- Логи "Stop and remove container" являются частью нормального cleanup процесса
- Провалы CI могут быть связаны с таймаутами сервисов или несовместимостью зависимостей
