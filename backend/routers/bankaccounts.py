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
        "statement_location": (payload.statement_location or "").strip(),
    }
    if not item["bankname"]:
        raise HTTPException(status_code=400, detail="bankname is required")
    state.BA_DB[key] = item
    # persist YAML
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
