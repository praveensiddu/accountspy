from __future__ import annotations
from typing import Dict, List, Optional, Any, IO
from pathlib import Path
import csv
import yaml
import re

ALNUM_LOWER_RE = re.compile(r"^[a-z0-9]+$")
ALNUM_UNDERSCORE_LOWER_RE = re.compile(r"^[a-z0-9_]+$")


def _dict_reader_ignoring_comments(f: IO[str]) -> csv.DictReader:
    lines = f.readlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if line.strip():
            header_idx = i
            break
    if header_idx == -1:
        return csv.DictReader([])
    header = lines[header_idx]
    data_lines = [ln for ln in lines[header_idx + 1 :] if ln.strip() and not ln.lstrip().startswith('#')]
    return csv.DictReader([header] + data_lines)


def _normalize_row_keys(row: Dict[str, str]) -> Dict[str, str]:
    return {(k.strip().lstrip('#') if isinstance(k, str) else k): v for k, v in row.items()}


def _get_any(row: Dict[str, str], keys: List[str]) -> str:
    for k in keys:
        if k in row:
            return row.get(k) or ""
    lower_map = {(str(k).lower() if isinstance(k, str) else k): k for k in row.keys()}
    for k in keys:
        lk = str(k).lower()
        if lk in lower_map:
            return row.get(lower_map[lk]) or ""
    return ""


def _split_pipe_list(value: str) -> List[str]:
    if not value:
        return []
    return [x.strip().lower() for x in value.split("|") if x.strip()]


def _normalize_str(val: Optional[str]) -> str:
    return (val or "").strip()


# Loaders

def load_properties_yaml_into_memory(properties_yaml_path: Path, db: Dict[str, Dict], comp_db: Dict[str, Dict], logger) -> None:
    db.clear()
    if not properties_yaml_path or not properties_yaml_path.exists():
        return
    try:
        with properties_yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                prop = (item.get('property') or '').strip().lower()
                if not prop:
                    continue
                try:
                    cost = int(item.get('cost') or 0)
                    land_value = int(item.get('landValue') or 0)
                    renov = int(item.get('renovation') or 0)
                    lcc = int(item.get('loanClosingCOst') or 0)
                    owners = int(item.get('ownerCount') or 0)
                except Exception:
                    continue
                comp_raw = (item.get('propMgmgtComp') or '').strip().lower()
                if not comp_raw or not ALNUM_LOWER_RE.match(comp_raw):
                    continue
                if comp_raw not in comp_db:
                    continue
                db[prop] = {
                    'property': prop,
                    'cost': cost,
                    'landValue': land_value,
                    'renovation': renov,
                    'loanClosingCOst': lcc,
                    'ownerCount': owners,
                    'purchaseDate': (item.get('purchaseDate') or '').strip(),
                    'propMgmgtComp': comp_raw,
                }
    except Exception as e:
        logger.error(f"Failed to load properties.yaml: {e}")


def load_companies_yaml_into_memory(companies_yaml_path: Path, comp_db: Dict[str, Dict], logger) -> None:
    comp_db.clear()
    if not companies_yaml_path or not companies_yaml_path.exists():
        return
    try:
        with companies_yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                raw = (item.get('companyname') or '').strip().lower()
                if not raw or not ALNUM_LOWER_RE.match(raw):
                    continue
                try:
                    rp = int(item.get('rentPercentage') or 0)
                except Exception:
                    rp = 0
                comp_db[raw] = { 'companyname': raw, 'rentPercentage': rp }
    except Exception as e:
        logger.error(f"Failed to load companies.yaml: {e}")


def load_bankaccounts_yaml_into_memory(yaml_path: Path, ba_db: Dict[str, Dict], logger) -> None:
    ba_db.clear()
    if not yaml_path or not yaml_path.exists():
        return
    try:
        with yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                key = (item.get('bankaccountname') or '').strip().lower()
                if not key or not ALNUM_UNDERSCORE_LOWER_RE.match(key):
                    continue
                bank = (item.get('bankname') or '').strip().lower()
                if not bank:
                    continue
                ba_db[key] = {
                    'bankaccountname': key,
                    'bankname': bank,
                    'statement_location': (item.get('statement_location') or '').strip(),
                    'abbreviation': (item.get('abbreviation') or '').strip(),
                }
    except Exception as e:
        logger.error(f"Failed to load bankaccounts.yaml: {e}")


