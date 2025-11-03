from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
from pathlib import Path
import csv
import hashlib

from .. import main as state
from .. import classify as classifier

router = APIRouter(prefix="/api", tags=["addendum"]) 

class AddendumRow(BaseModel):
    date: str
    description: str
    credit: str

@router.post("/addendum/{bankaccountname}")
async def add_addendum_row(bankaccountname: str, payload: AddendumRow) -> Dict[str, str]:
    bank = (bankaccountname or '').strip().lower()
    if not bank:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    if not state.ADDENDUM_DIR_PATH:
        raise HTTPException(status_code=500, detail="Addendum directory not configured")
    out_path: Path = state.ADDENDUM_DIR_PATH / f"{bank}.csv"
    # Ensure directory exists (should be ensured on startup)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = out_path.exists()
        # Normalize credit to match normalized formatting (int if whole, else float string)
        credit_txt = (payload.credit or '').strip()
        tr_credit = ''
        try:
            n = float(credit_txt)
            tr_credit = str(int(n)) if abs(n - int(n)) < 1e-9 else f"{n}"
        except Exception:
            tr_credit = credit_txt
        # Compute tr_id same as normalized: sha256 of bank+date+description+credit (lowercased, no spaces)
        s = (bank + (payload.date or '') + (payload.description or '') + tr_credit).lower()
        s = ''.join(s.split())
        tr_id = hashlib.sha256(s.encode()).hexdigest()[:10]
        # Enforce uniqueness by tr_id only
        if file_exists:
            with out_path.open('r', encoding='utf-8') as rf:
                reader = csv.DictReader(rf)
                for row in reader:
                    existing_tr_id = (row.get('tr_id') or '').strip()
                    if existing_tr_id and existing_tr_id == tr_id:
                        raise HTTPException(status_code=409, detail="Duplicate addendum row (tr_id already exists)")
        with out_path.open('a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['tr_id','date','description','credit'])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'tr_id': tr_id,
                'date': payload.date or '',
                'description': payload.description or '',
                'credit': tr_credit,
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write addendum CSV: {e}")

    # Reclassify this bank to propagate addendum to processed CSV
    try:
        classifier.classify_bank(bank)
    except Exception:
        # Do not fail request on classifier errors
        pass
    return {"ok": "true", "path": str(out_path)}
