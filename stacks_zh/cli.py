from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .constants import DEFAULT_LOCK_FILE, DEFAULT_RENDER_ROOT
from .decisions import validate_repository_decisions
from .extractor import extract_section, extract_tag
from .records import RecordError
from .provenance import ProvenanceError, validate_repository_provenance
from .schema_validation import validate_repository_schemas
from .tool_version import VERSION
from .upstream import validate_upstream_index
from .workflow import assemble_candidates, render_batch, stamp_units, validate_batch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and render structured Stacks Project Chinese candidates."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    stamp = subparsers.add_parser("stamp-units", help="calculate unit source hashes")
    stamp.add_argument("--input", required=True, type=Path)
    stamp.add_argument("--output", required=True, type=Path)

    extract = subparsers.add_parser(
        "extract-section",
        help="extract one unlabelled Section from the locked English harvest",
    )
    extract.add_argument("--harvest", required=True, type=Path)
    extract.add_argument("--chapter", required=True)
    extract.add_argument("--tag", required=True)
    extract.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)
    extract.add_argument("--output", required=True, type=Path)

    extract_any = subparsers.add_parser(
        "extract-tag",
        help="extract one supported permanent-Tag scope from the locked English harvest",
    )
    extract_any.add_argument("--harvest", required=True, type=Path)
    extract_any.add_argument("--chapter", required=True)
    extract_any.add_argument("--tag", required=True)
    extract_any.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)
    extract_any.add_argument("--output", required=True, type=Path)

    validate = subparsers.add_parser("validate", help="run deterministic candidate QA")
    validate.add_argument("--units", required=True, type=Path)
    validate.add_argument("--candidates", required=True, type=Path)
    validate.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)

    assemble = subparsers.add_parser(
        "assemble", help="attach provenance and deterministic status to translator output"
    )
    assemble.add_argument("--units", required=True, type=Path)
    assemble.add_argument("--drafts", required=True, type=Path)
    assemble.add_argument("--output", required=True, type=Path)
    assemble.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)
    assemble.add_argument("--model-id", required=True)
    assemble.add_argument("--model-lane", required=True)
    assemble.add_argument("--reasoning-effort", required=True)
    assemble.add_argument("--prompt-version", required=True)
    assemble.add_argument("--policy-revision", required=True)
    assemble.add_argument("--glossary-revision", required=True)
    assemble.add_argument("--created-at", required=True)
    assemble.add_argument("--harness-id", required=True)
    assemble.add_argument("--harness-version", required=True)
    assemble.add_argument("--model-record-id", required=True)
    assemble.add_argument("--run-id", required=True)
    assemble.add_argument("--model-snapshot")
    assemble.add_argument(
        "--model-identity-confidence",
        required=True,
        choices=["runtime-resolved", "owner-confirmed", "declared", "unknown"],
    )

    render = subparsers.add_parser("render", help="generate an ignored LaTeX preview directory")
    render.add_argument("--units", required=True, type=Path, nargs="+")
    render.add_argument("--candidates", required=True, type=Path, nargs="+")
    render.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)
    render.add_argument("--model-lane", required=True)
    render.add_argument("--display-name", required=True)
    render.add_argument("--chapter-manifest", type=Path)
    render.add_argument("--chapter-source-dir", type=Path)
    render.add_argument("--tags-file", type=Path)
    render.add_argument("--output-dir", type=Path)

    provenance = subparsers.add_parser(
        "provenance-check", help="verify candidates against immutable run manifests"
    )
    provenance.add_argument("--root", type=Path, default=Path("."))
    decisions = subparsers.add_parser(
        "decision-check", help="verify selections, human reviews and formal revisions"
    )
    decisions.add_argument("--root", type=Path, default=Path("."))
    schemas = subparsers.add_parser(
        "schema-check", help="validate every structured record against its JSON Schema"
    )
    schemas.add_argument("--root", type=Path, default=Path("."))
    upstream_index = subparsers.add_parser(
        "upstream-index-check", help="verify the locked Tag/chapter index and sync history"
    )
    upstream_index.add_argument("--root", type=Path, default=Path("."))
    upstream_index.add_argument("--harvest", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "stamp-units":
            count = stamp_units(args.input, args.output)
            print(f"Stamped {count} unit record(s): {args.output}")
            return 0
        if args.command == "extract-section":
            count = extract_section(
                args.harvest.resolve(),
                args.chapter,
                args.tag,
                args.lock.resolve(),
                args.output,
            )
            print(f"Extracted {count} unit record(s): {args.output}")
            return 0
        if args.command == "extract-tag":
            count = extract_tag(
                args.harvest.resolve(),
                args.chapter,
                args.tag,
                args.lock.resolve(),
                args.output,
            )
            print(f"Extracted {count} unit record(s): {args.output}")
            return 0
        if args.command == "validate":
            count, errors = validate_batch(args.units, args.candidates, args.lock)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"Candidate QA: PASS ({count} unit(s))")
            return 0
        if args.command == "assemble":
            count = assemble_candidates(
                args.units,
                args.drafts,
                args.output,
                args.lock,
                args.model_id,
                args.model_lane,
                args.reasoning_effort,
                args.prompt_version,
                args.policy_revision,
                args.glossary_revision,
                args.created_at,
                args.harness_id,
                args.harness_version,
                args.model_record_id,
                args.run_id,
                args.model_snapshot,
                args.model_identity_confidence,
            )
            print(f"Assembled {count} candidate record(s): {args.output}")
            return 0
        if args.command == "render":
            output_dir = args.output_dir or DEFAULT_RENDER_ROOT / args.model_lane
            written = render_batch(
                args.units,
                args.candidates,
                args.lock,
                output_dir,
                args.model_lane,
                args.display_name,
                args.chapter_manifest,
                args.tags_file,
                args.chapter_source_dir,
            )
            print(f"Rendered {len(written)} file(s): {output_dir}")
            return 0
        if args.command == "provenance-check":
            errors = validate_repository_provenance(args.root.resolve())
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("Model provenance: PASS")
            return 0
        if args.command == "decision-check":
            errors = validate_repository_decisions(args.root.resolve())
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("Selection and revision linkage: PASS")
            return 0
        if args.command == "schema-check":
            errors = validate_repository_schemas(args.root.resolve())
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("Repository JSON Schema: PASS")
            return 0
        if args.command == "upstream-index-check":
            errors = validate_upstream_index(args.root.resolve(), args.harvest.resolve())
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("Upstream index and history: PASS")
            return 0
    except (RecordError, ProvenanceError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    parser.error("unknown command")
    return 2
