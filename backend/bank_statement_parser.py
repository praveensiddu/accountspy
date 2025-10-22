from __future__ import annotations
from typing import Dict, List, Optional, Any
from pathlib import Path
import csv
from datetime import datetime


def _py_strptime(fmt: str) -> str:
    m = fmt
    m = m.replace('yyyy', '%Y').replace('yy', '%y')
    m = m.replace('MM', '%m').replace('M', '%-m')
    m = m.replace('dd', '%d').replace('d', '%-d')
    return m


def _normalize_date(s: str, raw_fmt: str) -> str:
    if not s:
        return ''
    ss = s.strip()
    if not ss:
        return ''
    py_fmt = _py_strptime(raw_fmt) if raw_fmt else ''
    fmts = [py_fmt] if py_fmt else []
    fmts += ['%m/%d/%Y', '%-m/%-d/%Y', '%Y-%m-%d']
    for f in fmts:
        try:
            dt = datetime.strptime(ss, f)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    return ss


def _parse_amount(s: str) -> str:
    if s is None:
        return ''
    txt = str(s).strip()
    if not txt:
        return ''
    neg = False
    if txt.startswith('(') and txt.endswith(')'):
        neg = True
        txt = txt[1:-1]
    for ch in ['$', ',', ' ']:
        txt = txt.replace(ch, '')
    try:
        val = float(txt)
        if neg:
            val = -val
        if abs(val - int(val)) < 1e-9:
            return str(int(val))
        return f"{val}"
    except Exception:
        return s


def _parse_amount_num(s: str) -> Optional[float]:
    try:
        txt = _parse_amount(s)
        if txt == '' or txt is None:
            return None
        return float(txt)
    except Exception:
        return None


def _process_bank_statement_for_account(bankaccountname: str, cfg: Dict[str, Any], src_path: Path, normalized_dir: Path, logger) -> None:
    if not normalized_dir:
        return
    if not src_path.exists() or not src_path.is_file():
        return
    delim = (cfg.get('delim') or ',')
    starts = cfg.get('ignore_lines_startswith') or []
    contains = cfg.get('ignore_lines_contains') or []
    columns_list = cfg.get('columns') or []
    colmap: Dict[str, int] = {}
    for entry in columns_list:
        if isinstance(entry, dict) and entry:
            colmap = entry
            break
    date_idx = int(colmap.get('date') or 0)
    desc_idx = int(colmap.get('description') or 0)
    debit_idx = int(colmap.get('debit') or 0)
    credit_idx = int(colmap.get('credit') or 0)
    if not (date_idx and desc_idx and (debit_idx or credit_idx)):
        return
    raw_fmt = (cfg.get('date_format') or '').strip()

    out_rows: List[Dict[str, str]] = []
    try:
        with src_path.open('r', encoding='utf-8') as rf:
            for raw_line in rf:
                line = raw_line.rstrip('\n')
                if not line.strip():
                    continue
                skip = False
                for s in starts:
                    try:
                        if s and line.startswith(s):
                            skip = True; break
                    except Exception:
                        continue
                if skip:
                    continue
                for c in contains:
                    try:
                        if c and (c in line):
                            skip = True; break
                    except Exception:
                        continue
                if skip:
                    continue
                parts = line.split(delim)
                def get_part(idx: int) -> str:
                    if idx <= 0:
                        return ''
                    return (parts[idx-1].strip() if len(parts) >= idx else '')
                date_val = get_part(date_idx)
                desc_val = get_part(desc_idx)
                debit_val = get_part(debit_idx) if debit_idx else ''
                credit_val = get_part(credit_idx) if credit_idx else ''
                date_out = _normalize_date(date_val, raw_fmt)
                amt_out = ''
                dv = _parse_amount_num(debit_val) if debit_val else None
                cv = _parse_amount_num(credit_val) if credit_val else None
                if dv is not None:
                    amt = -abs(dv)
                    amt_out = str(int(amt)) if abs(amt - int(amt)) < 1e-9 else f"{amt}"
                elif cv is not None:
                    amt = abs(cv)
                    amt_out = str(int(amt)) if abs(amt - int(amt)) < 1e-9 else f"{amt}"
                if not (date_out and desc_val):
                    continue
                out_rows.append({
                    'date': date_out,
                    'description': desc_val,
                    'credit': amt_out,
                    'comment': '',
                    'transaction_type': '',
                    'tax_category': '',
                    'property': '',
                    'company': '',
                    'otherentity': '',
                    'override': '',
                })
    except Exception as e:
        try:
            logger.error(f"Failed reading raw CSV for {bankaccountname}: {e}")
        except Exception:
            pass
        return

    if out_rows:
        header = ['date','description','credit','comment','transaction_type','tax_category','property','company','otherentity','override']
        out_path = normalized_dir / f"{bankaccountname}.csv"
        try:
            with out_path.open('w', newline='', encoding='utf-8') as wf:
                writer = csv.DictWriter(wf, fieldnames=header, extrasaction='ignore')
                writer.writeheader()
                for r in out_rows:
                    writer.writerow(r)
            try:
                logger.info(f"Wrote normalized CSV for {bankaccountname}: {out_path} rows={len(out_rows)}")
            except Exception:
                pass
        except Exception as e:
            try:
                logger.error(f"Failed to write normalized CSV for {bankaccountname}: {e}")
            except Exception:
                pass


def process_bank_statements_from_sources(
    ba_db: Dict[str, Dict[str, Any]],
    banks_cfg_db: Dict[str, Dict[str, Any]],
    current_year: str,
    normalized_dir: Path,
    logger,
) -> None:
    if not (ba_db and banks_cfg_db and normalized_dir and current_year):
        return
    for key, ba in list(ba_db.items()):
        try:
            stmt_loc = (ba.get('statement_location') or '').strip()
            bankname = (ba.get('bankname') or '').strip().lower()
            if not (stmt_loc and bankname):
                continue
            cfg = banks_cfg_db.get(bankname)
            if not cfg:
                continue
            src = Path(stmt_loc).expanduser().resolve() / str(current_year) / 'bank_stmts' / f"{key}.csv"
            _process_bank_statement_for_account(key, cfg, src, normalized_dir, logger)
        except Exception as e:
            try:
                logger.error(f"Failed processing account {key}: {e}")
            except Exception:
                pass
