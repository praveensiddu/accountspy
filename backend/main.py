from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
from backend.property_sum import prepare_and_save_property_sum
from backend.company_sum import prepare_and_save_company_sum
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
PROPERTIES_YAML_PATH = None  # set on startup 
COMP_YAML_PATH = None  # set on startup 
BANK_YAML_PATH = None  # set on startup  (bankaccounts)
GROUPS_YAML_PATH = None  # set on startup 
OWNERS_YAML_PATH = None  # set on startup 
BANKS_YAML_PATH = None  # set on startup  (bank configs)
TAX_YAML_PATH = None  # set on startup 
TT_YAML_PATH = None  # set on startup 
CLASSIFY_YAML_PATH = None  # set on startup  (for locating rules dir)

# Back-compat aliases for legacy code expecting *_CSV_PATH
CSV_PATH = None
COMP_CSV_PATH = None
BANK_CSV_PATH = None
GROUPS_CSV_PATH = None
OWNERS_CSV_PATH = None
TAX_CSV_PATH = None
TT_CSV_PATH = None
CLASSIFY_CSV_PATH = None
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

app = FastAPI(title="Properties API", version="1.0.0", debug=True)

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
    from backend.routers import rentalsummary as rentalsummary_router
    from backend.routers import companysummary as companysummary_router
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
    app.include_router(rentalsummary_router.router)
    app.include_router(companysummary_router.router)
except Exception as e:
    logger.exception("Router include failed", exc_info=e)


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
    global ACCOUNTS_DIR_PATH, CURRENT_YEAR
    if not ACCOUNTS_DIR_PATH or not CURRENT_YEAR:
        logger.info("entities_dir: unresolved because ACCOUNTS_DIR_PATH or CURRENT_YEAR missing")
        return None
    entities_dir: Path = (ACCOUNTS_DIR_PATH / CURRENT_YEAR / 'entities').expanduser().resolve()
    logger.info(f"entities_dir: {entities_dir} exists={entities_dir.exists() if entities_dir else False}")
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
        # Do not create or use a global addendum directory; per-bank statement_location paths are used instead
        ADDENDUM_DIR_PATH = None
    except Exception as e:
        logger.error(f"Failed to create processed directory: {e}")
        raise


def _compute_entity_paths(entities_dir: Optional[Path]) -> None:
    global PROPERTIES_YAML_PATH, COMP_YAML_PATH, BANK_YAML_PATH, GROUPS_YAML_PATH, OWNERS_YAML_PATH, BANKS_YAML_PATH, TAX_YAML_PATH, TT_YAML_PATH, CLASSIFY_YAML_PATH
    global CSV_PATH, COMP_CSV_PATH, BANK_CSV_PATH, GROUPS_CSV_PATH, OWNERS_CSV_PATH, TAX_CSV_PATH, TT_CSV_PATH, CLASSIFY_CSV_PATH
    if entities_dir:
        PROPERTIES_YAML_PATH = entities_dir / "properties.yaml"
        COMP_YAML_PATH = entities_dir / "companies.yaml"
        BANK_YAML_PATH = entities_dir / "bankaccounts.yaml"
        GROUPS_YAML_PATH = entities_dir / "groups.yaml"
        OWNERS_YAML_PATH = entities_dir / "owners.yaml"
        BANKS_YAML_PATH = entities_dir / "banks.yaml"
        TAX_YAML_PATH = entities_dir / "tax_category.yaml"
        TT_YAML_PATH = entities_dir / "transaction_types.yaml"
        CLASSIFY_YAML_PATH = entities_dir / "classify_rules.yaml"
    else:
        PROPERTIES_YAML_PATH = COMP_YAML_PATH = BANK_YAML_PATH = GROUPS_YAML_PATH = OWNERS_YAML_PATH = BANKS_YAML_PATH = TAX_YAML_PATH = TT_YAML_PATH = CLASSIFY_YAML_PATH = None

    # Backwards compatibility: set legacy *_CSV_PATH names to YAML paths so existing code keeps working
    CSV_PATH = PROPERTIES_YAML_PATH
    COMP_CSV_PATH = COMP_YAML_PATH
    BANK_CSV_PATH = BANK_YAML_PATH
    GROUPS_CSV_PATH = GROUPS_YAML_PATH
    OWNERS_CSV_PATH = OWNERS_YAML_PATH
    TAX_CSV_PATH = TAX_YAML_PATH
    TT_CSV_PATH = TT_YAML_PATH
    CLASSIFY_CSV_PATH = CLASSIFY_YAML_PATH


