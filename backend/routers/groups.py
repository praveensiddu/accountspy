from fastapi import APIRouter, HTTPException
from typing import List

from .. import main as state
from ..core.models import GroupRecord
from ..core.utils import dump_yaml_entities

router = APIRouter(prefix="/api", tags=["groups"])


@router.get("/groups", response_model=List[GroupRecord])
async def list_groups():
    return list(state.GROUP_DB.values())


@router.post("/groups", response_model=GroupRecord, status_code=201)
async def add_group(payload: GroupRecord):
    key = payload.groupname.strip().lower()
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid groupname: lowercase alphanumeric and underscore only")
    if key in state.GROUP_DB:
        raise HTTPException(status_code=409, detail="Group already exists")
    state.GROUP_DB[key] = {"groupname": key, "propertylist": [p.strip().lower() for p in payload.propertylist]}
    # persist YAML
    try:
        if state.GROUPS_CSV_PATH:
            dump_yaml_entities(state.GROUPS_CSV_PATH.with_suffix('.yaml'), list(state.GROUP_DB.values()), key_field='groupname')
    except Exception:
        pass
    return state.GROUP_DB[key]


@router.delete("/groups/{groupname}", status_code=204)
async def delete_group(groupname: str):
    key = groupname.strip().lower()
    if key not in state.GROUP_DB:
        raise HTTPException(status_code=404, detail="Group not found")
    del state.GROUP_DB[key]
    # persist YAML
    try:
        if state.GROUPS_CSV_PATH:
            dump_yaml_entities(state.GROUPS_CSV_PATH.with_suffix('.yaml'), list(state.GROUP_DB.values()), key_field='groupname')
    except Exception:
        pass
    return
