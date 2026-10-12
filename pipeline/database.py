from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .common import (
    IMPORTER_VERSION,
    ROOT,
    TABLES,
    PipelineError,
    canonical_hash,
    canonical_json,
    sha256_bytes,
    sorted_rows,
    stage_content_hash,
    stage_manifest,
)

MIGRATION_DIR = ROOT / "migrations"

# Composite/natural keys used to catch staging mistakes before SQLite does.
STAGE_UNIQUE_KEYS: dict[str, tuple[tuple[str, ...], ...]] = {
    "source_files": (("source_file_id",), ("relative_path",)),
    "source_records": (("source_record_id",),),
    "source_record_assertions": (("source_record_id", "assertion_key", "assertion_scope"),),
    "exams": (("exam_id",), ("code",)),
    "exam_sessions": (("session_id",), ("exam_id", "session_label", "exam_date")),
    "sections": (("section_id",), ("exam_id", "paper_number", "section_code")),
    "blueprint_versions": (("blueprint_id",), ("exam_id", "paper_number", "version_number", "label")),
    "blueprint_selection_groups": (("selection_group_id",), ("blueprint_id", "group_code")),
    "blueprint_sections": (("blueprint_section_id",), ("blueprint_id", "slot_code"), ("blueprint_id", "order_index")),
    "blueprint_section_locales": (("blueprint_section_id", "locale_code"),),
    "blueprint_selection_members": (("selection_group_id", "blueprint_section_id", "locale_code"),),
    "blueprint_rules": (("blueprint_id", "rule_code"),),
    "paper_forms": (("form_id",),),
    "paper_form_blueprints": (("form_id", "blueprint_id"),),
    "paper_form_sections": (("form_section_id",), ("form_id", "blueprint_section_id", "locale_code")),
    "question_types": (("type_code",),),
    "questions": (("question_id",),),
    "question_contents": (("question_id", "locale_code"),),
    "question_options": (("option_id",), ("question_id", "position"), ("question_id", "original_label")),
    "option_contents": (("option_id", "locale_code"),),
    "question_appearances": (("appearance_id",), ("form_section_id", "question_number"), ("form_section_id", "sequence_in_section")),
    "question_source_tags": (("question_id", "raw_tag", "source_record_id"),),
    "question_source_audits": (("question_id", "source_record_id"),),
    "stimuli": (("stimulus_id",),),
    "stimulus_contents": (("stimulus_id", "locale_code"),),
    "stimulus_question_links": (("stimulus_id", "appearance_id"), ("stimulus_id", "position")),
    "stimulus_review_records": (("review_id",),),
    "answer_key_versions": (("answer_key_version_id",), ("form_id", "version_label")),
    "answer_key_tables": (("answer_key_table_id",),),
    "answer_key_entries": (("answer_key_entry_id",), ("answer_key_table_id", "appearance_id")),
    "answer_key_entry_options": (("answer_key_entry_id", "option_id"), ("answer_key_entry_id", "position")),
    "question_search_documents": (("search_doc_id",), ("question_id", "locale_code")),
}


def migration_files() -> list[Path]:
    files = sorted(MIGRATION_DIR.glob("*.sql"))
    if not files:
        raise PipelineError(f"No SQL migrations found in {MIGRATION_DIR}")
    return files


def migration_hashes() -> list[str]:
    return [sha256_bytes(path.read_bytes()) for path in migration_files()]


def migration_manifest() -> list[dict[str, Any]]:
    return [
        {
            "version": int(re.match(r"^(\d+)_", path.name).group(1)) if re.match(r"^(\d+)_", path.name) else index,
            "name": path.name,
            "checksum": sha256_bytes(path.read_bytes()),
        }
        for index, path in enumerate(migration_files(), 1)
    ]


def _iter_sql_statements(script: str) -> list[str]:
    statements: list[str] = []
    current = ""
    for line in script.splitlines(keepends=True):
        current += line
        if sqlite3.complete_statement(current):
            statement = current.strip()
            if statement:
                statements.append(statement)
            current = ""
    if current.strip():
        raise PipelineError("Migration contains an incomplete SQL statement")
    return statements


