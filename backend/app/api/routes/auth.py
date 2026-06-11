from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.config import get_settings
from app.database import get_db
from app.models.entities import User
from app.schemas.requests import LoginRequest
from app.schemas.responses import TokenResponse
from app.security import verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    token = jwt.encode({"sub": str(user.id), "exp": expire}, settings.secret_key, algorithm="HS256")
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(user: User = Depends(require_admin)):
    return {"id": str(user.id), "email": user.email, "full_name": user.full_name, "is_admin": user.is_admin}
