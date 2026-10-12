from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .common import ROOT, PipelineError, init_stage, read_stage, stage_manifest, write_stage
from .ctet import parse_ctet
from .database import (
    rebuild_database,
    validate_stage,
    verify_database,
    write_data_quality_report,
)
from .exports import export_database
from .source_validation import validate_utet_sources
from .utet import parse_utet

DEFAULT_STAGE = ROOT / "build" / "xtet-stage.json"
DEFAULT_DB = ROOT / "data" / "xtet-question-bank.sqlite"
DEFAULT_REPORT = ROOT / "docs" / "DATA_QUALITY.md"


def parse_sources() -> dict[str, Any]:
    stage = init_stage()
    stage["diagnostics"]["ctet"] = parse_ctet(stage)
    stage["diagnostics"]["utet"] = parse_utet(stage)
    from .common import canonical_hash

    stage["meta"]["source_manifest_hash"] = canonical_hash(stage_manifest(stage))
    stage["diagnostics"]["stage_counts"] = validate_stage(stage, check_sources=True)
    return stage


def _json_print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m pipeline",
        description="Deterministic CTET/UTET parse, validate, SQLite build, verify, and report pipeline.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    parse_cmd = sub.add_parser("parse", help="Parse pinned sources into deterministic staging JSON.")
    parse_cmd.add_argument("--stage", type=Path, default=DEFAULT_STAGE)

    validate_cmd = sub.add_parser("validate", help="Re-validate staged records, source snapshots, and pipeline invariants.")
    validate_cmd.add_argument("--stage", type=Path, default=DEFAULT_STAGE)

    validate_sources_cmd = sub.add_parser("validate-sources", help="Run UTET Draft 2020-12 and data-count validation.")
    validate_sources_cmd.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    load_cmd = sub.add_parser("load", help="Load a validated stage into a fresh, atomic SQLite build.")
    load_cmd.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    load_cmd.add_argument("--db", type=Path, default=DEFAULT_DB)

    verify_cmd = sub.add_parser("verify", help="Run SQLite integrity, FK, FTS5, authority, and determinism checks.")
    verify_cmd.add_argument("--db", type=Path, default=DEFAULT_DB)

    report_cmd = sub.add_parser("report", help="Generate the checked-in data-quality report from a verified database.")
    report_cmd.add_argument("--db", type=Path, default=DEFAULT_DB)
    report_cmd.add_argument("--output", type=Path, default=DEFAULT_REPORT)

    export_cmd = sub.add_parser("export", help="Write deterministic, app-ready NDJSON exports from a verified database.")
    export_cmd.add_argument("--db", type=Path, default=DEFAULT_DB)
    export_cmd.add_argument("--output-dir", type=Path, default=ROOT / "build" / "exports")

    build_cmd = sub.add_parser("build", help="Run the full parse → validate → load → verify → report pipeline.")
    build_cmd.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    build_cmd.add_argument("--db", type=Path, default=DEFAULT_DB)
    build_cmd.add_argument("--report", type=Path, default=DEFAULT_REPORT)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate-sources":
            result = validate_utet_sources()
            if args.json:
                _json_print(result)
            else:
                print(
                    "UTET source validation passed: "
                    f"{result['schema_files_checked']} schemas, "
                    f"{sum(result['validated_records'].values())} data records, zero errors."
                )
            return 0

        if args.command == "parse":
            stage = parse_sources()
            write_stage(args.stage, stage)
            _json_print({"stage": str(args.stage), "source_manifest_hash": stage["meta"]["source_manifest_hash"], "counts": stage["diagnostics"]["stage_counts"]})
            return 0

        if args.command == "validate":
            stage = read_stage(args.stage)
            result = validate_stage(stage, check_sources=True)
            _json_print({"stage": str(args.stage), "status": "passed", "counts": result})
            return 0

        if args.command == "load":
            stage = read_stage(args.stage)
            result = rebuild_database(stage, args.db)
            _json_print(result)
            return 0

        if args.command == "verify":
            result = verify_database(args.db)
            _json_print({"database": str(args.db), **result})
            return 0

        if args.command == "report":
            result = verify_database(args.db)
            output = write_data_quality_report(args.db, args.output)
            _json_print({"report": str(output), "content_hash": result["content_hash"], "status": "written"})
            return 0

        if args.command == "export":
            result = export_database(args.db, args.output_dir)
            _json_print(result)
            return 0

        if args.command == "build":
            stage = parse_sources()
            write_stage(args.stage, stage)
            result = rebuild_database(stage, args.db)
            report_path = write_data_quality_report(args.db, args.report)
            _json_print(
                {
                    "stage": str(args.stage),
                    "report": str(report_path),
                    "status": "passed",
                    **result,
                }
            )
            return 0

        raise PipelineError(f"Unknown command: {args.command}")
    except (PipelineError, OSError, sqlite3.Error) as exc:  # type: ignore[name-defined]
        print(f"pipeline error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
