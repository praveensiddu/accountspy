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

    # Augment company summary with rentpassedtoowners and income derived from rentalsummary
    try:
        calculate_income_rentpassed(summary)
    except Exception:
        pass

    # Compute profit per company
    try:
        calc_profit(summary)
    except Exception:
        pass

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


def calc_profit(summary: Dict[str, Dict[str, float]]) -> None:
    """
    Compute per-company profit and store under key 'profit'.
    profit = sum of the following keys if present:
      income, rentpassedtoowners, bankfees, c_auto, c_donate, c_entertainment,
      c_internet, c_license, c_mobile, c_off_exp, c_parktoll, c_phone,
      c_website, ignore, insurane, insurance, proffees, utilities
    Values are summed as stored (some may be negative already).
    """
    keys = [
        'income', 'rentpassedtoowners', 'bankfees',
        'c_auto','c_donate','c_entertainment','c_internet','c_license','c_mobile',
        'c_off_exp','c_parktoll','c_phone','c_website','ignore','insurane','insurance',
        'proffees','utilities'
    ]
    for cname, totals in (summary or {}).items():
        try:
            s = 0.0
            for k in keys:
                try:
                    s += float(totals.get(k, 0.0) or 0.0)
                except Exception:
                    continue
            totals['profit'] = round(s, 2)
        except Exception:
            continue


def calculate_income_rentpassed(summary: Dict[str, Dict[str, float]]) -> None:
    """
    For each company in summary, compute:
    - rentpassedtoowners: sum of 'rent' from property rental summaries for properties managed by the company
    - income: rentpassedtoowners + (rentpassedtoowners * company.rentPercentage/100)
    Writes the values into summary[company]['rentpassedtoowners'] and summary[company]['income'].
    """
    try:
        rentals_dir: Path = state.ACCOUNTS_DIR_PATH / (state.CURRENT_YEAR or '') / 'rentalsummary'
        props = dict(getattr(state, 'DB', {}) or {})
        comps = dict(getattr(state, 'COMP_DB', {}) or {})
    except Exception:
        return
    # Ensure all companies present in summary have base keys
    for cname in list(comps.keys()):
        key = (cname or '').strip().lower()
        if not key:
            continue
        if key not in summary:
            summary[key] = {}
        summary[key]['rentpassedtoowners'] = 0.0
        summary[key]['income'] = 0.0

    # Aggregate rentpassedtoowners from property rental summaries
    try:
        if rentals_dir.exists() and rentals_dir.is_dir():
            for pkey, prec in props.items():
                prop_id = (pkey or '').strip().lower()
                if not prop_id:
                    continue
                comp_key = (prec.get('propMgmtComp') or '').strip().lower()
                if not comp_key:
                    continue
                p_yaml = rentals_dir / f"{prop_id}.yaml"
                if not p_yaml.exists():
                    continue
                try:
                    with p_yaml.open('r', encoding='utf-8') as pf:
                        pdata = yaml.safe_load(pf) or {}
                    rent_val = float((pdata.get('rent', 0.0) or 0.0))
                except Exception:
                    rent_val = 0.0
                if comp_key not in summary:
                    summary[comp_key] = {}
                summary[comp_key]['rentpassedtoowners'] += rent_val

            for comp_key in summary:
                summary[comp_key]['rentpassedtoowners'] = -round(summary[comp_key].get('rentpassedtoowners', 0.0) or 0.0, 2)
    except Exception:
        pass

    # Compute income per company
    for cname, totals in summary.items():
        try:
            comp_rec = comps.get(cname) or {}
            pct = float(comp_rec.get('rentPercentage', 0) or 0)
            rp = -(float(totals.get('rentpassedtoowners', 0.0) or 0.0))
            income = (rp * 100)/(100-pct)
            totals['income'] = round(income, 2)
        except Exception:
            continue
