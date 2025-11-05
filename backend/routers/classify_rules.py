from fastapi import APIRouter, HTTPException, Query
from typing import List

from .. import main as state
from .. import classify as classifier
from ..property_sum import prepare_and_save_property_sum
from ..company_sum import prepare_and_save_company_sum
from ..core.models import ClassifyRuleRecord, InheritRuleRecord
from pydantic import BaseModel
from ..core.utils import dump_yaml_entities
from pathlib import Path
import yaml

router = APIRouter(prefix="/api", tags=["classify-rules"])


class InheritRulePayload(BaseModel):
    bankaccountname: str
    tax_category: str = ""
    property: str = ""
    group: str = ""
    otherentity: str = ""

@router.get("/classify-rules", response_model=List[ClassifyRuleRecord])
async def list_classify_rules():
    return list(state.CLASSIFY_DB.values())


@router.get("/common-rules", response_model=List[ClassifyRuleRecord])
async def list_common_rules():
    """Return derived common rules (built on startup)."""
    return list(state.COMMON_RULES_DB.values())


@router.get("/inherit-common-to-bank", response_model=List[InheritRuleRecord])
async def list_inherit_common_to_bank():
    """Return derived inherit rules (built on startup)."""
    return list(state.INHERIT_RULES_DB.values())


def _bank_rules_path_for(bank: str) -> Path:
    bank = (bank or '').strip().lower()
    ba = state.BA_DB.get(bank) or {}
    sl = (ba.get('statement_location') or '').strip()
    year = state.CURRENT_YEAR or ''
    return Path(sl) / year / 'bank_rules' / f"{bank}.yaml"


# Bank rules served from per-bank YAML files under each bank's statement_location/CURRENT_YEAR/bank_rules/
@router.get("/bank-rules/banks", response_model=List[str])
async def list_bank_rules_banks():
    out = []
    for bank in (state.BA_DB or {}).keys():
        p = _bank_rules_path_for(bank)
        try:
            if p.exists():
                out.append(bank)
        except Exception:
            continue
    return sorted(out)


@router.get("/bank-rules", response_model=List[ClassifyRuleRecord])
async def get_bank_rules(bankaccountname: str = Query("")):
    bank = (bankaccountname or "").strip().lower()
    if not bank:
        return []
    if bank not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    ba = state.BA_DB.get(bank) or {}
    sl = (ba.get('statement_location') or '').strip()
    if not sl:
        raise HTTPException(status_code=400, detail="statement_location not set for this bank account")
    if not state.CURRENT_YEAR:
        raise HTTPException(status_code=400, detail="CURRENT_YEAR is not configured")
    rules_path: Path = _bank_rules_path_for(bank)
    if not rules_path.exists():
        return []
    try:
        with rules_path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or []
        if not isinstance(data, list):
            return []
        # ensure each item includes bankaccountname
        out = []
        for item in data:
            if not isinstance(item, dict):
                continue
            rec = {
                'bankaccountname': (item.get('bankaccountname') or bank),
                'transaction_type': (item.get('transaction_type') or ''),
                'pattern_match_logic': (item.get('pattern_match_logic') or ''),
                'tax_category': (item.get('tax_category') or ''),
                'property': (item.get('property') or ''),
                'group': (item.get('group') or ''),
                'company': (item.get('company') or ''),
                'otherentity': (item.get('otherentity') or ''),
                'order': int(item.get('order', 0) or 0),
            }
            out.append(rec)
        return out
    except Exception:
        return []


@router.get("/bank-rules/max-order")
async def get_bank_rules_max_order(bankaccountname: str = Query("")):
    """Return the maximum valid (>0) order for rules in the given bank's YAML file.
    If no rules or invalid orders, returns 0.
    """
    bank = (bankaccountname or "").strip().lower()
    if not bank:
        return {"max_order": 0}
    if bank not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    ba = state.BA_DB.get(bank) or {}
    sl = (ba.get('statement_location') or '').strip()
    if not sl:
        raise HTTPException(status_code=400, detail="statement_location not set for this bank account")
    if not state.CURRENT_YEAR:
        raise HTTPException(status_code=400, detail="CURRENT_YEAR is not configured")
    try:
        items = _read_bank_rules_list(bank)
        max_order = 0
        for it in items:
            try:
                o = int(it.get('order') or 0)
            except Exception:
                o = 0
            if o > 0 and o > max_order:
                max_order = o
        return {"max_order": max_order}
    except Exception:
        return {"max_order": 0}


