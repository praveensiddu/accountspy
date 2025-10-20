from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import re
import csv
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import yaml

ALNUM_LOWER_RE = re.compile(r"^[a-z0-9]+$")
ALNUM_UNDERSCORE_LOWER_RE = re.compile(r"^[a-z0-9_]+$")

# In-memory databases
DB: Dict[str, Dict] = {}
COMP_DB: Dict[str, Dict] = {}
BA_DB: Dict[str, Dict] = {}
GROUP_DB: Dict[str, Dict] = {}
OWNER_DB: Dict[str, Dict] = {}
BANKS_CFG_DB: Dict[str, Dict] = {}
TAX_DB: Dict[str, Dict] = {}
TT_DB: Dict[str, Dict] = {}
CLASSIFY_DB: Dict[str, Dict] = {}
COMMON_RULES_DB: Dict[str, Dict] = {}
INHERIT_RULES_DB: Dict[str, Dict] = {}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = None  # set on startup from ENTITIES_DIR
COMP_CSV_PATH = None  # set on startup from ENTITIES_DIR
BANK_CSV_PATH = None  # set on startup from ENTITIES_DIR
GROUPS_CSV_PATH = None  # set on startup from ENTITIES_DIR
OWNERS_CSV_PATH = None  # set on startup from ENTITIES_DIR
BANKS_YAML_PATH = None  # set on startup from ENTITIES_DIR
TAX_CSV_PATH = None  # set on startup from ENTITIES_DIR
TT_CSV_PATH = None  # set on startup from ENTITIES_DIR
CLASSIFY_CSV_PATH = None  # set on startup from ENTITIES_DIR
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Companies list loaded from env
COMPANIES: List[str] = []

class Property(BaseModel):
    property: str = Field(..., description="Unique property identifier")
    cost: int
    landValue: int
    renovation: int
    loanClosingCOst: int
    ownerCount: int
    purchaseDate: str
    propMgmgtComp: str


class CompanyRecord(BaseModel):
    companyname: str = Field(..., description="Unique company name")
    rentPercentage: int

class BankAccountRecord(BaseModel):
    bankaccountname: str = Field(..., description="Unique bank account name")
    bankname: str

class GroupRecord(BaseModel):
    groupname: str = Field(..., description="Unique group name")
    propertylist: List[str]

class OwnerRecord(BaseModel):
    name: str = Field(..., description="Owner name")
    bankaccounts: List[str] = []
    properties: List[str] = []
    companies: List[str] = []

class TaxCategoryRecord(BaseModel):
    category: str = Field(..., description="Tax category name")

class TransactionTypeRecord(BaseModel):
    transactiontype: str = Field(..., description="Transaction type name")

app = FastAPI(title="Properties API", version="1.0.0")

logger = logging.getLogger("uvicorn.error")

# Allow local dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers (incremental modularization)
try:
    from .routers import banks as banks_router
    from .routers import tax_categories as tax_categories_router
    from .routers import transaction_types as transaction_types_router
    from .routers import properties as properties_router
    from .routers import companies as companies_router
    from .routers import bankaccounts as bankaccounts_router
    from .routers import groups as groups_router
    from .routers import owners as owners_router
    from .routers import classify_rules as classify_rules_router
    app.include_router(banks_router.router)
    app.include_router(tax_categories_router.router)
    app.include_router(transaction_types_router.router)
    app.include_router(properties_router.router)
    app.include_router(companies_router.router)
    app.include_router(bankaccounts_router.router)
    app.include_router(groups_router.router)
    app.include_router(owners_router.router)
    app.include_router(classify_rules_router.router)
except Exception:
    # In case of import issues during incremental refactor, continue with inline endpoints
    pass


def _dict_reader_ignoring_comments(f) -> csv.DictReader:
    """
    Returns a DictReader that preserves the first non-empty line as header
    (even if it starts with '#', e.g., '#property') and filters out subsequent
    empty or comment lines (starting with '#').
    """
    lines = f.readlines()
    # find header line (first non-empty)
    header_idx = -1
    for i, line in enumerate(lines):
        if line.strip():
            header_idx = i
            break
    if header_idx == -1:
        return csv.DictReader([])
    header = lines[header_idx]
    data_lines = [
        ln for ln in lines[header_idx + 1 :]
        if ln.strip() and not ln.lstrip().startswith('#')
    ]
    return csv.DictReader([header] + data_lines)


def _normalize_row_keys(row: Dict[str, str]) -> Dict[str, str]:
    # Strip leading '#' and surrounding whitespace from keys, keep original casing otherwise
    # This preserves headers like 'rentPercentage' while normalizing '#groupname' -> 'groupname'
    return { (k.strip().lstrip('#') if isinstance(k, str) else k): v for k, v in row.items() }


