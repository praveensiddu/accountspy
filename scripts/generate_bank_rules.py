#!/usr/bin/env python3
"""
One-time utility to generate per-bank rule files by merging:
- inherit_common_to_bank.yaml (five fields)
- common_rules.yaml (transaction_type, pattern_match_logic)
- classify_rules.yaml (explicit bank rules)

Algorithm:
1) For each inherit rule I and each common rule C, create a merged rule R with:
   bankaccountname=I.bankaccountname
   transaction_type=C.transaction_type
   pattern_match_logic=normalized(C.pattern_match_logic)
   tax_category=I.tax_category
   property=I.property
   group=I.group
   otherentity=I.otherentity
   Add to merged_common_rules set (by composite key).
2) For each rule in classify_rules.yaml, if its composite key exists in merged_common_rules, skip; else include.
3) Output per bank files under bank_rules/<bankaccountname>.yaml as the union:
   merged_common_rules ∪ extra_classify_rules (merged rules take precedence), sorted deterministically.

Usage:
  python scripts/generate_bank_rules.py --entities-dir /path/to/entities
If --entities-dir is omitted, ENTITIES_DIR env var is used.
"""
import argparse
import os
from pathlib import Path
import sys
import yaml
from typing import Dict, List, Any, Tuple


def _normalize_str(s: str) -> str:
    return (s or '').strip().lower()


def _normalize_pattern(s: str) -> str:
    # Collapse internal whitespace and lowercase
    s = (s or '').strip()
    return ' '.join(s.split()).lower()


def _key(rec: Dict[str, Any]) -> str:
    return '|'.join([
        _normalize_str(rec.get('bankaccountname')),
        _normalize_str(rec.get('transaction_type')),
        _normalize_str(rec.get('property')),
        _normalize_str(rec.get('group')),
        _normalize_pattern(rec.get('pattern_match_logic')),
        _normalize_str(rec.get('tax_category')),
        (rec.get('otherentity') or '').strip(),  # case-sensitive keep as-is per existing data
    ])


def _read_yaml_list(path: Path) -> List[Dict[str, Any]]:
    if not path or not path.exists():
        return []
    with path.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or []
    if not isinstance(data, list):
        return []
    # ensure items are dicts
    return [x for x in data if isinstance(x, dict)]


def _write_yaml_list(path: Path, items: List[Dict[str, Any]]) -> None:
    # sort by bankaccountname, then transaction_type, then property, group, pattern, tax, other
    def sort_key(x: Dict[str, Any]) -> Tuple:
        return (
            _normalize_str(x.get('bankaccountname')),
            _normalize_str(x.get('transaction_type')),
            _normalize_str(x.get('property')),
            _normalize_str(x.get('group')),
            _normalize_pattern(x.get('pattern_match_logic')),
            _normalize_str(x.get('tax_category')),
            (x.get('otherentity') or ''),
        )
    items_sorted = sorted(items, key=sort_key)
    with path.open('w', encoding='utf-8') as f:
        yaml.safe_dump(items_sorted, f, sort_keys=True, allow_unicode=True)


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate bank_rules.yaml by merging inherit and common rules with classify overrides')
    parser.add_argument('--entities-dir', dest='entities_dir', default=os.getenv('ENTITIES_DIR', ''), help='Path to ENTITIES_DIR containing YAML files')
    args = parser.parse_args()

    if not args.entities_dir:
        print('Error: --entities-dir not provided and ENTITIES_DIR is not set', file=sys.stderr)
        return 2
    entities_dir = Path(args.entities_dir).expanduser().resolve()
    if not entities_dir.exists() or not entities_dir.is_dir():
        print(f'Error: entities dir not found: {entities_dir}', file=sys.stderr)
        return 2

    inherit_path = entities_dir / 'inherit_common_to_bank.yaml'
    common_path = entities_dir / 'common_rules.yaml'
    classify_yaml_path = entities_dir / 'classify_rules.yaml'
    out_dir = entities_dir / 'bank_rules'

    inherit_rules = _read_yaml_list(inherit_path)
    common_rules = _read_yaml_list(common_path)
    classify_rules = _read_yaml_list(classify_yaml_path)

    merged_map: Dict[str, Dict[str, Any]] = {}

    # Build merged common rules for each inherit x common
    for inh in inherit_rules:
        bank = _normalize_str(inh.get('bankaccountname'))
        tax = _normalize_str(inh.get('tax_category'))
        prop = _normalize_str(inh.get('property'))
        group = _normalize_str(inh.get('group'))
        other = (inh.get('otherentity') or '').strip()
        if not bank:
            continue
        for com in common_rules:
            ttype = _normalize_str(com.get('transaction_type'))
            patt = _normalize_pattern(com.get('pattern_match_logic'))
            if not (ttype and patt):
                continue
            rec = {
                'bankaccountname': bank,
                'transaction_type': ttype,
                'pattern_match_logic': patt,
                'tax_category': tax,
                'property': prop,
                'group': group,
                'otherentity': other,
            }
            merged_map[_key(rec)] = rec

    print(f' {len(merged_map)} merged common rules')
    print(f' {len(classify_rules)} classify_rules rules')
    # Now include classify rules that don't collide with merged
    final_map: Dict[str, Dict[str, Any]] = dict()
    for cr in classify_rules:
        rec = {
            'order': 10000,
            'bankaccountname': _normalize_str(cr.get('bankaccountname')),
            'transaction_type': _normalize_str(cr.get('transaction_type')),
            'pattern_match_logic': _normalize_pattern(cr.get('pattern_match_logic')),
            'tax_category': _normalize_str(cr.get('tax_category')),
            'property': _normalize_str(cr.get('property')),
            'group': _normalize_str(cr.get('group')),
            'otherentity': (cr.get('otherentity') or '').strip(),
        }
        if not rec['bankaccountname'] or not rec['transaction_type'] or not rec['pattern_match_logic']:
            # Skip incomplete classify entries
            continue
        k = _key(rec)
        if k in merged_map or k in final_map:
            # classify rule already covered by merged common rules or already added; skip
            continue
        final_map[k] = rec

    # Union: include merged common rules and classify extras for output
    union_map: Dict[str, Dict[str, Any]] = dict(merged_map)
    # Only extras remain in final_map; merged_map takes precedence by construction
    union_map.update(final_map)

    # Group by bankaccountname and write under bank_rules/<bank>.yaml
    out_dir.mkdir(parents=True, exist_ok=True)
    per_bank: Dict[str, List[Dict[str, Any]]] = {}
    for rec in union_map.values():
        bank = _normalize_str(rec.get('bankaccountname'))
        if not bank:
            continue
        per_bank.setdefault(bank, []).append(rec)

    total_rules = 0
    for bank, items in sorted(per_bank.items()):
        bank_file = out_dir / f'{bank}.yaml'
        _write_yaml_list(bank_file, items)
        print(f'Wrote {len(items)} rules -> {bank_file}')
        total_rules += len(items)

    print(f'Total banks: {len(per_bank)}, total rules: {total_rules}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
