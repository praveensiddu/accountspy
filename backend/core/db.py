import re
from typing import Dict, List

# Regexes
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

# Companies list loaded from env (optional)
COMPANIES: List[str] = []
