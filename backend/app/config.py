from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://tutor_user:tutor_pass_dev@localhost:5432/tutordb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct-q4_K_M"
    OLLAMA_EMBED_MODEL: str = "mxbai-embed-large"
    OLLAMA_TIMEOUT: int = 120
    EMBEDDING_DIMENSION: int = 1024

    # JWT
    SECRET_KEY: str = "REEMPLAZAR_CON_256_BITS_ALEATORIOS"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Aplicación
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'
    MAX_UPLOAD_SIZE_MB: int = 50

    # Rate limiting
    CHAT_RATE_LIMIT_PER_HOUR: int = 20
    API_RATE_LIMIT_PER_MINUTE: int = 100

    # RAG
    RAG_TOP_K: int = 7  # Sprint 4 iter v2: 5 → 7 (más contexto, mejor recall)
    RAG_SIMILARITY_THRESHOLD: float = 0.65  # Sprint 4 iter v2: 0.70 → 0.65 (permite más chunks relevantes)
    RAG_CONTEXT_WINDOW: int = 5
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Quiz IA
    QUIZ_NUM_QUESTIONS: int = 5
    QUIZ_SESSION_TTL: int = 1800  # 30 minutos

    # Uploads
    UPLOAD_DIR: str = "./uploads"

    # Admin inicial
    ADMIN_EMAIL: str = "admin@iestprfa.edu.pe"
    ADMIN_PASSWORD: str = "Admin123!"
    ADMIN_NAME: str = "Administrador del Sistema"

    @property
    def cors_origins(self) -> List[str]:
        return json.loads(self.BACKEND_CORS_ORIGINS)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
