from fastapi import APIRouter, HTTPException
from typing import List

from .. import main as state
from ..core.models import CompanyRecord
from ..core.utils import dump_yaml_entities

router = APIRouter(prefix="/api", tags=["companies"])


@router.get("/companies", response_model=List[str])
async def list_companies():
    return sorted(list(state.COMP_DB.keys()))


@router.get("/company-records", response_model=List[CompanyRecord])
async def list_company_records():
    return list(state.COMP_DB.values())


@router.post("/company-records", response_model=CompanyRecord, status_code=201)
async def add_company_record(payload: CompanyRecord):
    key = payload.companyname.strip().lower()
    if not state.ALNUM_LOWER_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid companyname: only lowercase alphanumeric allowed")
    if key in state.COMP_DB:
        raise HTTPException(status_code=409, detail="Company record already exists")
    item = payload.dict()
    item["companyname"] = key
    state.COMP_DB[key] = item
    # persist YAML
    try:
        if state.COMP_CSV_PATH:
            dump_yaml_entities(state.COMP_CSV_PATH.with_suffix('.yaml'), list(state.COMP_DB.values()), key_field='companyname')
    except Exception:
        pass
    return state.COMP_DB[key]


@router.delete("/company-records/{companyname}", status_code=204)
async def delete_company_record(companyname: str):
    key = companyname.strip().lower()
    if key not in state.COMP_DB:
        raise HTTPException(status_code=404, detail="Company record not found")
    del state.COMP_DB[key]
    # persist YAML
    try:
        if state.COMP_CSV_PATH:
            dump_yaml_entities(state.COMP_CSV_PATH.with_suffix('.yaml'), list(state.COMP_DB.values()), key_field='companyname')
    except Exception:
        pass
    return
