from fastapi import APIRouter, HTTPException, Query
from typing import List

from .. import main as state
from ..core.models import ClassifyRuleRecord
from ..core.utils import dump_yaml_entities

router = APIRouter(prefix="/api", tags=["classify-rules"])


@router.get("/classify-rules", response_model=List[ClassifyRuleRecord])
async def list_classify_rules():
    return list(state.CLASSIFY_DB.values())


@router.get("/common-rules", response_model=List[ClassifyRuleRecord])
async def list_common_rules():
    """Return derived common rules (built on startup)."""
    return list(state.COMMON_RULES_DB.values())


@router.get("/inherit-common-to-bank", response_model=List[ClassifyRuleRecord])
async def list_inherit_common_to_bank():
    """Return derived inherit rules (built on startup)."""
    return list(state.INHERIT_RULES_DB.values())


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


# Common Rules CRUD
@router.post("/common-rules", response_model=ClassifyRuleRecord, status_code=201)
async def add_common_rule(payload: ClassifyRuleRecord):
    ttype = (payload.transaction_type or "").strip().lower()
    patt = (payload.pattern_match_logic or "").strip()
    if not (ttype and patt):
        raise HTTPException(status_code=400, detail="transaction_type and pattern_match_logic are required")
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(ttype):
        raise HTTPException(status_code=400, detail="Invalid transaction_type: lowercase alphanumeric and underscore only")
    key = f"common|{ttype}|{patt}"
    rec = {
        "bankaccountname": "common",
        "transaction_type": ttype,
        "pattern_match_logic": patt,
        "tax_category": "",
        "property": "",
        "otherentity": "",
    }
    state.COMMON_RULES_DB[key] = rec
    # persist YAML
    if state.CLASSIFY_CSV_PATH:
        base_dir = state.CLASSIFY_CSV_PATH.parent
        dump_yaml_entities(base_dir / 'common_rules.yaml', list(state.COMMON_RULES_DB.values()), key_field='transaction_type')
    return rec


@router.delete("/common-rules", status_code=204)
async def delete_common_rule(
    transaction_type: str = Query(""),
    pattern_match_logic: str = Query("")
):
    ttype = (transaction_type or "").strip().lower()
    patt = (pattern_match_logic or "").strip()
    key = f"common|{ttype}|{patt}"
    if key not in state.COMMON_RULES_DB:
        raise HTTPException(status_code=404, detail="Common rule not found")
    del state.COMMON_RULES_DB[key]
    if state.CLASSIFY_CSV_PATH:
        base_dir = state.CLASSIFY_CSV_PATH.parent
        dump_yaml_entities(base_dir / 'common_rules.yaml', list(state.COMMON_RULES_DB.values()), key_field='transaction_type')
    return


# Inherit Common To Bank CRUD
@router.post("/inherit-common-to-bank", response_model=ClassifyRuleRecord, status_code=201)
async def add_inherit_rule(payload: ClassifyRuleRecord):
    bank = (payload.bankaccountname or "").strip().lower()
    ttype = (payload.transaction_type or "").strip().lower()
    patt = (payload.pattern_match_logic or "").strip()
    tax = (payload.tax_category or "").strip().lower()
    prop = (payload.property or "").strip().lower()
    other = (payload.otherentity or "").strip()
    if not (bank and ttype and patt):
        raise HTTPException(status_code=400, detail="bankaccountname, transaction_type and pattern_match_logic are required")
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(bank):
        raise HTTPException(status_code=400, detail="Invalid bankaccountname: lowercase alphanumeric and underscore only")
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(ttype):
        raise HTTPException(status_code=400, detail="Invalid transaction_type: lowercase alphanumeric and underscore only")
    # tax/property can be empty; if non-empty, validate
    if tax and not state.ALNUM_UNDERSCORE_LOWER_RE.match(tax):
        raise HTTPException(status_code=400, detail="Invalid tax_category: lowercase alphanumeric and underscore only")
    if prop and not state.ALNUM_UNDERSCORE_LOWER_RE.match(prop):
        raise HTTPException(status_code=400, detail="Invalid property: lowercase alphanumeric and underscore only")
    key = f"{bank}|{ttype}|{prop}|{patt}|{tax}|{other}"
    rec = {
        "bankaccountname": bank,
        "transaction_type": ttype,
        "pattern_match_logic": patt,
        "tax_category": tax,
        "property": prop,
        "otherentity": other,
    }
    state.INHERIT_RULES_DB[key] = rec
    if state.CLASSIFY_CSV_PATH:
        base_dir = state.CLASSIFY_CSV_PATH.parent
        dump_yaml_entities(base_dir / 'inherit_common_to_bank.yaml', list(state.INHERIT_RULES_DB.values()), key_field='bankaccountname')
    return rec


@router.delete("/inherit-common-to-bank", status_code=204)
async def delete_inherit_rule(
    bankaccountname: str = Query(""),
    transaction_type: str = Query(""),
    pattern_match_logic: str = Query(""),
    property: str = Query(""),
    tax_category: str = Query(""),
    otherentity: str = Query("")
):
    bank = (bankaccountname or "").strip().lower()
    ttype = (transaction_type or "").strip().lower()
    patt = (pattern_match_logic or "").strip()
    prop = (property or "").strip().lower()
    tax = (tax_category or "").strip().lower()
    other = (otherentity or "").strip()
    key = f"{bank}|{ttype}|{prop}|{patt}|{tax}|{other}"
    if key not in state.INHERIT_RULES_DB:
        raise HTTPException(status_code=404, detail="Inherit rule not found")
    del state.INHERIT_RULES_DB[key]
    if state.CLASSIFY_CSV_PATH:
        base_dir = state.CLASSIFY_CSV_PATH.parent
        dump_yaml_entities(base_dir / 'inherit_common_to_bank.yaml', list(state.INHERIT_RULES_DB.values()), key_field='bankaccountname')
    return
