from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from pathlib import Path
import csv

from .. import main as state
from ..core.models import BankAccountRecord
from ..core.utils import dump_yaml_entities
from ..bank_statement_parser import _normalize_date, _process_bank_statement_for_account
from ..classify import classify_bank

router = APIRouter(prefix="/api", tags=["bankaccounts"])


@router.get("/bankaccounts", response_model=List[BankAccountRecord])
async def list_bankaccounts():
    return list(state.BA_DB.values())


@router.post("/bankaccounts", response_model=BankAccountRecord, status_code=201)
async def add_bankaccount(payload: BankAccountRecord):
    key = payload.bankaccountname.strip().lower()
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid bankaccountname: lowercase alphanumeric and underscore only")
    if key in state.BA_DB:
        raise HTTPException(status_code=409, detail="Bank account already exists")
    item = {
        "bankaccountname": key,
        "bankname": (payload.bankname or "").strip().lower(),
        "statement_location": "",
    }
    if not item["bankname"]:
        raise HTTPException(status_code=400, detail="bankname is required")
    # Validate statement_location: require non-empty, strip edges, reject if whitespace in middle, ensure trailing '/'
    try:
        raw_sl = payload.statement_location or ""
        sl = raw_sl.strip()
        if not sl:
            raise HTTPException(status_code=400, detail="statement_location is required")
        # Any whitespace remaining implies internal whitespace -> reject
        if any(ch.isspace() for ch in sl):
            raise HTTPException(status_code=400, detail="statement_location must not contain spaces or whitespace")
        if not sl.endswith('/'):
            sl = sl + '/'
        item["statement_location"] = sl
    except HTTPException:
        raise
    except Exception:
        # Fallback to stripped value if unexpected error
        item["statement_location"] = (payload.statement_location or "").strip()
    state.BA_DB[key] = item
    # persist YAML
    try:
        if state.BANK_CSV_PATH:
            dump_yaml_entities(state.BANK_CSV_PATH.with_suffix('.yaml'), list(state.BA_DB.values()), key_field='bankaccountname')
    except Exception:
        pass
    return state.BA_DB[key]


@router.put("/bankaccounts/{bankaccountname}", response_model=BankAccountRecord)
async def update_bankaccount(bankaccountname: str, payload: BankAccountRecord):
    key = (bankaccountname or "").strip().lower()
    if not key:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    if key not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    # Do not allow renaming (path param controls identity)
    bankname = (payload.bankname or "").strip().lower()
    if not bankname:
        raise HTTPException(status_code=400, detail="bankname is required")
    # Validate statement_location: require non-empty, strip edges, reject if whitespace in middle, ensure trailing '/'
    try:
        raw_sl = payload.statement_location or ""
        sl = raw_sl.strip()
        if not sl:
            raise HTTPException(status_code=400, detail="statement_location is required")
        if any(ch.isspace() for ch in sl):
            raise HTTPException(status_code=400, detail="statement_location must not contain spaces or whitespace")
        if not sl.endswith('/'):
            sl = sl + '/'
    except HTTPException:
        raise
    except Exception:
        sl = (payload.statement_location or "").strip()

    # Update in-memory
    state.BA_DB[key] = {
        "bankaccountname": key,
        "bankname": bankname,
        "statement_location": sl,
    }
    # Persist YAML
    try:
        if state.BANK_CSV_PATH:
            dump_yaml_entities(state.BANK_CSV_PATH.with_suffix('.yaml'), list(state.BA_DB.values()), key_field='bankaccountname')
    except Exception:
        pass
    return state.BA_DB[key]

@router.delete("/bankaccounts/{bankaccountname}", status_code=204)
async def delete_bankaccount(bankaccountname: str):
    key = bankaccountname.strip().lower()
    if key not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    # 1) Remove related Classify Rules (bank rules)
    try:
        to_delete = [
            k for k, v in state.CLASSIFY_DB.items()
            if (v or {}).get("bankaccountname") == key
        ]
        for k in to_delete:
            del state.CLASSIFY_DB[k]
        if state.CLASSIFY_CSV_PATH:
            base_dir = state.CLASSIFY_CSV_PATH.parent
            dump_yaml_entities(base_dir / 'bank_rules.yaml', list(state.CLASSIFY_DB.values()), key_field='bankaccountname')
    except Exception:
        # proceed even if classify cleanup fails
        pass

    # 2) Remove related Inherit Common To Bank rules
    try:
        inh_delete = [
            k for k, v in state.INHERIT_RULES_DB.items()
            if (v or {}).get("bankaccountname") == key
        ]
        for k in inh_delete:
            del state.INHERIT_RULES_DB[k]
        if state.CLASSIFY_CSV_PATH:
            base_dir = state.CLASSIFY_CSV_PATH.parent
            dump_yaml_entities(base_dir / 'inherit_common_to_bank.yaml', list(state.INHERIT_RULES_DB.values()), key_field='bankaccountname')
    except Exception:
        pass

    # 3) Remove this bankaccount from all owners' bankaccounts lists
    try:
        for owner_key, owner in list(state.OWNER_DB.items()):
            if not isinstance(owner, dict):
                continue
            ba_list = list(owner.get('bankaccounts') or [])
            if key in ba_list:
                owner['bankaccounts'] = [b for b in ba_list if b != key]
        # persist owners.yaml if any change was made
        if state.OWNERS_CSV_PATH:
            dump_yaml_entities(state.OWNERS_CSV_PATH.with_suffix('.yaml'), list(state.OWNER_DB.values()), key_field='name')
    except Exception:
        pass

    # 4) Finally, delete the bank account itself
    del state.BA_DB[key]
    # persist YAML for bank accounts after deletion
    try:
        if state.BANK_CSV_PATH:
            dump_yaml_entities(state.BANK_CSV_PATH.with_suffix('.yaml'), list(state.BA_DB.values()), key_field='bankaccountname')
    except Exception:
        pass
    return


