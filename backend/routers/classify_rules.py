from fastapi import APIRouter, HTTPException, Query
from typing import List

from .. import main as state
from ..core.models import ClassifyRuleRecord
from ..core.utils import dump_yaml_entities

router = APIRouter(prefix="/api", tags=["classify-rules"])


@router.get("/classify-rules", response_model=List[ClassifyRuleRecord])
async def list_classify_rules():
    return list(state.CLASSIFY_DB.values())


@router.post("/classify-rules", response_model=ClassifyRuleRecord, status_code=201)
async def add_classify_rule(payload: ClassifyRuleRecord):
    bank = (payload.bankaccountname or "").strip().lower()
    ttype = (payload.transaction_type or "").strip().lower()
    patt = (payload.pattern_match_logic or "").strip()
    tax = (payload.tax_category or "").strip().lower()
    prop = (payload.property or "").strip().lower()
    other = (payload.otherentity or "").strip()

    if not (bank and ttype and patt and tax and prop and other):
        raise HTTPException(status_code=400, detail="All fields are required")
    # Enforce simple allowed patterns similar to other entities
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(bank):
        raise HTTPException(status_code=400, detail="Invalid bankaccountname: lowercase alphanumeric and underscore only")
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(ttype):
        raise HTTPException(status_code=400, detail="Invalid transaction_type: lowercase alphanumeric and underscore only")
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(tax):
        raise HTTPException(status_code=400, detail="Invalid tax_category: lowercase alphanumeric and underscore only")
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(prop):
        raise HTTPException(status_code=400, detail="Invalid property: lowercase alphanumeric and underscore only")

    # Allow multiple rules per triplet; use pattern in composite key to avoid overwrites
    key = f"{bank}|{ttype}|{prop}|{patt}"

    rec = {
        "bankaccountname": bank,
        "transaction_type": ttype,
        "pattern_match_logic": patt,
        "tax_category": tax,
        "property": prop,
        "otherentity": other,
    }
    state.CLASSIFY_DB[key] = rec

    if state.CLASSIFY_CSV_PATH:
        dump_yaml_entities(state.CLASSIFY_CSV_PATH.with_suffix('.yaml'), list(state.CLASSIFY_DB.values()), key_field='bankaccountname')

    return rec


@router.delete("/classify-rules", status_code=204)
async def delete_classify_rule(
    bankaccountname: str = Query(""),
    transaction_type: str = Query(""),
    property: str = Query("")
):
    bank = (bankaccountname or "").strip().lower()
    ttype = (transaction_type or "").strip().lower()
    prop = (property or "").strip().lower()
    # Delete all rules that match the triplet, regardless of pattern
    to_delete = [k for k, v in state.CLASSIFY_DB.items() if v.get("bankaccountname") == bank and v.get("transaction_type") == ttype and v.get("property") == prop]
    if not to_delete:
        raise HTTPException(status_code=404, detail="Classify rule not found")
    for k in to_delete:
        del state.CLASSIFY_DB[k]
    if state.CLASSIFY_CSV_PATH:
        dump_yaml_entities(state.CLASSIFY_CSV_PATH.with_suffix('.yaml'), list(state.CLASSIFY_DB.values()), key_field='bankaccountname')
    return
