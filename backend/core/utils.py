from typing import Dict, List
import csv
from pathlib import Path
import yaml
from .db import ALNUM_UNDERSCORE_LOWER_RE


def dict_reader_ignoring_comments(f) -> csv.DictReader:
    lines = f.readlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if line.strip():
            header_idx = i
            break
    if header_idx == -1:
        return csv.DictReader([])
    header = lines[header_idx]
    data_lines = [ln for ln in lines[header_idx + 1 :] if ln.strip() and not ln.lstrip().startswith('#')]
    return csv.DictReader([header] + data_lines)


def normalize_row_keys(row: Dict[str, str]) -> Dict[str, str]:
    return {(k.strip().lstrip('#') if isinstance(k, str) else k): v for k, v in row.items()}


def get_any(row: Dict[str, str], keys: List[str]) -> str:
    for k in keys:
        if k in row:
            return row.get(k) or ""
    lower_map = {(str(k).lower() if isinstance(k, str) else k): k for k in row.keys()}
    for k in keys:
        lk = str(k).lower()
        if lk in lower_map:
            return row.get(lower_map[lk]) or ""
    return ""


def dump_yaml_entities(path: Path, entities: List[Dict], key_field: str) -> None:
    sorted_entities = sorted(entities, key=lambda x: x.get(key_field, ""))
    normalized = []
    for ent in sorted_entities:
        ent_copy = {}
        for k, v in ent.items():
            if isinstance(v, list):
                ent_copy[k] = sorted(v)
            else:
                ent_copy[k] = v
        normalized.append(ent_copy)
    with path.open('w', encoding='utf-8') as yf:
        yaml.safe_dump(normalized, yf, sort_keys=True, allow_unicode=True)
