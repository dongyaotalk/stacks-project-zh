#!/usr/bin/env python3
"""Write a read-only source audit/coordinate proposal, never migrate facts.

Apply independently reviewed span corrections through immutable derivation
records. This tool does not write units, candidates, run manifests or approvals.
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
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        require_audit_output(args.root.resolve(), args.output)
        proposal, errors = audit_repository_source(args.root.resolve(), args.tags)
        proposal['diagnostics'] = errors
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, RecordError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'Wrote review proposal with {len(errors)} diagnostics: {args.output}')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