@router.post("/bankaccounts/{bankaccountname}/upload-statement")
async def upload_bank_statement(bankaccountname: str, file: UploadFile = File(...)):
    key = (bankaccountname or '').strip().lower()
    if not key or key not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    ba = state.BA_DB[key]
    bankname = (ba.get('bankname') or '').strip().lower()
    stmt_loc = (ba.get('statement_location') or '').strip()
    if not (bankname and stmt_loc):
        raise HTTPException(status_code=400, detail="Bank account is missing bankname or statement_location")
    cfg = state.BANKS_CFG_DB.get(bankname)
    if not cfg:
        raise HTTPException(status_code=400, detail=f"Missing bank config for {bankname}")

    # Read uploaded CSV into memory as text
    try:
        raw = await file.read()
        text = raw.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {e}")

    # Parse CSV using bank config and validate dates belong to CURRENT_YEAR
    delim = (cfg.get('delim') or ',')
    starts = cfg.get('ignore_lines_startswith') or []
    contains = cfg.get('ignore_lines_contains') or []
    columns_list = cfg.get('columns') or []
    colmap = {}
    for entry in columns_list:
        if isinstance(entry, dict) and entry:
            colmap = entry
            break
    date_idx = int(colmap.get('date') or 0)
    if not date_idx:
        raise HTTPException(status_code=400, detail="Bank config is missing date column index")
    raw_fmt = (cfg.get('date_format') or '').strip()
    year_expected = str(state.CURRENT_YEAR)

    # Filter lines according to ignore rules
    filtered_lines = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip('\n')
        if not line.strip():
            continue
        skip = False
        for s in starts:
            try:
                if s and line.startswith(s):
                    skip = True; break
            except Exception:
                continue
        if skip:
            continue
        for c in contains:
            try:
                if c and (c in line):
                    skip = True; break
            except Exception:
                continue
        if skip:
            continue
        filtered_lines.append(line)

    # Validate year on each row
    try:
        reader = csv.reader(filtered_lines, delimiter=delim)
        row_idx = 0
        for parts in reader:
            row_idx += 1
            if not parts:
                continue
            parts = [p.strip() for p in parts]
            if date_idx <= 0:
                continue
            date_val = parts[date_idx-1] if len(parts) >= date_idx else ''
            date_out = _normalize_date(date_val, raw_fmt)
            # Expect date_out like YYYY-MM-DD; validate year
            if not date_out or len(date_out) < 4 or date_out[:4] != year_expected:
                raise HTTPException(status_code=400, detail=f"Row {row_idx}: date not in CURRENT_YEAR {year_expected}: '{date_val}' -> '{date_out}'")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    # Save file to statement_location/CURRENT_YEAR/bank_stmts/<bankaccountname>.csv
    try:
        dest_dir = Path(stmt_loc).expanduser().resolve() / str(state.CURRENT_YEAR) / 'bank_stmts'
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{key}.csv"
        with dest_path.open('w', encoding='utf-8', newline='') as wf:
            wf.write(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # After saving the raw statement, prepare normalized CSV and classify
    try:
        normalized_dir = state.NORMALIZED_DIR_PATH
        if not normalized_dir:
            raise RuntimeError("NORMALIZED_DIR_PATH is not configured")
        # Build normalized CSV for this specific bank account
        _process_bank_statement_for_account(key, cfg, dest_path, normalized_dir, state.logger)
        # Classify this bank account using the freshly normalized data
        classify_bank(key)
    except Exception as e:
        # Surface errors so caller knows normalization/classification failed
        raise HTTPException(status_code=500, detail=f"Failed to normalize or classify statement: {e}")

    return {"ok": True, "path": str(dest_path)}
