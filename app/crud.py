from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict
from uuid import UUID

from app.models import Image


async def create_image(db: AsyncSession, original_url: str) -> Image:
    image = Image(status="NEW", original_url=original_url)
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


async def get_image(db: AsyncSession, image_id: UUID) -> Optional[Image]:
    result = await db.execute(select(Image).filter(Image.id == image_id))
    return result.scalar_one_or_none()


async def update_image_status(
    db: AsyncSession,
    image_id: UUID,
    status: str,
    thumbnails: Optional[Dict[str, str]] = None,
    error: Optional[str] = None,
) -> Optional[Image]:
    image = await get_image(db, image_id)
    if image:
        image.status = status
        if thumbnails is not None:
            image.thumbnails = thumbnails
        if error is not None:
            image.error_message = error
        await db.commit()
        await db.refresh(image)
    return image