def _read_bank_rules_list(bank: str):
    path = _bank_rules_path_for(bank)
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or []
    return data if isinstance(data, list) else []


def _write_bank_rules_list(bank: str, items: list):
    path = _bank_rules_path_for(bank)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        yaml.safe_dump(items, f, sort_keys=True, allow_unicode=True)


def _write_and_recompute(bank: str, items: list):
    _write_bank_rules_list(bank, items)
    try:
        classifier.classify_bank(bank)
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


class UpdateOrderPayload(BaseModel):
    currentorder: int
    updatedorder: int


@router.post("/bank-rules/update-order")
async def update_bank_rule_order(bankaccountname: str = Query(""), payload: UpdateOrderPayload = None):
    bank = (bankaccountname or '').strip().lower()
    if not bank:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    if bank not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    ba = state.BA_DB.get(bank) or {}
    sl = (ba.get('statement_location') or '').strip()
    if not sl:
        raise HTTPException(status_code=400, detail="statement_location not set for this bank account")
    if not state.CURRENT_YEAR:
        raise HTTPException(status_code=400, detail="CURRENT_YEAR is not configured")
    if payload is None:
        raise HTTPException(status_code=400, detail="payload is required")
    try:
        cur = int(payload.currentorder)
        new = int(payload.updatedorder)
    except Exception:
        raise HTTPException(status_code=400, detail="currentorder and updatedorder must be integers")
    if cur < 1 or new < 1:
        raise HTTPException(status_code=400, detail="orders must be >= 1")
    items = [dict(x) for x in _read_bank_rules_list(bank)]
    if not items:
        raise HTTPException(status_code=404, detail="No rules found for this bank")
    # Determine max order (>0)
    max_order = 0
    for it in items:
        try:
            o = int(it.get('order') or 0)
        except Exception:
            o = 0
        if o > max_order:
            max_order = o
    if new > max_order:
        raise HTTPException(status_code=400, detail=f"updatedorder must be between 1 and {max_order}")
    # Sort by current order and locate the target
    try:
        items.sort(key=lambda x: int(x.get('order') or 0))
    except Exception:
        pass
    target_idx = None
    for idx, it in enumerate(items):
        try:
            if int(it.get('order') or 0) == cur:
                target_idx = idx
                break
        except Exception:
            continue
    if target_idx is None:
        raise HTTPException(status_code=404, detail="Rule with currentorder not found")
    # Remove target and insert at updated position (1-based)
    target = items.pop(target_idx)
    insert_at = max(0, min(len(items), new - 1))
    items.insert(insert_at, target)
    # Renumber continuous 1..n
    for i, it in enumerate(items, start=1):
        it['order'] = i
    _write_and_recompute(bank, items)
    return {"ok": True, "max_order": max_order}


def _rule_key(rec: dict) -> str:
    def norm(s: str) -> str: return (s or '').strip().lower()
    def patt(s: str) -> str:
        s = (s or '').strip()
        return ' '.join(s.split()).lower()
    return '|'.join([
        norm(rec.get('bankaccountname')),
        norm(rec.get('transaction_type')),
        norm(rec.get('property')),
        norm(rec.get('group')),
        norm(rec.get('company')),
        patt(rec.get('pattern_match_logic')),
        norm(rec.get('tax_category')),
        (rec.get('otherentity') or '').strip(),
    ])


