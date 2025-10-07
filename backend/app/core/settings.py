# Pydantic settings: environment-driven configuration.
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Mongo connection
    MONGO_URI: str = "mongodb://mongo:27017"
    MONGO_DB: str = "aiinfl"

    # Public base URL for serving previews
    BASE_URL: str = "http://localhost:8000"

    # LLM key for captions/hashtags (cheap)
    OPENAI_API_KEY: str | None = None

    # Feature flags (keep images cheap during dev)
    USE_AI_IMAGES: bool = False

    # Trends defaults
    TRENDS_GEO: str = "HU"     # default: Hungary
    TRENDS_WINDOW: str = "90d" # "7d" | "30d" | "90d"
    TRENDS_TTL_SECONDS: int = 24 * 3600  # cache: 24h


    # Stable Diffusion (HuggingFace + StabilityAI)
    HF_TOKEN: str | None = None
    SDXL_MODEL: str = "stabilityai/stable-diffusion-xl-base-1.0"
    STABILITY_API_KEY: str | None = None
    STABILITY_ENGINE: str = "sdxl-1024-v1-0"
    MEDIA_DIR: str = "./uploads/images"

    class Config:
        env_file = ".env"

settings = Settings()
