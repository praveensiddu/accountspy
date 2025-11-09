from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, date
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
        return round(float(s), 2)
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
    # reverse map: property -> transaction_type -> list of {bankaccountname, description, credit}
    reverse_map: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

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
                desc = (r.get('description') or '').strip()
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
                    # build reverse map entry
                    if p not in reverse_map:
                        reverse_map[p] = {}
                    if tx_type not in reverse_map[p]:
                        reverse_map[p][tx_type] = []
                    reverse_map[p][tx_type].append({
                        'bankaccountname': ba,
                        'description': desc,
                        'credit': credit,
                    })
            except Exception:
                # Skip bad rows
                continue

    # Ensure rentalsummary dir
    out_dir: Path = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'rentalsummary'
    rev_dir: Path = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'rentalsummary_reverse'
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        rev_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return

    # Adjust rent using property management company rentPercentage
    try:
        rent_from_company(summary)
    except Exception:
        pass

    # Augment summary with depreciation numbers before dumping
    try:
        calculate_depreciation(summary)
    except Exception:
        pass

    # Compute profit per property
    try:
        calculate_profit(summary)
    except Exception:
        pass

    # Dump one YAML per property and corresponding reverse map
    for p, totals in summary.items():
        try:
            # Sort keys for determinism and round to 2 decimals
            ordered = { k: round(float(totals.get(k, 0.0)), 2) for k in sorted(totals.keys()) }
            out_path = out_dir / f"{p}.yaml"
            with out_path.open('w', encoding='utf-8') as yf:
                yaml.safe_dump(ordered, yf, sort_keys=True, allow_unicode=True)
            # dump reverse map for this property (keep list order as encountered)
            rev = reverse_map.get(p) or {}
            rev_out = rev_dir / f"{p}.yaml"
            with rev_out.open('w', encoding='utf-8') as rf:
                yaml.safe_dump(rev, rf, sort_keys=True, allow_unicode=True)
        except Exception:
            # continue with others
            continue


def calculate_depreciation(summary: Dict[str, Dict[str, float]]):
    """
    For each property in state.DB, compute depreciation and insert into summary under key 'depreciation'.
    - depreciation = (cost + renovation) * 3.64 / 100
    - If purchaseDate year equals CURRENT_YEAR, prorate by noOfDaysOwnedThisYear / 365
    """
    try:
        props = dict(getattr(state, 'DB', {}) or {})
    except Exception:
        props = {}
    if not props:
        return

    # Helper to parse a purchase date string into a date
    def _parse_date(ds: str) -> date:
        s = (ds or '').strip()
        if not s:
            return None
        fmts = ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%m/%d/%Y', '%d-%m-%Y']
        for fmt in fmts:
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        # Fallback: just try to take the first 10 chars as YYYY-MM-DD
        try:
            return datetime.strptime(s[:10], '%Y-%m-%d').date()
        except Exception:
            return None

    cy_str = state.CURRENT_YEAR or ''
    try:
        cy = int(cy_str)
    except Exception:
        cy = None

    for prop_id, prec in props.items():
        try:
            cost = float(prec.get('cost', 0) or 0)
            renovation = float(prec.get('renovation', 0) or 0)
            base = cost + renovation
            depreciation = round(base * 3.64 / 100.0, 2)

            pdate = _parse_date(prec.get('purchaseDate', ''))
            if pdate and cy is not None and pdate.year == cy:
                start = pdate
                end = date(cy, 12, 31)
                days_owned = max(0, (end - start).days + 1)
                depreciation = round(depreciation * (days_owned / 365.0), 2)

            if prop_id not in summary:
                summary[prop_id] = {}
            summary[prop_id]['depreciation'] = -(float(depreciation))
        except Exception:
            continue


def rent_from_company(summary: Dict[str, Dict[str, float]]):
    """
    For each property in summary, adjust 'rent' based on the property's
    management company's rentPercentage from state.COMP_DB.
    rentfromcompany = current_rent * (100 - rentPercentage) / 100
    """
    try:
        props = dict(getattr(state, 'DB', {}) or {})
        comps = dict(getattr(state, 'COMP_DB', {}) or {})
    except Exception:
        return
    for prop_id, totals in (summary or {}).items():
        try:
            prec = props.get(prop_id) or {}
            comp_key = (prec.get('propMgmgtComp') or '').strip().lower()
            comp = comps.get(comp_key) or {}
            pct = float(comp.get('rentPercentage', 0) or 0)
            current_rent = float(totals.get('rent', 0.0) or 0.0)
            adjusted = round(current_rent * ((100.0 - pct) / 100.0), 2)
            totals['rent'] = adjusted
        except Exception:
            continue


def calculate_profit(summary: Dict[str, Dict[str, float]]):
    """
    Compute per-property profit and store under key 'profit'.
    profit = rent + commissions + insurance + proffees + mortgageinterest + repairs + tax + utilities + depreciation + hoa
    Where 'rent' contributes as-is (income, positive), and all others contribute as expenses (negative).
    """
    expense_keys = [
        'commissions','insurance','proffees','mortgageinterest','repairs','tax','utilities','depreciation','hoa'
    ]
    for prop_id, totals in (summary or {}).items():
        try:
            rent_val = float(totals.get('rent', 0.0) or 0.0)
            expense_sum = 0.0
            for k in expense_keys:
                v = float(totals.get(k, 0.0) or 0.0)
                # Ensure expenses contribute negatively
                expense_sum += -abs(v)
            totals['profit'] = round(rent_val + expense_sum, 2)
        except Exception:
            continue
