import base64
import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.entities import KnownPerson, User
from app.schemas.requests import KnownPersonUpdate
from app.schemas.responses import KnownPersonResponse

router = APIRouter(prefix="/persons", tags=["Known Persons"])

REQUIRED_ANGLES = ["front", "left", "right", "up", "down"]


def _generate_embedding(image_data: bytes) -> list[float]:
    """Deterministic pseudo-embedding from image hash (production: InsightFace)."""
    digest = hashlib.sha256(image_data).digest()
    return [((b / 255.0) * 2 - 1) for b in digest[:128]]


@router.get("", response_model=list[KnownPersonResponse])
async def list_persons(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(KnownPerson).where(KnownPerson.is_active.is_(True)).order_by(KnownPerson.name))
    persons = result.scalars().all()
    return [
        KnownPersonResponse(
            id=p.id,
            name=p.name,
            role=p.role,
            access_level=p.access_level,
            is_active=p.is_active,
            visit_count=p.visit_count,
            last_seen=p.last_seen,
            embedding_count=len(p.embeddings or []),
        )
        for p in persons
    ]


@router.post("/register", response_model=KnownPersonResponse)
async def register_person(
    name: str = Form(...),
    role: str = Form("employee"),
    access_level: str = Form("authorized"),
    front: UploadFile = File(...),
    left: UploadFile = File(...),
    right: UploadFile = File(...),
    up: UploadFile = File(...),
    down: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Phase 2: Register known person with multi-angle face captures."""
    photos = {"front": front, "left": left, "right": right, "up": up, "down": down}
    embeddings = []
    photo_paths = []

    for angle, upload in photos.items():
        data = await upload.read()
        if len(data) < 100:
            raise HTTPException(400, f"Invalid image for angle: {angle}")
        embeddings.append(_generate_embedding(data))
        photo_paths.append(f"data/faces/{name.replace(' ', '_')}_{angle}.jpg")

    person = KnownPerson(
        name=name,
        role=role,
        access_level=access_level,
        embeddings=embeddings,
        photo_paths=photo_paths,
    )
    db.add(person)
    await db.flush()

    return KnownPersonResponse(
        id=person.id,
        name=person.name,
        role=person.role,
        access_level=person.access_level,
        is_active=person.is_active,
        visit_count=0,
        last_seen=None,
        embedding_count=len(embeddings),
    )


@router.patch("/{person_id}", response_model=KnownPersonResponse)
async def update_person(
    person_id: UUID,
    req: KnownPersonUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(KnownPerson).where(KnownPerson.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(404, "Person not found")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(person, field, value)
    await db.flush()
    return KnownPersonResponse(
        id=person.id,
        name=person.name,
        role=person.role,
        access_level=person.access_level,
        is_active=person.is_active,
        visit_count=person.visit_count,
        last_seen=person.last_seen,
        embedding_count=len(person.embeddings or []),
    )


@router.delete("/{person_id}")
async def delete_person(
    person_id: UUID,
    hard: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(KnownPerson).where(KnownPerson.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(404, "Person not found")
    if hard:
        await db.delete(person)
    else:
        person.is_active = False
    await db.flush()
    return {"status": "deleted" if hard else "deactivated", "id": str(person_id)}
