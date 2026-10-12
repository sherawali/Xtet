from __future__ import annotations

import calendar
import json
import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from .common import ROOT, canonical_json, sha256_bytes
from .database import verify_database

PAPER_ROMAN_NUMERALS = {1: "I", 2: "II"}


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


def _relative_path(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _paper_title(exam_code: str, exam_date: str, paper_number: int | None, set_code: str | None) -> str:
    """Deterministic human-readable label, e.g. ``CTET Feb 2026 Paper I (Set E)``."""
    try:
        year_text, month_text, _day = exam_date.split("-")
        month = calendar.month_abbr[int(month_text)]
        year: Any = int(year_text)
    except (AttributeError, TypeError, ValueError):
        return " ".join(part for part in (exam_code, f"Paper {paper_number}" if paper_number else None, f"(Set {set_code})" if set_code else None) if part)
    paper_label = PAPER_ROMAN_NUMERALS.get(paper_number, str(paper_number) if paper_number else "")
    title = f"{exam_code} {month} {year}".rstrip()
    if paper_label:
        title = f"{title} Paper {paper_label}"
    if set_code:
        title = f"{title} (Set {set_code})"
    return title


def _answer_rank(row: dict[str, Any]) -> tuple[int, str, str]:
    is_official = row["authority_class"] == "exam_authority" and row["status"] == "final"
    return (1 if is_official else 0, row["answer_key_version_id"], row["answer_key_entry_id"])


def _count_bucket() -> dict[str, Any]:
    return {"appearance_count": 0, "official_answer_count": 0, "provisional_answer_count": 0, "question_numbers": set(), "locales": set()}


def _finalize_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    numbers = bucket["question_numbers"]
    return {
        "appearance_count": bucket["appearance_count"],
        "official_answer_count": bucket["official_answer_count"],
        "provisional_answer_count": bucket["provisional_answer_count"],
        "question_number_min": min(numbers) if numbers else None,
        "question_number_max": max(numbers) if numbers else None,
        "locales": sorted(bucket["locales"]),
    }


def export_database(
    db_path: Path,
    output_dir: Path,
    app_json_path: Path | None = None,
    app_manifest_path: Path | None = None,
) -> dict[str, Any]:
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

        # Reverse stimulus mapping: every appearance carries the stimulus ids that own its context text.
        stimulus_ids_by_appearance: dict[str, list[str]] = defaultdict(list)
        for stimulus_id, links in links_by_stimulus.items():
            for link in links:
                stimulus_ids_by_appearance[link["appearance_id"]].append(stimulus_id)

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

        # Denormalized convenience mirror only: the authority remains answer_key_history / official_final_answers.
        best_answer_by_appearance: dict[str, dict[str, Any]] = {}
        for row in answer_history:
            current = best_answer_by_appearance.get(row["appearance_id"])
            if current is None or _answer_rank(row) > _answer_rank(current):
                best_answer_by_appearance[row["appearance_id"]] = row
        answer_mirror_by_appearance: dict[str, dict[str, Any]] = {}
        for appearance_id, row in best_answer_by_appearance.items():
            answer_mirror_by_appearance[appearance_id] = {
                "answer_key_entry_id": row["answer_key_entry_id"],
                "answer_key_version_id": row["answer_key_version_id"],
                "authority_class": row["authority_class"],
                "status": row["status"],
                "is_official": row["authority_class"] == "exam_authority" and row["status"] == "final",
                "raw_answer": row["raw_answer"],
                "correct_option_positions": [link["option_position"] for link in row["correct_options"]],
                "correct_option_labels": [link["original_label"] for link in row["correct_options"]],
            }

        form_buckets: dict[str, dict[str, Any]] = defaultdict(_count_bucket)
        section_buckets: dict[str, dict[str, Any]] = defaultdict(_count_bucket)
        for row in appearances:
            row["stimulus_ids"] = sorted(stimulus_ids_by_appearance.get(row["appearance_id"], []))
            row["answer"] = answer_mirror_by_appearance.get(row["appearance_id"])
            mirror = row["answer"]
            for bucket in (form_buckets[row["form_id"]], section_buckets[row["form_section_id"]]):
                bucket["appearance_count"] += 1
                bucket["question_numbers"].add(row["question_number"])
                if row["stream_locale"]:
                    bucket["locales"].add(row["stream_locale"])
                if mirror is not None:
                    if mirror["is_official"]:
                        bucket["official_answer_count"] += 1
                    else:
                        bucket["provisional_answer_count"] += 1

        form_rows = _rows(
            conn,
            "SELECT e.code AS exam_code, e.name AS exam_name, es.session_id, es.session_label, es.exam_date, "
            "pf.form_id, pf.paper_number, pf.set_code, pf.booklet_code, pf.shift, pf.duration_minutes, "
            "pf.total_questions, pf.total_marks, pf.negative_marking "
            "FROM paper_forms pf JOIN exam_sessions es USING(session_id) JOIN exams e USING(exam_id) "
            "ORDER BY e.code, es.exam_date, pf.form_id",
        )
        section_rows = _rows(
            conn,
            "SELECT pfs.form_id, pfs.form_section_id, pfs.locale_code, s.section_code, s.name_en, s.name_hi, "
            "bs.slot_code, bs.order_index, bs.question_count, bs.question_start, bs.question_end "
            "FROM paper_form_sections pfs JOIN blueprint_sections bs USING(blueprint_section_id) "
            "JOIN sections s USING(section_id) "
            "ORDER BY pfs.form_id, bs.order_index, pfs.locale_code, pfs.form_section_id",
        )
        sections_by_form: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in section_rows:
            counts = _finalize_bucket(section_buckets.get(row["form_section_id"], _count_bucket()))
            sections_by_form[row["form_id"]].append(
                {
                    "form_section_id": row["form_section_id"],
                    "section_code": row["section_code"],
                    "name_en": row["name_en"],
                    "name_hi": row["name_hi"],
                    "slot_code": row["slot_code"],
                    "order_index": row["order_index"],
                    "locale_code": row["locale_code"],
                    "question_start": row["question_start"],
                    "question_end": row["question_end"],
                    "declared_question_count": row["question_count"],
                    "appearance_count": counts["appearance_count"],
                    "official_answer_count": counts["official_answer_count"],
                    "provisional_answer_count": counts["provisional_answer_count"],
                    "question_number_min": counts["question_number_min"],
                    "question_number_max": counts["question_number_max"],
                }
            )
        papers: list[dict[str, Any]] = []
        for row in form_rows:
            exam_date = row["exam_date"] or ""
            bucket = form_buckets.get(row["form_id"], _count_bucket())
            papers.append(
                {
                    "form_id": row["form_id"],
                    "exam_code": row["exam_code"],
                    "exam_name": row["exam_name"],
                    "session_id": row["session_id"],
                    "session_label": row["session_label"],
                    "exam_date": row["exam_date"],
                    "year": int(exam_date[:4]) if exam_date[:4].isdigit() else None,
                    "paper_number": row["paper_number"],
                    "set_code": row["set_code"],
                    "booklet_code": row["booklet_code"],
                    "shift": row["shift"],
                    "title": _paper_title(row["exam_code"], exam_date, row["paper_number"], row["set_code"]),
                    "duration_minutes": row["duration_minutes"],
                    "total_questions": row["total_questions"],
                    "total_marks": row["total_marks"],
                    "negative_marking": row["negative_marking"],
                    **_finalize_bucket(bucket),
                    "sections": sections_by_form.get(row["form_id"], []),
                }
            )

        record_counts = {
            "papers": len(papers),
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
                "importer_version": metadata["importer_version"],
                "exam_codes": sorted({row["exam_code"] for row in appearances}),
                "record_counts": record_counts,
            },
            "papers": papers,
            "questions": questions,
            "appearances": appearances,
            "stimuli": stimuli,
            "answer_key_history": answer_history,
            "official_final_answers": official_rows,
        }
        app_bundle_bytes = (canonical_json(app_bundle) + "\n").encode("utf-8")

        app_manifest = {
            "format": "xtet-question-bank-manifest",
            "format_version": 1,
            "bundle_format_version": app_bundle["format_version"],
            "importer_version": metadata["importer_version"],
            "database_schema_version": metadata["schema_version"],
            "database_content_hash": metadata["content_hash"],
            "source_manifest_hash": metadata["source_manifest_hash"],
            "record_counts": record_counts,
            "papers": [
                {
                    "form_id": paper["form_id"],
                    "exam_code": paper["exam_code"],
                    "title": paper["title"],
                    "exam_date": paper["exam_date"],
                    "year": paper["year"],
                    "paper_number": paper["paper_number"],
                    "set_code": paper["set_code"],
                    "appearance_count": paper["appearance_count"],
                    "official_answer_count": paper["official_answer_count"],
                    "provisional_answer_count": paper["provisional_answer_count"],
                    "has_official_answers": paper["official_answer_count"] > 0,
                    "locales": paper["locales"],
                }
                for paper in papers
            ],
            "bundle": {
                "path": _relative_path(app_json_path) if app_json_path is not None else "question-bank.json",
                "byte_size": len(app_bundle_bytes),
                "sha256": sha256_bytes(app_bundle_bytes),
            },
        }
        app_manifest_bytes = (canonical_json(app_manifest) + "\n").encode("utf-8")

        output_dir.mkdir(parents=True, exist_ok=True)
        payloads: dict[str, bytes] = {}
        payloads["papers.ndjson"] = _write_ndjson(output_dir / "papers.ndjson", papers)
        payloads["questions.ndjson"] = _write_ndjson(output_dir / "questions.ndjson", questions)
        payloads["appearances.ndjson"] = _write_ndjson(output_dir / "appearances.ndjson", appearances)
        payloads["stimuli.ndjson"] = _write_ndjson(output_dir / "stimuli.ndjson", stimuli)
        payloads["answer-key-history.ndjson"] = _write_ndjson(output_dir / "answer-key-history.ndjson", answer_history)
        payloads["official-final-answers.ndjson"] = _write_ndjson(output_dir / "official-final-answers.ndjson", official_rows)
        payloads["question-bank.json"] = _write_bytes(output_dir / "question-bank.json", app_bundle_bytes)
        payloads["app-manifest.json"] = _write_bytes(output_dir / "app-manifest.json", app_manifest_bytes)
        if app_json_path is not None:
            _write_bytes(app_json_path, app_bundle_bytes)
        if app_manifest_path is not None:
            _write_bytes(app_manifest_path, app_manifest_bytes)
        export_manifest = {
            "export_version": 2,
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
            "app_manifest": str(app_manifest_path) if app_manifest_path is not None else str(output_dir / "app-manifest.json"),
            "manifest": export_manifest,
        }
    finally:
        conn.close()
