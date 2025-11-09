from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
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
    rev_base = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'rentalsummary_reverse'
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
                            # Attach reverse map if present (from rentalsummary_reverse/<property>.yaml)
                            try:
                                if rev_base.exists():
                                    rev_path = rev_base / f"{prop_name}.yaml"
                                    if rev_path.exists():
                                        with rev_path.open('r', encoding='utf-8') as rf:
                                            rdata = yaml.safe_load(rf) or {}
                                            if isinstance(rdata, dict):
                                                row['_reverse'] = rdata
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
    value: Optional[Any] = ''


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
    # If value is missing or None, record as empty string
    val = payload.value if payload.value is not None else ''
    current[field] = val
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


@router.post("/export-accounts")
async def export_accounts_excel() -> Dict[str, Any]:
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    base_dir = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR
    rent_dir = base_dir / 'rentalsummary'
    comp_dir = base_dir / 'companysummary'
    out_path = base_dir / f"accounts_{state.CURRENT_YEAR}.xlsx"

    # Collect rental summary rows
    rental_cols = [
        "property","rent","commissions","insurance","proffees","mortgageinterest","repairs","tax","utilities","depreciation","hoa","other","costbasis","renteddays","profit"
    ]
    rental_rows: List[Dict[str, Any]] = []
    try:
        if rent_dir.exists():
            for p in sorted(rent_dir.glob('*.yaml')):
                try:
                    with p.open('r', encoding='utf-8') as yf:
                        data = yaml.safe_load(yf) or {}
                        if isinstance(data, dict):
                            row: Dict[str, Any] = { 'property': p.stem }
                            for k, v in data.items():
                                kk = str(k).strip().lower()
                                if kk in rental_cols and v is not None and str(v) != '':
                                    row[kk] = v
                            rental_rows.append(row)
                except Exception:
                    continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read rentalsummary: {e}")

    # Collect company summary rows
    company_cols = [
        "Name","income","rentpassedtoowners","bankfees","c_auto","c_donate","c_entertainment","c_internet","c_license","c_mobile","c_off_exp","c_parktoll","c_phone","c_website","ignore","insurane","proffees","utilities","profit"
    ]
    company_rows: List[Dict[str, Any]] = []
    try:
        if comp_dir.exists():
            for p in sorted(comp_dir.glob('*.yaml')):
                try:
                    with p.open('r', encoding='utf-8') as yf:
                        data = yaml.safe_load(yf) or {}
                        if isinstance(data, dict):
                            row: Dict[str, Any] = { 'Name': p.stem }
                            for col in company_cols:
                                if col == 'Name':
                                    continue
                                row[col] = ''
                            for k, v in data.items():
                                kk = str(k).strip()
                                if kk in company_cols and v is not None and str(v) != '':
                                    row[kk] = v
                            company_rows.append(row)
                except Exception:
                    continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read companysummary: {e}")

    # Write Excel
    try:
        from openpyxl import Workbook
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"openpyxl not installed: {e}")

    try:
        wb = Workbook()
        # Rentalsummary sheet
        ws1 = wb.active
        ws1.title = 'rentalsummary'
        ws1.append(rental_cols)
        for r in rental_rows:
            ws1.append([r.get(c, '') for c in rental_cols])
        # Companysummary sheet
        ws2 = wb.create_sheet('companysummary')
        ws2.append(company_cols)
        for r in company_rows:
            ws2.append([r.get(c, '') for c in company_cols])
        # Ensure parent dir
        out_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(out_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write Excel: {e}")

    return {"ok": True, "path": str(out_path)}


@router.get("/export-accounts/download")
async def download_accounts_excel():
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    base_dir = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR
    out_path = base_dir / f"accounts_{state.CURRENT_YEAR}.xlsx"
    if not out_path.exists() or not out_path.is_file():
        raise HTTPException(status_code=404, detail="Export file not found. Run export first.")
    return FileResponse(str(out_path), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=out_path.name)