def load_groups_yaml_into_memory(groups_yaml_path: Path, group_db: Dict[str, Dict], logger) -> None:
    group_db.clear()
    if not groups_yaml_path or not groups_yaml_path.exists():
        return
    try:
        with groups_yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                key = (item.get('groupname') or '').strip().lower()
                if not key or not ALNUM_UNDERSCORE_LOWER_RE.match(key):
                    continue
                plist = item.get('propertylist') or []
                try:
                    plist_norm = sorted(set([(p or '').strip().lower() for p in plist if (p or '').strip()]))
                except Exception:
                    plist_norm = []
                group_db[key] = { 'groupname': key, 'propertylist': plist_norm }
    except Exception as e:
        logger.error(f"Failed to load groups.yaml: {e}")


def load_owners_yaml_into_memory(owners_yaml_path: Path, owner_db: Dict[str, Dict], logger) -> None:
    owner_db.clear()
    if not owners_yaml_path or not owners_yaml_path.exists():
        return
    try:
        with owners_yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                key = (item.get('name') or '').strip().lower()
                if not key or not ALNUM_UNDERSCORE_LOWER_RE.match(key):
                    continue
                def _norm_list(val):
                    try:
                        return sorted(set([(v or '').strip().lower() for v in (val or []) if (v or '').strip()]))
                    except Exception:
                        return []
                owner_db[key] = {
                    'name': key,
                    'bankaccounts': _norm_list(item.get('bankaccounts')),
                    'properties': _norm_list(item.get('properties')),
                    'companies': _norm_list(item.get('companies')),
                    'export_dir': (item.get('export_dir') or '').strip(),
                }
    except Exception as e:
        logger.error(f"Failed to load owners.yaml: {e}")


def load_banks_yaml_into_memory(banks_yaml_path: Path, banks_cfg_db: Dict[str, Dict], logger) -> None:
    banks_cfg_db.clear()
    if not banks_yaml_path:
        return
    if not banks_yaml_path.exists():
        default_cfg = [
            {"name": "amex", "ignore_lines_startswith": ["Transaction Type"], "date_format": "M/d/yyyy", "columns": [{"date": 1, "description": 4, "debit": 3}]},
            {"name": "bbt", "ignore_lines_startswith": ["Transaction Type"], "date_format": "M/d/yyyy", "columns": [{"date": 1, "description": 4, "debit": 5, "checkno": 3}]},
            {"name": "boa", "ignore_lines_contains": ["Ending balance"], "ignore_lines_startswith": ["Description", "Beginning balance", "Total credits", "Total debits", "Date"], "date_format": "M/d/yyyy", "delim": "|", "columns": [{"date": 1, "description": 2, "debit": 3, "checkno": 3}]},
            {"name": "citicard", "ignore_lines_startswith": ["Status"], "date_format": "M/d/yyyy", "columns": [{"date": 2, "description": 3, "debit": 4, "credit": 5}]},
            {"name": "dcu", "ignore_lines_contains": ["date range", "account number", "Account Name", "DATE"], "ignore_lines_startswith": ["Transaction Number"], "date_format": "M/d/yyyy", "columns": [{"date": 1, "description": 3, "memo": 6, "debit": 4}]},
            {"name": "dcuvisa", "ignore_lines_contains": ["date range", "account number", "Account Name", "DATE"], "ignore_lines_startswith": ["Transaction Number"], "date_format": "M/d/yyyy", "columns": [{"date": 2, "description": 3, "memo": 4, "debit": 5, "credit": 6, "checkno": 8, "fees": 9}]},
            {"name": "wellsfargo", "ignore_lines_contains": ["date range", "account number", "Account Name", "DATE"], "ignore_lines_startswith": ["Transaction Number"], "date_format": "M/d/yyyy", "columns": [{"date": 1, "description": 5, "debit": 2, "checkno": 4}]},
        ]
        banks_yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with banks_yaml_path.open('w', encoding='utf-8') as yf:
            yaml.safe_dump(default_cfg, yf, sort_keys=False, allow_unicode=True)
    try:
        with banks_yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                data = []
            normalized = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                name = (item.get("name") or "").strip().lower()
                if not name:
                    continue
                cfg = dict(item)
                cfg["name"] = name
                normalized.append(cfg)
            for cfg in normalized:
                banks_cfg_db[cfg["name"]] = cfg
    except Exception as e:
        logger.error(f"Failed to load banks.yaml: {e}")


def load_tax_categories_yaml_into_memory(tax_yaml_path: Path, tax_db: Dict[str, Dict], logger) -> None:
    tax_db.clear()
    if not tax_yaml_path or not tax_yaml_path.exists():
        return
    try:
        with tax_yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                raw = (item.get('category') or item.get('name') or '').strip().lower()
                if not raw or not ALNUM_UNDERSCORE_LOWER_RE.match(raw):
                    continue
                tax_db[raw] = { 'category': raw }
    except Exception as e:
        logger.error(f"Failed to load tax_category.yaml: {e}")


