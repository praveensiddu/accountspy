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

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CSV_PATH = None  # set on startup from ENTITIES_DIR
COMP_CSV_PATH = None  # set on startup from ENTITIES_DIR
BANK_CSV_PATH = None  # set on startup from ENTITIES_DIR
GROUPS_CSV_PATH = None  # set on startup from ENTITIES_DIR
OWNERS_CSV_PATH = None  # set on startup from ENTITIES_DIR
BANKS_YAML_PATH = None  # set on startup from ENTITIES_DIR
TAX_CSV_PATH = None  # set on startup from ENTITIES_DIR
TT_CSV_PATH = None  # set on startup from ENTITIES_DIR
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
    app.include_router(banks_router.router)
    app.include_router(tax_categories_router.router)
    app.include_router(transaction_types_router.router)
    app.include_router(properties_router.router)
    app.include_router(companies_router.router)
    app.include_router(bankaccounts_router.router)
    app.include_router(groups_router.router)
    app.include_router(owners_router.router)
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


def load_csv_into_memory(csv_path: Path) -> None:
    DB.clear()
    if not csv_path or not csv_path.exists():
        return
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
            # Header may have been '#property' which is normalized above
            prop_raw = (row.get("property") or "").strip()
            if not prop_raw:
                continue
            key = prop_raw.lower()
            row["property"] = key
            # Cast numeric fields
            try:
                row["cost"] = int(row.get("cost") or 0)
                row["landValue"] = int(row.get("landValue") or 0)
                row["renovation"] = int(row.get("renovation") or 0)
                row["loanClosingCOst"] = int(row.get("loanClosingCOst") or 0)
                row["ownerCount"] = int(row.get("ownerCount") or 0)
            except ValueError:
                continue
            # Normalize and validate propMgmgtComp against companies
            comp_raw = (row.get("propMgmgtComp") or "").strip().lower()
            if not comp_raw or not ALNUM_LOWER_RE.match(comp_raw):
                continue
            if comp_raw not in COMP_DB:
                continue
            row["propMgmgtComp"] = comp_raw
            DB[key] = row


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


def load_companies_csv_into_memory(companies_csv_path: Path) -> None:
    COMP_DB.clear()
    if not companies_csv_path or not companies_csv_path.exists():
        return
    with companies_csv_path.open(newline="", encoding="utf-8") as f:
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
            # Normalize header '#companyname' and values
            if not row.get("companyname"):
                continue
            key = row["companyname"].strip().lower()
            if not ALNUM_LOWER_RE.match(key):
                # Skip names that are not strictly lowercase alphanumeric
                continue
            try:
                row["rentPercentage"] = int(row.get("rentPercentage") or 0)
            except ValueError:
                continue
            row["companyname"] = key.lower()  # Lowercase companyname during CSV load
            COMP_DB[key] = row


def load_bankaccounts_csv_into_memory(bank_csv_path: Path) -> None:
    BA_DB.clear()
    if not bank_csv_path or not bank_csv_path.exists():
        return
    with bank_csv_path.open(newline="", encoding="utf-8") as f:
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
            if not row.get("bankaccountname"):
                continue
            key = row["bankaccountname"].strip().lower()
            # allow underscore in account names
            if not ALNUM_UNDERSCORE_LOWER_RE.match(key):
                continue
            bank = (row.get("bankname") or "").strip().lower()
            if not bank:
                continue
            BA_DB[key] = {"bankaccountname": key, "bankname": bank}


def _split_pipe_list(value: str) -> List[str]:
    if not value:
        return []
    return [x.strip().lower() for x in value.split("|") if x.strip()]


def load_groups_csv_into_memory(groups_csv_path: Path) -> None:
    GROUP_DB.clear()
    if not groups_csv_path or not groups_csv_path.exists():
        return
    with groups_csv_path.open(newline="", encoding="utf-8") as f:
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
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
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
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


