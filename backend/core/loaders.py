import csv
import yaml
from pathlib import Path
from typing import Dict, List
import logging

from .db import (
    DB, COMP_DB, BA_DB, GROUP_DB, OWNER_DB, BANKS_CFG_DB, TAX_DB, TT_DB,
    ALNUM_LOWER_RE, ALNUM_UNDERSCORE_LOWER_RE,
)
from .utils import (
    dict_reader_ignoring_comments,
    normalize_row_keys,
    get_any,
    dump_yaml_entities,
)

logger = logging.getLogger("uvicorn.error")


def _split_pipe_list(value: str) -> List[str]:
    if not value:
        return []
    return [x.strip().lower() for x in value.split("|") if x.strip()]


def load_companies_csv_into_memory(companies_csv_path: Path) -> None:
    COMP_DB.clear()
    if not companies_csv_path or not companies_csv_path.exists():
        return
    with companies_csv_path.open(newline="", encoding="utf-8") as f:
        reader = dict_reader_ignoring_comments(f)
        for row in reader:
            row = normalize_row_keys(row)
            if not row.get("companyname"):
                continue
            key = row["companyname"].strip().lower()
            if not ALNUM_LOWER_RE.match(key):
                continue
            try:
                row["rentPercentage"] = int(row.get("rentPercentage") or 0)
            except ValueError:
                continue
            row["companyname"] = key
            COMP_DB[key] = row


def load_csv_into_memory(csv_path: Path) -> None:
    DB.clear()
    if not csv_path or not csv_path.exists():
        return
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = dict_reader_ignoring_comments(f)
        for row in reader:
            row = normalize_row_keys(row)
            prop_raw = (row.get("property") or "").strip()
            if not prop_raw:
                continue
            key = prop_raw.lower()
            row["property"] = key
            try:
                row["cost"] = int(row.get("cost") or 0)
                row["landValue"] = int(row.get("landValue") or 0)
                row["renovation"] = int(row.get("renovation") or 0)
                row["loanClosingCost"] = int(row.get("loanClosingCost") or 0)
                row["ownerCount"] = int(row.get("ownerCount") or 0)
            except ValueError:
                continue
            comp_raw = (row.get("propMgmtComp") or "").strip().lower()
            if not comp_raw or not ALNUM_LOWER_RE.match(comp_raw):
                continue
            if comp_raw not in COMP_DB:
                continue
            row["propMgmtComp"] = comp_raw
            DB[key] = row


def load_bankaccounts_csv_into_memory(bank_csv_path: Path) -> None:
    BA_DB.clear()
    if not bank_csv_path or not bank_csv_path.exists():
        return
    with bank_csv_path.open(newline="", encoding="utf-8") as f:
        reader = dict_reader_ignoring_comments(f)
        for row in reader:
            row = normalize_row_keys(row)
            if not row.get("bankaccountname"):
                continue
            key = row["bankaccountname"].strip().lower()
            if not ALNUM_UNDERSCORE_LOWER_RE.match(key):
                continue
            bank = (row.get("bankname") or "").strip().lower()
            if not bank:
                continue
            BA_DB[key] = {"bankaccountname": key, "bankname": bank}


def load_groups_csv_into_memory(groups_csv_path: Path) -> None:
    GROUP_DB.clear()
    if not groups_csv_path or not groups_csv_path.exists():
        return
    with groups_csv_path.open(newline="", encoding="utf-8") as f:
        reader = dict_reader_ignoring_comments(f)
        for row in reader:
            row = normalize_row_keys(row)
            if not row.get("groupname"):
                continue
            key = row["groupname"].strip().lower()
            if not ALNUM_UNDERSCORE_LOWER_RE.match(key):
                continue
            plist = _split_pipe_list(row.get("propertylist") or "")
            plist = sorted(set(plist))
            GROUP_DB[key] = {"groupname": key, "propertylist": plist}


