import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.routers import auth, users, modules, topics, quiz, progress, achievements, chat, coding, assessment, admin, dashboard
from app.utils.logger import logger

# ------------------------------------------------------------------
# Rate limiter global (slowapi) · API_RATE_LIMIT_PER_MINUTE req/min/IP
# ------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.API_RATE_LIMIT_PER_MINUTE}/minute"],
)

app = FastAPI(
    title="Tutor IA - IESTP RFA",
    description="Sistema de Tutoría Inteligente con IA Generativa para Aplicaciones Móviles",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Request logging middleware · correlation id + timing
# ------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    with logger.contextualize(request_id=request_id, path=request.url.path, method=request.method):
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled exception in request pipeline")
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
        )
        response.headers["X-Request-ID"] = request_id
        return response


# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(modules.router, prefix="/api/v1")
app.include_router(topics.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(achievements.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(coding.router, prefix="/api/v1")
app.include_router(assessment.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "tutor-ia-rfa"}


@app.get("/api/v1/health")
async def api_health():
    return {"status": "ok", "version": "1.0.0"}
