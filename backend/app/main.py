from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, users, modules, topics, quiz, progress, achievements, chat, coding

app = FastAPI(
    title="Tutor IA - IESTP RFA",
    description="Sistema de Tutoría Inteligente con IA Generativa para Aplicaciones Móviles",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(modules.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(achievements.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(coding.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "tutor-ia-rfa"}


@app.get("/api/v1/health")
async def api_health():
    return {"status": "ok", "version": "1.0.0"}
