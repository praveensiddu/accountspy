from pathlib import Path
from typing import Dict, List, Any
import csv
import yaml

from . import main as state


def _read_processed_csv(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        with path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    'credit': row.get('credit',''),
                    'transaction_type': row.get('transaction_type',''),
                    'company': row.get('company',''),
                })
    except Exception:
        pass
    return rows


def _read_processed_yaml(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        rows.append({
                            'credit': item.get('credit',''),
                            'transaction_type': item.get('transaction_type',''),
                            'company': item.get('company',''),
                        })
    except Exception:
        pass
    return rows


def _to_float(val: Any) -> float:
    try:
        s = str(val).strip()
        if not s:
            return 0.0
        return round(float(s), 2)
    except Exception:
        return 0.0


def prepare_and_save_company_sum() -> None:
    """
    Build company summary per company by summing credits by transaction_type for
    any transaction that has a non-empty company field.
    Writes one YAML file per company at ACCOUNTS_DIR/CURRENT_YEAR/companysummary/<company>.yaml
    with a mapping { transaction_type: total }.
    """
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        return
    base_processed: Path = state.PROCESSED_DIR_PATH
    if not base_processed:
        return

    summary: Dict[str, Dict[str, float]] = {}

    for ba in list(state.BA_DB.keys()):
        py = base_processed / f"{ba}.yaml"
        if py.exists():
            rows = _read_processed_yaml(py)
        else:
            pc = base_processed / f"{ba}.csv"
            rows = _read_processed_csv(pc) if pc.exists() else []
        for r in rows:
            try:
                comp = (r.get('company') or '').strip().lower()
                if not comp:
                    continue
                tx_type = (r.get('transaction_type') or '').strip().lower()
                if not tx_type:
                    continue
                credit = _to_float(r.get('credit'))
                if comp not in summary:
                    summary[comp] = {}
                summary[comp][tx_type] = summary[comp].get(tx_type, 0.0) + credit
            except Exception:
                continue

    out_dir: Path = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'companysummary'
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return

    for c, totals in summary.items():
        try:
            ordered = { k: round(float(totals.get(k, 0.0)), 2) for k in sorted(totals.keys()) }
            out_path = out_dir / f"{c}.yaml"
            with out_path.open('w', encoding='utf-8') as yf:
                yaml.safe_dump(ordered, yf, sort_keys=True, allow_unicode=True)
        except Exception:
            continue
