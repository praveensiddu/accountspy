from fastapi import APIRouter, HTTPException
from typing import List

from .. import main as state
from ..core.models import Property
from ..core.utils import dump_yaml_entities

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
    comp = (payload.propMgmtComp or "").strip().lower()
    if not comp or not state.ALNUM_LOWER_RE.match(comp):
        raise HTTPException(status_code=400, detail="Invalid propMgmtComp: must be lowercase alphanumeric")
    if comp not in state.COMP_DB:
        raise HTTPException(status_code=400, detail="propMgmtComp not found in companies")
    item = payload.dict()
    item["propMgmtComp"] = comp
    state.DB[key] = item
    # persist YAML
    try:
        if state.CSV_PATH:
            dump_yaml_entities(state.CSV_PATH.with_suffix('.yaml'), list(state.DB.values()), key_field='property')
    except Exception:
        pass
    return state.DB[key]


@router.delete("/properties/{prop_id}", status_code=204)
async def delete_property(prop_id: str):
    if prop_id not in state.DB:
        raise HTTPException(status_code=404, detail="Property not found")
    del state.DB[prop_id]
    # persist YAML
    try:
        if state.CSV_PATH:
            dump_yaml_entities(state.CSV_PATH.with_suffix('.yaml'), list(state.DB.values()), key_field='property')
    except Exception:
        pass
    return
