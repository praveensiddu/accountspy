from fastapi import APIRouter, HTTPException
from typing import List

from .. import main as state
from ..core.models import BankAccountRecord
from ..core.utils import dump_yaml_entities

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
        "abbreviation": (getattr(payload, 'abbreviation', '') or '').strip(),
    }
    if not item["bankname"]:
        raise HTTPException(status_code=400, detail="bankname is required")
    # Validate statement_location: strip edges, reject if whitespace in middle, ensure trailing '/'
    try:
        raw_sl = payload.statement_location or ""
        sl = raw_sl.strip()
        if sl:
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
    abbreviation = (getattr(payload, 'abbreviation', '') or '').strip()
    # Validate statement_location: strip edges, reject if whitespace in middle, ensure trailing '/'
    try:
        raw_sl = payload.statement_location or ""
        sl = raw_sl.strip()
        if sl:
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
        "abbreviation": abbreviation,
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
