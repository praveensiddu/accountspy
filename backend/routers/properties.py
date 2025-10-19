from fastapi import APIRouter, HTTPException
from typing import List

from .. import main as state
from ..core.models import Property

router = APIRouter(prefix="/api", tags=["properties"])


@router.get("/properties", response_model=List[Property])
async def list_properties():
    return list(state.DB.values())


@router.get("/properties/{prop_id}", response_model=Property)
async def get_property(prop_id: str):
    item = state.DB.get(prop_id)
    if not item:
        raise HTTPException(status_code=404, detail="Property not found")
    return item


@router.post("/properties", response_model=Property, status_code=201)
async def add_property(payload: Property):
    key = payload.property
    if key in state.DB:
        raise HTTPException(status_code=409, detail="Property already exists")
    comp = (payload.propMgmgtComp or "").strip().lower()
    if not comp or not state.ALNUM_LOWER_RE.match(comp):
        raise HTTPException(status_code=400, detail="Invalid propMgmgtComp: must be lowercase alphanumeric")
    if comp not in state.COMP_DB:
        raise HTTPException(status_code=400, detail="propMgmgtComp not found in companies")
    item = payload.dict()
    item["propMgmgtComp"] = comp
    state.DB[key] = item
    return state.DB[key]


@router.delete("/properties/{prop_id}", status_code=204)
async def delete_property(prop_id: str):
    if prop_id not in state.DB:
        raise HTTPException(status_code=404, detail="Property not found")
    del state.DB[prop_id]
    return
