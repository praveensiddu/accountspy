from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from .. import main as state
from .. import classify as classifier
from ..property_sum import prepare_and_save_property_sum
from ..company_sum import prepare_and_save_company_sum
import csv
from pathlib import Path
import yaml

router = APIRouter(prefix="/api", tags=["transactions"])


class TransactionRow(BaseModel):
    tr_id: str = ''
    date: str = ''
    description: str = ''
    credit: str = ''  # positive for credit, negative for debit
    ruleid: str = ''
    comment: str = ''
    transaction_type: str = ''
    tax_category: str = ''
    property: str = ''
    group: str = ''
    company: str = ''
    otherentity: str = ''
    override: str = ''
    fromaddendum: str = ''


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
                    'tr_id': row.get('tr_id',''),
                    'date': row.get('date',''),
                    'description': row.get('description',''),
                    'credit': row.get('credit',''),
                    'ruleid': row.get('ruleid',''),
                    'comment': row.get('comment',''),
                    'transaction_type': row.get('transaction_type',''),
                    'tax_category': row.get('tax_category',''),
                    'property': row.get('property',''),
                    'group': row.get('group',''),
                    'company': row.get('company',''),
                    'otherentity': row.get('otherentity',''),
                    'override': row.get('override',''),
                    'fromaddendum': row.get('fromaddendum',''),
                })
    except Exception:
        state.logger.exception(f"Failed reading processed CSV: {path}")
    return rows


