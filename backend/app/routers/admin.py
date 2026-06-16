"""
routers/admin.py — Endpoints de administración.
Incluye: banco de evaluación, niveles usuarios, CRUD contenido
(módulos/temas/quiz/coding), corpus RAG (docs), gestión usuarios,
generador IA de desafíos.
"""
import os
import uuid
from pathlib import Path

from fastapi import (
    APIRouter, Depends, HTTPException, status, Query,
    UploadFile, File, BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.config import settings
from app.dependencies import require_admin, get_redis
from app.models.user import User
from app.models.user_level import UserLevel
from app.models.module import Module
from app.models.topic import Topic
from app.models.quiz import QuizQuestion
from app.models.coding import CodingChallenge
from app.models.document import Document
from app.models.assessment_bank import EntryAssessmentBank
from app.models.learning_resource import LearningResource
from app.schemas.learning_resource import (
    LearningResourceResponse,
    LearningResourceCreate,
    LearningResourceUpdate,
)
from app.schemas.admin_bank import (
    AssessmentBankItemCreate,
    AssessmentBankItemUpdate,
    AssessmentBankItemResponse,
    AdminUserLevelRow,
    AdminUserLevelOverride,
)
from app.schemas.admin import (
    ModuleCreateRequest, ModuleUpdateRequest, ModuleAdminResponse,
    TopicCreateRequest, TopicUpdateRequest, TopicAdminResponse,
    QuizQuestionCreateRequest, QuizQuestionUpdateRequest, QuizQuestionAdminResponse,
    CodingChallengeCreateRequest, CodingChallengeUpdateRequest, CodingChallengeAdminResponse,
    GenerateChallengeRequest, GeneratedChallengePreview,
    DocumentAdminResponse,
    UserAdminRow, UserAdminUpdate,
)
from app.schemas.user_level import UserLevelResponse
from app.services.companion_service import invalidate_companion
from app.services.resource_recommender_service import invalidate_resource_recs
from app.services.leveling_service import upsert_user_level
from app.services.ingest_service import process_document
from app.services.challenge_generator_service import (
    generate_challenge, ChallengeGenerationError,
)
from app.utils.logger import logger

router = APIRouter(prefix="/admin", tags=["admin"])


ALLOWED_MIME = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


# ==========================================================
# Assessment Bank CRUD
# ==========================================================

@router.get("/assessment-bank", response_model=list[AssessmentBankItemResponse])
async def list_bank(
    module_id: int | None = Query(None),
    difficulty: str | None = Query(None, pattern="^(easy|medium|hard)$"),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(EntryAssessmentBank)
    if module_id is not None:
        query = query.where(EntryAssessmentBank.module_id == module_id)
    if difficulty is not None:
        query = query.where(EntryAssessmentBank.difficulty == difficulty)
    query = query.order_by(EntryAssessmentBank.module_id, EntryAssessmentBank.id)
    result = await db.execute(query)
    items = result.scalars().all()
    return [AssessmentBankItemResponse.model_validate(i) for i in items]


@router.post("/assessment-bank", response_model=AssessmentBankItemResponse, status_code=status.HTTP_201_CREATED)
async def create_bank_item(
    data: AssessmentBankItemCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    item = EntryAssessmentBank(
        module_id=data.module_id,
        question_text=data.question_text,
        options=data.options,
        correct_index=data.correct_index,
        difficulty=data.difficulty,
        created_by=admin.id,
        is_active=True,
    )
    db.add(item)
    await db.flush()
    await db.commit()
    return AssessmentBankItemResponse.model_validate(item)


@router.put("/assessment-bank/{item_id}", response_model=AssessmentBankItemResponse)
async def update_bank_item(
    item_id: int,
    data: AssessmentBankItemUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EntryAssessmentBank).where(EntryAssessmentBank.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pregunta no encontrada")
    if data.question_text is not None:
        item.question_text = data.question_text
    if data.options is not None:
        if len(data.options) != 4:
            raise HTTPException(status_code=400, detail="Debe haber exactamente 4 opciones")
        item.options = data.options
    if data.correct_index is not None:
        item.correct_index = data.correct_index
    if data.difficulty is not None:
        item.difficulty = data.difficulty
    if data.is_active is not None:
        item.is_active = data.is_active
    await db.flush()
    await db.commit()
    return AssessmentBankItemResponse.model_validate(item)


@router.delete("/assessment-bank/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_item(
    item_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EntryAssessmentBank).where(EntryAssessmentBank.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pregunta no encontrada")
    await db.delete(item)
    await db.commit()


# ==========================================================
# Learning Resources CRUD (videos/libros curados — Fase 3)
# ==========================================================

@router.get("/resources", response_model=list[LearningResourceResponse])
async def list_resources_admin(
    module_id: int | None = Query(None),
    topic_id: int | None = Query(None),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(LearningResource)
    if module_id is not None:
        query = query.where(LearningResource.module_id == module_id)
    if topic_id is not None:
        query = query.where(LearningResource.topic_id == topic_id)
    query = query.order_by(LearningResource.module_id, LearningResource.order_index, LearningResource.id)
    result = await db.execute(query)
    return [LearningResourceResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/resources", response_model=LearningResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: LearningResourceCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    item = LearningResource(
        module_id=data.module_id,
        topic_id=data.topic_id,
        kind=data.kind,
        title=data.title,
        url=data.url,
        author=data.author,
        description=data.description,
        order_index=data.order_index,
        created_by=admin.id,
        is_active=True,
    )
    db.add(item)
    await db.flush()
    await db.commit()
    await db.refresh(item)
    return LearningResourceResponse.model_validate(item)


@router.put("/resources/{resource_id}", response_model=LearningResourceResponse)
async def update_resource(
    resource_id: int,
    data: LearningResourceUpdate,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LearningResource).where(LearningResource.id == resource_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso no encontrado")
    for field in ("module_id", "topic_id", "kind", "title", "url", "author", "description", "order_index", "is_active"):
        value = getattr(data, field)
        if value is not None:
            setattr(item, field, value)
    await db.flush()
    await db.commit()
    await db.refresh(item)
    return LearningResourceResponse.model_validate(item)


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LearningResource).where(LearningResource.id == resource_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso no encontrado")
    await db.delete(item)
    await db.commit()


# ==========================================================
# User Level overview + Override
# ==========================================================

@router.get("/user-levels", response_model=list[AdminUserLevelRow])
async def list_user_levels(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(User, UserLevel)
        .outerjoin(UserLevel, UserLevel.user_id == User.id)
        .where(User.role == "student")
        .order_by(User.full_name)
    )
    result = await db.execute(query)
    rows = result.all()
    return [
        AdminUserLevelRow(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            level=lvl.level if lvl else None,
            entry_score=lvl.entry_score if lvl else None,
            assessed_at=lvl.assessed_at if lvl else None,
            last_reassessed_at=lvl.last_reassessed_at if lvl else None,
        )
        for user, lvl in rows
    ]


@router.put("/user-levels/{user_id}", response_model=UserLevelResponse)
async def override_user_level(
    user_id: uuid.UUID,
    data: AdminUserLevelOverride,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    user_result = await db.execute(select(User).where(User.id == user_id))
    target = user_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    lvl_result = await db.execute(select(UserLevel).where(UserLevel.user_id == user_id))
    existing = lvl_result.scalar_one_or_none()
    score = existing.entry_score if existing else 50.0

    record = await upsert_user_level(
        db, user_id, data.level, score, reason=f"admin_override: {data.reason}"
    )
    await db.commit()
    # El companion depende del nivel: invalidar para que aparezca de inmediato
    await invalidate_companion(redis_client, user_id)
    await invalidate_resource_recs(redis_client, user_id)
    logger.info(f"Admin {admin.email} overrode user {user_id} level → {data.level}")
    return UserLevelResponse.model_validate(record)


# ==========================================================
# Modules CRUD
# ==========================================================

@router.get("/modules", response_model=list[ModuleAdminResponse])
async def admin_list_modules(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).order_by(Module.order_index))
    return [ModuleAdminResponse.model_validate(m) for m in result.scalars().all()]


@router.post("/modules", response_model=ModuleAdminResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_module(
    data: ModuleCreateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    module = Module(**data.model_dump())
    db.add(module)
    await db.flush()
    await db.commit()
    return ModuleAdminResponse.model_validate(module)


@router.put("/modules/{module_id}", response_model=ModuleAdminResponse)
async def admin_update_module(
    module_id: int,
    data: ModuleUpdateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(module, field, value)
    await db.flush()
    await db.commit()
    return ModuleAdminResponse.model_validate(module)


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_module(
    module_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Módulo no encontrado")
    await db.delete(module)
    await db.commit()


# ==========================================================
# Topics CRUD
# ==========================================================

@router.get("/topics", response_model=list[TopicAdminResponse])
async def admin_list_topics(
    module_id: int | None = Query(None),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Topic)
    if module_id is not None:
        query = query.where(Topic.module_id == module_id)
    query = query.order_by(Topic.module_id, Topic.order_index)
    result = await db.execute(query)
    return [TopicAdminResponse.model_validate(t) for t in result.scalars().all()]


@router.post("/topics", response_model=TopicAdminResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_topic(
    data: TopicCreateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    topic = Topic(**data.model_dump())
    db.add(topic)
    await db.flush()
    await db.commit()
    return TopicAdminResponse.model_validate(topic)


@router.put("/topics/{topic_id}", response_model=TopicAdminResponse)
async def admin_update_topic(
    topic_id: int,
    data: TopicUpdateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    await db.flush()
    await db.commit()
    return TopicAdminResponse.model_validate(topic)


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_topic(
    topic_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema no encontrado")
    await db.delete(topic)
    await db.commit()


# ==========================================================
# Quiz Questions CRUD (static bank)
# ==========================================================

@router.get("/quiz-questions", response_model=list[QuizQuestionAdminResponse])
async def admin_list_quiz_questions(
    topic_id: int | None = Query(None),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(QuizQuestion)
    if topic_id is not None:
        query = query.where(QuizQuestion.topic_id == topic_id)
    query = query.order_by(QuizQuestion.topic_id, QuizQuestion.order_index)
    result = await db.execute(query)
    return [QuizQuestionAdminResponse.model_validate(q) for q in result.scalars().all()]


@router.post("/quiz-questions", response_model=QuizQuestionAdminResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_quiz_question(
    data: QuizQuestionCreateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    q = QuizQuestion(**data.model_dump())
    db.add(q)
    await db.flush()
    await db.commit()
    return QuizQuestionAdminResponse.model_validate(q)


@router.put("/quiz-questions/{question_id}", response_model=QuizQuestionAdminResponse)
async def admin_update_quiz_question(
    question_id: int,
    data: QuizQuestionUpdateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pregunta no encontrada")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "options" and value is not None and len(value) != 4:
            raise HTTPException(status_code=400, detail="Debe haber exactamente 4 opciones")
        setattr(q, field, value)
    await db.flush()
    await db.commit()
    return QuizQuestionAdminResponse.model_validate(q)


@router.delete("/quiz-questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_quiz_question(
    question_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QuizQuestion).where(QuizQuestion.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pregunta no encontrada")
    await db.delete(q)
    await db.commit()


# ==========================================================
# Coding Challenges CRUD
# ==========================================================

@router.get("/coding-challenges", response_model=list[CodingChallengeAdminResponse])
async def admin_list_challenges(
    topic_id: int | None = Query(None),
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(CodingChallenge)
    if topic_id is not None:
        query = query.where(CodingChallenge.topic_id == topic_id)
    query = query.order_by(CodingChallenge.topic_id, CodingChallenge.order_index)
    result = await db.execute(query)
    return [CodingChallengeAdminResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/coding-challenges", response_model=CodingChallengeAdminResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_challenge(
    data: CodingChallengeCreateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    challenge = CodingChallenge(**data.model_dump())
    db.add(challenge)
    await db.flush()
    await db.commit()
    return CodingChallengeAdminResponse.model_validate(challenge)


@router.put("/coding-challenges/{challenge_id}", response_model=CodingChallengeAdminResponse)
async def admin_update_challenge(
    challenge_id: int,
    data: CodingChallengeUpdateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CodingChallenge).where(CodingChallenge.id == challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desafío no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(challenge, field, value)
    await db.flush()
    await db.commit()
    return CodingChallengeAdminResponse.model_validate(challenge)


@router.delete("/coding-challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_challenge(
    challenge_id: int,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CodingChallenge).where(CodingChallenge.id == challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desafío no encontrado")
    await db.delete(challenge)
    await db.commit()


# ==========================================================
# AI Challenge Generator
# ==========================================================

@router.post("/coding-challenges/generate", response_model=GeneratedChallengePreview)
async def admin_generate_challenge(
    body: GenerateChallengeRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate a coding challenge via LLM. Does NOT persist. Admin reviews + POSTs to /coding-challenges."""
    result = await db.execute(select(Topic).where(Topic.id == body.topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema no encontrado")
    if not topic.content or len(topic.content.strip()) < 100:
        raise HTTPException(status_code=400, detail="El tema no tiene suficiente contenido para generar un desafío")

    try:
        generated = await generate_challenge(
            topic_content=topic.content,
            difficulty=body.difficulty,
            target_level=body.target_level,
        )
    except ChallengeGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No se pudo generar el desafío: {e}",
        )

    return GeneratedChallengePreview(
        title=generated.title,
        description=generated.description,
        hints=generated.hints,
        solution_code=generated.solution_code,
        difficulty=generated.difficulty,
        language=generated.language,
    )


# ==========================================================
# Documents (RAG corpus)
# ==========================================================

@router.get("/documents", response_model=list[DocumentAdminResponse])
async def admin_list_documents(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).order_by(desc(Document.created_at)))
    return [DocumentAdminResponse.model_validate(d) for d in result.scalars().all()]


@router.post("/documents", response_model=DocumentAdminResponse, status_code=status.HTTP_202_ACCEPTED)
async def admin_upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to the RAG corpus. Processing happens in background."""
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no soportado: {file.content_type}",
        )

    # Enforce size limit
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo supera el límite de {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = uuid.uuid4()
    extension = ALLOWED_MIME[file.content_type]
    stored_name = f"{doc_id}{extension}"
    file_path = upload_dir / stored_name
    file_path.write_bytes(content)

    document = Document(
        id=doc_id,
        original_filename=file.filename or stored_name,
        stored_filename=stored_name,
        file_size_bytes=len(content),
        mime_type=file.content_type,
        status="pending",
        uploaded_by=admin.id,
    )
    db.add(document)
    await db.flush()
    await db.commit()

    # Schedule background processing
    background_tasks.add_task(process_document, doc_id, str(file_path), db)
    logger.info(f"Documento {doc_id} encolado para procesamiento")

    return DocumentAdminResponse.model_validate(document)


@router.post("/documents/{doc_id}/reprocess", response_model=DocumentAdminResponse)
async def admin_reprocess_document(
    doc_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reprocess a document that failed or needs re-ingestion."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")

    file_path = Path(settings.UPLOAD_DIR) / doc.stored_filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Archivo físico no encontrado en el servidor",
        )

    doc.status = "pending"
    doc.error_message = None
    doc.chunk_count = 0
    doc.processed_at = None
    await db.flush()
    await db.commit()

    background_tasks.add_task(process_document, doc.id, str(file_path), db)
    logger.info(f"Reprocesando documento {doc_id}")
    return DocumentAdminResponse.model_validate(doc)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_document(
    doc_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")

    file_path = Path(settings.UPLOAD_DIR) / doc.stored_filename
    try:
        if file_path.exists():
            file_path.unlink()
    except OSError as e:
        logger.warning(f"No se pudo borrar archivo {file_path}: {e}")

    await db.delete(doc)
    await db.commit()


# ==========================================================
# Users administration
# ==========================================================

@router.get("/users", response_model=list[UserAdminRow])
async def admin_list_users(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(User, UserLevel)
        .outerjoin(UserLevel, UserLevel.user_id == User.id)
        .order_by(User.created_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()
    return [
        UserAdminRow(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            level=lvl.level if lvl else None,
        )
        for u, lvl in rows
    ]


@router.put("/users/{user_id}", response_model=UserAdminRow)
async def admin_update_user(
    user_id: uuid.UUID,
    data: UserAdminUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == admin.id and data.is_active is False:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if data.role is not None:
        target.role = data.role
    if data.is_active is not None:
        target.is_active = data.is_active
    await db.flush()
    await db.commit()

    lvl_q = await db.execute(select(UserLevel).where(UserLevel.user_id == user_id))
    lvl = lvl_q.scalar_one_or_none()
    return UserAdminRow(
        id=target.id,
        email=target.email,
        full_name=target.full_name,
        role=target.role,
        is_active=target.is_active,
        created_at=target.created_at,
        level=lvl.level if lvl else None,
    )
