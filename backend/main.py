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
import sys
from dotenv import load_dotenv
import yaml
from datetime import datetime

# Ensure project root is on sys.path when running as a script (python backend/main.py)
_THIS_FILE = Path(__file__).resolve()
_PROJECT_ROOT = _THIS_FILE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Ensure a single module instance for state across imports
# When running `python backend/main.py`, this file is `__main__`.
# Routers import `backend.main`, which would otherwise be a second module copy with separate globals.
if __name__ == "__main__":
    sys.modules["backend.main"] = sys.modules[__name__]

from backend.bank_statement_parser import process_bank_statements_from_sources as process_bank_stmts
from backend import load_entities as loaders
from backend.classify import classify_all
import uvicorn

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

# Mandatory environment configuration
ACCOUNTS_DIR_PATH: Optional[Path] = None
CURRENT_YEAR: Optional[str] = None
PROCESSED_DIR_PATH: Optional[Path] = None
NORMALIZED_DIR_PATH: Optional[Path] = None
ADDENDUM_DIR_PATH: Optional[Path] = None

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
    from backend.routers import banks as banks_router
    from backend.routers import tax_categories as tax_categories_router
    from backend.routers import transaction_types as transaction_types_router
    from backend.routers import properties as properties_router
    from backend.routers import companies as companies_router
    from backend.routers import bankaccounts as bankaccounts_router
    from backend.routers import groups as groups_router
    from backend.routers import owners as owners_router
    from backend.routers import classify_rules as classify_rules_router
    from backend.routers import transactions as transactions_router
    from backend.routers import addendum as addendum_router
    app.include_router(banks_router.router)
    app.include_router(tax_categories_router.router)
    app.include_router(transaction_types_router.router)
    app.include_router(properties_router.router)
    app.include_router(companies_router.router)
    app.include_router(bankaccounts_router.router)
    app.include_router(groups_router.router)
    app.include_router(owners_router.router)
    app.include_router(classify_rules_router.router)
    app.include_router(transactions_router.router)
    app.include_router(addendum_router.router)
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


 


 


def _split_pipe_list(value: str) -> List[str]:
    if not value:
        return []
    return [x.strip().lower() for x in value.split("|") if x.strip()]


 


 


 


 

 


 


def _normalize_str(val: Optional[str]) -> str:
    return (val or "").strip()


 


 


 


 


def _init_fs_and_env() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)
    logger.info(f"ENV path: {env_path} exists={env_path.exists()}")
    return project_root


def _resolve_entities_dir() -> Optional[Path]:
    entities_dir_env = os.getenv("ENTITIES_DIR", "").strip()
    entities_dir = Path(entities_dir_env) if entities_dir_env else None
    if entities_dir:
        entities_dir = entities_dir.expanduser().resolve()
    logger.info(f"ENTITIES_DIR: {entities_dir} exists={entities_dir.exists() if entities_dir else False}")
    return entities_dir


def _read_mandatory_envs() -> None:
    global ACCOUNTS_DIR_PATH, CURRENT_YEAR
    accounts_dir_env = (os.getenv("ACCOUNTS_DIR", "") or "").strip()
    year_env = (os.getenv("CURRENT_YEAR", "") or "").strip()
    if not accounts_dir_env:
        logger.error("Missing mandatory environment variable: ACCOUNTS_DIR")
        raise RuntimeError("Missing mandatory environment variable: ACCOUNTS_DIR")
    if not year_env:
        logger.error("Missing mandatory environment variable: CURRENT_YEAR")
        raise RuntimeError("Missing mandatory environment variable: CURRENT_YEAR")
    try:
        ACCOUNTS_DIR_PATH = Path(accounts_dir_env).expanduser().resolve()
    except Exception:
        logger.error(f"Invalid ACCOUNTS_DIR path: {accounts_dir_env}")
        raise RuntimeError("Invalid ACCOUNTS_DIR path")
    if not ACCOUNTS_DIR_PATH.exists() or not ACCOUNTS_DIR_PATH.is_dir():
        logger.error(f"ACCOUNTS_DIR is not a directory: {ACCOUNTS_DIR_PATH}")
        raise RuntimeError(f"ACCOUNTS_DIR is not a directory: {ACCOUNTS_DIR_PATH}")
    CURRENT_YEAR = year_env
    logger.info(f"ACCOUNTS_DIR={ACCOUNTS_DIR_PATH}")
    logger.info(f"CURRENT_YEAR={CURRENT_YEAR}")


def _ensure_year_dirs() -> None:
    try:
        global PROCESSED_DIR_PATH, NORMALIZED_DIR_PATH, ADDENDUM_DIR_PATH
        PROCESSED_DIR_PATH = ACCOUNTS_DIR_PATH / CURRENT_YEAR / 'processed'
        PROCESSED_DIR_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured processed dir: {PROCESSED_DIR_PATH}")
        NORMALIZED_DIR_PATH = ACCOUNTS_DIR_PATH / CURRENT_YEAR / 'normalized'
        NORMALIZED_DIR_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured normalized dir: {NORMALIZED_DIR_PATH}")
        ADDENDUM_DIR_PATH = ACCOUNTS_DIR_PATH / CURRENT_YEAR / 'addendum'
        ADDENDUM_DIR_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured addendum dir: {ADDENDUM_DIR_PATH}")
    except Exception as e:
        logger.error(f"Failed to create processed directory: {e}")
        raise


