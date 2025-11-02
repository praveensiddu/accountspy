from fastapi import APIRouter, HTTPException, Query
from typing import List

from .. import main as state
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


# Bank rules served from per-bank YAML files under ENTITIES_DIR/bank_rules/
@router.get("/bank-rules/banks", response_model=List[str])
async def list_bank_rules_banks():
    base_dir = state.CLASSIFY_CSV_PATH.parent if state.CLASSIFY_CSV_PATH else None
    if not base_dir:
        return []
    rules_dir = base_dir / 'bank_rules'
    if not rules_dir.exists() or not rules_dir.is_dir():
        return []
    banks = []
    for p in rules_dir.glob('*.yaml'):
        try:
            banks.append(p.stem)
        except Exception:
            continue
    return sorted(banks)


@router.get("/bank-rules", response_model=List[ClassifyRuleRecord])
async def get_bank_rules(bankaccountname: str = Query("")):
    bank = (bankaccountname or "").strip().lower()
    base_dir = state.CLASSIFY_CSV_PATH.parent if state.CLASSIFY_CSV_PATH else None
    if not base_dir or not bank:
        return []
    rules_path: Path = (base_dir / 'bank_rules' / f"{bank}.yaml")
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
                'otherentity': (item.get('otherentity') or ''),
                'order': int(item.get('order', 0) or 0),
            }
            out.append(rec)
        return out
    except Exception:
        return []


def _read_bank_rules_list(base_dir: Path, bank: str):
    path = base_dir / 'bank_rules' / f"{bank}.yaml"
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or []
    return data if isinstance(data, list) else []


def _write_bank_rules_list(base_dir: Path, bank: str, items: list):
    path = base_dir / 'bank_rules' / f"{bank}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        yaml.safe_dump(items, f, sort_keys=True, allow_unicode=True)


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
        patt(rec.get('pattern_match_logic')),
        norm(rec.get('tax_category')),
        (rec.get('otherentity') or '').strip(),
    ])


@router.post("/bank-rules", response_model=ClassifyRuleRecord, status_code=201)
async def add_bank_rule(payload: ClassifyRuleRecord):
    base_dir = state.CLASSIFY_CSV_PATH.parent if state.CLASSIFY_CSV_PATH else None
    if not base_dir:
        raise HTTPException(status_code=500, detail="Entities base directory not configured")
    bank = (payload.bankaccountname or '').strip().lower()
    ttype = (payload.transaction_type or '').strip().lower()
    patt = (payload.pattern_match_logic or '').strip()
    tax = (payload.tax_category or '').strip().lower()
    prop = (payload.property or '').strip().lower()
    group = (payload.group or '').strip().lower()
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
        'otherentity': other,
        'order': order,
    }
    items = [dict(x) for x in _read_bank_rules_list(base_dir, bank) if isinstance(x, dict)]
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
        _write_bank_rules_list(base_dir, bank, merged_list)
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

    _write_bank_rules_list(base_dir, bank, merged_list)
    return rec


@router.delete("/bank-rules", status_code=204)
async def delete_bank_rule(
    bankaccountname: str = Query(""),
    transaction_type: str = Query(""),
    pattern_match_logic: str = Query(""),
    property: str = Query(""),
    group: str = Query(""),
    tax_category: str = Query(""),
    otherentity: str = Query("")
):
    base_dir = state.CLASSIFY_CSV_PATH.parent if state.CLASSIFY_CSV_PATH else None
    if not base_dir:
        raise HTTPException(status_code=500, detail="Entities base directory not configured")
    bank = (bankaccountname or '').strip().lower()
    ttype = (transaction_type or '').strip().lower()
    patt = (pattern_match_logic or '').strip()
    prop = (property or '').strip().lower()
    grp = (group or '').strip().lower()
    tax = (tax_category or '').strip().lower()
    other = (otherentity or '').strip()
    if not bank:
        raise HTTPException(status_code=400, detail="bankaccountname is required")
    items = _read_bank_rules_list(base_dir, bank)
    target_key = _rule_key({
        'bankaccountname': bank,
        'transaction_type': ttype,
        'pattern_match_logic': patt,
        'property': prop,
        'group': grp,
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
    _write_bank_rules_list(base_dir, bank, remaining)
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
