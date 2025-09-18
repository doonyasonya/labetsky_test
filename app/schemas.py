from pydantic import BaseModel
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime


class ImageBase(BaseModel):
    pass


class ImageCreate(ImageBase):
    pass


class ImageResponse(BaseModel):
    id: UUID
    status: str
    original_url: str
    thumbnails: Dict[str, str]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    task_id: UUID
    status: str


class HealthResponse(BaseModel):
    status: str
    db: str
    rabbitmq: str
