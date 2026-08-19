from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.media.models import MediaUpload


class MediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    content_type: str
    size_bytes: int


router = APIRouter(prefix="/api/v1/media", tags=["media"])
ALLOWED_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_BYTES = 8 * 1024 * 1024


@router.post("/uploads", response_model=MediaRead, status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MediaUpload:
    suffix = ALLOWED_TYPES.get(file.content_type or "")
    if suffix is None:
        raise HTTPException(status_code=415, detail="unsupported image type")
    content = await file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="image is too large")
    storage_key = f"{current_user.id}/{uuid4()}{suffix}"
    destination = (settings.media_root / storage_key).resolve()
    root = settings.media_root.resolve()
    if root not in destination.parents:
        raise HTTPException(status_code=400, detail="invalid storage path")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    upload = MediaUpload(
        user_id=current_user.id,
        storage_key=storage_key,
        content_type=file.content_type or "",
        size_bytes=len(content),
    )
    session.add(upload)
    session.commit()
    session.refresh(upload)
    return upload