def load_owners_csv_into_memory(owners_csv_path: Path) -> None:
    OWNER_DB.clear()
    if not owners_csv_path or not owners_csv_path.exists():
        return
    with owners_csv_path.open(newline="", encoding="utf-8") as f:
        reader = dict_reader_ignoring_comments(f)
        for row in reader:
            row = normalize_row_keys(row)
            if not row.get("name"):
                continue
            key = row["name"].strip().lower()
            if not ALNUM_UNDERSCORE_LOWER_RE.match(key):
                continue
            bankaccounts = sorted(set(_split_pipe_list(row.get("bankaccounts pipe separated") or "")))
            properties = sorted(set(_split_pipe_list(row.get("properties pipe separated") or "")))
            companies = sorted(set(_split_pipe_list(row.get("companies pipe separated") or "")))
            OWNER_DB[key] = {
                "name": key,
                "bankaccounts": bankaccounts,
                "properties": properties,
                "companies": companies,
            }


def load_banks_yaml_into_memory(banks_yaml_path: Path) -> None:
    BANKS_CFG_DB.clear()
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
                BANKS_CFG_DB[cfg["name"]] = cfg
    except Exception as e:
        logger.error(f"Failed to load banks.yaml: {e}")


def load_tax_categories_csv_into_memory(tax_csv_path: Path) -> None:
    TAX_DB.clear()
    if not tax_csv_path or not tax_csv_path.exists():
        return
    with tax_csv_path.open(newline="", encoding="utf-8") as f:
        reader = dict_reader_ignoring_comments(f)
        for row in reader:
            row = normalize_row_keys(row)
            raw = get_any(row, ["category", "name"]) or ""
            val = raw.strip().lower() if isinstance(raw, str) else ""
            if not isinstance(val, str) or not val:
                for v in (row or {}).values():
                    if isinstance(v, str) and v.strip():
                        val = v.strip().lower()
                        break
            if not val:
                continue
            if not ALNUM_UNDERSCORE_LOWER_RE.match(val):
                continue
            TAX_DB[val] = {"category": val}
    try:
        existing = set(TAX_DB.keys())
        with tax_csv_path.open('r', encoding='utf-8') as rf:
            for ln in rf:
                s = ln.strip()
                if not s or s.startswith('#'):
                    continue
                first = s.split(',')[0].strip().lower()
                if not first or first in existing or not ALNUM_UNDERSCORE_LOWER_RE.match(first):
                    continue
                TAX_DB[first] = {"category": first}
                existing.add(first)
    except Exception as e:
        logger.error(f"Tax CSV raw-line supplement failed: {e}")


def load_transaction_types_csv_into_memory(tt_csv_path: Path) -> None:
    TT_DB.clear()
    if not tt_csv_path or not tt_csv_path.exists():
        return
    with tt_csv_path.open(newline="", encoding="utf-8") as f:
        reader = dict_reader_ignoring_comments(f)
        for row in reader:
            row = normalize_row_keys(row)
            val = get_any(row, ["transactiontype", "type", "name"]).strip().lower()
            if not isinstance(val, str) or not val:
                for v in (row or {}).values():
                    if isinstance(v, str) and v.strip():
                        val = v.strip().lower()
                        break
            if not val:
                continue
            if not ALNUM_UNDERSCORE_LOWER_RE.match(val):
                continue
            TT_DB[val] = {"transactiontype": val}
    try:
        existing_tt = set(TT_DB.keys())
        with tt_csv_path.open('r', encoding='utf-8') as rf:
            for ln in rf:
                s = ln.strip()
                if not s or s.startswith('#'):
                    continue
                first = s.split(',')[0].strip().lower()
                if not first or first in existing_tt or not ALNUM_UNDERSCORE_LOWER_RE.match(first):
                    continue
                TT_DB[first] = {"transactiontype": first}
                existing_tt.add(first)
    except Exception as e:
        logger.error(f"Transaction types CSV raw-line supplement failed: {e}")
