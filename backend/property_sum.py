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
                    'date': row.get('date',''),
                    'description': row.get('description',''),
                    'credit': row.get('credit',''),
                    'transaction_type': row.get('transaction_type',''),
                    'tax_category': row.get('tax_category',''),
                    'property': row.get('property',''),
                    'group': row.get('group',''),
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
                            'date': item.get('date',''),
                            'description': item.get('description',''),
                            'credit': item.get('credit',''),
                            'transaction_type': item.get('transaction_type',''),
                            'tax_category': item.get('tax_category',''),
                            'property': item.get('property',''),
                            'group': item.get('group',''),
                        })
    except Exception:
        pass
    return rows


def _to_float(val: Any) -> float:
    try:
        s = str(val).strip()
        if not s:
            return 0.0
        return float(s)
    except Exception:
        return 0.0


def prepare_and_save_property_sum() -> None:
    """
    Build rental summary per property by summing credits by transaction_type for
    transactions with tax_category == 'rental'.
    Writes one YAML file per property at ACCOUNTS_DIR/CURRENT_YEAR/rentalsummary/<property>.yaml
    with a mapping { transaction_type: total }.
    """
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        return
    base_processed: Path = state.PROCESSED_DIR_PATH
    if not base_processed:
        return

    summary: Dict[str, Dict[str, float]] = {}

    # Iterate all bank accounts from state to know filenames
    for ba in list(state.BA_DB.keys()):
        py = base_processed / f"{ba}.yaml"
        if py.exists():
            rows = _read_processed_yaml(py)
        else:
            pc = base_processed / f"{ba}.csv"
            rows = _read_processed_csv(pc) if pc.exists() else []
        for r in rows:
            try:
                if (r.get('tax_category') or '').strip().lower() != 'rental':
                    continue
                tx_type = (r.get('transaction_type') or '').strip().lower()
                if not tx_type:
                    continue
                credit = _to_float(r.get('credit'))
                props: List[str] = []
                prop = (r.get('property') or '').strip().lower()
                grp = (r.get('group') or '').strip().lower()
                if prop:
                    props = [prop]
                elif grp:
                    try:
                        grp_rec = state.GROUP_DB.get(grp) or {}
                        props = [ (p or '').strip().lower() for p in (grp_rec.get('propertylist') or []) if (p or '').strip() ]
                    except Exception:
                        props = []
                if not props:
                    continue
                for p in props:
                    if not p:
                        continue
                    if p not in summary:
                        summary[p] = {}
                    summary[p][tx_type] = summary[p].get(tx_type, 0.0) + credit
            except Exception:
                # Skip bad rows
                continue

    # Ensure rentalsummary dir
    out_dir: Path = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'rentalsummary'
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return

    # Dump one YAML per property
    for p, totals in summary.items():
        try:
            # Sort keys for determinism
            ordered = { k: float(totals.get(k, 0.0)) for k in sorted(totals.keys()) }
            out_path = out_dir / f"{p}.yaml"
            with out_path.open('w', encoding='utf-8') as yf:
                yaml.safe_dump(ordered, yf, sort_keys=True, allow_unicode=True)
        except Exception:
            # continue with others
            continue
