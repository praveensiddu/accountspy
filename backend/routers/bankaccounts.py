from fastapi import APIRouter, HTTPException
from typing import List

from .. import main as state
from ..core.models import BankAccountRecord

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
    return state.BA_DB[key]


@router.delete("/bankaccounts/{bankaccountname}", status_code=204)
async def delete_bankaccount(bankaccountname: str):
    key = bankaccountname.strip().lower()
    if key not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    del state.BA_DB[key]
    return
