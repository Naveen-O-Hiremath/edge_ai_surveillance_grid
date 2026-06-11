from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.entities import Camera, EnvironmentObject, Room, User
from app.schemas.requests import RoomCreate, RoomUpdate
from app.schemas.responses import RoomResponse

router = APIRouter(prefix="/rooms", tags=["Rooms"])


async def _room_response(db: AsyncSession, room: Room) -> RoomResponse:
    cam_count = (await db.execute(select(func.count()).where(Camera.room_id == room.id))).scalar() or 0
    obj_count = (await db.execute(select(func.count()).where(EnvironmentObject.room_id == room.id))).scalar() or 0
    return RoomResponse(
        id=room.id,
        name=room.name,
        description=room.description,
        baseline_learned=room.baseline_learned,
        created_at=room.created_at,
        camera_count=cam_count,
        object_count=obj_count,
    )


@router.get("", response_model=list[RoomResponse])
async def list_rooms(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(Room).order_by(Room.name))
    rooms = result.scalars().all()
    return [await _room_response(db, room) for room in rooms]


@router.post("", response_model=RoomResponse)
async def create_room(req: RoomCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    room = Room(name=req.name, description=req.description)
    db.add(room)
    await db.flush()
    return await _room_response(db, room)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")
    return await _room_response(db, room)


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    req: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    await db.flush()
    return await _room_response(db, room)


@router.delete("/{room_id}")
async def delete_room(room_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Room not found")
    await db.delete(room)
    await db.flush()
    return {"status": "deleted", "id": str(room_id)}