def load_tax_categories_csv_into_memory(tax_csv_path: Path) -> None:
    TAX_DB.clear()
    if not tax_csv_path or not tax_csv_path.exists():
        return
    with tax_csv_path.open(newline="", encoding="utf-8") as f:
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
            # Accept 'category' or 'name' header (any casing)
            raw = _get_any(row, ["category", "name"]) or ""
            val = raw.strip().lower() if isinstance(raw, str) else ""
            if not isinstance(val, str) or not val:
                # Fallback: take the first non-empty cell value
                for v in (row or {}).values():
                    if isinstance(v, str) and v.strip():
                        val = v.strip().lower()
                        break
            if not val:
                continue
            if not ALNUM_UNDERSCORE_LOWER_RE.match(val):
                continue
            TAX_DB[val] = {"category": val}
    # Supplemental raw-line pass to include headerless first-line as a value and any missed rows
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
        reader = _dict_reader_ignoring_comments(f)
        for row in reader:
            row = _normalize_row_keys(row)
            # Accept 'transactiontype' or 'type' or 'name' (any casing)
            val = _get_any(row, ["transactiontype", "type", "name"]).strip().lower()
            if not isinstance(val, str) or not val:
                # Fallback: take the first non-empty cell value
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
    global CSV_PATH, COMP_CSV_PATH, BANK_CSV_PATH, GROUPS_CSV_PATH, OWNERS_CSV_PATH, TAX_CSV_PATH, TT_CSV_PATH, BANKS_YAML_PATH
    CSV_PATH = (entities_dir / "properties.csv") if entities_dir else None
    COMP_CSV_PATH = (entities_dir / "companies.csv") if entities_dir else None
    BANK_CSV_PATH = (entities_dir / "bankaccounts.csv") if entities_dir else None
    GROUPS_CSV_PATH = (entities_dir / "groups.csv") if entities_dir else None
    OWNERS_CSV_PATH = (entities_dir / "owners.csv") if entities_dir else None
    BANKS_YAML_PATH = (entities_dir / "banks.yaml") if entities_dir else None
    TAX_CSV_PATH = (entities_dir / "tax_category.csv") if entities_dir else None
    TT_CSV_PATH = (entities_dir / "transaction_types.csv") if entities_dir else None

    # Load CSVs
    load_companies_csv_into_memory(COMP_CSV_PATH)  # load companies first for validation
    logger.info(f"Loaded {len(COMP_DB)} company records from {COMP_CSV_PATH}")
    load_csv_into_memory(CSV_PATH)
    logger.info(f"Loaded {len(DB)} properties from {CSV_PATH}")
    load_bankaccounts_csv_into_memory(BANK_CSV_PATH)
    logger.info(f"Loaded {len(BA_DB)} bank accounts from {BANK_CSV_PATH}")
    load_groups_csv_into_memory(GROUPS_CSV_PATH)
    logger.info(f"Loaded {len(GROUP_DB)} groups from {GROUPS_CSV_PATH}")
    load_owners_csv_into_memory(OWNERS_CSV_PATH)
    logger.info(f"Loaded {len(OWNER_DB)} owners from {OWNERS_CSV_PATH}")
    load_tax_categories_csv_into_memory(TAX_CSV_PATH)
    logger.info(f"Loaded {len(TAX_DB)} tax categories from {TAX_CSV_PATH}")
    load_transaction_types_csv_into_memory(TT_CSV_PATH)
    logger.info(f"Loaded {len(TT_DB)} transaction types from {TT_CSV_PATH}")
    load_banks_yaml_into_memory(BANKS_YAML_PATH)
    logger.info(f"Loaded {len(BANKS_CFG_DB)} bank configs from {BANKS_YAML_PATH}")

    # Emit YAML snapshots sorted by primary key
    try:
        if COMP_CSV_PATH:
            _dump_yaml_entities(
                path=COMP_CSV_PATH.with_suffix('.yaml'),
                entities=list(COMP_DB.values()),
                key_field='companyname',
            )
        if CSV_PATH:
            _dump_yaml_entities(
                path=CSV_PATH.with_suffix('.yaml'),
                entities=list(DB.values()),
                key_field='property',
            )
        if BANK_CSV_PATH:
            _dump_yaml_entities(
                path=BANK_CSV_PATH.with_suffix('.yaml'),
                entities=list(BA_DB.values()),
                key_field='bankaccountname',
            )
        if GROUPS_CSV_PATH:
            _dump_yaml_entities(
                path=GROUPS_CSV_PATH.with_suffix('.yaml'),
                entities=list(GROUP_DB.values()),
                key_field='groupname',
            )
        if OWNERS_CSV_PATH:
            _dump_yaml_entities(
                path=OWNERS_CSV_PATH.with_suffix('.yaml'),
                entities=list(OWNER_DB.values()),
                key_field='name',
            )
        if TAX_CSV_PATH:
            _dump_yaml_entities(
                path=TAX_CSV_PATH.with_suffix('.yaml'),
                entities=list(TAX_DB.values()),
                key_field='category',
            )
        if TT_CSV_PATH:
            _dump_yaml_entities(
                path=TT_CSV_PATH.with_suffix('.yaml'),
                entities=list(TT_DB.values()),
                key_field='transactiontype',
            )
        if BANKS_YAML_PATH:
            # Dump sorted by name; keep keys order stable
            _dump_yaml_entities(
                path=BANKS_YAML_PATH,
                entities=list(BANKS_CFG_DB.values()),
                key_field='name',
            )
    except Exception as e:
        logger.error(f"Failed to write YAML snapshots: {e}")


# Properties moved to routers/properties.py


# Companies moved to routers/companies.py


# Serve static frontend
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
