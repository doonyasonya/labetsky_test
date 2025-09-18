from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/images_db"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    STORAGE_PATH: str = "/storage"
    APP_NAME: str = "ImageProcessingService"
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "Image Processing API"

    class Config:
        env_file = ".env"


settings = Settings()
