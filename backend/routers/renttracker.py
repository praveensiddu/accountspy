from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from .. import main as state
from ..property_sum import _read_processed_csv, _read_processed_yaml, _to_float

router = APIRouter(prefix="/api", tags=["rent-tracker"])


@router.get("/rent-tracker")
async def get_rent_tracker() -> List[Dict[str, Any]]:
    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR is not configured")
    base_processed: Path = state.PROCESSED_DIR_PATH
    if not base_processed:
        raise HTTPException(status_code=500, detail="Processed directory is not configured")

    summary: Dict[str, Dict[int, float]] = {}

    for ba in list(state.BA_DB.keys()):
        py = base_processed / f"{ba}.yaml"
        if py.exists():
            rows = _read_processed_yaml(py)
        else:
            pc = base_processed / f"{ba}.csv"
            rows = _read_processed_csv(pc) if pc.exists() else []
        for r in rows:
            try:
                tax = (r.get("tax_category") or "").strip().lower()
                if tax != "rental":
                    continue
                tx = (r.get("transaction_type") or "").strip().lower()
                if tx not in ("rent", "tenantfees"):
                    continue
                dt_raw = (r.get("date") or "").strip()
                if not dt_raw:
                    continue
                month_idx = 0
                try:
                    if len(dt_raw) >= 7 and dt_raw[4] == "-" and dt_raw[7-1].isdigit():
                        month_idx = int(dt_raw[5:7])
                    else:
                        d = datetime.fromisoformat(dt_raw[:10])
                        month_idx = d.month
                except Exception:
                    try:
                        d = datetime.strptime(dt_raw[:10], "%Y-%m-%d")
                        month_idx = d.month
                    except Exception:
                        continue
                if month_idx < 1 or month_idx > 12:
                    continue
                credit = _to_float(r.get("credit"))
                if credit == 0.0:
                    continue
                props: List[str] = []
                prop = (r.get("property") or "").strip().lower()
                grp = (r.get("group") or "").strip().lower()
                if prop:
                    props = [prop]
                elif grp:
                    try:
                        grp_rec = state.GROUP_DB.get(grp) or {}
                        props = [ (p or "").strip().lower() for p in (grp_rec.get("propertylist") or []) if (p or "").strip() ]
                    except Exception:
                        props = []
                if not props:
                    continue
                share = 0.0
                try:
                    if prop and len(props) == 1:
                        share = credit
                    else:
                        share = credit / float(len(props))
                except Exception:
                    share = 0.0
                for p in props:
                    if not p:
                        continue
                    if p not in summary:
                        summary[p] = {}
                    summary[p][month_idx] = summary[p].get(month_idx, 0.0) + share
            except Exception:
                continue

    month_keys = {
        1: "jan", 2: "feb", 3: "mar", 4: "apr", 5: "may", 6: "jun",
        7: "jul", 8: "aug", 9: "sep", 10: "oct", 11: "nov", 12: "dec",
    }
    out: List[Dict[str, Any]] = []
    for prop in sorted(summary.keys()):
        row: Dict[str, Any] = {"property": prop}
        months = summary.get(prop) or {}
        for idx, key in month_keys.items():
            val = float(months.get(idx, 0.0) or 0.0)
            row[key] = round(val, 2) if val != 0.0 else 0.0
        out.append(row)

    return out
