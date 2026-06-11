from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.entities import AlertRule, User
from app.schemas.requests import AlertRuleCreate, AlertRuleUpdate
from app.schemas.responses import AlertRuleResponse

router = APIRouter(prefix="/alerts", tags=["Alert Rules"])


@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(AlertRule).order_by(AlertRule.name))
    return result.scalars().all()


@router.post("/rules", response_model=AlertRuleResponse)
async def create_rule(req: AlertRuleCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    rule = AlertRule(
        name=req.name,
        event_type=req.event_type,
        min_severity=req.min_severity,
        channels=req.channels,
        sound_enabled=req.sound_enabled,
        room_ids=[str(r) for r in req.room_ids] if req.room_ids else None,
    )
    db.add(rule)
    await db.flush()
    return rule


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(
    rule_id: UUID,
    req: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        if field == "room_ids" and value is not None:
            value = [str(r) for r in value]
        setattr(rule, field, value)
    await db.flush()
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")
    await db.delete(rule)
    return {"status": "deleted"}
