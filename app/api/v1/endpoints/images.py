from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from pathlib import Path
import json
import aiofiles
import aio_pika
from typing import Optional
import os

from app.dependencies import get_db
from app.crud import create_image, update_image_status, get_image
from app.schemas import TaskResponse, ImageResponse
from app.core.config import settings

router = APIRouter()


@router.post("/images", response_model=TaskResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPEG/PNG allowed")

    # Сохранить файл
    file_extension = Path(file.filename).suffix if file.filename else '.jpg'
    file_id = uuid4()
    file_path = (Path(settings.STORAGE_PATH) / "original" /
                 f"{file_id}{file_extension}")
    file_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    original_url = str(file_path)
    image = await create_image(db, original_url)

    # Отправить в RabbitMQ
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue("images", durable=True)

        message_body = json.dumps({
            "image_id": str(image.id),
            "original_path": original_url
        })

        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body.encode()),
            routing_key="images"
        )

    await update_image_status(db, image.id, "PROCESSING")

    return TaskResponse(task_id=image.id, status="PROCESSING")


@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_image_info(
    image_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        uuid_image_id = UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    image = await get_image(db, uuid_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return ImageResponse.model_validate(image)


@router.get("/images/{image_id}/file")
async def view_image_file(
    image_id: str,
    size: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Просмотр файла изображения в браузере
    
    Args:
        image_id: UUID изображения
        size: Размер миниатюры (100x100, 300x300, 1200x1200)
              или None для оригинала
    """
    try:
        uuid_image_id = UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    image = await get_image(db, uuid_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if image.status != "DONE":
        raise HTTPException(
            status_code=409, 
            detail=f"Image is not ready. Status: {image.status}"
        )

    # Определяем путь к файлу
    if size:
        if size not in ["100x100", "300x300", "1200x1200"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid size. Available: 100x100, 300x300, 1200x1200"
            )
        
        if size not in image.thumbnails:
            raise HTTPException(
                status_code=404, 
                detail=f"Thumbnail {size} not found"
            )
        
        file_path = Path(image.thumbnails[size])
    else:
        file_path = Path(image.original_url)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Возвращаем файл для просмотра в браузере
    return FileResponse(
        file_path,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f"inline; filename={file_path.name}"
        }
    )


@router.get("/images/{image_id}/download")
async def download_image_file(
    image_id: str,
    size: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Скачивание файла изображения
    
    Args:
        image_id: UUID изображения
        size: Размер миниатюры (100x100, 300x300, 1200x1200)
              или None для оригинала
    """
    try:
        uuid_image_id = UUID(image_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    image = await get_image(db, uuid_image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if image.status != "DONE":
        raise HTTPException(
            status_code=409, 
            detail=f"Image is not ready. Status: {image.status}"
        )

    # Определяем путь к файлу и имя для скачивания
    if size:
        if size not in ["100x100", "300x300", "1200x1200"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid size. Available: 100x100, 300x300, 1200x1200"
            )
        
        if size not in image.thumbnails:
            raise HTTPException(
                status_code=404, 
                detail=f"Thumbnail {size} not found"
            )
        
        file_path = Path(image.thumbnails[size])
        # Создаем красивое имя файла для скачивания
        original_name = os.path.splitext(Path(image.original_url).name)[0]
        download_filename = f"{original_name}_{size}.jpg"
    else:
        file_path = Path(image.original_url)
        download_filename = file_path.name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Возвращаем файл для скачивания
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=download_filename,
        headers={
            "Content-Disposition": f"attachment; filename={download_filename}"
        }
    )
