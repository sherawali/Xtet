from __future__ import annotations

import copy
import hashlib
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
        bundle_path = first_dir / "question-bank.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        self.assertEqual(bundle["format"], "xtet-question-bank")
        self.assertEqual(bundle["format_version"], 1)
        self.assertEqual(bundle["metadata"]["database_content_hash"], self.build_result["content_hash"])
        self.assertEqual(bundle["metadata"]["exam_codes"], ["CTET", "UTET"])
        self.assertEqual(bundle["metadata"]["record_counts"], first["manifest"]["record_counts"])
        self.assertEqual(len(bundle["questions"]), 1830)
        self.assertEqual(len(bundle["appearances"]), 1950)
        shipped_json = ROOT / "data" / "xtet-question-bank.json"
        if shipped_json.exists():
            self.assertEqual(shipped_json.read_bytes(), bundle_path.read_bytes())
        history = [json.loads(line) for line in (first_dir / "answer-key-history.ndjson").read_text(encoding="utf-8").splitlines()]
        official = [json.loads(line) for line in (first_dir / "official-final-answers.ndjson").read_text(encoding="utf-8").splitlines()]
        papers_ndjson = [json.loads(line) for line in (first_dir / "papers.ndjson").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(history), 1950)
        self.assertEqual(len(official), 1050)
        self.assertEqual(len(papers_ndjson), 11)
        self.assertEqual(bundle["metadata"]["record_counts"]["papers"], 11)
        self.assertTrue(all(row["authority_class"] == "exam_authority" and row["status"] == "final" for row in official))
        self.assertTrue(any(row["authority_class"] == "source_repository" for row in history))
        shipped_manifest = ROOT / "data" / "xtet-question-bank.manifest.json"
        if shipped_json.exists() and shipped_manifest.exists():
            shipped = json.loads(shipped_manifest.read_text(encoding="utf-8"))
            self.assertEqual(shipped["format"], "xtet-question-bank-manifest")
            self.assertEqual(shipped["bundle"]["sha256"], hashlib.sha256(shipped_json.read_bytes()).hexdigest())
            self.assertEqual(shipped["bundle"]["byte_size"], shipped_json.stat().st_size)
            self.assertEqual(shipped["database_content_hash"], self.build_result["content_hash"])
            self.assertEqual([paper["form_id"] for paper in shipped["papers"]], [paper["form_id"] for paper in bundle["papers"]])

    def test_app_bundle_papers_and_denormalized_mirrors(self) -> None:
        export_dir = self.temp_path / "export-mirrors"
        app_json = self.temp_path / "xtet-app.json"
        app_manifest = self.temp_path / "xtet-app.manifest.json"
        result = export_database(self.db_path, export_dir, app_json, app_manifest)
        bundle = json.loads(app_json.read_text(encoding="utf-8"))
        manifest = json.loads(app_manifest.read_text(encoding="utf-8"))

        papers = {paper["form_id"]: paper for paper in bundle["papers"]}
        self.assertEqual(len(papers), 11)
        feb_2026 = papers["ctet-2026-02-08-set-e"]
        self.assertEqual(feb_2026["title"], "CTET Feb 2026 Paper I (Set E)")
        self.assertEqual(feb_2026["year"], 2026)
        self.assertEqual(feb_2026["exam_code"], "CTET")
        self.assertEqual(feb_2026["appearance_count"], 210)
        self.assertEqual(feb_2026["official_answer_count"], 210)
        self.assertEqual(feb_2026["provisional_answer_count"], 0)
        self.assertEqual((feb_2026["question_number_min"], feb_2026["question_number_max"]), (1, 150))
        self.assertEqual([section["section_code"] for section in feb_2026["sections"]][:3], ["cpd", "mathematics", "environmental-studies"])
        self.assertTrue(all(section["declared_question_count"] == section["appearance_count"] for section in feb_2026["sections"]))
        utet_2020 = papers["utet-p1-2020-set-a"]
        self.assertEqual(utet_2020["title"], "UTET Nov 2020 Paper I (Set A)")
        self.assertEqual(utet_2020["official_answer_count"], 0)
        self.assertEqual(utet_2020["provisional_answer_count"], 150)
        self.assertTrue(all(paper["exam_date"] and paper["year"] and paper["paper_number"] == 1 for paper in papers.values()))
        self.assertFalse(any(paper["form_id"].startswith("ctet-") and paper["provisional_answer_count"] for paper in papers.values()))

        self.assertEqual(manifest["format"], "xtet-question-bank-manifest")
        self.assertEqual(manifest["bundle_format_version"], bundle["format_version"])
        self.assertEqual(manifest["bundle"]["path"], app_json.resolve().as_posix())
        self.assertEqual(manifest["bundle"]["byte_size"], app_json.stat().st_size)
        self.assertEqual(manifest["bundle"]["sha256"], hashlib.sha256(app_json.read_bytes()).hexdigest())
        self.assertEqual([paper["form_id"] for paper in manifest["papers"]], [paper["form_id"] for paper in bundle["papers"]])
        self.assertEqual(manifest["record_counts"], bundle["metadata"]["record_counts"])
        self.assertTrue(all(paper["has_official_answers"] is (paper["official_answer_count"] > 0) for paper in manifest["papers"]))
        self.assertEqual(result["app_manifest"], str(app_manifest))
        self.assertEqual((export_dir / "app-manifest.json").read_bytes(), app_manifest.read_bytes())

        appearances = bundle["appearances"]
        self.assertTrue(all({"stimulus_ids", "answer"} <= set(appearance) for appearance in appearances))
        with_stimulus = [appearance for appearance in appearances if appearance["stimulus_ids"]]
        self.assertEqual(len(with_stimulus), 411)
        self.assertEqual(sum(len(appearance["stimulus_ids"]) for appearance in appearances), 411)
        answered = [appearance for appearance in appearances if appearance["answer"] is not None]
        self.assertEqual(len(answered), 1950)
        official_mirror = [appearance for appearance in answered if appearance["answer"]["is_official"]]
        self.assertEqual(len(official_mirror), 1050)
        self.assertTrue(all(appearance["exam_code"] == "CTET" for appearance in official_mirror))
        self.assertTrue(
            all(appearance["answer"]["status"] == "provisional" for appearance in answered if not appearance["answer"]["is_official"])
        )

        authority = {row["appearance_id"]: row for row in bundle["official_final_answers"]}
        for appearance in official_mirror:
            row = authority[appearance["appearance_id"]]
            self.assertEqual(appearance["answer"]["answer_key_entry_id"], row["answer_key_entry_id"])
            self.assertEqual(appearance["answer"]["raw_answer"], row["raw_answer"])
            self.assertEqual(appearance["answer"]["correct_option_positions"], [link["option_position"] for link in row["correct_options"]])
            self.assertEqual(appearance["answer"]["correct_option_labels"], [link["original_label"] for link in row["correct_options"]])
        self.assertTrue(any(len(appearance["answer"]["correct_option_positions"]) > 1 for appearance in official_mirror))

        stimulus_side = {link["appearance_id"]: stimulus["stimulus_id"] for stimulus in bundle["stimuli"] for link in stimulus["question_appearances"]}
        for appearance in with_stimulus:
            self.assertEqual(appearance["stimulus_ids"], [stimulus_side[appearance["appearance_id"]]])
        for appearance in appearances:
            if appearance["appearance_id"] not in stimulus_side:
                self.assertEqual(appearance["stimulus_ids"], [])


if __name__ == "__main__":
    unittest.main()