@router.post("/bank-rules", response_model=ClassifyRuleRecord, status_code=201)
async def add_bank_rule(payload: ClassifyRuleRecord):
    bank = (payload.bankaccountname or '').strip().lower()
    ttype = (payload.transaction_type or '').strip().lower()
    patt = (payload.pattern_match_logic or '').strip()
    tax = (payload.tax_category or '').strip().lower()
    prop = (payload.property or '').strip().lower()
    group = (payload.group or '').strip().lower()
    company = (getattr(payload, 'company', '') or '').strip().lower()
    other = (payload.otherentity or '').strip()
    # order is mandatory integer
    try:
        order = int(getattr(payload, 'order'))
    except Exception:
        raise HTTPException(status_code=400, detail="order must be an integer starting at 1")
    if order < 1:
        raise HTTPException(status_code=400, detail="order must be >= 1")
    if not (bank and ttype and patt):
        raise HTTPException(status_code=400, detail="bankaccountname, transaction_type, pattern_match_logic are required")
    if bank not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    ba = state.BA_DB.get(bank) or {}
    sl = (ba.get('statement_location') or '').strip()
    if not sl:
        raise HTTPException(status_code=400, detail="statement_location not set for this bank account")
    if not state.CURRENT_YEAR:
        raise HTTPException(status_code=400, detail="CURRENT_YEAR is not configured")
    # Require tax_category as well
    if not tax:
        raise HTTPException(status_code=400, detail="tax_category is required")
    # Only one of property or group may be set (or neither)
    if prop and group:
        raise HTTPException(status_code=400, detail="Only one of property or group may be set, not both")
    rec = {
        'bankaccountname': bank,
        'transaction_type': ttype,
        'pattern_match_logic': patt,
        'tax_category': tax,
        'property': prop,
        'group': group,
        'company': company,
        'otherentity': other,
        'order': order,
    }
    items = [dict(x) for x in _read_bank_rules_list(bank) if isinstance(x, dict)]
    new_key = _rule_key(rec)
    # Map existing items by key for quick lookup
    key_to_item = { _rule_key(x): x for x in items }

    # First: if any existing item in this bank has the same normalized pattern_match_logic,
    # update it and retain order. If multiple exist, collapse to a single one keeping the smallest order.
    patt_norm = ' '.join(patt.split()).lower()
    same_pattern_items = []
    for it in items:
        try:
            it_patt_norm = ' '.join(((it.get('pattern_match_logic') or '').strip()).split()).lower()
        except Exception:
            it_patt_norm = ''
        if it_patt_norm == patt_norm:
            same_pattern_items.append(it)

    if same_pattern_items:
        # Determine the minimal order among duplicates (default to 1 if invalid)
        keep_order = 1
        try:
            keep_order = min([int(x.get('order') or 0) or 1 for x in same_pattern_items]) or 1
        except Exception:
            keep_order = 1
        # Build the updated single record (ignore posted order)
        updated = {
            'bankaccountname': bank,
            'transaction_type': ttype,
            'pattern_match_logic': patt,
            'tax_category': tax,
            'property': prop,
            'group': group,
            'company': company,
            'otherentity': other,
            'order': keep_order,
        }
        # Remove all items with this pattern and add the single updated one
        merged_list = []
        for it in items:
            it_patt_norm = ' '.join(((it.get('pattern_match_logic') or '').strip()).split()).lower()
            if it_patt_norm != patt_norm:
                merged_list.append(it)
        merged_list.append(updated)
        # Renumber continuous 1..n by order
        merged_list.sort(key=lambda x: int(x.get('order') or 0))
        for idx, it in enumerate(merged_list, start=1):
            it['order'] = idx
        _write_and_recompute(bank, merged_list)
        return updated

    if new_key in key_to_item:
        # Update existing: keep original order, ignore payload order
        existing = key_to_item[new_key]
        rec['order'] = int(existing.get('order') or 0) or 1
        # Replace fields except we keep order as above
        key_to_item[new_key] = rec
        merged_list = list(key_to_item.values())
    else:
        # Validate requested order is within [1 .. highest+1]
        try:
            max_order = 0
            for it in items:
                try:
                    o = int(it.get('order') or 0)
                except Exception:
                    o = 0
                if o > max_order:
                    max_order = o
            if order > (max_order + 1):
                raise HTTPException(status_code=400, detail=f"order must be <= {max_order + 1}")
        except HTTPException:
            raise
        except Exception:
            # Fallback: if we cannot determine max, allow only order == 1
            if order > 1:
                raise HTTPException(status_code=400, detail="order must be <= 1")
        # Insert new: clamp order into [1..len(items)+1]
        n = len(items)
        insert_order = order if order <= n + 1 else (n + 1)
        # Shift items with order >= insert_order by +1
        for it in items:
            try:
                o = int(it.get('order') or 0)
            except Exception:
                o = 0
            if o >= insert_order and o > 0:
                it['order'] = o + 1
        rec['order'] = insert_order
        merged_list = items + [rec]

    # Renumber to ensure continuous 1..n
    merged_list.sort(key=lambda x: int(x.get('order') or 0))
    for idx, it in enumerate(merged_list, start=1):
        it['order'] = idx

    _write_and_recompute(bank, merged_list)
    return rec


