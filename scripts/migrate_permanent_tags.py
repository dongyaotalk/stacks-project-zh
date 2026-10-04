#!/usr/bin/env python3
"""Produce a permanent-Tag proposal without rewriting historical run manifests.

The earlier in-place migration is retired. Use an Issue-scoped immutable
candidate derivation to apply this mapping after QA and local acceptance.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stacks_zh.records import RecordError
from stacks_zh.source_integrity import audit_repository_source, require_audit_output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--tags', type=Path, required=True)
    parser.add_argument('--map', dest='map_path', type=Path, required=True)
    args = parser.parse_args()
    try:
        require_audit_output(args.root.resolve(), args.map_path)
        proposal, errors = audit_repository_source(args.root.resolve(), args.tags)
        mapping = {old: new for batch in proposal['coordinate_proposals']
                   for old, new in batch['unit_id_map'].items() if old != new}
        report = {'schema_version': 1, 'migration_kind': 'permanent-tag-proposal',
                  'source_commit': proposal['source_commit'], 'mapping': mapping,
                  'count': len(mapping), 'diagnostics': errors,
                  'policy': 'Read-only proposal; apply via immutable derivations. Original runs are never modified.'}
        args.map_path.parent.mkdir(parents=True, exist_ok=True)
        args.map_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, RecordError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'Permanent Tag proposal: {len(mapping)} mapping(s); no facts changed')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