def _read_processed_yaml(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Normalize to expected keys; ignore extra
                        rows.append({
                            'tr_id': item.get('tr_id',''),
                            'date': item.get('date',''),
                            'description': item.get('description',''),
                            'credit': item.get('credit',''),
                            'ruleid': item.get('ruleid',''),
                            'comment': item.get('comment',''),
                            'transaction_type': item.get('transaction_type',''),
                            'tax_category': item.get('tax_category',''),
                            'property': item.get('property',''),
                            'group': item.get('group',''),
                            'company': item.get('company',''),
                            'otherentity': item.get('otherentity',''),
                            'override': item.get('override',''),
                            'fromaddendum': item.get('fromaddendum',''),
                        })
    except Exception:
        pass
    return rows


@router.get("/transactions")
async def list_all_transactions() -> Dict[str, Any]:
    if not state.PROCESSED_DIR_PATH:
        raise HTTPException(status_code=500, detail="Processed directory not configured")
    result: Dict[str, Any] = {}
    try:
        for key in state.BA_DB.keys():
            py = state.PROCESSED_DIR_PATH / f"{key}.yaml"
            if py.exists():
                result[key] = _read_processed_yaml(py)
                continue
            pc = state.PROCESSED_DIR_PATH / f"{key}.csv"
            result[key] = _read_processed_csv(pc) if pc.exists() else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read processed CSVs: {e}")
    return result


@router.get("/transactions/config")
async def get_transactions_config() -> Dict[str, Any]:
    year = state.CURRENT_YEAR or ""
    mydict = {"current_year": year}
    state.logger.info(f"get_transactions_config: {mydict}")
    return mydict


@router.get("/transactions/{bankaccountname}")
async def get_transactions(bankaccountname: str) -> Dict[str, Any]:
    key = (bankaccountname or '').strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    if not state.PROCESSED_DIR_PATH:
        raise HTTPException(status_code=500, detail="Processed directory not configured")
    py = state.PROCESSED_DIR_PATH / f"{key}.yaml"
    if py.exists():
        rows = _read_processed_yaml(py)
    else:
        pc = state.PROCESSED_DIR_PATH / f"{key}.csv"
        rows = _read_processed_csv(pc) if pc.exists() else []
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

    # Guard: Do not allow deletion of normalized rows (identified by tr_id from normalized CSV)
    try:
        required_tr_ids = set()
        if state.NORMALIZED_DIR_PATH:
            norm_csv = state.NORMALIZED_DIR_PATH / f"{key}.csv"
            if norm_csv.exists():
                with norm_csv.open('r', encoding='utf-8') as nf:
                    reader = csv.DictReader(nf)
                    for row in reader:
                        tid = (row.get('tr_id') or '').strip()
                        if tid:
                            required_tr_ids.add(tid)
        incoming_tr_ids = set((r.tr_id or '').strip() for r in payload.rows if isinstance(r.tr_id, str))
        # All required tr_id must be present in incoming rows
        missing = [tid for tid in required_tr_ids if tid not in incoming_tr_ids]
        if missing:
            raise HTTPException(status_code=400, detail=f"Cannot delete normalized rows; missing tr_id: {', '.join(missing[:5])}{'...' if len(missing)>5 else ''}")
    except HTTPException:
        raise
    except Exception as e:
        # Fail safe: if guard check fails unexpectedly, reject to avoid destructive loss
        raise HTTPException(status_code=500, detail=f"Validation failed: {e}")
    # Write CSV with fixed header
    header = [
        'tr_id','date','description','credit','ruleid','comment','transaction_type','tax_category','property','group','company','otherentity','override','fromaddendum'
    ]
    out_path = state.PROCESSED_DIR_PATH / f"{key}.csv"
    try:
        with out_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
            writer.writeheader()
            for row in payload.rows:
                d = row.dict()
                try:
                    desc = d.get('description') or ''
                    # Collapse multiple spaces/tabs to a single space, trim, and lowercase
                    desc = ' '.join(str(desc).split()).strip().lower()
                    d['description'] = desc
                except Exception:
                    pass
                writer.writerow(d)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write CSV: {e}")

    # Also write addendum CSV under <statement_location>/<CURRENT_YEAR>/addendum/<bankaccountname>.csv
    try:
        ba = state.BA_DB.get(key) or {}
        sl = (ba.get('statement_location') or '').strip()
        if not sl:
            raise HTTPException(status_code=400, detail="statement_location not set for this bank account")
        base = Path(sl)
        addendum_dir = base / (state.CURRENT_YEAR or '') / 'addendum'
        addendum_dir.mkdir(parents=True, exist_ok=True)
        addendum_path = addendum_dir / f"{key}.csv"
        # Write all submitted rows to addendum with only required fields
        addendum_rows = list(payload.rows)
        addendum_header = ['tr_id','date','description','credit']
        with addendum_path.open('w', newline='', encoding='utf-8') as af:
            awriter = csv.DictWriter(af, fieldnames=addendum_header, extrasaction='ignore')
            awriter.writeheader()
            for row in addendum_rows:
                d = row.dict()
                try:
                    desc = d.get('description') or ''
                    desc = ' '.join(str(desc).split()).strip().lower()
                except Exception:
                    desc = (d.get('description') or '').lower()
                out = {
                    'tr_id': d.get('tr_id',''),
                    'date': d.get('date',''),
                    'description': desc,
                    'credit': d.get('credit',''),
                }
                awriter.writerow(out)
    except HTTPException:
        raise
    except Exception as e:
        # Non-fatal: proceed even if addendum write fails, but report in response
        state.logger.error(f"Failed to write addendum CSV for {key}: {e}")
    # Regenerate processed CSV using classifier to ensure consistency
    try:
        classifier.classify_bank(key)
    except Exception:
        # Do not fail the request if regeneration fails, but log details
        state.logger.exception(f"Failed to reclassify after save for {key}")
    # Update rental summaries
    try:
        prepare_and_save_property_sum()
    except Exception:
        state.logger.exception("Failed to update property summary after save")
    try:
        prepare_and_save_company_sum()
    except Exception:
        state.logger.exception("Failed to update company summary after save")
    return {"ok": True, "path": str(out_path)}


@router.delete("/transactions/{bankaccountname}")
async def delete_transaction(bankaccountname: str, payload: TransactionRow) -> Dict[str, Any]:
    key = (bankaccountname or '').strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    # Must be an addendum row; normalized rows cannot be deleted
    if not (payload.fromaddendum and str(payload.fromaddendum).strip()):
        raise HTTPException(status_code=400, detail="Only addendum rows can be deleted")
    # Locate per-bank addendum CSV
    ba = state.BA_DB.get(key) or {}
    sl = (ba.get('statement_location') or '').strip()
    if not sl:
        raise HTTPException(status_code=400, detail="statement_location not set for this bank account")
    addendum_dir = Path(sl) / (state.CURRENT_YEAR or '') / 'addendum'
    addendum_path = addendum_dir / f"{key}.csv"
    if not addendum_path.exists():
        raise HTTPException(status_code=404, detail="Addendum file not found for this bank account")
    # Read, filter out matching row by tr_id if present, else by fields
    try:
        rows: List[Dict[str, str]] = []
        with addendum_path.open('r', encoding='utf-8') as rf:
            reader = csv.DictReader(rf)
            for row in reader:
                rows.append(row)
        target_tid = (payload.tr_id or '').strip()
        def _matches(r: Dict[str,str]) -> bool:
            if target_tid:
                return (r.get('tr_id','').strip() == target_tid)
            # fallback match by fields
            return (
                (r.get('date','') or '') == (payload.date or '') and
                (r.get('description','') or '').lower() == (payload.description or '').lower() and
                str(r.get('credit','') or '') == str(payload.credit or '')
            )
        new_rows = [r for r in rows if not _matches(r)]
        if len(new_rows) == len(rows):
            raise HTTPException(status_code=404, detail="Addendum row not found")
        # Write back filtered CSV
        addendum_dir.mkdir(parents=True, exist_ok=True)
        with addendum_path.open('w', newline='', encoding='utf-8') as wf:
            header = ['tr_id','date','description','credit']
            writer = csv.DictWriter(wf, fieldnames=header, extrasaction='ignore')
            writer.writeheader()
            for r in new_rows:
                writer.writerow({
                    'tr_id': r.get('tr_id',''),
                    'date': r.get('date',''),
                    'description': (r.get('description') or ''),
                    'credit': r.get('credit',''),
                })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete addendum row: {e}")
    # Reclassify and update summaries
    try:
        classifier.classify_bank(key)
    except Exception:
        pass
    try:
        prepare_and_save_property_sum()
    except Exception:
        pass
    try:
        prepare_and_save_company_sum()
    except Exception:
        pass
    return {"ok": True}
