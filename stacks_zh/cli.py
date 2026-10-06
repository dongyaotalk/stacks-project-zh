from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .batching import write_batch_package
from .build_logs import validate_final_tex_log
from .chapter_templates import initialize_chapter_templates
from .constants import DEFAULT_LOCK_FILE, DEFAULT_RENDER_ROOT
from .decisions import validate_repository_decisions
from .harness import resolve_harness
from .planning import (
    build_translation_plan,
    render_task_selection,
    render_task_selection_json,
    select_next_task,
    update_translation_plan,
)
from .progress import update_progress_report
from .records import RecordError
from .extraction import write_inventory
from .source_alignment import write_alignment
from .source_containers import write_container_package
from .source_integrity import audit_repository_source, require_audit_output
from .source_terms import audit_repository_terms
from .source_reextractions import audit_repository_proofs
from .provenance import ProvenanceError, validate_repository_provenance
from .schema_validation import validate_repository_schemas
from .tool_version import VERSION
from .upstream import validate_upstream_index
from .workflow import (
    assemble_candidates,
    assemble_candidates_many,
    render_batch,
    stamp_units,
    validate_batch,
    validate_batches,
)


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
        "extract-all", help="inventory all locked English chapters without adopting data"
    )
    extract.add_argument("--root", type=Path, default=Path("."))
    extract.add_argument("--harvest", required=True, type=Path)
    extract.add_argument("--output", type=Path, default=Path("source-ir/extraction"))
    extract.add_argument("--chapter", action="append")
    extract.add_argument("--check", action="store_true")
    extract.add_argument("--require-ready", action="store_true")

    alignment = subparsers.add_parser(
        "source-alignment", help="align current units with locked source and prepare a repair queue"
    )
    alignment.add_argument("--root", type=Path, default=Path("."))
    alignment.add_argument("--harvest", required=True, type=Path)
    alignment.add_argument("--inventory", type=Path, default=Path("source-ir/extraction"))
    alignment.add_argument("--output", type=Path, default=Path("build/source-alignment"))
    alignment.add_argument("--check", action="store_true")

    containers = subparsers.add_parser('prepare-source-containers',
        help='prepare complete locked-Git containers and full old/new groups without adopting facts')
    containers.add_argument('--root', type=Path, default=Path('.'))
    containers.add_argument('--harvest', required=True, type=Path)
    containers.add_argument('--plan', required=True, type=Path)
    containers.add_argument('--output', type=Path, default=Path('build/source-containers'))
    containers.add_argument('--check', action='store_true')
    containers.add_argument('--require-prepared', action='store_true')

    init_chapters = subparsers.add_parser(
        "init-chapters",
        help="initialize deterministic task scaffolds for every locked chapter",
    )
    init_chapters.add_argument("--root", type=Path, default=Path("."))
    init_chapters.add_argument("--harvest", required=True, type=Path)
    init_chapters.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)
    init_chapters.add_argument(
        "--units-dir", type=Path, default=Path("translation-data/units")
    )
    init_chapters.add_argument(
        "--output-dir",
        type=Path,
        default=Path("translation-data/chapter-templates"),
    )
    init_chapters.add_argument("--check", action="store_true")

    validate = subparsers.add_parser("validate", help="run deterministic candidate QA")
    validate.add_argument("--units", required=True, type=Path)
    validate.add_argument("--candidates", required=True, type=Path)
    validate.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)

    validate_many = subparsers.add_parser(
        "validate-many",
        help="run deterministic candidate QA for several batches in one process",
    )
    validate_many.add_argument("--units", required=True, type=Path, nargs="+")
    validate_many.add_argument("--candidates", required=True, type=Path, nargs="+")
    validate_many.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)

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
    assemble.add_argument(
        "--harness-version",
        default="auto",
        choices=["auto"],
        help="observed version, or auto to execute the registered command (default)",
    )
    assemble.add_argument(
        "--harness-config", type=Path, default=Path("config/harnesses.yml")
    )
    assemble.add_argument("--model-record-id", required=True)
    assemble.add_argument("--run-id", required=True)
    assemble.add_argument("--model-snapshot")
    assemble.add_argument(
        "--model-identity-confidence",
        required=True,
        choices=["runtime-resolved", "owner-confirmed", "declared", "unknown"],
    )

    assemble_many = subparsers.add_parser(
        "assemble-many",
        help="split one combined translator JSONL into independent candidate files",
    )
    assemble_many.add_argument("--units", required=True, type=Path, nargs="+")
    assemble_many.add_argument("--drafts", required=True, type=Path)
    assemble_many.add_argument("--output", required=True, type=Path, nargs="+")
    assemble_many.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)
    assemble_many.add_argument("--model-id", required=True)
    assemble_many.add_argument("--model-lane", required=True)
    assemble_many.add_argument("--reasoning-effort", required=True)
    assemble_many.add_argument("--prompt-version", required=True)
    assemble_many.add_argument("--policy-revision", required=True)
    assemble_many.add_argument("--glossary-revision", required=True)
    assemble_many.add_argument("--created-at", required=True)
    assemble_many.add_argument("--harness-id", required=True)
    assemble_many.add_argument(
        "--harness-version",
        default="auto",
        choices=["auto"],
        help="resolve the registered Harness version once (default: auto)",
    )
    assemble_many.add_argument(
        "--harness-config", type=Path, default=Path("config/harnesses.yml")
    )
    assemble_many.add_argument("--model-record-id", required=True)
    assemble_many.add_argument("--run-id", required=True)
    assemble_many.add_argument("--model-snapshot")
    assemble_many.add_argument(
        "--model-identity-confidence",
        required=True,
        choices=["runtime-resolved", "owner-confirmed", "declared", "unknown"],
    )

    batch_pack = subparsers.add_parser(
        "batch-pack",
        help="package adjacent unit files for one structured model request",
    )
    batch_pack.add_argument("--units", required=True, type=Path, nargs="+")
    batch_pack.add_argument("--output", required=True, type=Path)
    batch_pack.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)
    batch_pack.add_argument(
        "--prompt", type=Path, default=Path("prompts/translator-v2.md")
    )
    batch_pack.add_argument(
        "--style-guide", type=Path, default=Path("config/style-guide.md")
    )
    batch_pack.add_argument(
        "--workflow-config", type=Path, default=Path("config/workflow.yml")
    )
    batch_pack.add_argument(
        "--chapter-templates",
        type=Path,
        default=Path("translation-data/chapter-templates"),
        help="chapter template directory used to enforce adjacent Section order",
    )
    batch_pack.add_argument(
        "--allow-outside-preferred-range",
        action="store_true",
        help="allow an indivisible scope outside the preferred source-word range",
    )

    render = subparsers.add_parser("render", help="generate an ignored LaTeX preview directory")
    render.add_argument("--units", required=True, type=Path, nargs="+")
    render.add_argument("--candidates", required=True, type=Path, nargs="+")
    render.add_argument("--lock", type=Path, default=DEFAULT_LOCK_FILE)
    render.add_argument("--model-lane", required=True)
    render.add_argument("--display-name", required=True)
    render.add_argument("--chapter-manifest", type=Path)
    render.add_argument("--chapter-title-map", type=Path)
    render.add_argument("--chapter-source-dir", type=Path)
    render.add_argument("--tags-file", type=Path)
    render.add_argument("--output-dir", type=Path)

    build_log = subparsers.add_parser("check-build-log", help="reject defects in a completed final TeX log")
    build_log.add_argument("--log", required=True, type=Path)

    source_audit = subparsers.add_parser("audit-source", help="audit statement Tags, TeX controls and hidden footnotes")
    source_audit.add_argument("--root", type=Path, default=Path("."))
    source_audit.add_argument("--tags", required=True, type=Path)
    source_audit.add_argument("--output", type=Path)

    proof_audit = subparsers.add_parser("audit-proof-source", help="compare all current proof groups with locked English Git objects")
    proof_audit.add_argument("--root", type=Path, default=Path("."))
    proof_audit.add_argument("--harvest", type=Path)
    proof_audit.add_argument("--output", type=Path)

    term_audit = subparsers.add_parser("audit-terms", help="independently audit English source term coverage")
    term_audit.add_argument("--root", type=Path, default=Path("."))
    term_audit.add_argument("--output", type=Path)

    provenance = subparsers.add_parser(
        "provenance-check", help="verify candidates against immutable run manifests"
    )
    provenance.add_argument("--root", type=Path, default=Path("."))
    provenance.add_argument("--harvest", type=Path)
    decisions = subparsers.add_parser(
        "decision-check", help="verify selections, human reviews and formal revisions"
    )
    decisions.add_argument("--root", type=Path, default=Path("."))
    decisions.add_argument("--harvest", type=Path)
    schemas = subparsers.add_parser(
        "schema-check", help="validate every structured record against its JSON Schema"
    )
    schemas.add_argument("--root", type=Path, default=Path("."))
    upstream_index = subparsers.add_parser(
        "upstream-index-check", help="verify the locked Tag/chapter index and sync history"
    )
    upstream_index.add_argument("--root", type=Path, default=Path("."))
    upstream_index.add_argument("--harvest", required=True, type=Path)

    progress = subparsers.add_parser(
        "progress", help="generate or check the README and per-chapter progress report"
    )
    progress.add_argument("--root", type=Path, default=Path("."))
    progress.add_argument("--tags", required=True, type=Path)
    progress.add_argument("--readme", type=Path, default=Path("README.md"))
    progress.add_argument(
        "--output", type=Path, default=Path("docs/translation-progress.md")
    )
    progress.add_argument("--check", action="store_true")

    plan = subparsers.add_parser(
        "plan", help="generate or check the priority-aware translation plan"
    )
    plan.add_argument("--root", type=Path, default=Path("."))
    plan.add_argument(
        "--priorities",
        type=Path,
        default=Path("config/translation-priorities.json"),
    )
    plan.add_argument("--readme", type=Path, default=Path("README.md"))
    plan.add_argument(
        "--output", type=Path, default=Path("docs/translation-plan.md")
    )
    plan.add_argument("--check", action="store_true")

    next_task = subparsers.add_parser(
        "next-task",
        help="select the next workflow action using an explicit scope or project priority",
    )
    next_task.add_argument("--root", type=Path, default=Path("."))
    next_task.add_argument(
        "--priorities",
        type=Path,
        default=Path("config/translation-priorities.json"),
    )
    next_task.add_argument(
        "--chapter", help="chapter slug or one-based chapter ordinal"
    )
    next_task.add_argument("--tag", help="parent permanent Tag within --chapter")
    next_task.add_argument(
        "--fallback",
        action="store_true",
        help="fall back to automatic selection when the explicit scope is complete",
    )
    next_task.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    harness_version = subparsers.add_parser(
        "harness-version", help="resolve a Harness version from its configured executable"
    )
    harness_version.add_argument("--harness-id", required=True)
    harness_version.add_argument(
        "--config", type=Path, default=Path("config/harnesses.yml")
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "stamp-units":
            count = stamp_units(args.input, args.output)
            print(f"Stamped {count} unit record(s): {args.output}")
            return 0
        if args.command == "extract-all":
            root = args.root.resolve()
            output = args.output if args.output.is_absolute() else root / args.output
            inventory = write_inventory(root, args.harvest.resolve(), output,
                                        chapters=args.chapter, check=args.check)
            print(f"Source inventory: {inventory['chapter_count']} chapters; "
                  f"{inventory['roundtrip_files']} byte-exact Git roundtrips; "
                  f"{inventory['unit_count']} proposed units "
                  f"(READY {inventory['ready']}, BLOCKED {inventory['blocked']}); "
                  f"{inventory['diagnostic_count']} diagnostics. Adopted: false.")
            if args.require_ready and not inventory['translation_ready']:
                print("ERROR: source inventory still contains blockers or unavailable chapters", file=sys.stderr)
                return 1
            return 0
        if args.command == "source-alignment":
            root = args.root.resolve()
            inventory = args.inventory if args.inventory.is_absolute() else root / args.inventory
            output = args.output if args.output.is_absolute() else root / args.output
            report = write_alignment(root, args.harvest.resolve(), inventory, output, check=args.check)
            print(f"Source alignment: {report['unit_count']} current units in {report['batch_count']} batches; "
                  f"{json.dumps(report['match_counts'], sort_keys=True)}; "
                  f"{report['term_candidate_failures']} term candidate failures; "
                  f"{report['proof_mismatches']} proof mismatches. Adopted: false. Repairs complete: false.")
            return 0
        if args.command == 'prepare-source-containers':
            root = args.root.resolve()
            plan = args.plan if args.plan.is_absolute() else root / args.plan
            output = args.output if args.output.is_absolute() else root / args.output
            report = write_container_package(root, args.harvest.resolve(), plan, output, check=args.check)
            print(f"Source containers: {report['input_unit_count']} full-batch inputs; "
                  f"{report['proposed_output_unit_count']} proposed outputs; {report['group_count']} groups; "
                  f"{report['blocked_group_count']} blocked; state={report['state']}. Adopted: false.")
            return 1 if args.require_prepared and report['state'] != 'PREPARED' else 0
        if args.command == "init-chapters":
            root = args.root.resolve()
            lock_path = args.lock if args.lock.is_absolute() else root / args.lock
            units_dir = (
                args.units_dir if args.units_dir.is_absolute() else root / args.units_dir
            )
            output_dir = (
                args.output_dir
                if args.output_dir.is_absolute()
                else root / args.output_dir
            )
            count, errors = initialize_chapter_templates(
                root,
                args.harvest.resolve(),
                lock_path,
                units_dir,
                output_dir,
                check=args.check,
            )
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            action = "Checked" if args.check else "Initialized"
            print(f"{action} {count} chapter template(s): {output_dir}")
            return 0
        if args.command == "validate":
            count, errors = validate_batch(args.units, args.candidates, args.lock)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(f"Candidate QA: PASS ({count} unit(s))")
            return 0
        if args.command == "validate-many":
            count, errors = validate_batches(args.units, args.candidates, args.lock)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print(
                "Candidate batch QA: PASS "
                f"({count} unit(s) across {len(args.units)} batch(es))"
            )
            return 0
        if args.command == "assemble":
            harness_config = (
                args.harness_config
                if args.harness_config.is_absolute()
                else Path.cwd() / args.harness_config
            )
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
                harness_config_path=harness_config,
            )
            print(f"Assembled {count} candidate record(s): {args.output}")
            return 0
        if args.command == "assemble-many":
            harness_config = (
                args.harness_config
                if args.harness_config.is_absolute()
                else Path.cwd() / args.harness_config
            )
            count = assemble_candidates_many(
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
                harness_config_path=harness_config,
            )
            print(
                f"Assembled {count} candidate record(s) across "
                f"{len(args.output)} batch(es)"
            )
            return 0
        if args.command == "batch-pack":
            summary = write_batch_package(
                args.units,
                args.output,
                args.lock,
                args.prompt,
                args.style_guide,
                args.workflow_config,
                allow_outside_preferred_range=args.allow_outside_preferred_range,
                chapter_templates_path=args.chapter_templates,
            )
            print(
                f"Packed {summary.unit_count} unit(s) across {summary.batch_count} "
                f"batch(es), {summary.source_word_count} source word(s): {summary.output_path}"
            )
            return 0
        if args.command == "harness-version":
            config_path = args.config if args.config.is_absolute() else Path.cwd() / args.config
            resolution = resolve_harness(args.harness_id, config_path)
            print(f"{resolution.harness_id}: {resolution.version}")
            print(f"command: {' '.join(resolution.command)}")
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
                args.chapter_title_map,
            )
            print(f"Rendered {len(written)} file(s): {output_dir}")
            return 0
        if args.command == "check-build-log":
            errors = validate_final_tex_log(args.log)
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            if errors:
                return 1
            print(f"Final TeX log: PASS ({args.log})")
            return 0
        if args.command == "audit-source":
            proposal, errors = audit_repository_source(args.root.resolve(), args.tags)
            if args.output:
                require_audit_output(args.root.resolve(), args.output)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"Source integrity: {len(errors)} issue(s); {proposal['wrong_statement_tags']} statement Tag mismatches, {proposal['unprotected_node_pairs']} raw TeX pairs, {proposal['hidden_footnotes']} hidden footnotes, {proposal['hidden_environment_titles']} hidden/invalid named titles")
            return 1 if errors else 0
        if args.command == "audit-terms":
            report, errors = audit_repository_terms(args.root.resolve())
            if args.output:
                require_audit_output(args.root.resolve(), args.output)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"Source terminology: {len(errors)} issue(s); {report['required_occurrences']} required occurrence(s) in {report['unit_count']} unit(s), {report['batch_count']} batch(es)")
            return 1 if errors else 0
        if args.command == "audit-proof-source":
            report, errors = audit_repository_proofs(args.root.resolve(), args.harvest)
            if args.output:
                require_audit_output(args.root.resolve(), args.output)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"Proof source: {report['proof_group_count']} groups, {report['proof_unit_count']} units; "
                  f"{report['matched']} matched, {report['mismatched']} mismatched, {report['unsupported']} unable to verify")
            return 1 if errors else 0
        if args.command == "provenance-check":
            errors = validate_repository_provenance(args.root.resolve(), args.harvest)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("Model provenance: PASS")
            return 0
        if args.command == "decision-check":
            errors = validate_repository_decisions(args.root.resolve(), args.harvest)
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
        if args.command == "progress":
            root = args.root.resolve()
            tags_path = args.tags if args.tags.is_absolute() else root / args.tags
            readme_path = args.readme if args.readme.is_absolute() else root / args.readme
            output_path = args.output if args.output.is_absolute() else root / args.output
            count, errors = update_progress_report(
                root,
                tags_path,
                readme_path,
                output_path,
                check=args.check,
            )
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            action = "Checked" if args.check else "Updated"
            print(f"{action} translation progress for {count} chapter(s)")
            return 0
        if args.command == "plan":
            root = args.root.resolve()
            priority_path = (
                args.priorities
                if args.priorities.is_absolute()
                else root / args.priorities
            )
            readme_path = args.readme if args.readme.is_absolute() else root / args.readme
            output_path = args.output if args.output.is_absolute() else root / args.output
            count, errors = update_translation_plan(
                root,
                readme_path,
                output_path,
                priority_path=priority_path,
                check=args.check,
            )
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            action = "Checked" if args.check else "Updated"
            print(f"{action} priority-aware translation plan for {count} chapter(s)")
            return 0
        if args.command == "next-task":
            root = args.root.resolve()
            priority_path = (
                args.priorities
                if args.priorities.is_absolute()
                else root / args.priorities
            )
            plan = build_translation_plan(root, priority_path)
            selection = select_next_task(
                plan,
                chapter=args.chapter,
                tag=args.tag,
                fallback=args.fallback,
            )
            if args.json:
                print(render_task_selection_json(selection), end="")
            else:
                print(render_task_selection(selection))
            return 0
    except (RecordError, ProvenanceError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    parser.error("unknown command")
    return 2
