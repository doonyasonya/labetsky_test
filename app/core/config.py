from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    STORAGE_PATH: str = "/storage"
    APP_NAME: str = "ImageProcessingService"
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "Image Processing API"

    class Config:
        env_file = ".env"


settings = Settings()