def load_transaction_types_yaml_into_memory(tt_yaml_path: Path, tt_db: Dict[str, Dict], logger) -> None:
    tt_db.clear()
    if not tt_yaml_path or not tt_yaml_path.exists():
        return
    try:
        with tt_yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                raw = (item.get('transactiontype') or item.get('type') or item.get('name') or '').strip().lower()
                if not raw or not ALNUM_UNDERSCORE_LOWER_RE.match(raw):
                    continue
                tt_db[raw] = { 'transactiontype': raw }
    except Exception as e:
        logger.error(f"Failed to load transaction_types.yaml: {e}")


def load_classify_rules_csv_into_memory(csv_path: Path, classify_db: Dict[str, Dict], common_rules_db: Dict[str, Dict], inherit_rules_db: Dict[str, Dict], logger) -> None:
    classify_db.clear()
    common_rules_db.clear()
    inherit_rules_db.clear()
    if not csv_path or not csv_path.exists():
        return
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
            bank = _normalize_str(_get_any(row, ["bankaccountname", "account", "bank_account", "bank"])) .lower()
            ttype = _normalize_str(_get_any(row, ["transaction_type", "transactiontype", "type"])) .lower()
            patt = _normalize_str(_get_any(row, ["pattern_match_logic", "pattern", "match", "rule"])) .lower()
            tax = _normalize_str(_get_any(row, ["tax_category", "category", "tax"])) .lower()
            prop = _normalize_str(_get_any(row, ["property", "prop"])) .lower()
            other = _normalize_str(_get_any(row, ["otherentity", "entity", "payee", "vendor"]))
            if not (bank and ttype and patt):
                continue
            key = f"{bank}|{ttype}|{prop}|{patt}"
            classify_db[key] = {
                "bankaccountname": bank,
                "transaction_type": ttype,
                "pattern_match_logic": patt,
                "tax_category": tax,
                "property": prop,
                "otherentity": other,
            }


def load_common_rules_yaml_into_memory(path: Path, common_rules_db: Dict[str, Dict], logger) -> None:
    common_rules_db.clear()
    if not path or not path.exists():
        return
    try:
        with path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                ttype = (item.get('transaction_type') or '').strip().lower()
                patt = (item.get('pattern_match_logic') or '').strip()
                patt_norm = ' '.join(patt.split()).lower()
                if not (ttype and patt_norm):
                    continue
                key = f"common|{ttype}|{patt_norm}"
                common_rules_db[key] = {
                    'bankaccountname': 'common',
                    'transaction_type': ttype,
                    'pattern_match_logic': patt_norm,
                    'tax_category': '',
                    'property': '',
                    'otherentity': '',
                }
    except Exception as e:
        logger.error(f"Failed to load common_rules.yaml: {e}")


def load_bank_rules_yaml_into_memory(path: Path, classify_db: Dict[str, Dict], logger) -> None:
    classify_db.clear()
    if not path or not path.exists():
        return
    try:
        with path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            # Validate uniqueness of pattern_match_logic per bank
            seen_per_bank: Dict[str, set] = {}
            for item in data:
                if not isinstance(item, dict):
                    continue
                bank = (item.get('bankaccountname') or '').strip().lower()
                ttype = (item.get('transaction_type') or '').strip().lower()
                patt = (item.get('pattern_match_logic') or '').strip()
                patt_norm = ' '.join(patt.split()).lower() if patt else ''
                tax = (item.get('tax_category') or '').strip().lower()
                prop = (item.get('property') or '').strip().lower()
                group = (item.get('group') or '').strip().lower()
                other = (item.get('otherentity') or '').strip()
                if not bank:
                    continue
                # Uniqueness check: pattern must be unique within the same bank file
                if bank not in seen_per_bank:
                    seen_per_bank[bank] = set()
                if patt_norm in seen_per_bank[bank]:
                    msg = f"Duplicate pattern_match_logic detected for bank '{bank}': '{patt_norm}'"
                    logger.error(msg)
                    raise RuntimeError(msg)
                seen_per_bank[bank].add(patt_norm)
                key = f"{bank}|{ttype}|{prop}|{group}|{patt_norm}"
                classify_db[key] = {
                    'bankaccountname': bank,
                    'transaction_type': ttype,
                    'pattern_match_logic': patt_norm,
                    'tax_category': tax,
                    'property': prop,
                    'group': group,
                    'otherentity': other,
                }
    except Exception as e:
        logger.error(f"Failed to load bank_rules.yaml: {e}")
        raise


