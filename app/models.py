from sqlalchemy import Column, String, DateTime, JSON, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Image(Base):
    __tablename__ = "images"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    status = Column(String(20), nullable=False)
    original_url = Column(String, nullable=False)
    thumbnails = Column(JSON, default=dict)
    error_message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        Index('ix_images_status', 'status'),
        Index('ix_images_created_at', 'created_at'),
    )