@router.delete("/bank-rules", status_code=204)
async def delete_bank_rule(
    bankaccountname: str = Query(""),
    transaction_type: str = Query(""),
    pattern_match_logic: str = Query(""),
    property: str = Query(""),
    group: str = Query(""),
    company: str = Query(""),
    tax_category: str = Query(""),
    otherentity: str = Query("")
):
    bank = (bankaccountname or '').strip().lower()
    ttype = (transaction_type or '').strip().lower()
    patt = (pattern_match_logic or '').strip()
    prop = (property or '').strip().lower()
    grp = (group or '').strip().lower()
    tax = (tax_category or '').strip().lower()
    other = (otherentity or '').strip()
    comp = (company or '').strip().lower()
    if not bank:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    if bank not in state.BA_DB:
        raise HTTPException(status_code=404, detail="Bank account not found")
    ba = state.BA_DB.get(bank) or {}
    sl = (ba.get('statement_location') or '').strip()
    if not sl:
        raise HTTPException(status_code=400, detail="statement_location not set for this bank account")
    if not state.CURRENT_YEAR:
        raise HTTPException(status_code=400, detail="CURRENT_YEAR is not configured")
    items = _read_bank_rules_list(bank)
    target_key = _rule_key({
        'bankaccountname': bank,
        'transaction_type': ttype,
        'pattern_match_logic': patt,
        'property': prop,
        'group': grp,
        'company': comp,
        'tax_category': tax,
        'otherentity': other,
    })
    remaining = [x for x in items if _rule_key(x) != target_key]
    if len(remaining) == len(items):
        raise HTTPException(status_code=404, detail="Rule not found")
    # Renumber remaining to continuous 1..n
    remaining = [dict(x) for x in remaining]
    try:
        remaining.sort(key=lambda x: int(x.get('order') or 0))
    except Exception:
        pass
    for idx, it in enumerate(remaining, start=1):
        it['order'] = idx
    _write_and_recompute(bank, remaining)
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
@router.post("/inherit-common-to-bank", response_model=InheritRuleRecord, status_code=201)
async def add_inherit_rule(payload: InheritRulePayload):
    bank = (payload.bankaccountname or "").strip().lower()
    tax = (payload.tax_category or "").strip().lower()
    prop = (payload.property or "").strip().lower()
    group = (payload.group or "").strip().lower()
    other = (payload.otherentity or "").strip()
    if not bank:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(bank):
        raise HTTPException(status_code=400, detail="Invalid bankaccountname: lowercase alphanumeric and underscore only")
    if tax and not state.ALNUM_UNDERSCORE_LOWER_RE.match(tax):
        raise HTTPException(status_code=400, detail="Invalid tax_category: lowercase alphanumeric and underscore only")
    if prop and not state.ALNUM_UNDERSCORE_LOWER_RE.match(prop):
        raise HTTPException(status_code=400, detail="Invalid property: lowercase alphanumeric and underscore only")
    if group and not state.ALNUM_UNDERSCORE_LOWER_RE.match(group):
        raise HTTPException(status_code=400, detail="Invalid group: lowercase alphanumeric and underscore only")
    key = f"{bank}|{prop}|{group}|{tax}|{other}"
    rec = {
        "bankaccountname": bank,
        "tax_category": tax,
        "property": prop,
        "group": group,
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
    property: str = Query(""),
    group: str = Query(""),
    tax_category: str = Query(""),
    otherentity: str = Query("")
):
    bank = (bankaccountname or "").strip().lower()
    prop = (property or "").strip().lower()
    grp = (group or "").strip().lower()
    tax = (tax_category or "").strip().lower()
    other = (otherentity or "").strip()
    key = f"{bank}|{prop}|{grp}|{tax}|{other}"
    if key not in state.INHERIT_RULES_DB:
        raise HTTPException(status_code=404, detail="Inherit rule not found")
    del state.INHERIT_RULES_DB[key]
    if state.CLASSIFY_CSV_PATH:
        base_dir = state.CLASSIFY_CSV_PATH.parent
        dump_yaml_entities(base_dir / 'inherit_common_to_bank.yaml', list(state.INHERIT_RULES_DB.values()), key_field='bankaccountname')
    return