def _get_any(row: Dict[str, str], keys: List[str]) -> str:
    """Return the first matching value for any key in keys, trying exact and case-insensitive variants."""
    for k in keys:
        if k in row:
            return row.get(k) or ""
    # fallback: case-insensitive
    lower_map = { (str(k).lower() if isinstance(k, str) else k): k for k in row.keys() }
    for k in keys:
        lk = str(k).lower()
        if lk in lower_map:
            return row.get(lower_map[lk]) or ""
    return ""


def load_properties_yaml_into_memory(properties_yaml_path: Path) -> None:
    DB.clear()
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
                if comp_raw not in COMP_DB:
                    continue
                DB[prop] = {
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


# Banks endpoints moved to routers/banks.py


# Tax categories endpoints moved to routers/tax_categories.py


# Transaction types endpoints moved to routers/transaction_types.py

def _dump_yaml_entities(path: Path, entities: List[Dict], key_field: str) -> None:
    # Sort records by key_field and sort keys within each dict for determinism
    sorted_entities = sorted(entities, key=lambda x: x.get(key_field, ""))
    # Ensure any list fields are sorted for determinism
    normalized = []
    for ent in sorted_entities:
        ent_copy = {}
        for k, v in ent.items():
            if isinstance(v, list):
                ent_copy[k] = sorted(v)
            else:
                ent_copy[k] = v
        normalized.append(ent_copy)
    with path.open('w', encoding='utf-8') as yf:
        yaml.safe_dump(normalized, yf, sort_keys=True, allow_unicode=True)


# Bank accounts moved to routers/bankaccounts.py


# Groups moved to routers/groups.py


# Owners moved to routers/owners.py


def load_companies_yaml_into_memory(companies_yaml_path: Path) -> None:
    COMP_DB.clear()
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
                COMP_DB[raw] = { 'companyname': raw, 'rentPercentage': rp }
    except Exception as e:
        logger.error(f"Failed to load companies.yaml: {e}")


def load_bankaccounts_yaml_into_memory(yaml_path: Path) -> None:
    """Load bank accounts from bankaccounts.yaml into BA_DB.
    Expected list of objects with fields: bankaccountname, bankname, optional statement_location.
    """
    BA_DB.clear()
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
                BA_DB[key] = {
                    'bankaccountname': key,
                    'bankname': bank,
                    'statement_location': (item.get('statement_location') or '').strip(),
                }
    except Exception as e:
        logger.error(f"Failed to load bankaccounts.yaml: {e}")


def _split_pipe_list(value: str) -> List[str]:
    if not value:
        return []
    return [x.strip().lower() for x in value.split("|") if x.strip()]


def load_groups_yaml_into_memory(groups_yaml_path: Path) -> None:
    GROUP_DB.clear()
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
                GROUP_DB[key] = { 'groupname': key, 'propertylist': plist_norm }
    except Exception as e:
        logger.error(f"Failed to load groups.yaml: {e}")


def load_owners_yaml_into_memory(owners_yaml_path: Path) -> None:
    OWNER_DB.clear()
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
                OWNER_DB[key] = {
                    'name': key,
                    'bankaccounts': _norm_list(item.get('bankaccounts')),
                    'properties': _norm_list(item.get('properties')),
                    'companies': _norm_list(item.get('companies')),
                }
    except Exception as e:
        logger.error(f"Failed to load owners.yaml: {e}")


def load_banks_yaml_into_memory(banks_yaml_path: Path) -> None:
    """Load bank parsing configuration from banks.yaml. If missing, create with defaults."""
    BANKS_CFG_DB.clear()
    if not banks_yaml_path:
        return
    if not banks_yaml_path.exists():
        # Create default content as provided
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
    # Load YAML content
    try:
        with banks_yaml_path.open('r', encoding='utf-8') as yf:
            data = yaml.safe_load(yf) or []
            if not isinstance(data, list):
                data = []
            # Normalize names to lowercase and index by name
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
            # Save to in-memory indexed by name
            for cfg in normalized:
                BANKS_CFG_DB[cfg["name"]] = cfg
    except Exception as e:
        logger.error(f"Failed to load banks.yaml: {e}")


def load_tax_categories_yaml_into_memory(tax_yaml_path: Path) -> None:
    TAX_DB.clear()
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
                TAX_DB[raw] = { 'category': raw }
    except Exception as e:
        logger.error(f"Failed to load tax_category.yaml: {e}")


def load_transaction_types_yaml_into_memory(tt_yaml_path: Path) -> None:
    TT_DB.clear()
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
                TT_DB[raw] = { 'transactiontype': raw }
    except Exception as e:
        logger.error(f"Failed to load transaction_types.yaml: {e}")


def _normalize_str(val: Optional[str]) -> str:
    return (val or "").strip()


def load_classify_rules_csv_into_memory(csv_path: Path) -> None:
    CLASSIFY_DB.clear()
    COMMON_RULES_DB.clear()
    INHERIT_RULES_DB.clear()
    if not csv_path or not csv_path.exists():
        return
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
            # Accept variant headers
            bank = _normalize_str(_get_any(row, ["bankaccountname", "account", "bank_account", "bank"])) .lower()
            ttype = _normalize_str(_get_any(row, ["transaction_type", "transactiontype", "type"])) .lower()
            patt = _normalize_str(_get_any(row, ["pattern_match_logic", "pattern", "match", "rule"])) .lower()
            tax = _normalize_str(_get_any(row, ["tax_category", "category", "tax"])) .lower()
            prop = _normalize_str(_get_any(row, ["property", "prop"])) .lower()
            other = _normalize_str(_get_any(row, ["otherentity", "entity", "payee", "vendor"]))
            # Require minimum fields
            if not (bank and ttype and patt):
                continue
            # Build a composite key that includes pattern to avoid overwrites
            key = f"{bank}|{ttype}|{prop}|{patt}"
            CLASSIFY_DB[key] = {
                "bankaccountname": bank,
                "transaction_type": ttype,
                "pattern_match_logic": patt,
                "tax_category": tax,
                "property": prop,
                "otherentity": other,
            }


def load_common_rules_yaml_into_memory(path: Path) -> None:
    """Load manually curated common rules from YAML into COMMON_RULES_DB.
    Expected format: list of objects with fields transaction_type, pattern_match_logic.
    """
    COMMON_RULES_DB.clear()
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
                COMMON_RULES_DB[key] = {
                    'bankaccountname': 'common',
                    'transaction_type': ttype,
                    'pattern_match_logic': patt_norm,
                    'tax_category': '',
                    'property': '',
                    'otherentity': '',
                }
    except Exception as e:
        logger.error(f"Failed to load common_rules.yaml: {e}")


def load_bank_rules_yaml_into_memory(path: Path) -> None:
    """Load bank-specific classify rules from YAML into CLASSIFY_DB.
    Expected format: list of objects with fields bankaccountname, transaction_type, pattern_match_logic,
    tax_category, property, group, otherentity. Fields may be omitted; missing values default to ''.
    """
    CLASSIFY_DB.clear()
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
                CLASSIFY_DB[key] = {
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


def load_inherit_rules_yaml_into_memory(path: Path) -> None:
    """Load manually curated inherit rules from YAML into INHERIT_RULES_DB.
    Expected format: list of objects with fields bankaccountname, transaction_type, pattern_match_logic, tax_category, property, otherentity.
    """
    INHERIT_RULES_DB.clear()
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
                # Only require bank; others are optional in YAML
                if not bank:
                    continue
                key = f"{bank}|{ttype}|{prop}|{group}|{patt_norm}|{tax}|{other}"
                INHERIT_RULES_DB[key] = {
                    'bankaccountname': bank,
                    'transaction_type': ttype,
                    'pattern_match_logic': patt_norm,
                    'tax_category': tax,
                    'property': prop,
                    'group': group,
                    'otherentity': other,
                }
    except Exception as e:
        logger.error(f"Failed to load inherit_common_to_bank.yaml: {e}")


@app.on_event("startup")
async def startup_event():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
    # Load .env from project root
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)
    logger.info(f"ENV path: {env_path} exists={env_path.exists()}")
    # Resolve ENTITIES_DIR
    entities_dir_env = os.getenv("ENTITIES_DIR", "").strip()
    entities_dir = Path(entities_dir_env) if entities_dir_env else None
    if entities_dir:
        entities_dir = entities_dir.expanduser().resolve()
    logger.info(f"ENTITIES_DIR: {entities_dir} exists={entities_dir.exists() if entities_dir else False}")

    # Compute CSV paths from ENTITIES_DIR
    global CSV_PATH, COMP_CSV_PATH, BANK_CSV_PATH, GROUPS_CSV_PATH, OWNERS_CSV_PATH, TAX_CSV_PATH, TT_CSV_PATH, BANKS_YAML_PATH, CLASSIFY_CSV_PATH
    CSV_PATH = (entities_dir / "properties.csv") if entities_dir else None
    COMP_CSV_PATH = (entities_dir / "companies.csv") if entities_dir else None
    BANK_CSV_PATH = (entities_dir / "bankaccounts.csv") if entities_dir else None
    GROUPS_CSV_PATH = (entities_dir / "groups.csv") if entities_dir else None
    OWNERS_CSV_PATH = (entities_dir / "owners.csv") if entities_dir else None
    BANKS_YAML_PATH = (entities_dir / "banks.yaml") if entities_dir else None
    TAX_CSV_PATH = (entities_dir / "tax_category.csv") if entities_dir else None
    TT_CSV_PATH = (entities_dir / "transaction_types.csv") if entities_dir else None
    CLASSIFY_CSV_PATH = (entities_dir / "classify_rules.csv") if entities_dir else None

    # Load CSVs
    # Load companies and properties from YAML (not CSV)
    comp_yaml_path = COMP_CSV_PATH.with_suffix('.yaml') if COMP_CSV_PATH else None
    load_companies_yaml_into_memory(comp_yaml_path)
    logger.info(f"Loaded {len(COMP_DB)} company records from {comp_yaml_path}")
    prop_yaml_path = CSV_PATH.with_suffix('.yaml') if CSV_PATH else None
    load_properties_yaml_into_memory(prop_yaml_path)
    logger.info(f"Loaded {len(DB)} properties from {prop_yaml_path}")
    # Load bank accounts from YAML instead of CSV
    bank_yaml_path = BANK_CSV_PATH.with_suffix('.yaml') if BANK_CSV_PATH else None
    load_bankaccounts_yaml_into_memory(bank_yaml_path)
    logger.info(f"Loaded {len(BA_DB)} bank accounts from {bank_yaml_path}")
    grp_yaml_path = GROUPS_CSV_PATH.with_suffix('.yaml') if GROUPS_CSV_PATH else None
    load_groups_yaml_into_memory(grp_yaml_path)
    logger.info(f"Loaded {len(GROUP_DB)} groups from {grp_yaml_path}")
    owners_yaml_path = OWNERS_CSV_PATH.with_suffix('.yaml') if OWNERS_CSV_PATH else None
    load_owners_yaml_into_memory(owners_yaml_path)
    logger.info(f"Loaded {len(OWNER_DB)} owners from {owners_yaml_path}")
    tax_yaml_path = TAX_CSV_PATH.with_suffix('.yaml') if TAX_CSV_PATH else None
    load_tax_categories_yaml_into_memory(tax_yaml_path)
    logger.info(f"Loaded {len(TAX_DB)} tax categories from {tax_yaml_path}")
    tt_yaml_path = TT_CSV_PATH.with_suffix('.yaml') if TT_CSV_PATH else None
    load_transaction_types_yaml_into_memory(tt_yaml_path)
    logger.info(f"Loaded {len(TT_DB)} transaction types from {tt_yaml_path}")
    load_banks_yaml_into_memory(BANKS_YAML_PATH)
    logger.info(f"Loaded {len(BANKS_CFG_DB)} bank configs from {BANKS_YAML_PATH}")

    # Load manually curated common and inherit rules
    try:
        if CLASSIFY_CSV_PATH:
            base_dir = CLASSIFY_CSV_PATH.parent
            # Load primary bank rules from YAML (for BankRules tab)
            load_bank_rules_yaml_into_memory(base_dir / 'bank_rules.yaml')
            # Load common and inherit YAMLs
            load_common_rules_yaml_into_memory(base_dir / 'common_rules.yaml')
            load_inherit_rules_yaml_into_memory(base_dir / 'inherit_common_to_bank.yaml')
            logger.info(
                f"Loaded manual lists -> bank_rules={len(CLASSIFY_DB)}, common_rules={len(COMMON_RULES_DB)}, inherit_rules={len(INHERIT_RULES_DB)}"
            )
    except Exception as e:
        logger.error(f"Failed to load manual lists: {e}")

    # Emit YAML snapshots sorted by primary key
    try:
        # Do not dump companies.yaml or properties.yaml at startup; YAMLs are sources of truth now.
        # Do not dump bankaccounts.yaml at startup; it is the source of truth now.
        # Do not dump groups.yaml or owners.yaml at startup; YAMLs are sources of truth now.
        # Do not dump tax_category.yaml or transaction_types.yaml at startup; YAMLs are sources of truth now.
        if BANKS_YAML_PATH:
            # Dump sorted by name; keep keys order stable
            _dump_yaml_entities(
                path=BANKS_YAML_PATH,
                entities=list(BANKS_CFG_DB.values()),
                key_field='name',
            )
        # Write derived YAMLs (do not write classify_rules.yaml)
        if CLASSIFY_CSV_PATH:
            base_dir = CLASSIFY_CSV_PATH.parent
            _dump_yaml_entities(
                path=base_dir / 'bank_rules.yaml',
                entities=list(CLASSIFY_DB.values()),
                key_field='bankaccountname',
            )
            # Do not write inherit_common_to_bank.yaml; it is manually curated.
            # Do not write common_rules.yaml; it is manually curated.
    except Exception as e:
        logger.error(f"Failed to write YAML snapshots: {e}")


# Properties moved to routers/properties.py


# Companies moved to routers/companies.py


# Serve static frontend
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
