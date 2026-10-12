from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IMPORTER_VERSION = "1.0.0"

TABLES = (
    "source_files",
    "source_records",
    "source_record_assertions",
    "exams",
    "exam_sessions",
    "sections",
    "blueprint_versions",
    "blueprint_selection_groups",
    "blueprint_sections",
    "blueprint_section_locales",
    "blueprint_selection_members",
    "blueprint_rules",
    "paper_forms",
    "paper_form_blueprints",
    "paper_form_sections",
    "question_types",
    "questions",
    "question_contents",
    "question_options",
    "option_contents",
    "question_appearances",
    "question_source_tags",
    "question_source_audits",
    "stimuli",
    "stimulus_contents",
    "stimulus_question_links",
    "stimulus_review_records",
    "answer_key_versions",
    "answer_key_tables",
    "answer_key_entries",
    "answer_key_entry_options",
    "explanations",
    "assets",
    "asset_locales",
    "question_assets",
    "option_assets",
    "stimulus_assets",
    "explanation_assets",
    "taxonomy_schemes",
    "taxonomy_nodes",
    "question_taxonomy_assignments",
    "question_assessments",
    "question_review_records",
    "appearance_review_records",
    "form_review_records",
    "answer_key_review_records",
    "question_search_documents",
)


class PipelineError(RuntimeError):
    """A source-aware, user-facing pipeline error."""


class SourceError(PipelineError):
    def __init__(self, path: str | Path, line: int | None, detail: str):
        self.path = str(path)
        self.line = line
        self.detail = detail
        location = self.path if line is None else f"{self.path}:{line}"
        super().__init__(f"{location}: {detail}")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_hash(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def slug(value: str) -> str:
    text = value.lower().replace("&", "-and-")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "item"


def stable_id(prefix: str, *parts: object, size: int = 24) -> str:
    material = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(material).hexdigest()[:size]}"


def init_stage() -> dict[str, Any]:
    return {
        "stage_version": 1,
        "meta": {},
        "rows": {table: [] for table in TABLES},
        "diagnostics": {},
    }


def add_row(stage: dict[str, Any], table: str, row: dict[str, Any]) -> None:
    if table not in stage["rows"]:
        raise PipelineError(f"Unknown staging table {table!r}")
    stage["rows"][table].append(row)


def lines_with_endings(text: str) -> list[str]:
    """Return source lines without normalizing CRLF/LF or final-newline state."""
    if not text:
        return []
    return text.splitlines(keepends=True)


def line_body(line: str) -> str:
    return line.rstrip("\r\n")


def add_source_file(
    stage: dict[str, Any],
    path: Path,
    *,
    source_root: Path = ROOT,
    source_uri: str | None = None,
    upstream_repo: str | None = None,
    upstream_commit: str | None = None,
    license_id: str | None = None,
    attribution: str | None = None,
) -> tuple[str, bytes, str]:
    path = path.resolve()
    try:
        rel = path.relative_to(source_root.resolve()).as_posix()
    except ValueError as exc:
        raise PipelineError(f"Source file is outside the repository root: {path}") from exc
    data = path.read_bytes()
    digest = sha256_bytes(data)
    file_id = stable_id("sf", rel, size=24)
    media_type = "application/x-ndjson" if path.suffix == ".ndjson" else "text/plain"
    if path.suffix == ".json":
        media_type = "application/json"
    if path.suffix == ".md":
        media_type = "text/markdown"
    if path.suffix == ".txt":
        media_type = "text/plain; charset=utf-8"
    if path.suffix == ".sql":
        media_type = "application/sql"
    file_row = {
        "source_file_id": file_id,
        "relative_path": rel,
        "source_uri": source_uri,
        "upstream_repo": upstream_repo,
        "upstream_commit": upstream_commit,
        "media_type": media_type,
        "byte_size": len(data),
        "sha256": digest,
        "license_id": license_id,
        "attribution": attribution,
    }
    existing = next((r for r in stage["rows"]["source_files"] if r["source_file_id"] == file_id), None)
    if existing is None:
        add_row(stage, "source_files", file_row)
    elif existing != file_row:
        raise PipelineError(f"Conflicting metadata for source file {rel}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        line = data[: exc.start].count(b"\n") + 1
        raise SourceError(rel, line, f"input is not valid UTF-8 at byte {exc.start}") from exc
    return file_id, data, text


def add_source_record(
    stage: dict[str, Any],
    *,
    source_file_id: str,
    relative_path: str,
    line_start: int,
    line_end: int,
    raw_text: str,
    extraction_method: str,
    imported_from: str,
    byte_start: int | None = None,
    byte_end: int | None = None,
) -> str:
    raw_hash = sha256_bytes(raw_text.encode("utf-8"))
    record_id = stable_id(
        "sr",
        relative_path,
        line_start,
        line_end,
        extraction_method,
        raw_hash,
        size=32,
    )
    row = {
        "source_record_id": record_id,
        "source_file_id": source_file_id,
        "line_start": line_start,
        "line_end": line_end,
        "byte_start": byte_start,
        "byte_end": byte_end,
        "extraction_method": extraction_method,
        "imported_from": imported_from,
        "raw_text": raw_text,
        "raw_sha256": raw_hash,
    }
    rows = stage["rows"]["source_records"]
    if not any(r["source_record_id"] == record_id for r in rows):
        add_row(stage, "source_records", row)
    return record_id


def add_assertion(stage: dict[str, Any], record_id: str, key: str, scope: str, value: Any) -> None:
    add_row(
        stage,
        "source_record_assertions",
        {
            "source_record_id": record_id,
            "assertion_key": key,
            "assertion_scope": scope,
            "value_json": canonical_json(value),
        },
    )


def write_stage(path: Path, stage: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(stage) + "\n", encoding="utf-8", newline="\n")


def read_stage(path: Path) -> dict[str, Any]:
    try:
        stage = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"Cannot read staging file {path}: {exc}") from exc
    if stage.get("stage_version") != 1 or set(stage.get("rows", {})) != set(TABLES):
        raise PipelineError(f"Unsupported or malformed staging document: {path}")
    return stage


def sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=canonical_json)


def stage_manifest(stage: dict[str, Any]) -> dict[str, str]:
    return {r["relative_path"]: r["sha256"] for r in sorted_rows(stage["rows"]["source_files"])}


def stage_content_hash(stage: dict[str, Any], migration_hashes: list[str]) -> str:
    payload = {
        "stage_version": stage["stage_version"],
        "importer_version": IMPORTER_VERSION,
        "source_manifest_hash": stage["meta"]["source_manifest_hash"],
        "migration_hashes": migration_hashes,
        "rows": {name: sorted_rows(stage["rows"][name]) for name in sorted(stage["rows"])},
    }
    return canonical_hash(payload)
