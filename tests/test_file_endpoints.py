import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
import tempfile
import os

from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_view_image_file_not_found():
    """Тест просмотра несуществующего изображения"""
    image_id = str(uuid4())
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = client.get(f"/api/v1/images/{image_id}/file")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_view_image_file_not_ready():
    """Тест просмотра изображения, которое еще не обработано"""
    image_id = str(uuid4())
    get_patch = 'app.api.v1.endpoints.images.get_image'
    
    # Создаем мок изображения со статусом PROCESSING
    mock_image = MagicMock()
    mock_image.status = "PROCESSING"
    
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_image
        response = client.get(f"/api/v1/images/{image_id}/file")
        assert response.status_code == 409
        assert "not ready" in response.json()["detail"]


@pytest.mark.asyncio
async def test_view_image_file_invalid_uuid():
    """Тест просмотра с неверным UUID"""
    response = client.get("/api/v1/images/invalid-uuid/file")
    assert response.status_code == 400
    assert "Invalid UUID" in response.json()["detail"]


@pytest.mark.asyncio
async def test_view_image_file_success():
    """Тест успешного просмотра изображения"""
    image_id = str(uuid4())
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp.write(b'fake image data')
        tmp_path = tmp.name
    
    try:
        # Создаем мок изображения
        mock_image = MagicMock()
        mock_image.status = "DONE"
        mock_image.original_url = tmp_path
        mock_image.thumbnails = {
            "100x100": f"{tmp_path}_100x100.jpg",
            "300x300": f"{tmp_path}_300x300.jpg"
        }
        
        get_patch = 'app.api.v1.endpoints.images.get_image'
        with patch(get_patch, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_image
            
            # Тест просмотра оригинала
            response = client.get(f"/api/v1/images/{image_id}/file")
            assert response.status_code == 200
            
    finally:
        # Удаляем временный файл
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_view_thumbnail_not_found():
    """Тест просмотра несуществующей миниатюры"""
    image_id = str(uuid4())
    
    mock_image = MagicMock()
    mock_image.status = "DONE"
    mock_image.thumbnails = {"100x100": "/path/to/thumb.jpg"}
    
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_image
        
        response = client.get(
            f"/api/v1/images/{image_id}/file?size=300x300"
        )
        assert response.status_code == 404
        assert "Thumbnail 300x300 not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_view_image_invalid_size():
    """Тест просмотра с неверным размером"""
    image_id = str(uuid4())
    
    mock_image = MagicMock()
    mock_image.status = "DONE"
    mock_image.thumbnails = {}
    
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_image
        
        response = client.get(
            f"/api/v1/images/{image_id}/file?size=invalid"
        )
        assert response.status_code == 400
        assert "Invalid size" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_image_file_not_found():
    """Тест скачивания несуществующего изображения"""
    image_id = str(uuid4())
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = client.get(f"/api/v1/images/{image_id}/download")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_image_file_invalid_size():
    """Тест скачивания с неверным размером"""
    image_id = str(uuid4())
    
    mock_image = MagicMock()
    mock_image.status = "DONE"
    mock_image.thumbnails = {}
    
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_image
        
        response = client.get(
            f"/api/v1/images/{image_id}/download?size=invalid"
        )
        assert response.status_code == 400
        assert "Invalid size" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_image_file_missing_thumbnail():
    """Тест скачивания несуществующей миниатюры"""
    image_id = str(uuid4())
    
    mock_image = MagicMock()
    mock_image.status = "DONE"
    mock_image.thumbnails = {"100x100": "/path/to/thumb.jpg"}
    
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_image
        
        response = client.get(
            f"/api/v1/images/{image_id}/download?size=300x300"
        )
        assert response.status_code == 404
        assert "Thumbnail 300x300 not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_image_file_success():
    """Тест успешного скачивания изображения"""
    image_id = str(uuid4())
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp.write(b'fake image data')
        tmp_path = tmp.name
    
    try:
        mock_image = MagicMock()
        mock_image.status = "DONE"
        mock_image.original_url = tmp_path
        mock_image.thumbnails = {
            "100x100": tmp_path
        }
        
        get_patch = 'app.api.v1.endpoints.images.get_image'
        with patch(get_patch, new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_image
            
            # Тест скачивания миниатюры
            response = client.get(
                f"/api/v1/images/{image_id}/download?size=100x100"
            )
            assert response.status_code == 200
            assert (response.headers["content-type"] == 
                    "application/octet-stream")
            
            # Тест скачивания оригинала
            response = client.get(
                f"/api/v1/images/{image_id}/download"
            )
            assert response.status_code == 200
            assert (response.headers["content-type"] == 
                    "application/octet-stream")
            
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@pytest.mark.asyncio
async def test_download_file_not_on_disk():
    """Тест скачивания когда файл отсутствует на диске"""
    image_id = str(uuid4())
    
    mock_image = MagicMock()
    mock_image.status = "DONE"
    mock_image.original_url = "/nonexistent/path/file.jpg"
    mock_image.thumbnails = {}
    
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_image
        
        response = client.get(f"/api/v1/images/{image_id}/download")
        assert response.status_code == 404
        assert "File not found on disk" in response.json()["detail"]


@pytest.mark.asyncio
async def test_view_file_not_on_disk():
    """Тест просмотра когда файл отсутствует на диске"""
    image_id = str(uuid4())
    
    mock_image = MagicMock()
    mock_image.status = "DONE"
    mock_image.original_url = "/nonexistent/path/file.jpg"
    mock_image.thumbnails = {}
    
    get_patch = 'app.api.v1.endpoints.images.get_image'
    with patch(get_patch, new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_image
        
        response = client.get(f"/api/v1/images/{image_id}/file")
        assert response.status_code == 404
        assert "File not found on disk" in response.json()["detail"]