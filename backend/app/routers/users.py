from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.user_level import UserLevel
from app.schemas.user import UserResponse, UserUpdateRequest, PasswordChangeRequest
from app.schemas.user_level import UserLevelResponse, ReassessmentProposal, ReassessmentConfirmRequest
from app.schemas.auth import MessageResponse
from app.services.leveling_service import check_reassessment, apply_reassessment
from app.utils.security import verify_password, hash_password

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    await db.flush()
    return current_user


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )
    current_user.hashed_password = hash_password(data.new_password)
    await db.flush()
    return {"message": "Contraseña actualizada exitosamente"}


@router.get("/me/level", response_model=UserLevelResponse)
async def get_my_level(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Current student level + history. Empty fields if not yet assessed."""
    result = await db.execute(select(UserLevel).where(UserLevel.user_id == current_user.id))
    lvl = result.scalar_one_or_none()
    if not lvl:
        return UserLevelResponse(
            level=None,
            entry_score=None,
            assessed_at=None,
            last_reassessed_at=None,
            history=[],
        )
    return UserLevelResponse.model_validate(lvl)


@router.get("/me/reassessment", response_model=ReassessmentProposal)
async def get_reassessment_proposal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether system proposes to change the student's level."""
    proposal = await check_reassessment(db, current_user.id)
    return ReassessmentProposal(**{
        "should_reassess": proposal.get("should_reassess", False),
        "direction": proposal.get("direction"),
        "current_level": proposal.get("current_level"),
        "proposed_level": proposal.get("proposed_level"),
        "reason": proposal.get("reason"),
    })


@router.post("/me/reassess", response_model=UserLevelResponse)
async def accept_reassessment(
    body: ReassessmentConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply (or dismiss) a pending reassessment proposal."""
    proposal = await check_reassessment(db, current_user.id)
    if not proposal.get("should_reassess"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No hay propuesta de re-asignación pendiente",
        )

    if body.accept:
        await apply_reassessment(db, current_user.id, proposal)
        await db.commit()

    result = await db.execute(select(UserLevel).where(UserLevel.user_id == current_user.id))
    lvl = result.scalar_one_or_none()
    return UserLevelResponse.model_validate(lvl)