def load_inherit_rules_yaml_into_memory(path: Path, inherit_rules_db: Dict[str, Dict], logger) -> None:
    inherit_rules_db.clear()
    if not path or not path.exists():
        return
    try:
        with path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                bank = (item.get('bankaccountname') or '').strip().lower()
                tax = (item.get('tax_category') or '').strip().lower()
                prop = (item.get('property') or '').strip().lower()
                group = (item.get('group') or '').strip().lower()
                other = (item.get('otherentity') or '').strip()
                if not bank:
                    continue
                key = f"{bank}|{prop}|{group}|{tax}|{other}"
                inherit_rules_db[key] = {
                    'bankaccountname': bank,
                    'tax_category': tax,
                    'property': prop,
                    'group': group,
                    'otherentity': other,
                }
    except Exception as e:
        logger.error(f"Failed to load inherit_common_to_bank.yaml: {e}")

def validate_bank_rules_yaml(path: Path, logger) -> None:
    if not path or not path.exists():
        return
    try:
        with path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            seen_patterns: set = set()
            for item in data:
                if not isinstance(item, dict):
                    continue
                patt = (item.get('pattern_match_logic') or '').strip()
                patt_norm = ' '.join(patt.split()).lower() if patt else ''
                if patt_norm in seen_patterns:
                    msg = f"Duplicate pattern_match_logic detected: '{patt_norm}'"
                    logger.error(msg)
                    raise RuntimeError(msg)
                seen_patterns.add(patt_norm)
    except Exception as e:
        logger.error(f"Failed to validate bank_rules.yaml: {e}")

def dedupe_bank_rules_dir(rules_dir: Path, logger) -> None:
    """For each YAML in rules_dir, remove duplicate pattern_match_logic entries.
    Keep the entry with the smallest valid order; then renumber 1..n and save back.
    """
    if not rules_dir or not rules_dir.exists() or not rules_dir.is_dir():
        return
    for p in rules_dir.glob('*.yaml'):
        try:
            with p.open('r', encoding='utf-8') as yf:
                data = yaml.safe_load(yf) or []
                if not isinstance(data, list):
                    continue
            # Build map patt_norm -> best item (smallest order)
            best_by_pattern: Dict[str, dict] = {}
            for item in data:
                if not isinstance(item, dict):
                    continue
                patt = (item.get('pattern_match_logic') or '').strip()
                patt_norm = ' '.join(patt.split()).lower() if patt else ''
                try:
                    o = int(item.get('order') or 0)
                except Exception:
                    o = 0
                cur = best_by_pattern.get(patt_norm)
                if cur is None:
                    best_by_pattern[patt_norm] = dict(item)
                else:
                    try:
                        cur_o = int(cur.get('order') or 0)
                    except Exception:
                        cur_o = 0
                    if o != 0 and (cur_o == 0 or o < cur_o):
                        best_by_pattern[patt_norm] = dict(item)
            # Prepare list and renumber by ascending order
            merged = list(best_by_pattern.values())
            try:
                merged.sort(key=lambda x: int(x.get('order') or 0))
            except Exception:
                pass
            for idx, it in enumerate(merged, start=1):
                it['order'] = idx
            with p.open('w', encoding='utf-8') as yf:
                yaml.safe_dump(merged, yf, sort_keys=True, allow_unicode=True)
            # Log action if duplicates were removed
            if len(merged) < len(data):
                logger.error(f"Removed {len(data) - len(merged)} duplicate pattern_match_logic entries in {p.name}")
        except Exception as e:
            logger.error(f"Failed to dedupe {p}: {e}")

def load_bank_rules_yaml_into_memory(path: Path, classify_db: Dict[str, Dict], logger) -> None:
    validate_bank_rules_yaml(path, logger)
    classify_db.clear()
    if not path or not path.exists():
        return
    try:
        with path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                return
            for item in data:
                if not isinstance(item, dict):
                    continue
                bank = (item.get('bankaccountname') or '').strip().lower()
                ttype = (item.get('transaction_type') or '').strip().lower()
                patt = (item.get('pattern_match_logic') or '').strip()
                patt_norm = ' '.join(patt.split()).lower() if patt else ''
                tax = (item.get('tax_category') or '').strip().lower()
                prop = (item.get('property') or '').strip().lower()
                group = (item.get('group') or '').strip().lower()
                other = (item.get('otherentity') or '').strip()
                if not bank:
                    continue
                key = f"{bank}|{ttype}|{prop}|{group}|{patt_norm}"
                classify_db[key] = {
                    'bankaccountname': bank,
                    'transaction_type': ttype,
                    'pattern_match_logic': patt_norm,
                    'tax_category': tax,
                    'property': prop,
                    'group': group,
                    'otherentity': other,
                }
    except Exception as e:
        logger.error(f"Failed to load bank_rules.yaml: {e}")
        raise
