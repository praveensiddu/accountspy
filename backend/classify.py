from __future__ import annotations

import copy
import re
import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from . import main as state

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s %(levelname)s {Path(__file__).name}:%(lineno)d %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ProcRow:
    date: str
    description: str
    credit: str
    tr_id: str = ""
    ruleid: str = ""
    comment: str = ""
    transaction_type: str = ""
    tax_category: str = ""
    property: str = ""
    group: str = ""
    company: str = ""
    otherentity: str = ""
    override: str = ""

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ProcRow":
        return ProcRow(
            date=str(d.get("date", "")),
            description=str(d.get("description", "")),
            credit=str(d.get("credit", "")),
            tr_id=str(d.get("tr_id", "")),
            ruleid=str(d.get("ruleid", "")),
            comment=str(d.get("comment", "")),
            transaction_type=str(d.get("transaction_type", "")),
            tax_category=str(d.get("tax_category", "")),
            property=str(d.get("property", "")),
            group=str(d.get("group", "")),
            company=str(d.get("company", "")),
            otherentity=str(d.get("otherentity", "")),
            override=str(d.get("override", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "description": self.description,
            "credit": self.credit,
            "tr_id": self.tr_id,
            "ruleid": self.ruleid,
            "comment": self.comment,
            "transaction_type": self.transaction_type,
            "tax_category": self.tax_category,
            "property": self.property,
            "group": self.group,
            "company": self.company,
            "otherentity": self.otherentity,
            "override": self.override,
        }


# --------------------------
# Public API
# --------------------------

def classify_all() -> None:
    """Classify for every bank account in the Bank Accounts table."""
    logger.info("Classifying all bank accounts")
    if not state.BA_DB:
        return
    for bank in state.BA_DB.keys():
        try:
            classify_bank(bank)
        except Exception:
            continue


def classify_bank(bankaccountname: str) -> None:
    """Classify a single bank account's normalized rows into processed YAML."""
    logger.info(f"Classifying bank account: {bankaccountname}")
    bank = (bankaccountname or "").strip().lower()
    if not bank:
        logger.info(f"No bank account found for {bankaccountname}")
        return
    norm_dir: Optional[Path] = state.NORMALIZED_DIR_PATH
    proc_dir: Optional[Path] = state.PROCESSED_DIR_PATH
    if not norm_dir or not proc_dir:
        logger.info(f"No normalized or processed directory found for {bank}")
        return

    # 1) Seed processed from normalized CSV only
    processed: Dict[str, List[Dict[str, Any]]] = {}
    seed_rows: List[ProcRow] = []
    norm_csv = norm_dir / f"{bank}.csv"
    if not norm_csv.exists():
        logger.info(f"No normalized CSV found for {bank}")
        return
    try:
        with norm_csv.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Expecting columns: tr_id,date,description,credit
                seed_rows.append(ProcRow.from_dict(row))
    except Exception as e:
        logger.info(f"Error loading normalized CSV for {bank}: {e}")
        return

    processed[bank] = [r.to_dict() for r in seed_rows]

    # 1b) Append addendum CSV rows if present (date, description, credit)
    try:
        add_csv: Optional[Path] = None
        # Prefer per-bank statement_location
        try:
            ba = state.BA_DB.get(bank) or {}
            sl = (ba.get('statement_location') or '').strip()
            if sl and state.CURRENT_YEAR:
                per_bank_add = Path(sl) / state.CURRENT_YEAR / 'addendum' / f"{bank}.csv"
                if per_bank_add.exists():
                    add_csv = per_bank_add
        except Exception:
            add_csv = None
        # Fallback to global ADDENDUM_DIR_PATH
        if add_csv is None and state.ADDENDUM_DIR_PATH:
            candidate = state.ADDENDUM_DIR_PATH / f"{bank}.csv"
            if candidate.exists():
                add_csv = candidate
        if add_csv and add_csv.exists():
            with add_csv.open("r", encoding="utf-8") as af:
                areader = csv.DictReader(af)
                for row in areader:
                    processed[bank].append(ProcRow.from_dict(row).to_dict())
    except Exception:
        # ignore addendum errors to avoid blocking classification
        pass

    # 2) Apply bank rules if present
    # Only check per-bank bank_rules under statement_location/CURRENT_YEAR/bank_rules
    per_bank_candidate: Optional[Path] = None
    bank_rules_path: Optional[Path] = None
    try:
        ba = state.BA_DB.get(bank) or {}
        sl = (ba.get('statement_location') or '').strip()
        if sl and state.CURRENT_YEAR:
            per_bank_candidate = Path(sl) / state.CURRENT_YEAR / 'bank_rules' / f"{bank}.yaml"
            if per_bank_candidate.exists():
                bank_rules_path = per_bank_candidate
    except Exception:
        bank_rules_path = None

    if not bank_rules_path or not bank_rules_path.exists():
        logger.info(
            f"No bank rules found at per-bank path: {per_bank_candidate}"
        )
        return

    try:
        with bank_rules_path.open("r", encoding="utf-8") as f:
            rules_raw = yaml.safe_load(f) or []
            rules: List[Dict[str, Any]] = [r for r in rules_raw if isinstance(r, dict)]
    except Exception:
        rules = []

    def _float_or_none(s: str) -> Optional[float]:
        try:
            return float(s)
        except Exception:
            return None

    def _matches(rule: Dict[str, Any], rec: Dict[str, Any]) -> bool:
        patt = str(rule.get("pattern_match_logic", ""))
        desc = str(rec.get("description", ""))
        credit = _float_or_none(str(rec.get("credit", "")))
        # desc_contains
        m = re.search(r"desc_contains\s*=\s*(.+)", patt, flags=re.IGNORECASE)
        if m:
            pattern_val = m.group(1).strip()
            if pattern_val and pattern_val.lower() in desc.lower():
                return True
        # desc_startswith
        m = re.search(r"desc_startswith\s*=\s*(.+)", patt, flags=re.IGNORECASE)
        if m:
            pattern_val = m.group(1).strip()
            if pattern_val and desc.lower().startswith(pattern_val.lower()):
                return True
        # credit_equals
        m = re.search(r"credit_equals\s*=\s*([-+]?[0-9]*\.?[0-9]+)", patt, flags=re.IGNORECASE)
        if m and credit is not None:
            try:
                pattern_val = float(m.group(1))
                if abs(credit - pattern_val) < 0.10:
                    return True
            except Exception:
                pass
        return False

    # iterate processed records; for each, scan rules in the order in file
    for rec in processed[bank]:
        matched = False
        for rule in rules:
            if _matches(rule, rec):
                rec["ruleid"] = str(int(rule.get("order") or 0))
                rec["transaction_type"] = str(rule.get("transaction_type", ""))
                rec["tax_category"] = str(rule.get("tax_category", ""))
                rec["property"] = str(rule.get("property", ""))
                rec["group"] = str(rule.get("group", ""))
                rec["company"] = str(rule.get("company", ""))
                rec["otherentity"] = str(rule.get("otherentity", ""))
                matched = True
                break
        if not matched:
            # leave as-is when no match
            pass

    # 3) Save processed CSV sorted by date, then description, then credit
    out_rows = processed.get(bank, [])
    def _credit_as_float(v: Any) -> float:
        try:
            return float(v)
        except Exception as e:
            logger.info(f"Error converting credit to float: {v} {e}")
            return 0.0

    out_rows.sort(key=lambda r: (str(r.get("date", "")), str(r.get("description", "")), _credit_as_float(r.get("credit", 0))))

    proc_dir.mkdir(parents=True, exist_ok=True)
    out_csv = proc_dir / f"{bank}.csv"
    header = ['tr_id','date','description','credit','ruleid','comment','transaction_type','tax_category','property','group','company','otherentity','override']
    try:
        with out_csv.open("w", newline='', encoding="utf-8") as wf:
            writer = csv.DictWriter(wf, fieldnames=header, extrasaction='ignore')
            writer.writeheader()
            for r in out_rows:
                writer.writerow(r)
        logger.info(f"Saved processed CSV for {bank}")
    except Exception as e:
        logger.info(f"Error saving processed CSV for {bank}: {e}")
