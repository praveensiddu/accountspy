from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from pathlib import Path
import shutil
import yaml

from .. import main as state
from ..core.models import OwnerRecord
from ..core.utils import dump_yaml_entities

router = APIRouter(prefix="/api", tags=["owners"])


@router.get("/owners", response_model=List[OwnerRecord])
async def list_owners():
    return list(state.OWNER_DB.values())


@router.post("/owners", response_model=OwnerRecord, status_code=201)
async def add_owner(payload: OwnerRecord):
    key = payload.name.strip().lower()
    if not state.ALNUM_UNDERSCORE_LOWER_RE.match(key):
        raise HTTPException(status_code=400, detail="Invalid owner name: lowercase alphanumeric and underscore only")
    if key in state.OWNER_DB:
        raise HTTPException(status_code=409, detail="Owner already exists")
    state.OWNER_DB[key] = {
        "name": key,
        "bankaccounts": [b.strip().lower() for b in payload.bankaccounts],
        "properties": [p.strip().lower() for p in payload.properties],
        "companies": [c.strip().lower() for c in payload.companies],
    }
    # persist YAML
    try:
        if state.OWNERS_CSV_PATH:
            dump_yaml_entities(state.OWNERS_CSV_PATH.with_suffix('.yaml'), list(state.OWNER_DB.values()), key_field='name')
    except Exception:
        pass
    return state.OWNER_DB[key]


@router.delete("/owners/{name}", status_code=204)
async def delete_owner(name: str):
    key = name.strip().lower()
    if key not in state.OWNER_DB:
        raise HTTPException(status_code=404, detail="Owner not found")
    del state.OWNER_DB[key]
    # persist YAML
    try:
        if state.OWNERS_CSV_PATH:
            dump_yaml_entities(state.OWNERS_CSV_PATH.with_suffix('.yaml'), list(state.OWNER_DB.values()), key_field='name')
    except Exception:
        pass
    return


class OwnerExportPayload(BaseModel):
    name: str


@router.post("/owners/export")
async def export_owner(payload: OwnerExportPayload):
    name = (payload.name or "").strip().lower()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    owner = state.OWNER_DB.get(name)
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    if not state.ACCOUNTS_DIR_PATH or not state.CURRENT_YEAR:
        raise HTTPException(status_code=500, detail="ACCOUNTS_DIR or CURRENT_YEAR not configured")

    # Determine ENTITIES_DIR base using known computed paths
    entities_dir: Path = None  # type: ignore
    try:
        if state.CLASSIFY_CSV_PATH:
            entities_dir = state.CLASSIFY_CSV_PATH.parent
        elif state.BANKS_YAML_PATH:
            entities_dir = state.BANKS_YAML_PATH.parent
    except Exception:
        entities_dir = None  # type: ignore
    if not entities_dir or not entities_dir.exists():
        raise HTTPException(status_code=500, detail="ENTITIES_DIR not resolved")

    dest_root: Path = state.ACCOUNTS_DIR_PATH / state.CURRENT_YEAR / 'export' / name / 'entities'
    bank_rules_dest: Path = dest_root / 'bank_rules'
    try:
        bank_rules_dest.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create export dirs: {e}")

    # Copy selected per-bank rule YAMLs
    try:
        bank_rules_src = entities_dir / 'bank_rules'
        selected_bas: List[str] = [ (b or '').strip().lower() for b in (owner.get('bankaccounts') or []) ]
        for ba in selected_bas:
            if not ba:
                continue
            src = bank_rules_src / f"{ba}.yaml"
            dst = bank_rules_dest / f"{ba}.yaml"
            if src.exists() and src.is_file():
                shutil.copy2(src, dst)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed copying bank rule files: {e}")

    # Copy banks.yaml, classify_rules.yaml, common_rules.yaml to entities/
    try:
        for fname in ['banks.yaml', 'inherit_common_to_bank.yaml', 'common_rules.yaml']:
            src = entities_dir / fname
            if src.exists() and src.is_file():
                shutil.copy2(src, dest_root / fname)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed copying top-level YAMLs: {e}")

    # Filtered lists: companies.yaml, properties.yaml, bankaccounts.yaml
    def _load_yaml_list(path: Path) -> List[Dict[str, Any]]:
        try:
            with path.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or []
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_yaml_list(path: Path, rows: List[Dict[str, Any]]):
        try:
            with path.open('w', encoding='utf-8') as f:
                yaml.safe_dump(rows, f, sort_keys=True, allow_unicode=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed writing {path.name}: {e}")

    # companies.yaml
    try:
        comp_src = entities_dir / 'companies.yaml'
        all_comp = _load_yaml_list(comp_src)
        want = set([ (c or '').strip().lower() for c in (owner.get('companies') or []) ])
        filtered = []
        for rec in all_comp:
            if not isinstance(rec, dict):
                continue
            key = (str(rec.get('companyname') or '')).strip().lower()
            if key and key in want:
                filtered.append(rec)
        _save_yaml_list(dest_root / 'companies.yaml', filtered)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed filtering companies.yaml: {e}")

    # properties.yaml
    try:
        prop_src = entities_dir / 'properties.yaml'
        all_props = _load_yaml_list(prop_src)
        want = set([ (p or '').strip().lower() for p in (owner.get('properties') or []) ])
        filtered = []
        for rec in all_props:
            if not isinstance(rec, dict):
                continue
            key = (str(rec.get('property') or '')).strip().lower()
            if key and key in want:
                filtered.append(rec)
        _save_yaml_list(dest_root / 'properties.yaml', filtered)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed filtering properties.yaml: {e}")

    # bankaccounts.yaml
    try:
        ba_src = entities_dir / 'bankaccounts.yaml'
        all_bas = _load_yaml_list(ba_src)
        want = set([ (b or '').strip().lower() for b in (owner.get('bankaccounts') or []) ])
        filtered = []
        for rec in all_bas:
            if not isinstance(rec, dict):
                continue
            key = (str(rec.get('bankaccountname') or '')).strip().lower()
            if key and key in want:
                filtered.append(rec)
        _save_yaml_list(dest_root / 'bankaccounts.yaml', filtered)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed filtering bankaccounts.yaml: {e}")

    return {"status": "ok", "owner": name, "export_path": str(dest_root)}
