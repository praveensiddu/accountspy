from fastapi import APIRouter, HTTPException
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
    try:
        all_rows: List[Dict[str, Any]] = []
        if base.exists() and base.is_dir():
            for p in sorted(base.glob('*.yaml')):
                try:
                    with p.open('r', encoding='utf-8') as yf:
                        data = yaml.safe_load(yf) or {}
                        if isinstance(data, dict):
                            # Start with Name and defaults for all expected fields (empty string)
                            row: Dict[str, Any] = { 'Name': p.stem }
                            for col in _EXPECTED_FIELDS:
                                if col == 'Name':
                                    continue
                                row[col] = ''
                            # Fill from YAML where present
                            for k, v in data.items():
                                kk = str(k).strip()
                                if kk in _EXPECTED_FIELDS and v is not None and str(v) != '':
                                    row[kk] = v
                            all_rows.append(row)
                except Exception as e:
                    state.logger.error(f"Failed to read company summary file {p}: {e}")
        return all_rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read company summary files: {e}")
