from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
import yaml

from .. import main as state

router = APIRouter(prefix="/api", tags=["company-summary"]) 

_EXPECTED_FIELDS = [
    "Name",
    "income",
    "rentpassedtoowners",
    "bankfees",
    "c_auto",
    "c_donate",
    "c_entertainment",
    "c_internet",
    "c_license",
    "c_mobile",
    "c_off_exp",
    "c_parktoll",
    "c_phone",
    "c_website",
    "ignore",
    "insurane",
    "proffees",
    "utilities",
    "profit",
]


@router.get("/company-summary")
async def get_company_summary() -> List[Dict[str, Any]]:
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'companysummary'
    ver_base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'companysummary_verified'
    try:
        all_rows: List[Dict[str, Any]] = []
        if base.exists() and base.is_dir():
            for p in sorted(base.glob('*.yaml')):
                try:
                    with p.open('r', encoding='utf-8') as yf:
                        data = yaml.safe_load(yf) or {}
                        if isinstance(data, dict):
                            # Start with Name and defaults for all expected fields (empty string)
                            name = p.stem
                            row: Dict[str, Any] = { 'Name': name }
                            for col in _EXPECTED_FIELDS:
                                if col == 'Name':
                                    continue
                                row[col] = ''
                            # Fill from YAML where present
                            for k, v in data.items():
                                kk = str(k).strip()
                                if kk in _EXPECTED_FIELDS and v is not None and str(v) != '':
                                    row[kk] = v
                            # Attach verified values if present
                            try:
                                ver_path = ver_base / f"{name}.yaml"
                                if ver_path.exists():
                                    with ver_path.open('r', encoding='utf-8') as vf:
                                        vdata = yaml.safe_load(vf) or {}
                                        if isinstance(vdata, dict):
                                            verified: Dict[str, Any] = {}
                                            for vk, vv in vdata.items():
                                                vkk = str(vk).strip()
                                                if vkk in _EXPECTED_FIELDS and vkk != 'Name':
                                                    verified[vkk] = vv
                                            if verified:
                                                row['_verified'] = verified
                            except Exception:
                                pass
                            all_rows.append(row)
                except Exception as e:
                    state.logger.error(f"Failed to read company summary file {p}: {e}")
        return all_rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read company summary files: {e}")


class VerifyCompanyCellPayload(BaseModel):
    Name: str
    field: str
    value: Any


@router.post("/company-summary/verify")
async def verify_company_summary_cell(payload: VerifyCompanyCellPayload) -> Dict[str, Any]:
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    name = (payload.Name or '').strip()
    field = (payload.field or '').strip()
    if not (name and field):
        raise HTTPException(status_code=400, detail="Name and field are required")
    if field not in _EXPECTED_FIELDS or field == 'Name':
        raise HTTPException(status_code=400, detail="Invalid field to verify")
    ver_base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'companysummary_verified'
    ver_base.mkdir(parents=True, exist_ok=True)
    ver_path = ver_base / f"{name}.yaml"
    current: Dict[str, Any] = {}
    try:
        if ver_path.exists():
            with ver_path.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    current = data
    except Exception:
        current = {}
    current[field] = payload.value
    try:
        with ver_path.open('w', encoding='utf-8') as f:
            yaml.safe_dump(current, f, sort_keys=True, allow_unicode=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write verified file: {e}")
    return {"ok": True}


class UnverifyCompanyCellPayload(BaseModel):
    Name: str
    field: str


@router.delete("/company-summary/verify")
async def unverify_company_summary_cell(payload: UnverifyCompanyCellPayload) -> Dict[str, Any]:
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    name = (payload.Name or '').strip()
    field = (payload.field or '').strip()
    if not (name and field):
        raise HTTPException(status_code=400, detail="Name and field are required")
    if field not in _EXPECTED_FIELDS or field == 'Name':
        raise HTTPException(status_code=400, detail="Invalid field to unverify")
    ver_base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'companysummary_verified'
    ver_base.mkdir(parents=True, exist_ok=True)
    ver_path = ver_base / f"{name}.yaml"
    try:
        current: Dict[str, Any] = {}
        if ver_path.exists():
            with ver_path.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    current = data
        if field in current:
            del current[field]
        with ver_path.open('w', encoding='utf-8') as f:
            yaml.safe_dump(current, f, sort_keys=True, allow_unicode=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update verified file: {e}")
    return {"ok": True}
