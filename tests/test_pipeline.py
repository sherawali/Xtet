from __future__ import annotations

import copy
import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.__main__ import parse_sources
from pipeline.database import rebuild_database, verify_database, write_data_quality_report
from pipeline.exports import export_database
from pipeline.source_validation import validate_utet_sources

ROOT = Path(__file__).resolve().parents[1]


class PipelineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.stage = parse_sources()
        cls.tempdir = tempfile.TemporaryDirectory(prefix="xtet-pipeline-test-")
        cls.temp_path = Path(cls.tempdir.name)
        cls.db_path = cls.temp_path / "xtet-test.sqlite"
        cls.build_result = rebuild_database(copy.deepcopy(cls.stage), cls.db_path)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tempdir.cleanup()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def test_source_json_schemas_and_record_counts(self) -> None:
        report = validate_utet_sources()
        self.assertEqual(report["schema_files_checked"], 12)
        self.assertEqual(report["errors"], 0)
        self.assertEqual(
            report["validated_records"],
            {"appearances.ndjson": 900, "forms.ndjson": 6, "questions.ndjson": 900, "stimuli.ndjson": 24},
        )

    def test_parsed_source_counts_and_ctet_canonicalization(self) -> None:
        counts = self.stage["diagnostics"]["stage_counts"]
        self.assertEqual(counts["questions"], {"ctet": 930, "utet": 900})
        self.assertEqual(counts["appearances"], {"ctet": 1050, "utet": 900})
        self.assertEqual(counts["stimuli"], 64)
        self.assertEqual(counts["stimulus_links"], 411)
        self.assertEqual(counts["answer_option_links"], 1968)
        self.assertEqual(len(self.stage["rows"]["question_review_records"]), 120)
        ctet_versions = [row for row in self.stage["rows"]["answer_key_versions"] if row["form_id"].startswith("ctet-")]
        self.assertEqual(len(ctet_versions), 5)
        self.assertTrue(all(row["authority_class"] == "exam_authority" and row["status"] == "final" for row in ctet_versions))
        utet_versions = [row for row in self.stage["rows"]["answer_key_versions"] if row["form_id"].startswith("utet-")]
        self.assertEqual(len(utet_versions), 6)
        self.assertTrue(all(row["authority_class"] == "source_repository" and row["status"] == "provisional" for row in utet_versions))

    def test_raw_provenance_and_source_snapshot(self) -> None:
        self.assertEqual(len(self.stage["rows"]["source_files"]), 109)
        self.assertGreaterEqual(len(self.stage["rows"]["source_records"]), 4900)
        utet_files = [row for row in self.stage["rows"]["source_files"] if row["relative_path"].startswith("data/utet/bank-v2/")]
        self.assertTrue(utet_files)
        self.assertTrue(all(row["upstream_commit"] == "6792637052eb0bcddd27b9290ddd082faa725a4d" for row in utet_files))
        self.assertTrue(all(row["license_id"] == "CC-BY-4.0" for row in utet_files))
        relative_path_by_file = {row["source_file_id"]: row["relative_path"] for row in self.stage["rows"]["source_files"]}
        question_records = [
            row for row in self.stage["rows"]["source_records"]
            if relative_path_by_file[row["source_file_id"]].endswith("questions.ndjson")
        ]
        self.assertTrue(question_records)
        self.assertTrue(all(row["line_start"] == row["line_end"] for row in question_records))
        self.assertTrue(all(row["raw_text"].endswith("\n") for row in question_records))

    def test_ctet_official_answer_key_spot_checks(self) -> None:
        conn = self.connect()
        try:
            def option_set(form_id: str, number: int, slot_code: str, locale: str | None = None) -> list[tuple[str, tuple[str, tuple[int, ...]]]]:
                sql = (
                    "SELECT pfs.locale_code, ake.raw_answer, qo.position "
                    "FROM answer_key_versions akv JOIN answer_key_tables akt USING(answer_key_version_id) "
                    "JOIN answer_key_entries ake USING(answer_key_table_id) "
                    "JOIN question_appearances qa USING(appearance_id) "
                    "JOIN paper_form_sections pfs USING(form_section_id) "
                    "JOIN blueprint_sections bs USING(blueprint_section_id) "
                    "JOIN answer_key_entry_options aeo USING(answer_key_entry_id) "
                    "JOIN question_options qo USING(option_id, question_id) "
                    "WHERE akv.form_id=? AND qa.question_number=? AND bs.slot_code=? "
                )
                args: list[object] = [form_id, number, slot_code]
                if locale is not None:
                    sql += " AND pfs.locale_code=?"
                    args.append(locale)
                sql += " ORDER BY pfs.locale_code, aeo.position"
                rows = conn.execute(sql, args).fetchall()
                by_locale = {}
                for row in rows:
                    value = by_locale.setdefault(row[0], {"raw": row[1], "positions": []})
                    value["positions"].append(row[2])
                return [(locale_code, (value["raw"], tuple(value["positions"]))) for locale_code, value in sorted(by_locale.items())]

            self.assertEqual(option_set("ctet-2023-08-20-set-a", 40, "mathematics"), [("hi", ("A", (1, 2)))])
            self.assertEqual(option_set("ctet-2024-01-21-set-i", 80, "environmental-studies"), [("mul", ("Z", (1, 2, 3, 4)))])
            self.assertEqual(option_set("ctet-2024-01-21-set-i", 106, "language-1"), [("en", ("E", (2, 4))), ("hi", ("E", (2, 4)))])
            self.assertEqual(option_set("ctet-2024-07-07-set-a", 35, "mathematics"), [("mul", ("Z", (1, 2, 3, 4)))])
            self.assertEqual(option_set("ctet-2024-07-07-set-a", 48, "mathematics"), [("mul", ("Z", (1, 2, 3, 4)))])
            self.assertEqual(option_set("ctet-2024-07-07-set-a", 63, "environmental-studies"), [("mul", ("D", (2, 3)))])
            self.assertEqual(option_set("ctet-2024-07-07-set-a", 90, "environmental-studies"), [("mul", ("A", (1, 2)))])
            self.assertEqual(option_set("ctet-2024-07-07-set-a", 136, "language-2"), [("en", ("B", (1, 3))), ("hi", ("B", (1, 3)))])
            self.assertEqual(option_set("ctet-2026-02-08-set-e", 26, "cpd"), [("mul", ("F", (3, 4)))])
            self.assertEqual(option_set("ctet-2026-02-08-set-e", 125, "language-2", "en"), [("en", ("F", (3, 4)))])
            self.assertEqual(option_set("ctet-2021-01-31-set-i", 90, "environmental-studies"), [("mul", ("3", (3,)))])
            self.assertEqual(option_set("ctet-2021-01-31-set-i", 145, "language-2", "en"), [("en", ("3", (3,)))])
            self.assertEqual(option_set("ctet-2021-01-31-set-i", 106, "language-1", "hi"), [("hi", ("2", (2,)))])
        finally:
            conn.close()

    def test_database_integrity_and_authority_boundary(self) -> None:
        result = verify_database(self.db_path)
        self.assertEqual(result["integrity_check"], "ok")
        self.assertEqual(result["foreign_key_violations"], 0)
        self.assertEqual(result["fts_integrity"], "ok")
        self.assertEqual(result["official_final_answers"], 1050)
        self.assertEqual(result["provisional_repository_answers"], 900)
        self.assertEqual(result["table_counts"]["questions"], 1830)
        self.assertEqual(result["table_counts"]["question_search_documents"], 2850)
        conn = self.connect()
        try:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM v_official_final_answers WHERE form_id LIKE 'utet-%'").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM v_official_final_answers WHERE form_id LIKE 'ctet-%'").fetchone()[0], 1050)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM taxonomy_nodes").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM explanations").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0], 0)
            key = json.loads(
                conn.execute(
                    "SELECT options_json FROM v_question_locales WHERE question_id=? AND locale_code='en'",
                    ("ctet-2024-07-07-set-a-cpd-q001",),
                ).fetchone()[0]
            )
            self.assertEqual(len(key), 4)
        finally:
            conn.close()

    def test_rebuild_content_hash_is_deterministic(self) -> None:
        second = self.temp_path / "xtet-test-second.sqlite"
        result = rebuild_database(copy.deepcopy(self.stage), second)
        self.assertEqual(self.build_result["content_hash"], result["content_hash"])
        self.assertEqual(self.build_result["table_counts"], result["table_counts"])
        shipped_db = ROOT / "data" / "xtet-question-bank.sqlite"
        if shipped_db.exists():
            shipped = verify_database(shipped_db)
            self.assertEqual(self.build_result["content_hash"], shipped["content_hash"])

    def test_all_documented_sql_examples_execute(self) -> None:
        text = (ROOT / "docs" / "QUERIES.md").read_text(encoding="utf-8")
        queries = re.findall(r"```sql\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        self.assertGreaterEqual(len(queries), 20)
        conn = self.connect()
        try:
            for index, query in enumerate(queries, 1):
                with self.subTest(query=index):
                    self.assertTrue(query.strip().lower().startswith(("select", "with")))
                    conn.execute(query).fetchall()
        finally:
            conn.close()

    def test_data_quality_report_is_reproducible_and_honest(self) -> None:
        output = self.temp_path / "DATA_QUALITY.md"
        write_data_quality_report(self.db_path, output)
        report = output.read_text(encoding="utf-8")
        self.assertIn(self.stage["meta"]["source_manifest_hash"], report)
        self.assertIn("source_repository", report)
        self.assertIn("provisional", report)
        self.assertIn("transcription", report)
        self.assertIn("ctet-2023-08-20-set-a", report)

    def test_app_ready_exports_are_deterministic_and_authority_scoped(self) -> None:
        first_dir = self.temp_path / "export-one"
        second_dir = self.temp_path / "export-two"
        first = export_database(self.db_path, first_dir)
        second = export_database(self.db_path, second_dir)
        self.assertEqual(first["manifest"], second["manifest"])
        self.assertEqual(first["manifest"]["record_counts"]["questions"], 1830)
        self.assertEqual(first["manifest"]["record_counts"]["official_final_answers"], 1050)
        for name in first["manifest"]["files"]:
            self.assertEqual((first_dir / name).read_bytes(), (second_dir / name).read_bytes())
        history = [json.loads(line) for line in (first_dir / "answer-key-history.ndjson").read_text(encoding="utf-8").splitlines()]
        official = [json.loads(line) for line in (first_dir / "official-final-answers.ndjson").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(history), 1950)
        self.assertEqual(len(official), 1050)
        self.assertTrue(all(row["authority_class"] == "exam_authority" and row["status"] == "final" for row in official))
        self.assertTrue(any(row["authority_class"] == "source_repository" for row in history))


if __name__ == "__main__":
    unittest.main()