def _apply_migrations(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    applied: dict[int, tuple[str, str]] = {}
    existing_tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    if "schema_migrations" in existing_tables:
        for version, name, checksum in conn.execute("SELECT version, name, checksum FROM schema_migrations"):
            applied[int(version)] = (name, checksum)
    manifest = migration_manifest()
    for item, path in zip(manifest, migration_files(), strict=True):
        version = item["version"]
        if version in applied:
            if applied[version] != (item["name"], item["checksum"]):
                raise PipelineError(
                    f"Applied migration {version} does not match the checked-in file; create a new migration instead of rewriting history"
                )
            continue
        if applied and version <= max(applied):
            raise PipelineError(f"Migration sequence gap or downgrade at {path.name}")
        conn.execute("BEGIN IMMEDIATE")
        try:
            for statement in _iter_sql_statements(path.read_text(encoding="utf-8")):
                conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migrations(version, name, checksum) VALUES (?, ?, ?)",
                (version, item["name"], item["checksum"]),
            )
            conn.execute(f"PRAGMA user_version = {version}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        applied[version] = (item["name"], item["checksum"])
    return manifest


def _validate_source_snapshot(stage: dict[str, Any]) -> None:
    rows = stage.get("rows", {}).get("source_files", [])
    seen_paths: set[str] = set()
    for row in rows:
        relative = row["relative_path"]
        if relative in seen_paths:
            raise PipelineError(f"Duplicate source path in stage: {relative}")
        seen_paths.add(relative)
        path = (ROOT / relative).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise PipelineError(f"Staged source path escapes repository: {relative}") from exc
        try:
            actual_hash = sha256_bytes(path.read_bytes())
        except OSError as exc:
            raise PipelineError(f"Cannot read staged source {relative}: {exc}") from exc
        if actual_hash != row["sha256"]:
            raise PipelineError(
                f"Staged source changed since parse: {relative} (expected {row['sha256']}, found {actual_hash})"
            )
        if len(actual_hash) != 64 or row["byte_size"] < 0:
            raise PipelineError(f"Invalid source metadata for {relative}")


def _validate_unique_rows(stage: dict[str, Any]) -> None:
    for table, constraints in STAGE_UNIQUE_KEYS.items():
        rows = stage["rows"].get(table, [])
        for columns in constraints:
            observed: dict[tuple[Any, ...], int] = {}
            for row in rows:
                key = tuple(row.get(column) for column in columns)
                observed[key] = observed.get(key, 0) + 1
            duplicates = [key for key, count in observed.items() if count > 1]
            if duplicates:
                raise PipelineError(f"Stage uniqueness violation in {table} on {columns}: {duplicates[:5]}")


def _validate_stage_foreign_references(stage: dict[str, Any]) -> None:
    rows = stage["rows"]
    source_file_ids = {row["source_file_id"] for row in rows["source_files"]}
    source_record_ids = {row["source_record_id"] for row in rows["source_records"]}
    for record in rows["source_records"]:
        if record["source_file_id"] not in source_file_ids:
            raise PipelineError(f"Source record {record['source_record_id']} has no source file")
        if record["raw_sha256"] != sha256_bytes(record["raw_text"].encode("utf-8")):
            raise PipelineError(f"Source record {record['source_record_id']} raw hash mismatch")
    for table, table_rows in rows.items():
        for row in table_rows:
            record_id = row.get("source_record_id") or row.get("primary_source_record_id")
            if record_id is not None and record_id not in source_record_ids:
                raise PipelineError(f"{table} row references missing source record {record_id}")
            file_id = row.get("source_file_id")
            if file_id is not None and file_id not in source_file_ids:
                raise PipelineError(f"{table} row references missing source file {file_id}")
    for assertion in rows["source_record_assertions"]:
        if assertion["source_record_id"] not in source_record_ids:
            raise PipelineError(f"Assertion references missing source record {assertion['source_record_id']}")
        try:
            json.loads(assertion["value_json"])
        except json.JSONDecodeError as exc:
            raise PipelineError(f"Invalid JSON assertion value: {exc}") from exc


def _validate_question_rows(stage: dict[str, Any]) -> None:
    rows = stage["rows"]
    questions = {row["question_id"]: row for row in rows["questions"]}
    question_types = {row["type_code"] for row in rows["question_types"]}
    contents_by_question: dict[str, set[str]] = defaultdict(set)
    for content in rows["question_contents"]:
        if content["question_id"] not in questions:
            raise PipelineError(f"Question content references unknown question {content['question_id']}")
        contents_by_question[content["question_id"]].add(content["locale_code"])
    options_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for option in rows["question_options"]:
        if option["question_id"] not in questions:
            raise PipelineError(f"Option references unknown question {option['question_id']}")
        options_by_question[option["question_id"]].append(option)
    option_contents: dict[str, set[str]] = defaultdict(set)
    for content in rows["option_contents"]:
        option_contents[content["option_id"]].add(content["locale_code"])
    option_by_id = {row["option_id"]: row for row in rows["question_options"]}
    for question_id, question in questions.items():
        if question["type_code"] not in question_types:
            raise PipelineError(f"Question {question_id} references unknown type {question['type_code']}")
        locales = contents_by_question.get(question_id, set())
        options = sorted(options_by_question.get(question_id, []), key=lambda row: row["position"])
        if not locales:
            raise PipelineError(f"Question {question_id} has no localized content")
        if [option["position"] for option in options] != [1, 2, 3, 4]:
            raise PipelineError(f"Question {question_id} does not have exactly four ordered options")
        for option in options:
            if option_contents.get(option["option_id"], set()) != locales:
                raise PipelineError(
                    f"Option {option['option_id']} locales {sorted(option_contents.get(option['option_id'], set()))} "
                    f"do not match question locales {sorted(locales)}"
                )
    for content in rows["option_contents"]:
        option = option_by_id.get(content["option_id"])
        if option is None or option["question_id"] != content["question_id"]:
            raise PipelineError(f"Option content has invalid question/option relation: {content['option_id']}")
    appearances = {row["appearance_id"]: row for row in rows["question_appearances"]}
    paper_form_sections = {row["form_section_id"]: row for row in rows["paper_form_sections"]}
    for appearance in appearances.values():
        if appearance["form_section_id"] not in paper_form_sections:
            raise PipelineError(f"Appearance {appearance['appearance_id']} has no paper-form section")
        if appearance["question_id"] not in questions:
            raise PipelineError(f"Appearance {appearance['appearance_id']} has no question")
    for entry in rows["answer_key_entries"]:
        if entry["appearance_id"] not in appearances:
            raise PipelineError(f"Answer entry {entry['answer_key_entry_id']} references missing appearance")
        if appearances[entry["appearance_id"]]["question_id"] != entry["question_id"]:
            raise PipelineError(f"Answer entry {entry['answer_key_entry_id']} has inconsistent question")
    entries_by_id = {row["answer_key_entry_id"]: row for row in rows["answer_key_entries"]}
    options_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for option_link in rows["answer_key_entry_options"]:
        entry = entries_by_id.get(option_link["answer_key_entry_id"])
        option = option_by_id.get(option_link["option_id"])
        if entry is None or option is None:
            raise PipelineError(f"Answer-key option has invalid entry/option foreign reference")
        if entry["question_id"] != option_link["question_id"] or option["question_id"] != option_link["question_id"]:
            raise PipelineError(f"Answer-key option is linked to a different question")
        options_by_entry[option_link["answer_key_entry_id"]].append(option_link)
    for entry_id, entry in entries_by_id.items():
        option_links = options_by_entry.get(entry_id, [])
        positions = sorted(row["position"] for row in option_links)
        if not positions or positions != list(range(1, len(positions) + 1)):
            raise PipelineError(f"Answer entry {entry_id} has no contiguous correct-option set")
        if len({row["option_id"] for row in option_links}) != len(option_links):
            raise PipelineError(f"Answer entry {entry_id} repeats a correct option")


def _validate_counts(stage: dict[str, Any]) -> dict[str, Any]:
    rows = stage["rows"]
    sessions = {row["session_id"]: row for row in rows["exam_sessions"]}
    forms = rows["paper_forms"]
    form_exam = {form["form_id"]: sessions[form["session_id"]]["exam_id"] for form in forms}
    ctet_forms = {form_id for form_id, exam_id in form_exam.items() if exam_id == "ctet"}
    utet_forms = {form_id for form_id, exam_id in form_exam.items() if exam_id == "utet"}
    if len(ctet_forms) != 5 or len(utet_forms) != 6:
        raise PipelineError(f"Expected five CTET and six UTET forms, found {len(ctet_forms)} and {len(utet_forms)}")
    q_ids_by_exam = {
        "ctet": {row["question_id"] for row in rows["questions"] if row["question_id"].startswith("ctet-")},
        "utet": {row["question_id"] for row in rows["questions"] if row["question_id"].startswith("utet-")},
    }
    if (len(q_ids_by_exam["ctet"]), len(q_ids_by_exam["utet"])) != (930, 900):
        raise PipelineError(f"Expected 930 canonical CTET and 900 UTET questions; found {len(q_ids_by_exam['ctet'])} and {len(q_ids_by_exam['utet'])}")
    form_section_form = {row["form_section_id"]: row["form_id"] for row in rows["paper_form_sections"]}
    appearances_by_form: Counter[str] = Counter(
        form_section_form[row["form_section_id"]] for row in rows["question_appearances"]
    )
    expected_app_count = {**{form_id: 210 for form_id in ctet_forms}, **{form_id: 150 for form_id in utet_forms}}
    for form_id, expected in expected_app_count.items():
        if appearances_by_form[form_id] != expected:
            raise PipelineError(f"Form {form_id} has {appearances_by_form[form_id]} appearances, expected {expected}")
    answer_versions = {row["answer_key_version_id"]: row for row in rows["answer_key_versions"]}
    tables = {row["answer_key_table_id"]: row for row in rows["answer_key_tables"]}
    answer_count_by_form: Counter[str] = Counter(
        answer_versions[tables[entry["answer_key_table_id"]]["answer_key_version_id"]]["form_id"]
        for entry in rows["answer_key_entries"]
    )
    for form_id in ctet_forms:
        if answer_count_by_form[form_id] != 210:
            raise PipelineError(f"CTET form {form_id} has {answer_count_by_form[form_id]} key rows, expected 210")
        if not any(row["authority_class"] == "exam_authority" and row["status"] == "final" and row["form_id"] == form_id for row in rows["answer_key_versions"]):
            raise PipelineError(f"CTET form {form_id} has no source-documented CBSE final key version")
    for form_id in utet_forms:
        if answer_count_by_form[form_id] != 150:
            raise PipelineError(f"UTET form {form_id} has {answer_count_by_form[form_id]} embedded source answers, expected 150")
        if any(row["authority_class"] == "exam_authority" and row["status"] == "final" and row["form_id"] == form_id for row in rows["answer_key_versions"]):
            raise PipelineError(f"UTET source-repository answers were incorrectly promoted to official final for {form_id}")
    if len(rows["stimuli"]) != 64 or len(rows["stimulus_question_links"]) != 411:
        raise PipelineError(f"Expected 64 CTET+UTET stimuli and 411 linked appearances; found {len(rows['stimuli'])} and {len(rows['stimulus_question_links'])}")
    if len(rows["question_review_records"]) != 120:
        raise PipelineError(f"Expected 120 CTET reviewed mirror question records, found {len(rows['question_review_records'])}")
    if len(rows["question_source_audits"]) != 900:
        raise PipelineError(f"Expected 900 UTET source audit links, found {len(rows['question_source_audits'])}")
    if len(rows["answer_key_entries"]) != 1950 or len(rows["answer_key_entry_options"]) != 1968:
        raise PipelineError(
            f"Unexpected answer expansion totals: entries={len(rows['answer_key_entries'])}, option links={len(rows['answer_key_entry_options'])}"
        )
    if len(rows["source_files"]) != 109:
        raise PipelineError(f"Expected 109 reviewed source files, found {len(rows['source_files'])}")
    empty_tables = ("explanations", "assets", "asset_locales", "question_assets", "option_assets", "stimulus_assets", "stimulus_review_records", "explanation_assets", "taxonomy_schemes", "taxonomy_nodes", "question_taxonomy_assignments", "question_assessments", "appearance_review_records", "form_review_records", "answer_key_review_records")
    nonempty = {name: len(rows[name]) for name in empty_tables if rows[name]}
    if nonempty:
        raise PipelineError(f"Expected annotations/taxonomy/assets to remain initially empty, found {nonempty}")
    return {
        "forms": {"ctet": len(ctet_forms), "utet": len(utet_forms)},
        "questions": {"ctet": len(q_ids_by_exam["ctet"]), "utet": len(q_ids_by_exam["utet"])},
        "appearances": {"ctet": sum(appearances_by_form[f] for f in ctet_forms), "utet": sum(appearances_by_form[f] for f in utet_forms)},
        "answer_entries": {"ctet": sum(answer_count_by_form[f] for f in ctet_forms), "utet": sum(answer_count_by_form[f] for f in utet_forms)},
        "source_files": len(rows["source_files"]),
        "stimuli": len(rows["stimuli"]),
        "stimulus_links": len(rows["stimulus_question_links"]),
        "question_locales": len(rows["question_contents"]),
        "answer_option_links": len(rows["answer_key_entry_options"]),
        "official_final_ctet_entries": sum(
            len([entry for entry in rows["answer_key_entries"] if tables[entry["answer_key_table_id"]]["answer_key_version_id"] == version["answer_key_version_id"]])
            for version in rows["answer_key_versions"]
            if version["authority_class"] == "exam_authority" and version["status"] == "final"
        ),
    }


def validate_stage(stage: dict[str, Any], *, check_sources: bool = True) -> dict[str, Any]:
    if stage.get("stage_version") != 1 or set(stage.get("rows", {})) != set(TABLES):
        raise PipelineError("Unsupported or malformed stage document")
    if check_sources:
        _validate_source_snapshot(stage)
    expected_manifest_hash = canonical_hash(stage_manifest(stage))
    if stage.get("meta", {}).get("source_manifest_hash") != expected_manifest_hash:
        raise PipelineError("Stage source_manifest_hash does not match staged source files")
    _validate_unique_rows(stage)
    _validate_stage_foreign_references(stage)
    _validate_question_rows(stage)
    counts = _validate_counts(stage)
    return counts


def build_search_documents(stage: dict[str, Any]) -> int:
    rows = stage["rows"]
    if rows["question_search_documents"]:
        raise PipelineError("Search documents already exist in the stage; refusing to append duplicates")
    content_by_question: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows["question_contents"]:
        content_by_question[row["question_id"]][row["locale_code"]] = row
    option_text: dict[str, dict[str, str]] = defaultdict(dict)
    option_labels: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows["question_options"]:
        option_labels[row["question_id"]][row["option_id"]] = f"{row['position']}. {row['original_label']}"
    for row in rows["option_contents"]:
        option_text[row["question_id"]][f"{row['option_id']}\x1f{row['locale_code']}"] = row["display_text"]
    option_rows_by_q: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows["question_options"]:
        option_rows_by_q[row["question_id"]].append(row)
    explanations_by_q_locale: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows["explanations"]:
        explanations_by_q_locale[(row["question_id"], row["locale_code"])].append(row["display_text"])
    appearance_by_id = {row["appearance_id"]: row for row in rows["question_appearances"]}
    appearance_ids_by_question: dict[str, list[str]] = defaultdict(list)
    for row in rows["question_appearances"]:
        appearance_ids_by_question[row["question_id"]].append(row["appearance_id"])
    links_by_appearance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows["stimulus_question_links"]:
        links_by_appearance[row["appearance_id"]].append(row)
    stimulus_contents = {(row["stimulus_id"], row["locale_code"]): row["display_text"] for row in rows["stimulus_contents"]}

    doc_id = 0
    for question_id in sorted(content_by_question):
        for locale in sorted(content_by_question[question_id]):
            doc_id += 1
            options = []
            for option in sorted(option_rows_by_q[question_id], key=lambda row: row["position"]):
                text = option_text.get(question_id, {}).get(f"{option['option_id']}\x1f{locale}")
                if text is None:
                    raise PipelineError(f"Missing option text for FTS document {question_id}/{locale}/{option['option_id']}")
                options.append(f"{option['original_label']}. {text}")
            stimulus_texts: list[str] = []
            seen_stimuli: set[str] = set()
            for appearance_id in appearance_ids_by_question.get(question_id, []):
                if appearance_id not in appearance_by_id:
                    continue
                for link in sorted(links_by_appearance.get(appearance_id, []), key=lambda row: row["position"]):
                    stimulus_id = link["stimulus_id"]
                    if stimulus_id in seen_stimuli:
                        continue
                    seen_stimuli.add(stimulus_id)
                    text = stimulus_contents.get((stimulus_id, locale))
                    if text:
                        stimulus_texts.append(text)
            add = {
                "search_doc_id": doc_id,
                "question_id": question_id,
                "locale_code": locale,
                "stem": content_by_question[question_id][locale]["display_stem"],
                "options": "\n".join(options),
                "explanations": "\n".join(explanations_by_q_locale.get((question_id, locale), [])),
                "stimuli": "\n\n".join(stimulus_texts),
            }
            rows["question_search_documents"].append(add)
    return doc_id


def _insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    columns_info = conn.execute(f"PRAGMA table_info({table})").fetchall()
    columns = [row[1] for row in columns_info]
    row_keys = set(rows[0])
    if row_keys != set(columns):
        missing = sorted(set(columns) - row_keys)
        extra = sorted(row_keys - set(columns))
        raise PipelineError(f"Stage columns for {table} disagree with migration; missing={missing}, extra={extra}")
    ordered_rows = sorted_rows(rows)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})"
    try:
        conn.executemany(sql, [tuple(row[column] for column in columns) for row in ordered_rows])
    except sqlite3.IntegrityError as exc:
        raise PipelineError(f"SQLite rejected staged {table} rows: {exc}") from exc


