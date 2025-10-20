from fastapi import APIRouter, HTTPException
from typing import List

from .. import main as state
from ..core.models import OwnerRecord
from ..core.utils import dump_yaml_entities

router = APIRouter(prefix="/api", tags=["owners"])


@router.get("/owners", response_model=List[OwnerRecord])
async def list_owners():
    return list(state.OWNER_DB.values())


@router.post("/owners", response_model=OwnerRecord, status_code=201)
async def add_owner(payload: OwnerRecord):
    key = payload.name.strip().lower()
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid owner name: lowercase alphanumeric and underscore only")
    if key in state.OWNER_DB:
        raise HTTPException(status_code=409, detail="Owner already exists")
    state.OWNER_DB[key] = {
        "name": key,
        "bankaccounts": [b.strip().lower() for b in payload.bankaccounts],
        "properties": [p.strip().lower() for p in payload.properties],
        "companies": [c.strip().lower() for c in payload.companies],
    }
    # persist YAML
    try:
        if state.OWNERS_CSV_PATH:
            dump_yaml_entities(state.OWNERS_CSV_PATH.with_suffix('.yaml'), list(state.OWNER_DB.values()), key_field='name')
    except Exception:
        pass
    return state.OWNER_DB[key]


@router.delete("/owners/{name}", status_code=204)
async def delete_owner(name: str):
    key = name.strip().lower()
    if key not in state.OWNER_DB:
        raise HTTPException(status_code=404, detail="Owner not found")
    del state.OWNER_DB[key]
    # persist YAML
    try:
        if state.OWNERS_CSV_PATH:
            dump_yaml_entities(state.OWNERS_CSV_PATH.with_suffix('.yaml'), list(state.OWNER_DB.values()), key_field='name')
    except Exception:
        pass
    return
