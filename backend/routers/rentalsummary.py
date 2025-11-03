from fastapi import APIRouter, HTTPException
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
                            row: Dict[str, Any] = { 'property': p.stem }
                            for k, v in data.items():
                                kk = str(k).strip().lower()
                                if kk in _EXPECTED_FIELDS and v is not None and str(v) != '':
                                    row[kk] = v
                            all_rows.append(row)
                except Exception as e:
                    state.logger.error(f"Failed to read rental summary file {p}: {e}")
        return all_rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read rental summary files: {e}")
