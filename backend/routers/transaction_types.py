from fastapi import APIRouter, HTTPException
from typing import List

from .. import main as state
from ..core.utils import dump_yaml_entities
from ..core.models import TransactionTypeRecord

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
