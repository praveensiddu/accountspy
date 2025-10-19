from fastapi import APIRouter, HTTPException
from typing import List

# Use main module state
from .. import main as state
from ..core.utils import dump_yaml_entities
from ..core.models import TaxCategoryRecord

router = APIRouter(prefix="/api", tags=["tax-categories"])


@router.get("/tax-categories", response_model=List[TaxCategoryRecord])
async def list_tax_categories():
    return list(state.TAX_DB.values())


@router.post("/tax-categories", response_model=TaxCategoryRecord, status_code=201)
async def add_tax_category(payload: TaxCategoryRecord):
    key = (payload.category or "").strip().lower()
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid category: lowercase alphanumeric and underscore only")
    if key in state.TAX_DB:
        raise HTTPException(status_code=409, detail="Tax category already exists")
    state.TAX_DB[key] = {"category": key}
    if state.TAX_CSV_PATH:
        dump_yaml_entities(state.TAX_CSV_PATH.with_suffix('.yaml'), list(state.TAX_DB.values()), key_field='category')
    return state.TAX_DB[key]


@router.delete("/tax-categories/{category}", status_code=204)
async def delete_tax_category(category: str):
    key = category.strip().lower()
    if key not in state.TAX_DB:
        raise HTTPException(status_code=404, detail="Tax category not found")
    del state.TAX_DB[key]
    if state.TAX_CSV_PATH:
        dump_yaml_entities(state.TAX_CSV_PATH.with_suffix('.yaml'), list(state.TAX_DB.values()), key_field='category')
    return