def _database_rows(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    for table in TABLES:
        rows = [dict(row) for row in conn.execute(f"SELECT * FROM {table}")]
        output[table] = sorted_rows(rows)
    return output


def rebuild_database(stage: dict[str, Any], db_path: Path) -> dict[str, Any]:
    validate_stage(stage, check_sources=True)
    expected_search_count = sum(len({row["locale_code"] for row in stage["rows"]["question_contents"] if row["question_id"] == q["question_id"]}) for q in stage["rows"]["questions"])
    actual_search_count = build_search_documents(stage)
    if actual_search_count != expected_search_count:
        raise PipelineError(f"Search document count mismatch: expected {expected_search_count}, built {actual_search_count}")
    counts = validate_stage(stage, check_sources=False)
    migration_info = migration_manifest()
    hashes = [item["checksum"] for item in migration_info]
    source_hash = canonical_hash(stage_manifest(stage))
    if stage["meta"].get("source_manifest_hash") != source_hash:
        raise PipelineError("Source manifest changed after parse")
    content_hash = stage_content_hash(stage, hashes)
    db_path = db_path.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = db_path.with_name(db_path.name + ".tmp")
    if temp_path.exists():
        temp_path.unlink()
    try:
        conn = sqlite3.connect(temp_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA page_size = 4096")
        conn.execute("PRAGMA journal_mode = DELETE")
        conn.execute("PRAGMA synchronous = FULL")
        applied = _apply_migrations(conn)
        if [item["checksum"] for item in applied] != hashes:
            raise PipelineError("Applied migration checksums differ from the content-hash inputs")
        conn.execute("BEGIN IMMEDIATE")
        try:
            for table in TABLES:
                _insert_rows(conn, table, stage["rows"][table])
            conn.execute(
                "INSERT INTO build_metadata(singleton, schema_version, importer_version, source_manifest_hash, content_hash, sqlite_runtime, fts5_enabled) VALUES (1, ?, ?, ?, ?, ?, 1)",
                (applied[-1]["version"], IMPORTER_VERSION, source_hash, content_hash, sqlite3.sqlite_version),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        check = verify_database(conn, expected_content_hash=content_hash)
        conn.execute("PRAGMA optimize")
        conn.close()
        os.replace(temp_path, db_path)
        return {**check, "database": str(db_path), "content_hash": content_hash, "counts": counts}
    except Exception:
        try:
            conn.close()  # type: ignore[possibly-undefined]
        except Exception:
            pass
        if temp_path.exists():
            temp_path.unlink()
        raise


def verify_database(
    conn_or_path: sqlite3.Connection | Path,
    *,
    expected_content_hash: str | None = None,
    run_integrity: bool = True,
) -> dict[str, Any]:
    owns_connection = not isinstance(conn_or_path, sqlite3.Connection)
    conn = sqlite3.connect(conn_or_path) if owns_connection else conn_or_path
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        if run_integrity:
            integrity = conn.execute("PRAGMA integrity_check").fetchall()
            if len(integrity) != 1 or integrity[0][0] != "ok":
                raise PipelineError(f"SQLite integrity_check failed: {[row[0] for row in integrity[:10]]}")
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise PipelineError(f"SQLite foreign_key_check found {len(fk_errors)} violation(s): {[tuple(r) for r in fk_errors[:10]]}")
        migrations = migration_manifest()
        applied = [dict(row) for row in conn.execute("SELECT version, name, checksum FROM schema_migrations ORDER BY version")]
        if applied != migrations:
            raise PipelineError("Database schema_migrations do not match the checked-in migration files")
        migration_hash_list = [row["checksum"] for row in applied]
        source_files = [dict(row) for row in conn.execute("SELECT relative_path, sha256 FROM source_files ORDER BY relative_path")]
        manifest_hash = canonical_hash({row["relative_path"]: row["sha256"] for row in source_files})
        metadata = conn.execute("SELECT * FROM build_metadata WHERE singleton=1").fetchone()
        if metadata is None:
            raise PipelineError("Database is missing build_metadata singleton row")
        if metadata["source_manifest_hash"] != manifest_hash:
            raise PipelineError("build_metadata source_manifest_hash does not match source_files")
        db_rows = _database_rows(conn)
        content_stage = {
            "stage_version": 1,
            "meta": {"source_manifest_hash": manifest_hash},
            "rows": db_rows,
        }
        computed_hash = stage_content_hash(content_stage, migration_hash_list)
        if metadata["content_hash"] != computed_hash:
            raise PipelineError(
                f"Database content hash mismatch: metadata={metadata['content_hash']}, computed={computed_hash}"
            )
        if expected_content_hash is not None and computed_hash != expected_content_hash:
            raise PipelineError(f"Database content hash {computed_hash} differs from expected {expected_content_hash}")
        counts = {table: conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in TABLES}
        table_defs = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "question_search_fts" not in table_defs:
            raise PipelineError("FTS5 virtual table question_search_fts is missing")
        fts_rows = conn.execute("SELECT count(*) FROM question_search_fts").fetchone()[0]
        if fts_rows != counts["question_search_documents"]:
            raise PipelineError(f"FTS row count {fts_rows} differs from search-document count {counts['question_search_documents']}")
        conn.execute("INSERT INTO question_search_fts(question_search_fts, rank) VALUES ('integrity-check', 1)")
        official_count = conn.execute("SELECT count(*) FROM v_official_final_answers").fetchone()[0]
        provisional_count = conn.execute(
            "SELECT count(*) FROM v_answer_key_history WHERE authority_class='source_repository' AND status='provisional'"
        ).fetchone()[0]
        if official_count != 1050 or provisional_count != 900:
            raise PipelineError(f"Answer-view authority boundary failed: official={official_count}, provisional={provisional_count}")
        answer_option_links = conn.execute("SELECT count(*) FROM answer_key_entry_options").fetchone()[0]
        if answer_option_links != 1968:
            raise PipelineError(f"Expected 1,968 expanded correct-option links, found {answer_option_links}")
        unlinked_stimuli = conn.execute(
            "SELECT count(*) FROM stimuli s WHERE NOT EXISTS (SELECT 1 FROM stimulus_question_links l WHERE l.stimulus_id=s.stimulus_id)"
        ).fetchone()[0]
        if unlinked_stimuli:
            raise PipelineError(f"Found {unlinked_stimuli} unreferenced stimuli")
        wrong_locale_options = conn.execute(
            "SELECT count(*) FROM question_options o JOIN questions q USING(question_id) "
            "WHERE (SELECT count(*) FROM option_contents oc WHERE oc.option_id=o.option_id) "
            "!= (SELECT count(*) FROM question_contents qc WHERE qc.question_id=o.question_id)"
        ).fetchone()[0]
        if wrong_locale_options:
            raise PipelineError(f"Found {wrong_locale_options} options with incomplete locale coverage")
        fts_hits = conn.execute(
            "SELECT count(*) FROM question_search_fts WHERE question_search_fts MATCH ?",
            ('"बाल" OR "education"',),
        ).fetchone()[0]
        expected_counts = {
            "exams": 2,
            "exam_sessions": 11,
            "paper_forms": 11,
            "questions": 1830,
            "question_appearances": 1950,
            "stimuli": 64,
            "stimulus_question_links": 411,
            "answer_key_versions": 11,
            "answer_key_entries": 1950,
            "question_search_documents": 2850,
        }
        for table, expected in expected_counts.items():
            if counts[table] != expected:
                raise PipelineError(f"Unexpected {table} count: expected {expected}, found {counts[table]}")
        return {
            "integrity_check": "ok" if run_integrity else "skipped",
            "foreign_key_violations": 0,
            "fts5_rows": fts_rows,
            "fts_integrity": "ok",
            "fts_sample_hits": fts_hits,
            "official_final_answers": official_count,
            "provisional_repository_answers": provisional_count,
            "content_hash": computed_hash,
            "table_counts": counts,
        }
    finally:
        if owns_connection:
            conn.close()


def data_quality_markdown(db_path: Path) -> str:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        verification = verify_database(conn)
        counts = verification["table_counts"]
        content_hash = verification["content_hash"]
        build_meta = conn.execute("SELECT source_manifest_hash, sqlite_runtime FROM build_metadata WHERE singleton=1").fetchone()
        source_manifest_hash = build_meta["source_manifest_hash"]
        sqlite_runtime = build_meta["sqlite_runtime"]
        forms = conn.execute(
            "SELECT e.code AS exam_code, pf.form_id, es.exam_date, pf.set_code, pf.total_questions, "
            "COUNT(DISTINCT qa.appearance_id) AS imported_appearances, "
            "COUNT(DISTINCT ake.answer_key_entry_id) AS answer_entries "
            "FROM paper_forms pf JOIN exam_sessions es USING(session_id) JOIN exams e USING(exam_id) "
            "LEFT JOIN paper_form_sections pfs USING(form_id) LEFT JOIN question_appearances qa USING(form_section_id) "
            "LEFT JOIN answer_key_versions akv USING(form_id) LEFT JOIN answer_key_tables akt USING(answer_key_version_id) "
            "LEFT JOIN answer_key_entries ake USING(answer_key_table_id) "
            "GROUP BY e.code, pf.form_id ORDER BY e.code, es.exam_date"
        ).fetchall()
        key_versions = conn.execute(
            "SELECT e.code AS exam_code, akv.form_id, akv.authority_class, akv.status, akv.version_label, akv.authority_uri "
            "FROM answer_key_versions akv JOIN paper_forms pf USING(form_id) JOIN exam_sessions es USING(session_id) "
            "JOIN exams e USING(exam_id) ORDER BY e.code, es.exam_date"
        ).fetchall()
        source_licenses = conn.execute(
            "SELECT license_id, COUNT(*) AS files FROM source_files GROUP BY license_id ORDER BY license_id"
        ).fetchall()
        answer_counts_by_exam = {
            row["code"]: row["answer_entries"]
            for row in conn.execute(
                "SELECT e.code, COUNT(ake.answer_key_entry_id) AS answer_entries "
                "FROM exams e JOIN exam_sessions es USING(exam_id) JOIN paper_forms pf USING(session_id) "
                "LEFT JOIN answer_key_versions akv USING(form_id) LEFT JOIN answer_key_tables akt USING(answer_key_version_id) "
                "LEFT JOIN answer_key_entries ake USING(answer_key_table_id) GROUP BY e.code"
            )
        }
        per_exam = conn.execute(
            "SELECT e.code, COUNT(DISTINCT q.question_id) AS questions, COUNT(DISTINCT qa.appearance_id) AS appearances, "
            "COUNT(DISTINCT pf.form_id) AS forms "
            "FROM exams e JOIN exam_sessions es USING(exam_id) JOIN paper_forms pf USING(session_id) "
            "LEFT JOIN paper_form_sections pfs USING(form_id) LEFT JOIN question_appearances qa USING(form_section_id) "
            "LEFT JOIN questions q USING(question_id) GROUP BY e.code ORDER BY e.code"
        ).fetchall()
        missing_uri = [row["form_id"] for row in key_versions if row["authority_class"] == "exam_authority" and row["status"] == "final" and not row["authority_uri"]]
        locale_counts = conn.execute(
            "SELECT locale_code, COUNT(*) AS contents FROM question_contents GROUP BY locale_code ORDER BY locale_code"
        ).fetchall()
    finally:
        conn.close()

    missing_uri_text = ", ".join(f"`{form_id}`" for form_id in missing_uri) or "none"
    try:
        database_display = Path(db_path).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        database_display = Path(db_path).name
    lines = [
        "# Data quality report",
        "",
        f"**Database:** `{database_display}`<br>",
        f"**Content hash:** `{content_hash}`<br>",
        f"**Source manifest hash:** `{source_manifest_hash}`<br>",
        f"**SQLite runtime:** `{sqlite_runtime}` (FTS5/JSON1 enabled)<br>",
        "**Verification:** SQLite integrity, foreign keys, FTS5 integrity, counts, answer-key boundaries, and content hash passed.",
        "",
        "## Imported inventory",
        "",
        "| Exam | Forms | Canonical questions | Question appearances | Answer-key entries |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in per_exam:
        answer_count = answer_counts_by_exam.get(row["code"], 0)
        lines.append(f"| {row['code']} | {row['forms']} | {row['questions']} | {row['appearances']} | {answer_count} |")
    lines.extend(
        [
            "",
            f"The database contains **{counts['source_files']} source files**, **{counts['source_records']} source records**, "
            f"**{counts['question_contents']} localized question-content rows**, **{counts['question_options']} options**, "
            f"**{counts['stimuli']} stimuli**, and **{counts['stimulus_question_links']} stimulus-to-appearance links**.",
            "",
            "## Form-level structural counts",
            "",
            "| Exam | Form | Date | Set | Configured questions | Imported appearances | Key entries |",
            "|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in forms:
        lines.append(
            f"| {row['exam_code']} | `{row['form_id']}` | {row['exam_date']} | {row['set_code']} | "
            f"{row['total_questions']} | {row['imported_appearances']} | {row['answer_entries']} |"
        )
    lines.extend(
        [
            "",
            "CTET imports **210 file appearances and 210 key rows per form** because all four optional language streams are retained. Candidate-facing form configuration still specifies 150 questions and requires one locale per language slot. UTET has 150 appearances and 150 embedded source-answer rows per form.",
            "",
            "## Answer authority and multi-correct expansions",
            "",
            "| Exam | Form | Authority class | Status | Authority URI recorded |",
            "|---|---|---|---|---|",
        ]
    )
    for row in key_versions:
        uri = f"<{row['authority_uri']}>" if row["authority_uri"] else "Not linked in source README"
        lines.append(f"| {row['exam_code']} | `{row['form_id']}` | {row['authority_class']} | {row['status']} | {uri} |")
    lines.extend(
        [
            "",
            f"**Official-final view rows:** {verification['official_final_answers']}. **UTET provisional source-repository answer rows kept out of that view:** {verification['provisional_repository_answers']}.",
            f"The parser expanded multi-correct source letters into **{counts['answer_key_entry_options']} correct-option links** across **{counts['answer_key_entries']} answer entries**; source tokens remain stored verbatim.",
            "",
            f"The CTET `Answer-Key.txt` values are imported as the official-final versions described by the corresponding paper READMEs. This is a structural parse, not a re-comparison against the linked CBSE PDF. Forms without a direct official-key URI in source metadata: {missing_uri_text}. The UTET repository's embedded answers are explicitly `source_repository`/`provisional`; no official UBSE key was evidenced in the pinned manifest/audit sources.",
            "",
            "## Locale, stimuli, annotations, and provenance",
            "",
            "| Question locale | Content rows |",
            "|---|---:|",
        ]
    )
    for row in locale_counts:
        lines.append(f"| {row['locale_code']} | {row['contents']} |")
    lines.extend(
        [
            "",
            f"- **Stimuli:** {counts['stimuli']} total; all have at least one linked question appearance. Inline CTET reading blocks and UTET stimulus rows are separate entities.",
            f"- **Source audits:** {counts['question_source_audits']} UTET audit records are linked to their canonical questions.",
            f"- **Assets/explanations:** {counts['assets']} assets and {counts['explanations']} explanations are imported; source inputs provide no relevant files/content in this scope.",
            f"- **Taxonomy/difficulty/Bloom:** {counts['taxonomy_nodes']} taxonomy nodes, {counts['question_taxonomy_assignments']} assignments, and {counts['question_assessments']} assessments. These remain intentionally empty/unrated.",
            f"- **FTS5:** {verification['fts5_rows']} localized search documents; `integrity-check` passed and sample multilingual search returned {verification['fts_sample_hits']} rows.",
            "- **Raw provenance:** every imported source file is SHA-256 fingerprinted. Extracted question/key/audit records retain raw source text, file path, line range, extraction method, `imported_from`, and (for UTET) pinned commit/license/attribution metadata.",
            "",
            "## Source license and limitations",
            "",
        ]
    )
    for row in source_licenses:
        lines.append(f"- `{row['license_id'] or 'Unassigned / not asserted'}`: {row['files']} source files.")
    lines.extend(
        [
            "- CTET source files are not assigned a license by this pipeline; paper READMEs include source-quality notes, including legacy-font transcription/review limitations. Raw text remains unchanged and no editorial correction is applied.",
            "- UTET source is pinned to `sherawali/tet` commit `6792637052eb0bcddd27b9290ddd082faa725a4d`, CC BY 4.0, attributed to TET Question Bank contributors (2026). Its `verified` flags are repository-level assertions, not an official UBSE endorsement.",
            "- No content-level re-verification against exam authority scans/PDFs was performed. Validation gates cover source/schema structure, database constraints, linkage, answer expansion, deterministic content hashing, and search integrity.",
            "",
            "## Validation summary",
            "",
            f"- `PRAGMA integrity_check`: {verification['integrity_check']}",
            f"- `PRAGMA foreign_key_check`: {verification['foreign_key_violations']} violations",
            f"- FTS5 integrity: {verification['fts_integrity']}",
            f"- Content hash re-computation: `{verification['content_hash']}`",
            "",
            "To regenerate: `python -m pipeline report --db data/xtet-question-bank.sqlite --output docs/DATA_QUALITY.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_data_quality_report(db_path: Path, output_path: Path) -> Path:
    report = data_quality_markdown(db_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8", newline="\n")
    return output_path