def _compute_entity_paths(entities_dir: Optional[Path]) -> None:
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


def _load_entities() -> None:
    comp_yaml_path = COMP_CSV_PATH.with_suffix('.yaml') if COMP_CSV_PATH else None
    loaders.load_companies_yaml_into_memory(comp_yaml_path, COMP_DB, logger)
    logger.info(f"Loaded {len(COMP_DB)} company records from {comp_yaml_path}")
    prop_yaml_path = CSV_PATH.with_suffix('.yaml') if CSV_PATH else None
    loaders.load_properties_yaml_into_memory(prop_yaml_path, DB, COMP_DB, logger)
    logger.info(f"Loaded {len(DB)} properties from {prop_yaml_path}")
    bank_yaml_path = BANK_CSV_PATH.with_suffix('.yaml') if BANK_CSV_PATH else None
    loaders.load_bankaccounts_yaml_into_memory(bank_yaml_path, BA_DB, logger)
    logger.info(f"Loaded {len(BA_DB)} bank accounts from {bank_yaml_path}")
    grp_yaml_path = GROUPS_CSV_PATH.with_suffix('.yaml') if GROUPS_CSV_PATH else None
    loaders.load_groups_yaml_into_memory(grp_yaml_path, GROUP_DB, logger)
    logger.info(f"Loaded {len(GROUP_DB)} groups from {grp_yaml_path}")
    owners_yaml_path = OWNERS_CSV_PATH.with_suffix('.yaml') if OWNERS_CSV_PATH else None
    loaders.load_owners_yaml_into_memory(owners_yaml_path, OWNER_DB, logger)
    logger.info(f"Loaded {len(OWNER_DB)} owners from {owners_yaml_path}")
    tax_yaml_path = TAX_CSV_PATH.with_suffix('.yaml') if TAX_CSV_PATH else None
    loaders.load_tax_categories_yaml_into_memory(tax_yaml_path, TAX_DB, logger)
    logger.info(f"Loaded {len(TAX_DB)} tax categories from {tax_yaml_path}")
    tt_yaml_path = TT_CSV_PATH.with_suffix('.yaml') if TT_CSV_PATH else None
    loaders.load_transaction_types_yaml_into_memory(tt_yaml_path, TT_DB, logger)
    logger.info(f"Loaded {len(TT_DB)} transaction types from {tt_yaml_path}")
    loaders.load_banks_yaml_into_memory(BANKS_YAML_PATH, BANKS_CFG_DB, logger)
    logger.info(f"Loaded {len(BANKS_CFG_DB)} bank configs from {BANKS_YAML_PATH}")


def _load_manual_rules() -> None:
    if CLASSIFY_CSV_PATH:
        base_dir = CLASSIFY_CSV_PATH.parent
        # Dedupe per-bank YAML files to remove duplicate pattern_match_logic entries
        loaders.dedupe_bank_rules_dir(base_dir / 'bank_rules', logger)
        # Let exceptions propagate so startup fails (e.g., duplicate patterns)
        loaders.load_bank_rules_yaml_into_memory(base_dir / 'bank_rules.yaml', CLASSIFY_DB, logger)
        loaders.load_common_rules_yaml_into_memory(base_dir / 'common_rules.yaml', COMMON_RULES_DB, logger)
        loaders.load_inherit_rules_yaml_into_memory(base_dir / 'inherit_common_to_bank.yaml', INHERIT_RULES_DB, logger)
        logger.info(
            f"Loaded manual lists -> bank_rules={len(CLASSIFY_DB)}, common_rules={len(COMMON_RULES_DB)}, inherit_rules={len(INHERIT_RULES_DB)}"
        )


def _emit_yaml_snapshots() -> None:
    try:
        if BANKS_YAML_PATH:
            _dump_yaml_entities(
                path=BANKS_YAML_PATH,
                entities=list(BANKS_CFG_DB.values()),
                key_field='name',
            )
        if CLASSIFY_CSV_PATH:
            base_dir = CLASSIFY_CSV_PATH.parent
            _dump_yaml_entities(
                path=base_dir / 'bank_rules.yaml',
                entities=list(CLASSIFY_DB.values()),
                key_field='bankaccountname',
            )
    except Exception as e:
        logger.error(f"Failed to write YAML snapshots: {e}")


def _process_statements() -> None:
    try:
        process_bank_stmts(BA_DB, BANKS_CFG_DB, CURRENT_YEAR, NORMALIZED_DIR_PATH, logger)
    except Exception as e:
        logger.error(f"Failed processing bank statements from sources: {e}")


@app.on_event("startup")
async def startup_event():
    _init_fs_and_env()
    entities_dir = _resolve_entities_dir()
    _read_mandatory_envs()
    _ensure_year_dirs()
    _compute_entity_paths(entities_dir)
    _load_entities()
    _load_manual_rules()
    _emit_yaml_snapshots()
    _process_statements()
    # Classify all bank accounts based on normalized files and bank rules
    try:
        classify_all()
    except Exception as e:
        logger.error(f"Failed to classify on startup: {e}")


# Properties moved to routers/properties.py


# Companies moved to routers/companies.py


# Serve static frontend
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)

