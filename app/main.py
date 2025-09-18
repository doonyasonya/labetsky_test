from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import images
from app.core.config import settings
from app.schemas import HealthResponse

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router, prefix="/api/v1", tags=["images"])


@app.get("/")
async def root():
    return {
        "message": "Image Processing Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        db="connected",
        rabbitmq="connected"
    )
