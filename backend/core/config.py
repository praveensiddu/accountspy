from pathlib import Path
from typing import Optional

# Paths configured at startup
DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data"
FRONTEND_DIR: Path = Path(__file__).resolve().parent.parent.parent / "frontend"

CSV_PATH: Optional[Path] = None
COMP_CSV_PATH: Optional[Path] = None
BANK_CSV_PATH: Optional[Path] = None
GROUPS_CSV_PATH: Optional[Path] = None
OWNERS_CSV_PATH: Optional[Path] = None
BANKS_YAML_PATH: Optional[Path] = None
TAX_CSV_PATH: Optional[Path] = None
TT_CSV_PATH: Optional[Path] = None
