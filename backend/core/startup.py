import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from . import config
from .db import (
    DB, COMP_DB, BA_DB, GROUP_DB, OWNER_DB, TAX_DB, TT_DB, BANKS_CFG_DB,
)
from .utils import dump_yaml_entities
from .loaders import (
    load_companies_csv_into_memory,
    load_csv_into_memory,
    load_bankaccounts_csv_into_memory,
    load_groups_csv_into_memory,
    load_owners_csv_into_memory,
    load_tax_categories_csv_into_memory,
    load_transaction_types_csv_into_memory,
    load_banks_yaml_into_memory,
)

logger = logging.getLogger("uvicorn.error")


def init_from_env(project_root: Path) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

    env_path = project_root / ".env"
    load_dotenv(env_path)
    logger.info(f"ENV path: {env_path} exists={env_path.exists()}")

    entities_dir_env = os.getenv("ENTITIES_DIR", "").strip()
    entities_dir = Path(entities_dir_env) if entities_dir_env else None
    if entities_dir:
        entities_dir = entities_dir.expanduser().resolve()
    logger.info(f"ENTITIES_DIR: {entities_dir} exists={entities_dir.exists() if entities_dir else False}")

    config.CSV_PATH = (entities_dir / "properties.csv") if entities_dir else None
    config.COMP_CSV_PATH = (entities_dir / "companies.csv") if entities_dir else None
    config.BANK_CSV_PATH = (entities_dir / "bankaccounts.csv") if entities_dir else None
    config.GROUPS_CSV_PATH = (entities_dir / "groups.csv") if entities_dir else None
    config.OWNERS_CSV_PATH = (entities_dir / "owners.csv") if entities_dir else None
    config.BANKS_YAML_PATH = (entities_dir / "banks.yaml") if entities_dir else None
    config.TAX_CSV_PATH = (entities_dir / "tax_category.csv") if entities_dir else None
    config.TT_CSV_PATH = (entities_dir / "transaction_types.csv") if entities_dir else None

    # Load CSVs/YAML
    load_companies_csv_into_memory(config.COMP_CSV_PATH)
    logger.info(f"Loaded {len(COMP_DB)} company records from {config.COMP_CSV_PATH}")
    load_csv_into_memory(config.CSV_PATH)
    logger.info(f"Loaded {len(DB)} properties from {config.CSV_PATH}")
    load_bankaccounts_csv_into_memory(config.BANK_CSV_PATH)
    logger.info(f"Loaded {len(BA_DB)} bank accounts from {config.BANK_CSV_PATH}")
    load_groups_csv_into_memory(config.GROUPS_CSV_PATH)
    logger.info(f"Loaded {len(GROUP_DB)} groups from {config.GROUPS_CSV_PATH}")
    load_owners_csv_into_memory(config.OWNERS_CSV_PATH)
    logger.info(f"Loaded {len(OWNER_DB)} owners from {config.OWNERS_CSV_PATH}")
    load_tax_categories_csv_into_memory(config.TAX_CSV_PATH)
    logger.info(f"Loaded {len(TAX_DB)} tax categories from {config.TAX_CSV_PATH}")
    load_transaction_types_csv_into_memory(config.TT_CSV_PATH)
    logger.info(f"Loaded {len(TT_DB)} transaction types from {config.TT_CSV_PATH}")
    load_banks_yaml_into_memory(config.BANKS_YAML_PATH)
    logger.info(f"Loaded {len(BANKS_CFG_DB)} bank configs from {config.BANKS_YAML_PATH}")

    try:
        if config.COMP_CSV_PATH:
            dump_yaml_entities(
                path=config.COMP_CSV_PATH.with_suffix('.yaml'),
                entities=list(COMP_DB.values()),
                key_field='companyname',
            )
        if config.CSV_PATH:
            dump_yaml_entities(
                path=config.CSV_PATH.with_suffix('.yaml'),
                entities=list(DB.values()),
                key_field='property',
            )
        if config.BANK_CSV_PATH:
            dump_yaml_entities(
                path=config.BANK_CSV_PATH.with_suffix('.yaml'),
                entities=list(BA_DB.values()),
                key_field='bankaccountname',
            )
        if config.GROUPS_CSV_PATH:
            dump_yaml_entities(
                path=config.GROUPS_CSV_PATH.with_suffix('.yaml'),
                entities=list(GROUP_DB.values()),
                key_field='groupname',
            )
        if config.OWNERS_CSV_PATH:
            dump_yaml_entities(
                path=config.OWNERS_CSV_PATH.with_suffix('.yaml'),
                entities=list(OWNER_DB.values()),
                key_field='name',
            )
        if config.TAX_CSV_PATH:
            dump_yaml_entities(
                path=config.TAX_CSV_PATH.with_suffix('.yaml'),
                entities=list(TAX_DB.values()),
                key_field='category',
            )
        if config.TT_CSV_PATH:
            dump_yaml_entities(
                path=config.TT_CSV_PATH.with_suffix('.yaml'),
                entities=list(TT_DB.values()),
                key_field='transactiontype',
            )
        if config.BANKS_YAML_PATH:
            dump_yaml_entities(
                path=config.BANKS_YAML_PATH,
                entities=list(BANKS_CFG_DB.values()),
                key_field='name',
            )
    except Exception as e:
        logger.error(f"Failed to write YAML snapshots: {e}")
