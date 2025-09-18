# flake8: noqa
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io
import time

from app.main import app

client = TestClient(app)


@pytest.mark.integration
def test_full_image_processing_workflow():
    """
    Интеграционный тест полного жизненного цикла обработки изображения
    Требует запущенного сервиса с RabbitMQ и PostgreSQL
    """
    # Создаем тестовое изображение
    img = Image.new('RGB', (200, 200), color=(100, 150, 200))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    # 1. Загружаем изображение
    files = {'file': ('test_integration.jpg', img_bytes.getvalue(), 'image/jpeg')}
    response = client.post("/api/v1/images", files=files)
    
    assert response.status_code == 200
    data = response.json()
    task_id = data['task_id']
    assert data['status'] == 'PROCESSING'
    
    # 2. Ожидаем обработки (максимум 30 секунд)
    max_attempts = 30
    for attempt in range(max_attempts):
        status_response = client.get(f"/api/v1/images/{task_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        if status_data['status'] == 'DONE':
            # Проверяем что созданы все миниатюры
            assert len(status_data['thumbnails']) == 3
            assert '100x100' in status_data['thumbnails']
            assert '300x300' in status_data['thumbnails']
            assert '1200x1200' in status_data['thumbnails']
            break
        elif status_data['status'] == 'ERROR':
            pytest.fail(f"Image processing failed: {status_data.get('error_message')}")
        else:
            time.sleep(1)
    else:
        pytest.fail("Image processing timed out")
    
    # 3. Тестируем просмотр оригинала
    view_response = client.get(f"/api/v1/images/{task_id}/file")
    assert view_response.status_code == 200
    assert view_response.headers['content-type'] == 'image/jpeg'
    assert 'inline' in view_response.headers.get('content-disposition', '')
    
    # 4. Тестируем просмотр миниатюр
    sizes = ['100x100', '300x300', '1200x1200']
    for size in sizes:
        thumb_response = client.get(f"/api/v1/images/{task_id}/file?size={size}")
        assert thumb_response.status_code == 200
        assert thumb_response.headers['content-type'] == 'image/jpeg'
        assert len(thumb_response.content) > 0
    
    # 5. Тестируем скачивание
    download_response = client.get(f"/api/v1/images/{task_id}/download")
    assert download_response.status_code == 200
    assert download_response.headers['content-type'] == 'application/octet-stream'
    assert 'attachment' in download_response.headers.get('content-disposition', '')
    
    # 6. Тестируем скачивание миниатюр
    for size in sizes:
        download_thumb_response = client.get(
            f"/api/v1/images/{task_id}/download?size={size}"
        )
        assert download_thumb_response.status_code == 200
        assert download_thumb_response.headers['content-type'] == 'application/octet-stream'
        assert len(download_thumb_response.content) > 0


@pytest.mark.integration
def test_health_check_with_dependencies():
    """Интеграционный тест проверки здоровья с реальными зависимостями"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['db'] in ['connected', 'disconnected']
    assert data['rabbitmq'] in ['connected', 'disconnected']


@pytest.mark.integration  
def test_swagger_documentation_available():
    """Тест доступности документации Swagger"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.integration
def test_api_root_endpoint():
    """Тест корневого эндпоинта API"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Image Processing Service"
    assert data["version"] == "1.0.0"
    assert "/docs" in data["docs"]
    assert "/health" in data["health"]
    assert "/api/v1" in data["api"]


@pytest.mark.integration
def test_invalid_file_upload():
    """Тест загрузки недопустимого файла"""
    # Попытка загрузить текстовый файл
    files = {'file': ('test.txt', b'This is not an image', 'text/plain')}
    response = client.post("/api/v1/images", files=files)
    
    assert response.status_code == 400
    assert "Only JPEG/PNG allowed" in response.json()["detail"]


@pytest.mark.integration
def test_missing_file_upload():
    """Тест запроса без файла"""
    response = client.post("/api/v1/images")
    assert response.status_code == 422  # Validation error


@pytest.mark.integration
def test_nonexistent_image_endpoints():
    """Тест обращения к несуществующим изображениям"""
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    # Тест получения информации
    response = client.get(f"/api/v1/images/{fake_id}")
    assert response.status_code == 404
    
    # Тест просмотра
    response = client.get(f"/api/v1/images/{fake_id}/file")
    assert response.status_code == 404
    
    # Тест скачивания
    response = client.get(f"/api/v1/images/{fake_id}/download")
    assert response.status_code == 404


@pytest.mark.integration
def test_invalid_uuid_format():
    """Тест неверного формата UUID"""
    invalid_id = "invalid-uuid-format"
    
    # Тест получения информации
    response = client.get(f"/api/v1/images/{invalid_id}")
    assert response.status_code == 400
    assert "Invalid UUID" in response.json()["detail"]
    
    # Тест просмотра
    response = client.get(f"/api/v1/images/{invalid_id}/file")
    assert response.status_code == 400
    assert "Invalid UUID" in response.json()["detail"]
    
    # Тест скачивания
    response = client.get(f"/api/v1/images/{invalid_id}/download")
    assert response.status_code == 400
    assert "Invalid UUID" in response.json()["detail"]