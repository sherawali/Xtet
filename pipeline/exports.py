from __future__ import annotations

import json
import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from .common import canonical_json, sha256_bytes
from .database import verify_database


def _rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params)]


def _decoded_json(value: str | None) -> Any:
    if value is None:
        return None
    return json.loads(value)


def _write_bytes(path: Path, payload: bytes) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(payload)
    os.replace(temp, path)
    return payload


def _write_ndjson(path: Path, records: list[dict[str, Any]]) -> bytes:
    payload = "".join(canonical_json(record) + "\n" for record in records).encode("utf-8")
    return _write_bytes(path, payload)


def export_database(db_path: Path, output_dir: Path, app_json_path: Path | None = None) -> dict[str, Any]:
    verification = verify_database(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        metadata = dict(conn.execute("SELECT * FROM build_metadata WHERE singleton=1").fetchone())
        source_lookup = {
            row["source_record_id"]: row
            for row in _rows(
                conn,
                "SELECT sr.source_record_id, sf.relative_path, sr.line_start, sr.line_end, "
                "sr.extraction_method, sr.imported_from, sr.raw_sha256 "
                "FROM source_records sr JOIN source_files sf USING(source_file_id)",
            )
        }
        contents_by_question: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        for row in _rows(conn, "SELECT * FROM question_contents ORDER BY question_id, locale_code"):
            contents_by_question[row["question_id"]][row["locale_code"]] = {
                "raw_stem": row["raw_stem"],
                "display_stem": row["display_stem"],
                "content_format": row["content_format"],
                "structured": _decoded_json(row["structured_json"]),
                "source_record_id": row["source_record_id"],
            }
        options_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for option in _rows(conn, "SELECT * FROM question_options ORDER BY question_id, position"):
            options_by_question[option["question_id"]].append(
                {
                    "option_id": option["option_id"],
                    "position": option["position"],
                    "original_label": option["original_label"],
                    "source_record_id": option["source_record_id"],
                    "contents": {},
                }
            )
        option_by_id = {
            option["option_id"]: option
            for options in options_by_question.values()
            for option in options
        }
        for row in _rows(conn, "SELECT * FROM option_contents ORDER BY question_id, locale_code, option_id"):
            option_by_id[row["option_id"]]["contents"][row["locale_code"]] = {
                "raw_text": row["raw_text"],
                "display_text": row["display_text"],
                "content_format": row["content_format"],
                "structured": _decoded_json(row["structured_json"]),
                "source_record_id": row["source_record_id"],
            }
        tags_by_question: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in _rows(conn, "SELECT question_id, raw_tag, source_record_id FROM question_source_tags ORDER BY question_id, raw_tag"):
            tags_by_question[row["question_id"]].append({"raw_tag": row["raw_tag"], "source_record_id": row["source_record_id"]})
        audits_by_question: dict[str, list[str]] = defaultdict(list)
        for row in _rows(conn, "SELECT question_id, source_record_id FROM question_source_audits ORDER BY question_id, source_record_id"):
            audits_by_question[row["question_id"]].append(row["source_record_id"])
        question_rows = _rows(conn, "SELECT * FROM questions ORDER BY question_id")
        questions: list[dict[str, Any]] = []
        for question in question_rows:
            source_id = question["primary_source_record_id"]
            questions.append(
                {
                    **question,
                    "contents": contents_by_question.get(question["question_id"], {}),
                    "options": options_by_question.get(question["question_id"], []),
                    "source_tags": tags_by_question.get(question["question_id"], []),
                    "source_audit_record_ids": audits_by_question.get(question["question_id"], []),
                    "primary_source": source_lookup[source_id],
                }
            )

        appearances = _rows(
            conn,
            "SELECT e.code AS exam_code, es.exam_date, pf.form_id, pf.set_code, pf.paper_number, "
            "pfs.form_section_id, pfs.locale_code AS stream_locale, bs.slot_code, s.section_code, "
            "qa.appearance_id, qa.question_id, qa.question_number, qa.sequence_in_section, qa.points, "
            "qa.source_record_id, sf.relative_path, sr.line_start, sr.line_end, sr.imported_from "
            "FROM question_appearances qa JOIN paper_form_sections pfs USING(form_section_id) "
            "JOIN paper_forms pf USING(form_id) JOIN exam_sessions es USING(session_id) JOIN exams e USING(exam_id) "
            "JOIN blueprint_sections bs USING(blueprint_section_id) JOIN sections s USING(section_id) "
            "JOIN source_records sr ON sr.source_record_id=qa.source_record_id JOIN source_files sf USING(source_file_id) "
            "ORDER BY e.code, es.exam_date, pf.form_id, bs.order_index, pfs.locale_code, qa.question_number"
        )

        stimulus_content: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        for row in _rows(conn, "SELECT * FROM stimulus_contents ORDER BY stimulus_id, locale_code"):
            stimulus_content[row["stimulus_id"]][row["locale_code"]] = {
                "raw_text": row["raw_text"],
                "display_text": row["display_text"],
                "instructions": row["instructions"],
                "content_format": row["content_format"],
                "structured": _decoded_json(row["structured_json"]),
                "source_record_id": row["source_record_id"],
            }
        links_by_stimulus: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in _rows(
            conn,
            "SELECT sl.stimulus_id, sl.appearance_id, sl.relation_code, sl.position, "
            "qa.question_id, qa.question_number, pfs.form_id, pfs.locale_code "
            "FROM stimulus_question_links sl JOIN question_appearances qa USING(appearance_id) "
            "JOIN paper_form_sections pfs USING(form_section_id) "
            "ORDER BY sl.stimulus_id, sl.position, pfs.form_id",
        ):
            links_by_stimulus[row["stimulus_id"]].append(row)
        stimuli = []
        for row in _rows(conn, "SELECT * FROM stimuli ORDER BY stimulus_id"):
            stimuli.append(
                {
                    **row,
                    "contents": stimulus_content.get(row["stimulus_id"], {}),
                    "question_appearances": links_by_stimulus.get(row["stimulus_id"], []),
                }
            )

        answer_rows = _rows(
            conn,
            "SELECT akv.answer_key_version_id, akv.form_id, akv.version_label, akv.authority_class, akv.status, "
            "akv.published_date, akv.authority_uri, akv.content_hash AS version_content_hash, "
            "akt.answer_key_table_id, akt.table_label, akt.raw_heading, akt.locale_code, akt.slot_code, "
            "akt.question_start, akt.question_end, ake.answer_key_entry_id, ake.appearance_id, ake.question_id, "
            "qa.question_number, ake.raw_answer, ake.answer_mode, ake.scalar_answer, ake.response_json, "
            "ake.source_record_id AS answer_source_record_id "
            "FROM answer_key_versions akv JOIN answer_key_tables akt USING(answer_key_version_id) "
            "JOIN answer_key_entries ake USING(answer_key_table_id) JOIN question_appearances qa USING(appearance_id) "
            "ORDER BY akv.form_id, akv.version_label, akt.table_label, qa.question_number"
        )
        option_links_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in _rows(
            conn,
            "SELECT aeo.answer_key_entry_id, aeo.option_id, aeo.position AS correct_option_order, "
            "qo.position AS option_position, qo.original_label "
            "FROM answer_key_entry_options aeo JOIN question_options qo USING(option_id, question_id) "
            "ORDER BY aeo.answer_key_entry_id, aeo.position",
        ):
            option_links_by_entry[row["answer_key_entry_id"]].append(row)
        answer_history = [
            {**row, "correct_options": option_links_by_entry.get(row["answer_key_entry_id"], [])}
            for row in answer_rows
        ]
        official_rows = [row for row in answer_history if row["authority_class"] == "exam_authority" and row["status"] == "final"]
        record_counts = {
            "questions": len(questions),
            "appearances": len(appearances),
            "stimuli": len(stimuli),
            "answer_key_history": len(answer_history),
            "official_final_answers": len(official_rows),
        }
        app_bundle = {
            "format": "xtet-question-bank",
            "format_version": 1,
            "metadata": {
                "database_content_hash": metadata["content_hash"],
                "source_manifest_hash": metadata["source_manifest_hash"],
                "database_schema_version": metadata["schema_version"],
                "exam_codes": sorted({row["exam_code"] for row in appearances}),
                "record_counts": record_counts,
            },
            "questions": questions,
            "appearances": appearances,
            "stimuli": stimuli,
            "answer_key_history": answer_history,
            "official_final_answers": official_rows,
        }
        app_bundle_bytes = (canonical_json(app_bundle) + "\n").encode("utf-8")

        output_dir.mkdir(parents=True, exist_ok=True)
        payloads: dict[str, bytes] = {}
        payloads["questions.ndjson"] = _write_ndjson(output_dir / "questions.ndjson", questions)
        payloads["appearances.ndjson"] = _write_ndjson(output_dir / "appearances.ndjson", appearances)
        payloads["stimuli.ndjson"] = _write_ndjson(output_dir / "stimuli.ndjson", stimuli)
        payloads["answer-key-history.ndjson"] = _write_ndjson(output_dir / "answer-key-history.ndjson", answer_history)
        payloads["official-final-answers.ndjson"] = _write_ndjson(output_dir / "official-final-answers.ndjson", official_rows)
        payloads["question-bank.json"] = _write_bytes(output_dir / "question-bank.json", app_bundle_bytes)
        if app_json_path is not None:
            _write_bytes(app_json_path, app_bundle_bytes)
        export_manifest = {
            "export_version": 1,
            "content_hash": metadata["content_hash"],
            "source_manifest_hash": metadata["source_manifest_hash"],
            "database_schema_version": metadata["schema_version"],
            "record_counts": record_counts,
            "files": {
                name: {"byte_size": len(payload), "sha256": sha256_bytes(payload)}
                for name, payload in sorted(payloads.items())
            },
            "verification": {
                "content_hash": verification["content_hash"],
                "foreign_key_violations": verification["foreign_key_violations"],
                "fts_integrity": verification["fts_integrity"],
            },
        }
        manifest_bytes = (canonical_json(export_manifest) + "\n").encode("utf-8")
        temp_manifest = output_dir / "manifest.json.tmp"
        temp_manifest.write_bytes(manifest_bytes)
        os.replace(temp_manifest, output_dir / "manifest.json")
        return {
            "output_dir": str(output_dir),
            "app_json": str(app_json_path or (output_dir / "question-bank.json")),
            "manifest": export_manifest,
        }
    finally:
        conn.close()
