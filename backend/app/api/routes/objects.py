from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.entities import EnvironmentObject, User
from app.schemas.requests import EnvironmentObjectUpdate, LabelUnknownObjectRequest
from app.schemas.responses import EnvironmentObjectResponse

router = APIRouter(prefix="/objects", tags=["Environment Objects"])


@router.get("/room/{room_id}", response_model=list[EnvironmentObjectResponse])
async def list_room_objects(room_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(
        select(EnvironmentObject).where(EnvironmentObject.room_id == room_id).order_by(EnvironmentObject.name)
    )
    return result.scalars().all()


@router.patch("/{object_id}", response_model=EnvironmentObjectResponse)
async def update_object(
    object_id: UUID,
    req: EnvironmentObjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(EnvironmentObject).where(EnvironmentObject.id == object_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(404, "Object not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    return obj


@router.delete("/{object_id}")
async def delete_object(object_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(EnvironmentObject).where(EnvironmentObject.id == object_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(404, "Object not found")
    await db.delete(obj)
    await db.flush()
    return {"status": "deleted", "id": str(object_id)}


@router.post("/{object_id}/label", response_model=EnvironmentObjectResponse)
async def label_unknown_object(
    object_id: UUID,
    req: LabelUnknownObjectRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(EnvironmentObject).where(EnvironmentObject.id == object_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(404, "Object not found")

    obj.name = req.name
    obj.label = req.name
    obj.category = req.category
    obj.is_tracked = req.is_tracked
    obj.admin_labeled = True
    obj.confidence = 100.0
    await db.flush()
    return obj
