#!/usr/bin/env python3
"""Write a separate public receipt; never overwrite a private capture or Git record."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stacks_zh.runtime_public_copies import project_runtime_copy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--input', type=Path, required=True)
parser.add_argument('--freeze', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.root.resolve()
source = args.input.resolve()
freeze = args.freeze.resolve()
output = args.output.resolve()
if not output.is_relative_to(root / 'build') or any(p.is_symlink() for p in args.output.parents):
    parser.error('public output must be a separate ordinary file under this root/build')
if args.input.is_symlink() or args.freeze.is_symlink() or source == args.output.resolve():
    parser.error('inputs must be ordinary files and output must be separate')
relative = source.relative_to(root).as_posix()
if not relative.startswith('docs/evidence/') or not relative.endswith('-runtime.json'):
    parser.error('input must be an exact runtime evidence copy')
head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'])
if subprocess.check_output(['git', '-C', str(root), 'log', '--format=%H', 'HEAD', '--', relative]).strip():
    parser.error('an execution capture already added to Git cannot be republished')
raw = source.read_bytes()
frozen_bytes = freeze.read_bytes()
frozen = json.loads(frozen_bytes)
if (relative != 'docs/evidence/' + frozen['adoption_id'] + '-runtime.json'
        or freeze.relative_to(root).as_posix() != 'translation-data/source-adoption-inputs/' + frozen['adoption_id'] + '.json'):
    parser.error('runtime and freeze paths differ from the actual adoption identity')
registry = subprocess.check_output(['git', '-C', str(root), 'show',
    frozen['origin_commit'] + ':config/harnesses.yml'])
result = project_runtime_copy(frozen, raw, registry)
if (source.read_bytes() != raw or freeze.read_bytes() != frozen_bytes
        or subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD']) != head):
    parser.error('input changed while projecting')
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open('x') as stream:
    stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