def _load_entities() -> None:
    loaders.load_companies_yaml_into_memory(COMP_YAML_PATH, COMP_DB, logger)
    logger.info(f"Loaded {len(COMP_DB)} company records from {COMP_YAML_PATH}")
    loaders.load_properties_yaml_into_memory(PROPERTIES_YAML_PATH, DB, COMP_DB, logger)
    logger.info(f"Loaded {len(DB)} properties from {PROPERTIES_YAML_PATH}")
    loaders.load_bankaccounts_yaml_into_memory(BANK_YAML_PATH, BA_DB, logger)
    logger.info(f"Loaded {len(BA_DB)} bank accounts from {BANK_YAML_PATH}")
    loaders.load_groups_yaml_into_memory(GROUPS_YAML_PATH, GROUP_DB, logger)
    logger.info(f"Loaded {len(GROUP_DB)} groups from {GROUPS_YAML_PATH}")
    loaders.load_owners_yaml_into_memory(OWNERS_YAML_PATH, OWNER_DB, logger)
    logger.info(f"Loaded {len(OWNER_DB)} owners from {OWNERS_YAML_PATH}")
    loaders.load_tax_categories_yaml_into_memory(TAX_YAML_PATH, TAX_DB, logger)
    logger.info(f"Loaded {len(TAX_DB)} tax categories from {TAX_YAML_PATH}")
    loaders.load_transaction_types_yaml_into_memory(TT_YAML_PATH, TT_DB, logger)
    logger.info(f"Loaded {len(TT_DB)} transaction types from {TT_YAML_PATH}")
    loaders.load_banks_yaml_into_memory(BANKS_YAML_PATH, BANKS_CFG_DB, logger)
    logger.info(f"Loaded {len(BANKS_CFG_DB)} bank configs from {BANKS_YAML_PATH}")


def _load_manual_rules() -> None:
    if CLASSIFY_YAML_PATH:
        base_dir = CLASSIFY_YAML_PATH.parent
        # Dedupe per-bank YAML files to remove duplicate pattern_match_logic entries
        loaders.dedupe_bank_rules_dir(base_dir / 'bank_rules', logger)
        # Do not load bank_rules.yaml anymore; rules are sourced from per-bank files under bank_rules/
        # Let exceptions propagate so startup fails (e.g., duplicate patterns)
        loaders.load_common_rules_yaml_into_memory(base_dir / 'common_rules.yaml', COMMON_RULES_DB, logger)
        loaders.load_inherit_rules_yaml_into_memory(base_dir / 'inherit_common_to_bank.yaml', INHERIT_RULES_DB, logger)
        logger.info(
            f"Loaded manual lists -> bank_rules={len(CLASSIFY_DB)}, common_rules={len(COMMON_RULES_DB)}, inherit_rules={len(INHERIT_RULES_DB)}"
        )


def _emit_yaml_snapshots() -> None:
    # No-op: do not prepare or write banks.yaml or bank_rules.yaml at startup
    return


def _process_statements() -> None:
    try:
        process_bank_stmts(BA_DB, BANKS_CFG_DB, CURRENT_YEAR, NORMALIZED_DIR_PATH, logger)
    except Exception as e:
        logger.error(f"Failed processing bank statements from sources: {e}")


@app.on_event("startup")
async def startup_event():
    _init_fs_and_env()
    _read_mandatory_envs()
    entities_dir = _resolve_entities_dir()
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
    # Build initial rental summaries
    try:
        prepare_and_save_property_sum()
    except Exception as e:
        logger.error(f"Failed to build rental summary on startup: {e}")
    # Build initial company summaries
    try:
        prepare_and_save_company_sum()
    except Exception as e:
        logger.error(f"Failed to build company summary on startup: {e}")


# Minimal SPA fallback for Classify Rules client routes
FRONTEND_INDEX = (Path(__file__).resolve().parent.parent / "frontend" / "index.html")

@app.get("/classifyrules")
async def spa_classifyrules_root():
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    raise HTTPException(status_code=404, detail="index.html not found")

# Transactions SPA fallback
@app.get("/transactions")
async def spa_transactions_root():
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    raise HTTPException(status_code=404, detail="index.html not found")

# Company Summary SPA fallback
@app.get("/companysummary")
async def spa_companysummary_root():
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    raise HTTPException(status_code=404, detail="index.html not found")

# Rental Summary SPA fallback
@app.get("/rentalsummary")
async def spa_rentalsummary_root():
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    raise HTTPException(status_code=404, detail="index.html not found")

# Report SPA fallback
@app.get("/report")
async def spa_report_root():
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/classifyrules/{rest:path}")
async def spa_classifyrules(rest: str = ""):
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    raise HTTPException(status_code=404, detail="index.html not found")

# Setup SPA fallbacks
@app.get("/setup")
async def spa_setup_root():
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/setup/{rest:path}")
async def spa_setup(rest: str = ""):
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    raise HTTPException(status_code=404, detail="index.html not found")

# Serve static frontend
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)

