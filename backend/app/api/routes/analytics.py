from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.entities import User
from app.schemas.requests import SummaryRequest
from app.schemas.responses import AnalyticsResponse, SummaryResponse
from app.services.ai_summary import ai_summary_service
from app.services.analytics import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsResponse)
async def dashboard(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    return await analytics_service.get_dashboard(db)


@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(
    req: SummaryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    from datetime import datetime, timezone

    summary = await ai_summary_service.generate_daily_summary(db, req.room_id)
    return SummaryResponse(
        period=req.period,
        room_id=req.room_id,
        narrative=summary.narrative,
        stats=summary.stats,
        generated_at=datetime.now(timezone.utc),
    )
