from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .common import (
    ROOT,
    PipelineError,
    SourceError,
    add_assertion,
    add_row,
    add_source_file,
    add_source_record,
    canonical_hash,
    canonical_json,
    lines_with_endings,
    stable_id,
)
from .source_validation import UTET_ROOT, validate_utet_sources

UPSTREAM_REPO = "https://github.com/sherawali/tet"
UPSTREAM_COMMIT = "6792637052eb0bcddd27b9290ddd082faa725a4d"
LICENSE_ID = "CC-BY-4.0"
ATTRIBUTION = "TET Question Bank contributors (2026)"
SECTION_MAP = {
    "cdp": ("cdp", "Child Development and Pedagogy", 1),
    "language-1": ("language-1", "Language I", 2),
    "language-2": ("language-2", "Language II", 3),
    "mathematics": ("mathematics", "Mathematics", 4),
    "environmental-studies": ("environmental-studies", "Environmental Studies", 5),
}


def _upstream_uri(relative: str) -> str:
    upstream_path = relative
    if relative.startswith("data/utet/"):
        upstream_path = relative.removeprefix("data/utet/")
    return f"{UPSTREAM_REPO}/blob/{UPSTREAM_COMMIT}/{upstream_path}"


def _load_json_lines(path: Path, stage: dict[str, Any]) -> tuple[str, list[tuple[int, dict[str, Any], str]]]:
    relative = path.relative_to(ROOT).as_posix()
    file_id, _, text = add_source_file(
        stage,
        path,
        source_uri=_upstream_uri(relative),
        upstream_repo=UPSTREAM_REPO,
        upstream_commit=UPSTREAM_COMMIT,
        license_id=LICENSE_ID,
        attribution=ATTRIBUTION,
    )
    parsed: list[tuple[int, dict[str, Any], str]] = []
    lines = lines_with_endings(text)
    for line_number, raw_line in enumerate(lines, 1):
        if not raw_line.strip():
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise SourceError(relative, line_number, f"invalid NDJSON: {exc.msg}") from exc
        record = add_source_record(
            stage,
            source_file_id=file_id,
            relative_path=relative,
            line_start=line_number,
            line_end=line_number,
            raw_text=raw_line,
            extraction_method="utet-bank-v2-ndjson-line-v1",
            imported_from=f"sherawali/tet@{UPSTREAM_COMMIT}:{relative}#{line_number}",
        )
        parsed.append((line_number, obj, record))
    return file_id, parsed


