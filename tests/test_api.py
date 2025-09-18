import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_upload_image():
    create_patch = 'app.api.v1.endpoints.images.create_image'
    status_patch = 'app.api.v1.endpoints.images.update_image_status'
    
    with patch(create_patch, new_callable=AsyncMock) as mock_create:
        # Создаем мок объекта изображения с UUID id
        mock_image = AsyncMock()
        mock_image.id = uuid4()
        mock_create.return_value = mock_image
        
        with patch(status_patch, new_callable=AsyncMock):
            with patch('aio_pika.connect_robust', new_callable=AsyncMock):
                with patch('app.api.v1.endpoints.images.uuid4') as mock_uuid:
                    mock_uuid.return_value = uuid4()
                    response = client.post(
                        "/api/v1/images",
                        files={
                            "file": (
                                "test.jpg",
                                b"fake image data",
                                "image/jpeg"
                            )
                        }
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "task_id" in data
                    assert data["status"] == "PROCESSING"


@pytest.mark.asyncio
async def test_get_image_not_found():
    image_id = str(uuid4())
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = client.get(f"/api/v1/images/{image_id}")
        assert response.status_code == 404


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Image Processing Service"
    assert data["version"] == "1.0.0"
    assert "/docs" in data["docs"]
    assert "/health" in data["health"]
    assert "/api/v1" in data["api"]


@pytest.mark.asyncio
async def test_health_endpoint():
    """Тест эндпоинта проверки здоровья"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "rabbitmq" in data
