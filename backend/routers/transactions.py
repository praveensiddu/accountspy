from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from .. import main as state
import csv
from pathlib import Path

router = APIRouter(prefix="/api", tags=["transactions"])


class TransactionRow(BaseModel):
    date: str = ''
    description: str = ''
    credit: str = ''  # positive for credit, negative for debit
    comment: str = ''
    transaction_type: str = ''
    tax_category: str = ''
    property: str = ''
    company: str = ''
    otherentity: str = ''
    override: str = ''


class TransactionsPayload(BaseModel):
    rows: List[TransactionRow]


def _read_processed_csv(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        with path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize to expected keys; ignore extra
                rows.append({
                    'date': row.get('date',''),
                    'description': row.get('description',''),
                    'credit': row.get('credit',''),
                    'comment': row.get('comment',''),
                    'transaction_type': row.get('transaction_type',''),
                    'tax_category': row.get('tax_category',''),
                    'property': row.get('property',''),
                    'company': row.get('company',''),
                    'otherentity': row.get('otherentity',''),
                    'override': row.get('override',''),
                })
    except Exception:
        pass
    return rows


@router.get("/transactions")
async def list_all_transactions() -> Dict[str, Any]:
    if not (state.PROCESSED_DIR_PATH or state.NORMALIZED_DIR_PATH):
        raise HTTPException(status_code=500, detail="Processed/normalized directory not configured")
    result: Dict[str, Any] = {}
    try:
        for key in state.BA_DB.keys():
            p = None
            if state.PROCESSED_DIR_PATH:
                cand = state.PROCESSED_DIR_PATH / f"{key}.csv"
                if cand.exists():
                    p = cand
            if p is None and state.NORMALIZED_DIR_PATH:
                cand = state.NORMALIZED_DIR_PATH / f"{key}.csv"
                if cand.exists():
                    p = cand
            result[key] = _read_processed_csv(p) if p else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read processed CSVs: {e}")
    return result


@router.get("/transactions/{bankaccountname}")
async def get_transactions(bankaccountname: str) -> Dict[str, Any]:
    key = (bankaccountname or '').strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    if not (state.PROCESSED_DIR_PATH or state.NORMALIZED_DIR_PATH):
        raise HTTPException(status_code=500, detail="Processed/normalized directory not configured")
    p = None
    if state.PROCESSED_DIR_PATH:
        cand = state.PROCESSED_DIR_PATH / f"{key}.csv"
        if cand.exists():
            p = cand
    if p is None and state.NORMALIZED_DIR_PATH:
        cand = state.NORMALIZED_DIR_PATH / f"{key}.csv"
        if cand.exists():
            p = cand
    rows = _read_processed_csv(p) if p else []
    return {"bankaccountname": key, "rows": rows}

@router.post("/transactions/{bankaccountname}")
async def save_transactions(bankaccountname: str, payload: TransactionsPayload) -> Dict[str, Any]:
    key = (bankaccountname or '').strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    # Optional: validate the bank account exists
    if key not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    if not state.PROCESSED_DIR_PATH:
        raise HTTPException(status_code=500, detail="Processed directory not configured")
    # Write CSV with fixed header
    header = [
        'date','description','credit','comment','transaction_type','tax_category','property','company','otherentity','override'
    ]
    out_path = state.PROCESSED_DIR_PATH / f"{key}.csv"
    try:
        with out_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
            writer.writeheader()
            for row in payload.rows:
                writer.writerow(row.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write CSV: {e}")
    return {"ok": True, "path": str(out_path)}