def _load_json_document(path: Path, stage: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
    relative = path.relative_to(ROOT).as_posix()
    file_id, _, text = add_source_file(
        stage,
        path,
        source_uri=_upstream_uri(relative),
        upstream_repo=UPSTREAM_REPO,
        upstream_commit=UPSTREAM_COMMIT,
        license_id=LICENSE_ID,
        attribution=ATTRIBUTION,
    )
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SourceError(relative, exc.lineno, f"invalid JSON: {exc.msg}") from exc
    count = max(1, len(text.splitlines()))
    record = add_source_record(
        stage,
        source_file_id=file_id,
        relative_path=relative,
        line_start=1,
        line_end=count,
        raw_text=text,
        extraction_method="utet-bank-v2-json-document-v1",
        imported_from=f"sherawali/tet@{UPSTREAM_COMMIT}:{relative}",
    )
    return file_id, obj, record


def _all_vendor_sources(stage: dict[str, Any]) -> None:
    for path in sorted(UTET_ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix == ".ndjson":
            # The actual rows are captured by _load_json_lines; register empty streams too.
            add_source_file(
                stage,
                path,
                source_uri=_upstream_uri(relative),
                upstream_repo=UPSTREAM_REPO,
                upstream_commit=UPSTREAM_COMMIT,
                license_id=LICENSE_ID,
                attribution=ATTRIBUTION,
            )
        else:
            add_source_file(
                stage,
                path,
                source_uri=_upstream_uri(relative),
                upstream_repo=UPSTREAM_REPO,
                upstream_commit=UPSTREAM_COMMIT,
                license_id=LICENSE_ID,
                attribution=ATTRIBUTION,
            )


def _locale_blocks(blocks: list[dict[str, Any]], available: list[str], path: str, line: int, field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = defaultdict(lambda: {"text": [], "blocks": []})
    for block in blocks:
        kind = block.get("kind", "markdown")
        localized = block.get("text")
        if not isinstance(localized, dict):
            raise SourceError(path, line, f"{field} content block is missing a localized `text` mapping")
        for locale in available:
            if locale not in localized:
                raise SourceError(path, line, f"{field} lacks required locale {locale!r}")
            raw = localized[locale]
            if not isinstance(raw, str):
                raise SourceError(path, line, f"{field} locale {locale!r} must be text, found {type(raw).__name__}")
            result[locale]["text"].append(raw)
            result[locale]["blocks"].append({"kind": kind, "text": raw})
    return {locale: {"raw_text": "\n\n".join(value["text"]), "blocks": value["blocks"]} for locale, value in result.items()}


def _module_code(module: dict[str, Any]) -> tuple[str, str, int, str, str]:
    section = module.get("section")
    language_slot = module.get("languageSlot")
    if section == "language":
        if language_slot not in (1, 2) or module.get("language") not in ("hi", "en"):
            raise PipelineError(f"Unsupported UTET language module in form metadata: {module}")
        slot = f"language-{language_slot}"
        return slot, slot, 2 if language_slot == 1 else 3, module["language"], "language"
    if section not in SECTION_MAP or section.startswith("language-"):
        raise PipelineError(f"Unknown UTET source module section {section!r}")
    code, _, order = SECTION_MAP[section]
    locale = "mul" if section in ("cdp", "mathematics", "environmental-studies") else module.get("language")
    return code, code, order, locale, section


def _source_assertions(stage: dict[str, Any], source_record_id: str, scope: str, values: dict[str, Any]) -> None:
    for key, value in sorted(values.items()):
        add_assertion(stage, source_record_id, key, scope, value)


def _register_file_record(
    stage: dict[str, Any],
    path: Path,
    *,
    method: str,
    imported_from: str,
) -> tuple[str, str]:
    relative = path.relative_to(ROOT).as_posix()
    file_id, _, text = add_source_file(
        stage,
        path,
        source_uri=_upstream_uri(relative),
        upstream_repo=UPSTREAM_REPO,
        upstream_commit=UPSTREAM_COMMIT,
        license_id=LICENSE_ID,
        attribution=ATTRIBUTION,
    )
    line_count = max(1, len(text.splitlines()))
    record_id = add_source_record(
        stage,
        source_file_id=file_id,
        relative_path=relative,
        line_start=1,
        line_end=line_count,
        raw_text=text,
        extraction_method=method,
        imported_from=imported_from,
    )
    return file_id, record_id


def parse_utet(stage: dict[str, Any]) -> dict[str, Any]:
    schema_report = validate_utet_sources()
    _all_vendor_sources(stage)

    # Also retain the snapshot/notice as project-local provenance documentation.
    for path in (ROOT / "data" / "utet" / "SNAPSHOT.json", ROOT / "data" / "utet" / "NOTICE.md"):
        if path.exists():
            source_file_id, _, text = add_source_file(stage, path)
            lines = lines_with_endings(text)
            add_source_record(
                stage,
                source_file_id=source_file_id,
                relative_path=path.relative_to(ROOT).as_posix(),
                line_start=1,
                line_end=max(1, len(lines)),
                raw_text=text,
                extraction_method="project-source-snapshot-note-v1",
                imported_from=path.relative_to(ROOT).as_posix(),
            )

    forms_path = UTET_ROOT / "paper-forms" / "utet" / "paper-1" / "forms.ndjson"
    appearances_path = UTET_ROOT / "paper-forms" / "utet" / "paper-1" / "appearances.ndjson"
    forms_file_id, form_rows = _load_json_lines(forms_path, stage)
    appearances_file_id, appearance_rows = _load_json_lines(appearances_path, stage)

    questions_by_id: dict[str, tuple[dict[str, Any], str, str, int]] = {}
    question_stream_counts: Counter[str] = Counter()
    question_rows: list[tuple[dict[str, Any], str, str, int, str]] = []
    for path in sorted((UTET_ROOT / "exams" / "utet" / "paper-1").rglob("questions.ndjson")):
        file_id, rows = _load_json_lines(path, stage)
        for line_number, question, record_id in rows:
            source_path = path.relative_to(ROOT).as_posix()
            question_id = question["id"]
            if question_id in questions_by_id:
                raise SourceError(source_path, line_number, f"duplicate UTET question id {question_id}")
            questions_by_id[question_id] = (question, record_id, file_id, line_number)
            stream = path.parent.relative_to(UTET_ROOT / "exams" / "utet" / "paper-1").as_posix()
            question_stream_counts[stream] += 1
            question_rows.append((question, record_id, file_id, line_number, source_path))
    if len(questions_by_id) != 900:
        raise PipelineError(f"UTET source contains {len(questions_by_id)} questions; expected 900")

    stimulus_rows: list[tuple[dict[str, Any], str, str, int, str]] = []
    stimuli_by_id: dict[str, tuple[dict[str, Any], str, str, int]] = {}
    for path in sorted((UTET_ROOT / "exams" / "utet" / "paper-1").rglob("stimuli.ndjson")):
        file_id, rows = _load_json_lines(path, stage)
        for line_number, stimulus, record_id in rows:
            source_path = path.relative_to(ROOT).as_posix()
            if stimulus["id"] in stimuli_by_id:
                raise SourceError(source_path, line_number, f"duplicate UTET stimulus id {stimulus['id']}")
            stimuli_by_id[stimulus["id"]] = (stimulus, record_id, file_id, line_number)
            stimulus_rows.append((stimulus, record_id, file_id, line_number, source_path))
    if len(stimuli_by_id) != 24:
        raise PipelineError(f"UTET source contains {len(stimuli_by_id)} stimuli; expected 24")

    audit_by_question: dict[str, tuple[dict[str, Any], str, int, str]] = {}
    audit_count = 0
    for path in sorted((UTET_ROOT / "audits").glob("utet-p1-*-question-audit.ndjson")):
        _, rows = _load_json_lines(path, stage)
        for line_number, audit, record_id in rows:
            source_path = path.relative_to(ROOT).as_posix()
            question_id = audit["questionId"]
            if question_id in audit_by_question:
                raise SourceError(source_path, line_number, f"duplicate audit record for {question_id}")
            audit_by_question[question_id] = (audit, record_id, line_number, source_path)
            audit_count += 1
    if audit_count != 900 or set(audit_by_question) != set(questions_by_id):
        raise PipelineError(f"UTET audits must cover each of 900 question IDs exactly once; found {audit_count}")

    manifests_by_year: dict[str, str] = {}
    for path in sorted((UTET_ROOT / "sources").glob("utet-p1-*-sources.json")):
        _, manifest, record_id = _load_json_document(path, stage)
        manifests_by_year[str(manifest["cycleLabel"])] = record_id
    if len(manifests_by_year) != 6:
        raise PipelineError(f"Expected six UTET source manifests, found {len(manifests_by_year)}")

    # Retain the top-level upstream license and bank README as provenance sources.
    license_path = ROOT / "data" / "utet" / "LICENSE"
    if license_path.exists():
        _register_file_record(stage, license_path, method="upstream-license-document-v1", imported_from="sherawali/tet@pinned:LICENSE")
    bank_readme = UTET_ROOT / "README.md"
    if bank_readme.exists():
        _register_file_record(stage, bank_readme, method="upstream-bank-readme-v1", imported_from=f"sherawali/tet@{UPSTREAM_COMMIT}:bank-v2/README.md")

    # Create catalog/form rows. Module order and question numbers come from source form/appearance metadata.
    if not any(row["exam_id"] == "utet" for row in stage["rows"]["exams"]):
        first_form_record = form_rows[0][2]
        add_row(
            stage,
            "exams",
            {
                "exam_id": "utet",
                "code": "UTET",
                "name": "Uttarakhand Teacher Eligibility Test",
                "conducting_authority": "UBSE (source attribution; not independently verified)",
                "source_record_id": first_form_record,
            },
        )

    form_module_config: dict[str, list[dict[str, Any]]] = {}
    form_rows_by_id: dict[str, tuple[dict[str, Any], str, int]] = {}
    all_appearance_by_id = {row[1]["id"]: (row[1], row[2], row[0]) for row in appearance_rows}
    if len(all_appearance_by_id) != 900:
        raise PipelineError(f"UTET appearance IDs are not unique: {len(all_appearance_by_id)} unique from 900 source rows")

    module_blueprint = None
    blueprint_record_id = form_rows[0][2]
    for line_number, form, form_record in form_rows:
        form_id = form["id"]
        if form_id in form_rows_by_id:
            raise SourceError(forms_path.relative_to(ROOT).as_posix(), line_number, f"duplicate form id {form_id}")
        form_rows_by_id[form_id] = (form, form_record, line_number)
        date = form["examDate"]
        session_id = f"utet-session-{date}"
        source_manifest_record = manifests_by_year.get(str(date[:4]), form_record)
        add_row(
            stage,
            "exam_sessions",
            {
                "session_id": session_id,
                "exam_id": "utet",
                "session_label": f"UTET {date[:4]}",
                "exam_date": date,
                "source_record_id": source_manifest_record,
            },
        )
        add_row(
            stage,
            "paper_forms",
            {
                "form_id": form_id,
                "session_id": session_id,
                "paper_number": int(form["paper"]),
                "set_code": form["setCode"],
                "booklet_code": None,
                "shift": int(form["shift"]) if form.get("shift") is not None else None,
                "duration_minutes": int(form["durationMinutes"]) if form.get("durationMinutes") is not None else None,
                "total_questions": int(form["totalQuestions"]),
                "total_marks": float(form["totalMarks"]),
                "negative_marking": float(form["negativeMarking"]) if form.get("negativeMarking") is not None else None,
                "source_record_id": form_record,
            },
        )
        add_assertion(stage, form_record, "verificationStatus", "paper-form", form.get("verificationStatus"))
        add_assertion(stage, form_record, "sourceRef", "paper-form", form.get("sourceRef"))
        modules: list[dict[str, Any]] = []
        for module_order, module in enumerate(form["modules"], 1):
            slot_code, section_code, order_index, locale_code, section_source_code = _module_code(module)
            if module_order != order_index:
                raise SourceError(
                    forms_path.relative_to(ROOT).as_posix(),
                    line_number,
                    f"form {form_id}: module {module['id']} at source order {module_order}, expected order {order_index}",
                )
            mapped_appearances: list[tuple[dict[str, Any], str, int]] = []
            for appearance_id in module["appearanceIds"]:
                if appearance_id not in all_appearance_by_id:
                    raise SourceError(forms_path.relative_to(ROOT).as_posix(), line_number, f"module {module['id']} references missing appearance {appearance_id}")
                appearance, appearance_record, appearance_line = all_appearance_by_id[appearance_id]
                if appearance["paperFormId"] != form_id or appearance["section"] != module["section"]:
                    raise SourceError(appearances_path.relative_to(ROOT).as_posix(), appearance_line, f"appearance {appearance_id} does not match form/module {form_id}/{module['id']}")
                mapped_appearances.append((appearance, appearance_record, appearance_line))
            if len(mapped_appearances) != int(module["questionCount"]):
                raise SourceError(forms_path.relative_to(ROOT).as_posix(), line_number, f"module {module['id']} declares {module['questionCount']} questions but lists {len(mapped_appearances)} appearance IDs")
            numbers = sorted(row[0]["questionNumber"] for row in mapped_appearances)
            if numbers != list(range(numbers[0], numbers[-1] + 1)) or len(numbers) != 30:
                raise SourceError(forms_path.relative_to(ROOT).as_posix(), line_number, f"module {module['id']} question numbers are not one contiguous 30-question range: {numbers}")
            modules.append(
                {
                    "module": module,
                    "source_record_id": form_record,
                    "slot_code": slot_code,
                    "section_code": section_code,
                    "order_index": order_index,
                    "locale_code": locale_code,
                    "section_source_code": section_source_code,
                    "question_start": numbers[0],
                    "question_end": numbers[-1],
                    "appearance_ids": list(module["appearanceIds"]),
                }
            )
        if sum(m["module"]["questionCount"] for m in modules) != int(form["totalQuestions"]):
            raise SourceError(forms_path.relative_to(ROOT).as_posix(), line_number, f"form {form_id}: module question counts do not total {form['totalQuestions']}")
        structure = [
            (m["slot_code"], m["order_index"], m["question_start"], m["question_end"], m["locale_code"])
            for m in modules
        ]
        if module_blueprint is None:
            module_blueprint = structure
        elif module_blueprint != structure:
            raise SourceError(forms_path.relative_to(ROOT).as_posix(), line_number, "UTET module blueprint differs across source forms; create an explicit blueprint version")
        form_module_config[form_id] = modules

    utet_blueprint_id = "utet-paper-1-blueprint-v1"
    blueprint_hash = canonical_hash(module_blueprint)
    add_row(
        stage,
        "blueprint_versions",
        {
            "blueprint_id": utet_blueprint_id,
            "exam_id": "utet",
            "paper_number": 1,
            "version_number": 1,
            "label": "UTET Paper I source schema v1",
            "expected_questions": 150,
            "total_marks": 150.0,
            "duration_minutes": 150,
            "status": "active",
            "rules_json": canonical_json({"module_selection": "all_required", "language_slots_are_mandatory": True}),
            "content_hash": blueprint_hash,
            "source_record_id": blueprint_record_id,
        },
    )

    for modules in form_module_config.values():
        for meta in modules:
            section_id = f"utet-paper-1-{meta['section_code']}"
            existing = next((row for row in stage["rows"]["sections"] if row["section_id"] == section_id), None)
            if existing is None:
                name_en = (
                    f"Language {meta['order_index'] - 1}"
                    if meta["section_source_code"] == "language"
                    else SECTION_MAP[meta["section_source_code"]][1]
                )
                add_row(
                    stage,
                    "sections",
                    {
                        "section_id": section_id,
                        "exam_id": "utet",
                        "paper_number": 1,
                        "section_code": meta["section_code"],
                        "name_en": name_en,
                        "name_hi": None,
                        "source_record_id": meta["source_record_id"],
                    },
                )
            blueprint_section_id = f"bs-utet-paper-1-{meta['slot_code']}"
            if not any(row["blueprint_section_id"] == blueprint_section_id for row in stage["rows"]["blueprint_sections"]):
                add_row(
                    stage,
                    "blueprint_sections",
                    {
                        "blueprint_section_id": blueprint_section_id,
                        "blueprint_id": utet_blueprint_id,
                        "section_id": section_id,
                        "slot_code": meta["slot_code"],
                        "order_index": meta["order_index"],
                        "question_count": 30,
                        "question_start": meta["question_start"],
                        "question_end": meta["question_end"],
                        "required": 1,
                        "selection_group_id": None,
                        "source_record_id": meta["source_record_id"],
                    },
                )
                add_row(
                    stage,
                    "blueprint_section_locales",
                    {
                        "blueprint_section_id": blueprint_section_id,
                        "locale_code": meta["locale_code"],
                        "content_mode": "combined" if meta["locale_code"] == "mul" else "single",
                        "candidate_selectable": 0,
                        "source_record_id": meta["source_record_id"],
                    },
                )

    question_type_source = next(iter(questions_by_id.values()))[1]
    if not any(row["type_code"] == "single_choice" for row in stage["rows"]["question_types"]):
        add_row(
            stage,
            "question_types",
            {
                "type_code": "single_choice",
                "answer_mode": "option_set",
                "options_min": 4,
                "options_max": 4,
                "allows_multiple": 0,
                "configuration_json": canonical_json({"option_order_is_significant": True}),
                "source_record_id": question_type_source,
            },
        )

    form_sections: dict[tuple[str, str], dict[str, Any]] = {}
    for form_id, modules in form_module_config.items():
        form_record = form_rows_by_id[form_id][1]
        add_row(
            stage,
            "paper_form_blueprints",
            {"form_id": form_id, "blueprint_id": utet_blueprint_id, "source_record_id": form_record},
        )
        for meta in modules:
            form_section_id = f"fs-{form_id}-{meta['slot_code']}-{meta['locale_code']}"
            if meta["section_source_code"] == "language":
                language_directory = {"hi": "hindi", "en": "english"}[meta["module"]["language"]]
                stream_directory = f"language-{meta['module']['languageSlot']}/{language_directory}"
            else:
                stream_directory = meta["section_source_code"]
            module_paths = [
                p
                for p in (UTET_ROOT / "exams" / "utet" / "paper-1").rglob("questions.ndjson")
                if p.parent.relative_to(UTET_ROOT / "exams" / "utet" / "paper-1").as_posix() == stream_directory
            ]
            if len(module_paths) != 1:
                raise PipelineError(f"Cannot resolve one UTET question stream for module {meta['module']['id']}: {module_paths}")
            module_file = next(row for row in stage["rows"]["source_files"] if row["relative_path"] == module_paths[0].relative_to(ROOT).as_posix())
            add_row(
                stage,
                "paper_form_sections",
                {
                    "form_section_id": form_section_id,
                    "form_id": form_id,
                    "blueprint_section_id": f"bs-utet-paper-1-{meta['slot_code']}",
                    "locale_code": meta["locale_code"],
                    "source_file_id": module_file["source_file_id"],
                    "source_record_id": form_record,
                },
            )
            form_sections[(form_id, meta["module"]["id"])] = {
                "form_section_id": form_section_id,
                "locale_code": meta["locale_code"],
                "module": meta["module"],
                "metadata": meta,
            }

    appearance_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    question_content_by_id: dict[str, dict[str, Any]] = {}
    option_id_by_source: dict[tuple[str, str], str] = {}
    for question, question_record, question_file_id, question_line, source_path in sorted(question_rows, key=lambda row: row[0]["id"]):
        question_id = question["id"]
        available = list(question.get("availableLocales", []))
        if question.get("type") != "single-choice" or question.get("answer", {}).get("kind") != "single":
            raise SourceError(source_path, question_line, f"unsupported UTET type/answer combination for {question_id}")
        prompt_by_locale = _locale_blocks(question.get("prompt", []), available, source_path, question_line, "prompt")
        options = question.get("options", [])
        if len(options) != 4:
            raise SourceError(source_path, question_line, f"{question_id}: expected four options, found {len(options)}")
        option_locale_text: dict[str, list[dict[str, Any]]] = {locale: [] for locale in available}
        for position, option in enumerate(options, 1):
            content_by_locale = _locale_blocks(option.get("content", []), available, source_path, question_line, f"option {option.get('id')}")
            for locale in available:
                option_locale_text[locale].append(content_by_locale[locale])
        add_row(
            stage,
            "questions",
            {
                "question_id": question_id,
                "type_code": "single_choice",
                "lifecycle_status": question.get("status", "published"),
                "primary_source_record_id": question_record,
                "canonical_fingerprint": canonical_hash(
                    {
                        "prompt": {locale: prompt_by_locale[locale]["raw_text"] for locale in available},
                        "options": [opt["id"] for opt in options],
                    }
                ),
            },
        )
        question_content_by_id[question_id] = prompt_by_locale
        for locale in available:
            add_row(
                stage,
                "question_contents",
                {
                    "question_id": question_id,
                    "locale_code": locale,
                    "content_format": "markdown",
                    "raw_stem": prompt_by_locale[locale]["raw_text"],
                    "display_stem": prompt_by_locale[locale]["raw_text"],
                    "structured_json": canonical_json(prompt_by_locale[locale]["blocks"]),
                    "source_record_id": question_record,
                },
            )
        for position, option in enumerate(options, 1):
            source_option_id = option["id"]
            option_id = f"{question_id}-opt-{source_option_id}"
            option_id_by_source[(question_id, source_option_id)] = option_id
            add_row(
                stage,
                "question_options",
                {
                    "option_id": option_id,
                    "question_id": question_id,
                    "position": position,
                    "original_label": source_option_id,
                    "source_record_id": question_record,
                },
            )
            localized = _locale_blocks(option.get("content", []), available, source_path, question_line, f"option {source_option_id}")
            for locale in available:
                add_row(
                    stage,
                    "option_contents",
                    {
                        "option_id": option_id,
                        "question_id": question_id,
                        "locale_code": locale,
                        "content_format": "markdown",
                        "raw_text": localized[locale]["raw_text"],
                        "display_text": localized[locale]["raw_text"],
                        "structured_json": canonical_json(localized[locale]["blocks"]),
                        "source_record_id": question_record,
                    },
                )
        for tag in question.get("tags", []):
            add_row(
                stage,
                "question_source_tags",
                {"question_id": question_id, "raw_tag": str(tag), "source_record_id": question_record},
            )
        _source_assertions(
            stage,
            question_record,
            "question",
            {
                "sourceType": question.get("sourceType"),
                "difficulty": question.get("difficulty"),
                "cognitiveLevel": question.get("cognitiveLevel"),
                "review": question.get("review", {}),
                "availableLocales": available,
                "stimulusId": question.get("stimulusId"),
            },
        )
        audit, audit_record, audit_line, audit_path = audit_by_question[question_id]
        add_row(stage, "question_source_audits", {"question_id": question_id, "source_record_id": audit_record})
        _source_assertions(stage, audit_record, "question-audit", {k: v for k, v in audit.items() if k not in ("schemaVersion", "questionId")})
        add_assertion(stage, audit_record, "audit_question_id", "question-audit", question_id)

    stimulus_content_by_id: dict[str, dict[str, Any]] = {}
    for stimulus, record_id, file_id, line_number, source_path in stimulus_rows:
        if stimulus.get("type") not in ("prose", "poem"):
            raise SourceError(source_path, line_number, f"unsupported stimulus type {stimulus.get('type')!r}")
        content_by_locale = _locale_blocks(stimulus.get("content", []), list((stimulus.get("content", [{}])[0].get("text", {})).keys()), source_path, line_number, "stimulus")
        locale_codes = sorted(content_by_locale)
        if len(locale_codes) != 1:
            raise SourceError(source_path, line_number, f"UTET stimulus expected one locale-specific row, found {locale_codes}")
        locale = locale_codes[0]
        if stimulus["id"] in question_content_by_id:
            raise SourceError(source_path, line_number, f"stimulus id conflicts with question id {stimulus['id']}")
        add_row(
            stage,
            "stimuli",
            {
                "stimulus_id": stimulus["id"],
                "stimulus_type": stimulus["type"],
                "lifecycle_status": stimulus.get("status", "published"),
                "source_record_id": record_id,
            },
        )
        instructions = stimulus.get("instructions", {}).get(locale)
        add_row(
            stage,
            "stimulus_contents",
            {
                "stimulus_id": stimulus["id"],
                "locale_code": locale,
                "content_format": "markdown",
                "raw_text": content_by_locale[locale]["raw_text"],
                "display_text": content_by_locale[locale]["raw_text"],
                "instructions": instructions,
                "structured_json": canonical_json(content_by_locale[locale]["blocks"]),
                "source_record_id": record_id,
            },
        )
        _source_assertions(
            stage,
            record_id,
            "stimulus",
            {
                "sourceType": stimulus.get("sourceType"),
                "selectionPolicy": stimulus.get("selectionPolicy"),
                "minimumQuestions": stimulus.get("minimumQuestions"),
                "review": stimulus.get("review", {}),
            },
        )
        stimulus_content_by_id[stimulus["id"]] = {"locale": locale, "record_id": record_id, "value": stimulus}

    # Form modules point to source appearance IDs; each actual appearance links one question row.
    for form_id, modules in form_module_config.items():
        for meta in modules:
            module = meta["module"]
            section = meta["section_source_code"]
            module_lang_slot = module.get("languageSlot")
            module_locale = module.get("language")
            for appearance_id in module["appearanceIds"]:
                appearance, appearance_record, appearance_line = all_appearance_by_id[appearance_id]
                question_id = appearance["questionId"]
                question, question_record, question_file_id, question_line = questions_by_id[question_id]
                if question.get("section") != section or question.get("languageSlot") != module_lang_slot or question.get("language") != module_locale:
                    raise SourceError(appearances_path.relative_to(ROOT).as_posix(), appearance_line, f"appearance {appearance_id} metadata does not match question {question_id}")
                form_section = form_sections[(form_id, module["id"])]
                form_section_id = form_section["form_section_id"]
                appearance_id_out = appearance["id"]
                if (form_id, appearance_id_out) in appearance_lookup:
                    raise SourceError(appearances_path.relative_to(ROOT).as_posix(), appearance_line, f"appearance {appearance_id_out} is listed in more than one module")
                add_row(
                    stage,
                    "question_appearances",
                    {
                        "appearance_id": appearance_id_out,
                        "form_section_id": form_section_id,
                        "question_id": question_id,
                        "question_number": int(appearance["questionNumber"]),
                        "sequence_in_section": int(appearance["questionNumber"]) - meta["question_start"] + 1,
                        "points": 1.0,
                        "source_record_id": appearance_record,
                    },
                )
                appearance_lookup[(form_id, appearance_id_out)] = {
                    "appearance": appearance,
                    "appearance_record": appearance_record,
                    "question": question,
                    "question_record": question_record,
                    "module": meta,
                }
                _source_assertions(
                    stage,
                    appearance_record,
                    "appearance",
                    {
                        "verificationStatus": appearance.get("verificationStatus"),
                        "sourceRef": appearance.get("sourceRef"),
                        "officialOptionId": appearance.get("officialOptionId"),
                    },
                )
                source_answer = question["answer"]["optionId"]
                if source_answer != appearance.get("officialOptionId"):
                    raise SourceError(appearances_path.relative_to(ROOT).as_posix(), appearance_line, f"appearance answer {appearance.get('officialOptionId')} disagrees with question answer {source_answer}")

    if len(appearance_lookup) != 900:
        raise PipelineError(f"Expected 900 mapped UTET appearances, built {len(appearance_lookup)}")
    for qid, (question, record_id, file_id, line_number) in questions_by_id.items():
        if qid not in {value["appearance"]["questionId"] for value in appearance_lookup.values()}:
            raise PipelineError(f"UTET question {qid} has no paper-form appearance")
        stimulus_id = question.get("stimulusId")
        if stimulus_id:
            if stimulus_id not in stimulus_content_by_id:
                raise SourceError(
                    next(item[4] for item in question_rows if item[0]["id"] == qid),
                    line_number,
                    f"question {qid} references missing stimulus {stimulus_id}",
                )
            form_appearance = next(
                (value for value in appearance_lookup.values() if value["appearance"]["questionId"] == qid), None
            )
            if not form_appearance:
                raise PipelineError(f"UTET stimulus-linked question {qid} has no appearance")
            appearance = form_appearance["appearance"]
            link_order = 1 + sum(
                1 for row in stage["rows"]["stimulus_question_links"] if row["stimulus_id"] == stimulus_id
            )
            add_row(
                stage,
                "stimulus_question_links",
                {
                    "stimulus_id": stimulus_id,
                    "appearance_id": appearance["id"],
                    "relation_code": "context",
                    "position": link_order,
                    "source_record_id": record_id,
                },
            )

    # Preserve the embedded repository answers as a separately versioned, provisional key.
    answer_version_ids: dict[str, str] = {}
    for form_id, (form, form_record, form_line) in form_rows_by_id.items():
        version_id = f"akv-{form_id}-source-provisional"
        answer_version_ids[form_id] = version_id
        form_rows_for_appearances = [value for key, value in appearance_lookup.items() if key[0] == form_id]
        if len(form_rows_for_appearances) != 150:
            raise SourceError(forms_path.relative_to(ROOT).as_posix(), form_line, f"form {form_id} maps {len(form_rows_for_appearances)} appearances, expected 150")
        source_manifest_record = manifests_by_year.get(str(form["examDate"][:4]), form_record)
        add_row(
            stage,
            "answer_key_versions",
            {
                "answer_key_version_id": version_id,
                "form_id": form_id,
                "version_label": "source-repository-answers-unverified-as-authority",
                "authority_class": "source_repository",
                "status": "provisional",
                "published_date": None,
                "authority_uri": None,
                "source_record_id": source_manifest_record,
                "content_hash": canonical_hash(
                    sorted(
                        [
                            {
                                "question_id": value["appearance"]["questionId"],
                                "answer": value["question"]["answer"],
                                "number": value["appearance"]["questionNumber"],
                            }
                            for value in form_rows_for_appearances
                        ],
                        key=canonical_json,
                    )
                ),
            },
        )
        table_id = f"akt-{form_id}-embedded-answer-fields"
        add_row(
            stage,
            "answer_key_tables",
            {
                "answer_key_table_id": table_id,
                "answer_key_version_id": version_id,
                "table_label": "question NDJSON embedded answers",
                "raw_heading": "question.answer.optionId and appearance.officialOptionId (upstream source fields)",
                "locale_code": None,
                "slot_code": "all",
                "question_start": 1,
                "question_end": 150,
                "source_record_id": form_record,
            },
        )
        for value in sorted(form_rows_for_appearances, key=lambda row: row["appearance"]["questionNumber"]):
            answer_token = value["question"]["answer"]["optionId"]
            question_id = value["appearance"]["questionId"]
            option_id = option_id_by_source.get((question_id, answer_token))
            if option_id is None:
                raise SourceError(appearances_path.relative_to(ROOT).as_posix(), value["appearance"]["questionNumber"], f"question {question_id} answer references unknown option id {answer_token}")
            key_entry_id = stable_id("ake", version_id, value["appearance"]["id"], size=28)
            add_row(
                stage,
                "answer_key_entries",
                {
                    "answer_key_entry_id": key_entry_id,
                    "answer_key_table_id": table_id,
                    "appearance_id": value["appearance"]["id"],
                    "question_id": question_id,
                    "raw_answer": answer_token,
                    "answer_mode": "option_set",
                    "scalar_answer": None,
                    "response_json": None,
                    "source_record_id": value["question_record"],
                },
            )
            add_row(
                stage,
                "answer_key_entry_options",
                {
                    "answer_key_entry_id": key_entry_id,
                    "question_id": question_id,
                    "option_id": option_id,
                    "position": 1,
                    "source_record_id": value["question_record"],
                },
            )

    return {
        "schema_validation": schema_report,
        "forms": len(form_rows),
        "questions": len(questions_by_id),
        "appearances": len(appearance_lookup),
        "stimuli": len(stimuli_by_id),
        "audits": audit_count,
        "nonempty_question_streams": dict(sorted(question_stream_counts.items())),
        "answer_authority": "source_repository/provisional; excluded from official-final view",
    }
