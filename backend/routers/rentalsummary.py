from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
import yaml

from .. import main as state

router = APIRouter(prefix="/api", tags=["rental-summary"]) 

_EXPECTED_FIELDS = [
    "property",
    "rent",
    "commissions",
    "insurance",
    "proffees",
    "mortgageinterest",
    "repairs",
    "tax",
    "utilities",
    "depreciation",
    "hoa",
    "other",
    "costbasis",
    "renteddays",
    "profit",
]


def _normalize_key(k: Any) -> str:
    try:
        s = str(k)
    except Exception:
        return ""
    s = s.strip().lstrip('#').strip()
    return s.lower()


@router.get("/rental-summary")
async def get_rental_summary() -> List[Dict[str, Any]]:
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'rentalsummary'
    ver_base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'rentalsummary_verified'
    try:
        all_rows: List[Dict[str, Any]] = []
        if base.exists() and base.is_dir():
            # Read ONLY YAML files; no CSV fallback
            for p in sorted(base.glob('*.yaml')):
                try:
                    with p.open('r', encoding='utf-8') as yf:
                        data = yaml.safe_load(yf) or {}
                        if isinstance(data, dict):
                            # Build row with property and only expected fields present in YAML
                            prop_name = p.stem
                            row: Dict[str, Any] = { 'property': prop_name }
                            for k, v in data.items():
                                kk = str(k).strip().lower()
                                if kk in _EXPECTED_FIELDS and v is not None and str(v) != '':
                                    row[kk] = v
                            # Attach verified values if present (from rentalsummary_verified/<property>.yaml)
                            try:
                                ver_path = ver_base / f"{prop_name}.yaml"
                                if ver_path.exists():
                                    with ver_path.open('r', encoding='utf-8') as vf:
                                        vdata = yaml.safe_load(vf) or {}
                                        if isinstance(vdata, dict):
                                            # Normalize keys to lowercase
                                            verified: Dict[str, Any] = {}
                                            for vk, vv in vdata.items():
                                                vkk = str(vk).strip().lower()
                                                if vkk in _EXPECTED_FIELDS:
                                                    verified[vkk] = vv
                                            if verified:
                                                row['_verified'] = verified
                            except Exception:
                                pass
                            all_rows.append(row)
                except Exception as e:
                    state.logger.error(f"Failed to read rental summary file {p}: {e}")
        return all_rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read rental summary files: {e}")


class VerifyCellPayload(BaseModel):
    property: str
    field: str
    value: Any


@router.post("/rental-summary/verify")
async def verify_rental_summary_cell(payload: VerifyCellPayload) -> Dict[str, Any]:
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    prop = (payload.property or '').strip().lower()
    field = (payload.field or '').strip().lower()
    if not (prop and field):
        raise HTTPException(status_code=400, detail="property and field are required")
    if field not in _EXPECTED_FIELDS or field == 'property':
        raise HTTPException(status_code=400, detail="Invalid field to verify")
    ver_base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'rentalsummary_verified'
    ver_base.mkdir(parents=True, exist_ok=True)
    ver_path = ver_base / f"{prop}.yaml"
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


class UnverifyCellPayload(BaseModel):
    property: str
    field: str


@router.delete("/rental-summary/verify")
async def unverify_rental_summary_cell(payload: UnverifyCellPayload) -> Dict[str, Any]:
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    prop = (payload.property or '').strip().lower()
    field = (payload.field or '').strip().lower()
    if not (prop and field):
        raise HTTPException(status_code=400, detail="property and field are required")
    if field not in _EXPECTED_FIELDS or field == 'property':
        raise HTTPException(status_code=400, detail="Invalid field to unverify")
    ver_base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'rentalsummary_verified'
    ver_base.mkdir(parents=True, exist_ok=True)
    ver_path = ver_base / f"{prop}.yaml"
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
