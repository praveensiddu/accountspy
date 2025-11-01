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
                'order': int(item.get('order') or 0),
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
    order = None
    try:
        order = int(getattr(payload, 'order', 0) or 0)
    except Exception:
        order = 0
    if order == 0:
        order = 10000
    if not (bank and ttype and patt):
        raise HTTPException(status_code=400, detail="bankaccountname, transaction_type, pattern_match_logic are required")
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
    items = _read_bank_rules_list(base_dir, bank)
    # de-dup by composite key
    seen = { _rule_key(x): x for x in items if isinstance(x, dict) }
    seen[_rule_key(rec)] = rec
    _write_bank_rules_list(base_dir, bank, list(seen.values()))
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
    _write_bank_rules_list(base_dir, bank, remaining)
    return


@router.post("/classify-rules", response_model=ClassifyRuleRecord, status_code=201)
async def add_classify_rule(payload: ClassifyRuleRecord):
    bank = (payload.bankaccountname or "").strip().lower()
    ttype = (payload.transaction_type or "").strip().lower()
    patt = (payload.pattern_match_logic or "").strip()
    tax = (payload.tax_category or "").strip().lower()
    prop = (payload.property or "").strip().lower()
    group = (payload.group or "").strip().lower()
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
    if group and not state.ALNUM_UNDERSCORE_LOWER_RE.match(group):
        raise HTTPException(status_code=400, detail="Invalid group: lowercase alphanumeric and underscore only")

    # Allow multiple rules per triplet; use pattern in composite key to avoid overwrites
    key = f"{bank}|{ttype}|{prop}|{group}|{patt}"

    rec = {
        "bankaccountname": bank,
        "transaction_type": ttype,
        "pattern_match_logic": patt,
        "tax_category": tax,
        "property": prop,
        "group": group,
        "otherentity": other,
    }
    state.CLASSIFY_DB[key] = rec
    # Persist to bank_rules.yaml
    if state.CLASSIFY_CSV_PATH:
        base_dir = state.CLASSIFY_CSV_PATH.parent
        dump_yaml_entities(base_dir / 'bank_rules.yaml', list(state.CLASSIFY_DB.values()), key_field='bankaccountname')

    return rec


@router.delete("/classify-rules", status_code=204)
async def delete_classify_rule(
    bankaccountname: str = Query(""),
    transaction_type: str = Query(""),
    property: str = Query(""),
    group: str = Query("")
):
    bank = (bankaccountname or "").strip().lower()
    ttype = (transaction_type or "").strip().lower()
    prop = (property or "").strip().lower()
    grp = (group or "").strip().lower()
    # Delete all rules that match the triplet, regardless of pattern
    to_delete = [
        k for k, v in state.CLASSIFY_DB.items()
        if v.get("bankaccountname") == bank and v.get("transaction_type") == ttype and v.get("property") == prop and (not grp or v.get("group", "") == grp)
    ]
    if not to_delete:
        raise HTTPException(status_code=404, detail="Classify rule not found")
    for k in to_delete:
        del state.CLASSIFY_DB[k]
    # Persist to bank_rules.yaml
    if state.CLASSIFY_CSV_PATH:
        base_dir = state.CLASSIFY_CSV_PATH.parent
        dump_yaml_entities(base_dir / 'bank_rules.yaml', list(state.CLASSIFY_DB.values()), key_field='bankaccountname')
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
