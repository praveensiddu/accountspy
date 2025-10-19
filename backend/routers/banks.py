from fastapi import APIRouter, HTTPException
from typing import List, Dict

# Use state from main module to keep a single source during incremental refactor
from .. import main as state
from ..core.utils import dump_yaml_entities

router = APIRouter(prefix="/api", tags=["banks"])


@router.get("/banks", response_model=List[Dict])
async def list_banks_config():
    return [state.BANKS_CFG_DB[k] for k in sorted(state.BANKS_CFG_DB.keys())]


@router.post("/banks", response_model=Dict, status_code=201)
async def add_bank_config(payload: Dict):
    name = (payload.get("name") or "").strip().lower()
    if not name or not state.ALNUM_UNDERSCORE_LOWER_RE.match(name):
        raise HTTPException(status_code=400, detail="Invalid name: use lowercase [a-z0-9_] only")
    if name in state.BANKS_CFG_DB:
        raise HTTPException(status_code=409, detail="Bank config already exists")
    cfg = dict(payload)
    cfg["name"] = name
    state.BANKS_CFG_DB[name] = cfg
    if state.BANKS_YAML_PATH:
        dump_yaml_entities(state.BANKS_YAML_PATH, list(state.BANKS_CFG_DB.values()), key_field='name')
    return cfg


@router.delete("/banks/{name}", status_code=204)
async def delete_bank_config(name: str):
    key = (name or "").strip().lower()
    if key not in state.BANKS_CFG_DB:
        raise HTTPException(status_code=404, detail="Bank config not found")
    del state.BANKS_CFG_DB[key]
    if state.BANKS_YAML_PATH:
        dump_yaml_entities(state.BANKS_YAML_PATH, list(state.BANKS_CFG_DB.values()), key_field='name')
    return
