from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.foods.schemas import FoodDetail, FoodSearchResponse, ImportReport, ImportRequest
from app.foods.tka_provider import TkaProvider


router = APIRouter(prefix="/api/v1", tags=["foods"])


@router.get("/foods/search", response_model=FoodSearchResponse)
def search_foods(
    q: str = Query(min_length=1, max_length=100),
    locale: str = Query(default="zh-CN", max_length=16),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> FoodSearchResponse:
    return FoodSearchResponse(items=TkaProvider(session).search(q, locale=locale))


@router.get("/foods/{source_food_id}", response_model=FoodDetail)
def get_food(
    source_food_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> FoodDetail:
    food = TkaProvider(session).get_food(source_food_id)
    if food is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到食物")
    return food


@router.post("/admin/foods/import", response_model=ImportReport)
def import_foods(
    body: ImportRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ImportReport:
    root = settings.tka_import_root.resolve()
    path = Path(body.path).resolve()
    if path != root and root not in path.parents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件不在允许目录")
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导入文件不存在")
    return TkaProvider(session).import_dataset(path, body.version, dry_run=body.dry_run)

