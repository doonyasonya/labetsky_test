import asyncio
import aio_pika
import json
import sys
import logging
from pathlib import Path
from PIL import Image
from PIL.Image import Resampling
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import time

# Add project root to path
sys.path.append('/app')

from app.core.config import settings  # noqa: E402
from app.dependencies import AsyncSessionLocal  # noqa: E402
from app.crud import update_image_status  # noqa: E402

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_image(image_id: str, original_path: str, db: AsyncSession):
    logger.info(f"Processing image {image_id} from {original_path}")
    try:
        await update_image_status(db, UUID(image_id), "PROCESSING")

        # Загрузить оригинал
        with Image.open(original_path) as orig_img:
            logger.info(f"Original image size: {orig_img.size}")
            thumbnails = {}
            sizes = [(100, 100), (300, 300), (1200, 1200)]

            for width, height in sizes:
                thumb = orig_img.copy()
                thumb.thumbnail((width, height), resample=Resampling.LANCZOS)

                thumb_dir = (Path(settings.STORAGE_PATH) / "thumbs" /
                             f"{width}x{height}")
                thumb_dir.mkdir(parents=True, exist_ok=True)
                thumb_filename = f"{image_id}_{width}x{height}.jpg"
                thumb_path = thumb_dir / thumb_filename

                thumb.save(thumb_path, "JPEG", quality=85, optimize=True)
                thumbnails[f"{width}x{height}"] = str(thumb_path)
                thumb_info = f"Created thumbnail {width}x{height}: {thumb_path}"
                logger.info(thumb_info)

        await update_image_status(db, UUID(image_id), "DONE", thumbnails)
        logger.info(f"Successfully processed image {image_id}")

    except Exception as e:
        logger.error(f"Error processing image {image_id}: {e}")
        await update_image_status(db, UUID(image_id), "ERROR", error=str(e))
        raise


async def connect_to_rabbitmq_with_retry(max_retries=10, retry_delay=5):
    """Подключение к RabbitMQ с повторными попытками"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{max_retries})")
            connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            logger.info("Successfully connected to RabbitMQ")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Exiting.")
                raise


async def main():
    logger.info("Starting image processing worker...")
    
    connection = await connect_to_rabbitmq_with_retry()
    
    try:
        async with connection:
            channel = await connection.channel()
            
            # Устанавливаем QoS для обработки по одному сообщению за раз
            await channel.set_qos(prefetch_count=1)
            
            queue = await channel.declare_queue("images", durable=True)
            logger.info("Worker is ready to process messages")

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            data = json.loads(message.body.decode())
                            logger.info(f"Received message: {data}")
                            
                            async with AsyncSessionLocal() as db:
                                await process_image(
                                    data["image_id"], data["original_path"], db
                                )
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            # Сообщение будет отклонено и может быть обработано повторно
                            raise
    except Exception as e:
        logger.error(f"Fatal error in worker: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
