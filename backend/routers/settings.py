from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from pathlib import Path
import csv

from .. import main as state

router = APIRouter(prefix="/api/settings", tags=["settings"]) 

class PrepYearPayload(BaseModel):
    year: str

@router.post("/prepyear")
async def prep_year(payload: PrepYearPayload) -> Dict[str, Any]:
    if not state.ACCOUNTS_DIR_PATH:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR not configured")
    year = (payload.year or '').strip()
    if not year.isdigit():
        raise HTTPException(status_code=400, detail="year must be a number")
    cur_year = int(year)

    # Ensure ACCOUNTS_DIR/<year>/ exists
    base = state.ACCOUNTS_DIR_PATH / str(cur_year)
    try:
        base.mkdir(parents=True, exist_ok=True)

        # Entities copy forward if missing in current year but present in previous year
        cur_entities = base / 'entities'
        if not cur_entities.exists():
            prev_entities = state.ACCOUNTS_DIR_PATH / str(cur_year - 1) / 'entities'
            if prev_entities.exists() and prev_entities.is_dir():
                cur_entities.mkdir(parents=True, exist_ok=True)
                for p in prev_entities.iterdir():
                    if p.is_file():
                        (cur_entities / p.name).write_bytes(p.read_bytes())

        # Addendum handling per bankaccount using statement_location
        # For each bank account in BA_DB, determine per-account locations
        for ba_name, ba_cfg in (state.BA_DB or {}).items():
            try:
                stmt_loc = ba_cfg.get('statement_location') if isinstance(ba_cfg, dict) else None
                if not stmt_loc:
                    continue
                stmt_root = Path(str(stmt_loc)).expanduser().resolve()
                prev_addendum_dir = stmt_root / str(cur_year - 1) / 'addendum'
                cur_addendum_dir = stmt_root / str(cur_year) / 'addendum'
                cur_addendum_dir.mkdir(parents=True, exist_ok=True)
                prev_file = prev_addendum_dir / f"{ba_name}.csv"
                cur_file = cur_addendum_dir / f"{ba_name}.csv"
                # If already exists in current year, do not overwrite
                if cur_file.exists():
                    continue
                if not prev_file.exists():
                    continue
                rows = []
                with prev_file.open('r', encoding='utf-8') as rf:
                    reader = csv.DictReader(rf)
                    # Preserve header fields where possible; normalize required columns
                    headers = reader.fieldnames or []
                    # Ensure required columns exist in output
                    out_headers = list(dict.fromkeys([*(headers or []), 'tr_id', 'date', 'description', 'credit']))
                    for row in reader:
                        rows.append({
                            'tr_id': row.get('tr_id',''),
                            'date': row.get('date',''),
                            'description': row.get('description',''),
                            'credit': '0',
                        })
                with cur_file.open('w', newline='', encoding='utf-8') as wf:
                    header = ['tr_id','date','description','credit']
                    writer = csv.DictWriter(wf, fieldnames=header, extrasaction='ignore')
                    writer.writeheader()
                    for r in rows:
                        writer.writerow(r)
            except Exception:
                # Continue with other bank accounts if any error
                continue

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"prepyear failed: {e}")

    return {"ok": True, "year": str(cur_year)}
