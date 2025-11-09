from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from .. import main as state
from ..core.utils import dump_yaml_entities
from ..core.models import TransactionTypeRecord
from .classify_rules import _read_bank_rules_list, _write_bank_rules_list, _recompute

router = APIRouter(prefix="/api", tags=["transaction-types"])


@router.get("/transaction-types", response_model=List[TransactionTypeRecord])
async def list_transaction_types():
    return list(state.TT_DB.values())


@router.post("/transaction-types", response_model=TransactionTypeRecord, status_code=201)
async def add_transaction_type(payload: TransactionTypeRecord):
    key = (payload.transactiontype or "").strip().lower()
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid transaction type: lowercase alphanumeric and underscore only")
    if key in state.TT_DB:
        raise HTTPException(status_code=409, detail="Transaction type already exists")
    state.TT_DB[key] = {"transactiontype": key}
    if state.TT_CSV_PATH:
        dump_yaml_entities(state.TT_CSV_PATH.with_suffix('.yaml'), list(state.TT_DB.values()), key_field='transactiontype')
    return state.TT_DB[key]


@router.delete("/transaction-types/{transactiontype}", status_code=204)
async def delete_transaction_type(transactiontype: str):
    key = transactiontype.strip().lower()
    if key not in state.TT_DB:
        raise HTTPException(status_code=404, detail="Transaction type not found")
    del state.TT_DB[key]
    if state.TT_CSV_PATH:
        dump_yaml_entities(state.TT_CSV_PATH.with_suffix('.yaml'), list(state.TT_DB.values()), key_field='transactiontype')
    return


class RenameTxTypePayload(BaseModel):
    from_type: str
    to_type: str


@router.post("/transaction-types/rename")
async def rename_transaction_type(payload: RenameTxTypePayload) -> Dict[str, Any]:
    old = (payload.from_type or "").strip().lower()
    new = (payload.to_type or "").strip().lower()
    if not old or not new:
        raise HTTPException(status_code=400, detail="from_type and to_type are required")
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(new):
        raise HTTPException(status_code=400, detail="Invalid new transaction type: lowercase alphanumeric and underscore only")
    if old not in state.TT_DB:
        raise HTTPException(status_code=404, detail="Old transaction type not found")
    if new in state.TT_DB and new != old:
        raise HTTPException(status_code=409, detail="New transaction type already exists")

    # Update transaction types DB (rename key)
    if new != old:
        del state.TT_DB[old]
        state.TT_DB[new] = {"transactiontype": new}
        if state.TT_CSV_PATH:
            dump_yaml_entities(state.TT_CSV_PATH.with_suffix('.yaml'), list(state.TT_DB.values()), key_field='transactiontype')

    # Update all bank rules for each bankaccount
    changed_banks = []
    for bank in list((state.BA_DB or {}).keys()):
        try:
            items = _read_bank_rules_list(bank)
            if not isinstance(items, list) or not items:
                continue
            updated = False
            new_items = []
            for it in items:
                if not isinstance(it, dict):
                    new_items.append(it)
                    continue
                tt = (it.get('transaction_type') or '').strip().lower()
                if tt == old:
                    it = dict(it)
                    it['transaction_type'] = new
                    updated = True
                new_items.append(it)
            if updated:
                _write_bank_rules_list(bank, new_items)
                changed_banks.append(bank)
        except Exception:
            continue

    # Recompute for affected banks
    for bank in changed_banks:
        try:
            _recompute(bank)
        except Exception:
            pass

    return {"ok": True, "renamed": new, "banks_updated": changed_banks}
