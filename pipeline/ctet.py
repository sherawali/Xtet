from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
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
    line_body,
    lines_with_endings,
    slug,
    stable_id,
)

CTET_FOLDER_GLOB = "20??/CTET_Paper1_*"
CORE_BY_FILENAME = {
    "cpd.txt": ("cpd", "Child Development and Pedagogy", 1),
    "maths.txt": ("mathematics", "Mathematics", 2),
    "evs.txt": ("environmental-studies", "Environmental Studies", 3),
}
PART_RANGE_RE = re.compile(
    r"^Part\s+([IVX]+)\s*[-–]\s*Questions?\s+(\d+)\s+(?:to|[-–])\s+(\d+)", re.I
)
QUESTION_START_RE = re.compile(r"^\s*(\d{1,3})\.\s+(.+?)\s*$")
OPTION_RE = re.compile(r"^\s*\(\s*([1-4])\s*\)\s*(.*?)\s*$")
STIMULUS_WORDS = re.compile(
    r"passage|poem|poetry|extract|prose|gadyansh|kavyansh|kavita|padyansh|"
    r"अनुच्छेद|गद्यांश|काव्यांश|कविता|पद्यांश|काव्य|पाठांश",
    re.I,
)
STIMULUS_DIRECTION = re.compile(
    r"directions?|read\b|answer\s+the\s+questions|निर्देश|पढ़कर|पढ़िए|चुनिए|चयन",
    re.I,
)
QUESTION_RANGE_RE = re.compile(r"(?<!\d)(\d{2,3})\s*(?:to|से|[-–])\s*(\d{2,3})(?!\d)", re.I)


def _int(value: str | None) -> int | None:
    return int(value) if value is not None else None


def _extract_official_key_uri(readme_text: str) -> str | None:
    candidates: list[str] = []
    for line in readme_text.splitlines():
        lowered = line.lower()
        if "official" not in lowered or "answer key" not in lowered:
            continue
        for url in re.findall(r"https?://[^\s)>,]+", line):
            clean = url.rstrip(".,;:")
            if "cdnbbsr.s3waas.gov.in" in clean or "ctet.nic.in" in clean:
                candidates.append(clean)
    direct_pdf = next((url for url in candidates if url.lower().endswith(".pdf")), None)
    return direct_pdf or next(iter(candidates), None)


def _readme_metadata(readme_text: str) -> dict[str, Any]:
    cycle_match = re.search(r"^\s*-\s*Exam cycle:\s*(.+)$", readme_text, re.I | re.M)
    cycle = cycle_match.group(1).strip() if cycle_match else None
    total_match = re.search(r"^\s*-\s*Total Questions:\s*(\d+)", readme_text, re.I | re.M)
    if not total_match:
        total_match = re.search(r"^\s*-\s*Total questions:\s*(\d+)", readme_text, re.I | re.M)
    duration = None
    duration_match = re.search(r"^\s*-\s*Duration:\s*([^\n]+)", readme_text, re.I | re.M)
    if duration_match:
        value = duration_match.group(1)
        hours = re.search(r"(\d+(?:\.\d+)?)\s*hours?", value, re.I)
        mins = re.search(r"(\d+)\s*minutes?", value, re.I)
        if hours:
            duration = round(float(hours.group(1)) * 60)
        elif mins:
            duration = int(mins.group(1))
    shift = None
    shift_match = re.search(r"\bshift\s*([1-9])\b", readme_text, re.I)
    if shift_match:
        shift = int(shift_match.group(1))
    negative = None
    negative_match = re.search(r"^\s*-\s*Negative marking:\s*([^\n]+)", readme_text, re.I | re.M)
    if negative_match:
        text = negative_match.group(1).strip().lower()
        if any(token in text for token in ("nahi", "no", "none", "not applicable")):
            negative = 0.0
        else:
            amount = re.search(r"\d+(?:\.\d+)?", text)
            if amount:
                negative = float(amount.group(0))
    return {
        "cycle_label": cycle,
        "total_questions": int(total_match.group(1)) if total_match else None,
        "duration_minutes": duration,
        "shift": shift,
        "negative_marking": negative,
    }


def _parse_exam_date(value: str, path: str, line: int) -> str:
    value = value.strip()
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise SourceError(path, line, f"cannot parse exam date {value!r}; expected an explicit source date")


def _section_identity(path: Path, section_header: str, part: str, source_path: str, line: int) -> dict[str, Any]:
    filename = path.name.lower()
    if filename in CORE_BY_FILENAME:
        code, name, order = CORE_BY_FILENAME[filename]
        return {
            "section_code": code,
            "section_name_en": name,
            "slot_code": code,
            "order_index": order,
            "language_slot": None,
            "locale_hint": None,
            "is_core": True,
        }

    if part.upper() == "IV":
        language_slot, order = 1, 4
    elif part.upper() == "V":
        language_slot, order = 2, 5
    else:
        raise SourceError(source_path, line, f"unrecognized section file {path.name!r} has Part {part!r}")
    if re.search(r"\bEnglish\b", section_header, re.I):
        locale = "en"
        language_name = "English"
    elif re.search(r"\bHindi\b|हिन्दी|हिंदी", section_header, re.I):
        locale = "hi"
        language_name = "Hindi"
    else:
        raise SourceError(source_path, line, f"cannot identify language from section header {section_header!r}")
    return {
        "section_code": f"language-{language_slot}",
        "section_name_en": f"Language {language_slot}",
        "slot_code": f"language-{language_slot}",
        "order_index": order,
        "language_slot": language_slot,
        "locale_hint": locale,
        "language_name": language_name,
        "is_core": False,
    }


def _infer_locale(text: str) -> str | None:
    devanagari = sum(1 for char in text if "\u0900" <= char <= "\u097f")
    latin = sum(1 for char in text if ("A" <= char <= "Z") or ("a" <= char <= "z"))
    if devanagari == 0 and latin == 0:
        return None
    # Hindi stems/options may contain Latin variables and units; script presence in a
    # substantial fraction of the stem is stronger evidence than raw Latin counts.
    return "hi" if devanagari > 0 and devanagari >= latin * 0.25 else "en"


def _clean_display(raw: str) -> str:
    # Keep internal whitespace/codepoints verbatim; discard only structural outer blank lines.
    return raw.strip("\r\n")


def _make_stimuli(
    *,
    lines: list[str],
    q_starts: dict[int, int],
    q_min: int,
    q_max: int,
    source_path: str,
) -> tuple[list[dict[str, Any]], set[int]]:
    found: list[dict[str, Any]] = []
    directive_indexes: set[int] = set()
    for index, line in enumerate(lines):
        body = line_body(line)
        if not STIMULUS_WORDS.search(body) or not STIMULUS_DIRECTION.search(body):
            continue
        ranges = [
            (int(m.group(1)), int(m.group(2)))
            for m in QUESTION_RANGE_RE.finditer(body)
            if q_min <= int(m.group(1)) <= int(m.group(2)) <= q_max
        ]
        if len(ranges) != 1:
            continue
        start, end = ranges[0]
        if start not in q_starts or end not in q_starts:
            raise SourceError(source_path, index + 1, f"stimulus directive declares Q{start}-{end}, but one boundary question is missing")
        qstart_index = q_starts[start]
        if qstart_index <= index:
            raise SourceError(source_path, index + 1, f"stimulus directive for Q{start}-{end} appears after its first question")
        raw_span = "".join(lines[index:qstart_index])
        if not raw_span.strip():
            raise SourceError(source_path, index + 1, f"empty stimulus content before Q{start}")
        if re.search(r"\bpoem\b|\bpoetry\b|काव्यांश|कविता|पद्यांश|काव्य", body, re.I):
            kind = "poem"
        elif re.search(r"\bextract\b", body, re.I):
            kind = "extract"
        else:
            kind = "prose"
        found.append(
            {
                "question_start": start,
                "question_end": end,
                "directive_index": index,
                "question_start_index": qstart_index,
                "raw_span": raw_span,
                "raw_content": "".join(lines[index + 1 : qstart_index]),
                "kind": kind,
            }
        )
        directive_indexes.add(index)
    found.sort(key=lambda value: value["question_start"])
    for left, right in zip(found, found[1:]):
        if left["question_end"] >= right["question_start"]:
            raise SourceError(source_path, left["directive_index"] + 1, "overlapping stimulus question ranges")
    return found, directive_indexes


def _parse_option_groups(
    block_lines: list[str],
    *,
    question_number: int,
    source_path: str,
    line_start: int,
    core: bool,
    locale_hint: str | None,
) -> list[dict[str, Any]]:
    markers: list[tuple[int, int, str]] = []
    for index, line in enumerate(block_lines):
        match = OPTION_RE.match(line_body(line))
        if match:
            markers.append((index, int(match.group(1)), match.group(2)))
    if not markers:
        raise SourceError(source_path, line_start, f"Q{question_number}: expected option marker (1), found none")

    groups: list[list[tuple[int, int, str]]] = []
    current: list[tuple[int, int, str]] = []
    for marker in markers:
        index, label, first_line_text = marker
        if label == 1 and current:
            if [item[1] for item in current] != [1, 2, 3, 4]:
                raise SourceError(source_path, line_start + index, f"Q{question_number}: option block ended with labels {[item[1] for item in current]}, expected 1–4")
            groups.append(current)
            current = []
        expected_label = len(current) + 1
        if label != expected_label:
            raise SourceError(source_path, line_start + index, f"Q{question_number}: found option ({label}) where ({expected_label}) was expected")
        current.append(marker)
    if current:
        if [item[1] for item in current] != [1, 2, 3, 4]:
            raise SourceError(source_path, line_start + current[-1][0], f"Q{question_number}: final option block has labels {[item[1] for item in current]}, expected 1–4")
        groups.append(current)
    if len(groups) not in (1, 2):
        raise SourceError(source_path, line_start, f"Q{question_number}: found {len(groups)} option blocks; expected one or two")
    if not core and len(groups) != 1:
        raise SourceError(source_path, line_start, f"Q{question_number}: language stream must have one option block; found {len(groups)}")

    parsed: list[dict[str, Any]] = []
    prior_group_end = 0
    for group_index, group in enumerate(groups):
        group_start = group[0][0]
        stem_raw = "".join(block_lines[prior_group_end:group_start])
        if group_index == 0:
            # The question number remains in the exact source record and appearance row.
            first_line = block_lines[0]
            first_body = line_body(first_line)
            match = QUESTION_START_RE.match(first_body)
            if match:
                ending = first_line[len(first_body):]
                stem_raw = re.sub(r"^\s*\d{1,3}\.\s*", "", first_body, count=1) + ending + "".join(block_lines[1:group_start])
        display_stem = _clean_display(stem_raw)
        if not display_stem.strip():
            raise SourceError(source_path, line_start + group_start, f"Q{question_number}: empty question stem")

        option_rows: list[dict[str, Any]] = []
        next_group_start = groups[group_index + 1][0][0] if group_index + 1 < len(groups) else len(block_lines)
        option4_end = next_group_start
        separator_start: int | None = None
        if group_index + 1 < len(groups):
            after_option4 = group[-1][0] + 1
            for index in range(after_option4, next_group_start):
                if not line_body(block_lines[index]).strip():
                    separator_start = index
                    break
            if separator_start is None:
                raise SourceError(
                    source_path,
                    line_start + group[-1][0],
                    f"Q{question_number}: bilingual option blocks have no blank-line separator after option (4)",
                )
            option4_end = separator_start

        for option_index, (marker_index, label, first_line_text) in enumerate(group):
            if label == 4 and group_index + 1 < len(groups):
                content_end = option4_end
            elif option_index + 1 < len(group):
                content_end = group[option_index + 1][0]
            elif group_index + 1 < len(groups):
                content_end = option4_end
            else:
                content_end = len(block_lines)
            body_lines: list[str] = []
            source_option_line = block_lines[marker_index]
            first_line = line_body(source_option_line)
            matched = OPTION_RE.match(first_line)
            assert matched is not None
            ending = source_option_line[len(first_line):]
            body_lines.append(matched.group(2) + ending)
            body_lines.extend(block_lines[marker_index + 1 : content_end])
            raw_body = "".join(body_lines)
            display_body = _clean_display(raw_body)
            if not display_body.strip():
                raise SourceError(source_path, line_start + marker_index, f"Q{question_number} option ({label}) has empty text")
            option_rows.append(
                {
                    "position": label,
                    "label": str(label),
                    "raw_text": raw_body,
                    "display_text": display_body,
                }
            )

        group_text_for_locale = display_stem
        try:
            locale = _infer_locale(group_text_for_locale) if core else locale_hint
            if core and locale is None:
                locale = _infer_locale("\n".join(row["display_text"] for row in option_rows))
        except ValueError as exc:
            raise SourceError(source_path, line_start + group_start, f"Q{question_number}: {exc}") from exc
        if locale not in ("en", "hi"):
            raise SourceError(source_path, line_start + group_start, f"Q{question_number}: unresolved locale {locale!r}")
        if locale_hint and locale != locale_hint and not core:
            raise SourceError(source_path, line_start + group_start, f"Q{question_number}: header says {locale_hint}, content looks like {locale}")
        parsed.append(
            {
                "locale": locale,
                "raw_stem": stem_raw,
                "display_stem": display_stem,
                "options": option_rows,
                "group_start": group_start,
                "group_end": option4_end if group_index + 1 < len(groups) else len(block_lines),
            }
        )
        if group_index + 1 < len(groups):
            # The blank separating the first locale's final option from the next stem is structural.
            cursor = separator_start + 1
            while cursor < next_group_start and not line_body(block_lines[cursor]).strip():
                cursor += 1
            prior_group_end = cursor

    locales = [group["locale"] for group in parsed]
    if len(set(locales)) != len(locales):
        raise SourceError(source_path, line_start, f"Q{question_number}: duplicate locale blocks {locales}")
    return parsed


def _parse_section(path: Path, stage: dict[str, Any], form_hint: dict[str, Any] | None = None) -> dict[str, Any]:
    source_file_id, _, text = add_source_file(stage, path)
    lines = lines_with_endings(text)
    bodies = [line_body(line) for line in lines]
    source_path = path.relative_to(ROOT).as_posix()
    section_match = next((re.match(r"^Section:\s*(.+)$", body, re.I) for body in bodies if re.match(r"^Section:\s*(.+)$", body, re.I)), None)
    part_match = next((PART_RANGE_RE.match(body.strip()) for body in bodies if PART_RANGE_RE.match(body.strip())), None)
    if not section_match or not part_match:
        raise SourceError(source_path, 1, "missing parseable `Section:` or `Part ... Questions X to Y` header")
    section_header = section_match.group(1).strip()
    part, q_min_text, q_max_text = part_match.groups()
    q_min, q_max = int(q_min_text), int(q_max_text)
    identity = _section_identity(path, section_header, part, source_path, 1)
    date_match = re.search(
        r"^Exam Date:\s*([^|\n]+)\s*\|\s*Paper Set:\s*([^|\n]+)(?:\s*\|\s*Booklet Code:\s*([^|\n]+))?",
        text,
        re.I | re.M,
    )
    if not date_match:
        raise SourceError(source_path, 1, "missing explicit `Exam Date | Paper Set` metadata")
    exam_date = _parse_exam_date(date_match.group(1), source_path, next(i for i, b in enumerate(bodies, 1) if b.startswith("Exam Date:")))
    set_code = date_match.group(2).strip()
    booklet_code = date_match.group(3).strip() if date_match.group(3) else None
    title = bodies[0].strip() if bodies else "CTET Paper 1"
    header_end = next((i for i, body in enumerate(bodies, 1) if body.startswith("Exam Date:")), min(5, len(bodies)))
    header_record = add_source_record(
        stage,
        source_file_id=source_file_id,
        relative_path=source_path,
        line_start=1,
        line_end=header_end,
        raw_text="".join(lines[:header_end]),
        extraction_method="ctet-section-header-v1",
        imported_from=source_path,
    )

    q_starts: dict[int, int] = {}
    for index, body in enumerate(bodies):
        match = QUESTION_START_RE.match(body)
        if not match:
            continue
        number = int(match.group(1))
        if q_min <= number <= q_max:
            if number in q_starts:
                raise SourceError(source_path, index + 1, f"duplicate question-number marker {number} within declared range {q_min}-{q_max}")
            q_starts[number] = index
    expected = list(range(q_min, q_max + 1))
    actual = sorted(q_starts)
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        detail = f"question markers do not match declared range {q_min}-{q_max}; missing={missing[:10]}, extra={extra[:10]}"
        raise SourceError(source_path, 1, detail)

    stimuli, directive_indexes = _make_stimuli(
        lines=lines, q_starts=q_starts, q_min=q_min, q_max=q_max, source_path=source_path
    )
    question_starts = sorted((number, index) for number, index in q_starts.items())
    questions: dict[int, dict[str, Any]] = {}
    for q_index, (number, start_index) in enumerate(question_starts):
        next_question_index = question_starts[q_index + 1][1] if q_index + 1 < len(question_starts) else len(lines)
        next_directive_index = min((idx for idx in directive_indexes if start_index < idx < next_question_index), default=next_question_index)
        end_index = min(next_question_index, next_directive_index)
        block_lines = lines[start_index:end_index]
        blocks = _parse_option_groups(
            block_lines,
            question_number=number,
            source_path=source_path,
            line_start=start_index + 1,
            core=identity["is_core"],
            locale_hint=identity["locale_hint"],
        )
        block_record = add_source_record(
            stage,
            source_file_id=source_file_id,
            relative_path=source_path,
            line_start=start_index + 1,
            line_end=end_index,
            raw_text="".join(block_lines),
            extraction_method="ctet-question-block-v1",
            imported_from=f"{source_path}#Q{number}",
        )
        questions[number] = {
            "question_number": number,
            "source_record_id": block_record,
            "source_file_id": source_file_id,
            "source_path": source_path,
            "line_start": start_index + 1,
            "line_end": end_index,
            "locale_blocks": {block["locale"]: block for block in blocks},
            "stimulus_ids": [],
        }

    parsed_stimuli: list[dict[str, Any]] = []
    for stimulus in stimuli:
        raw_span = stimulus["raw_span"]
        start_index = stimulus["directive_index"]
        end_index = stimulus["question_start_index"]
        source_record = add_source_record(
            stage,
            source_file_id=source_file_id,
            relative_path=source_path,
            line_start=start_index + 1,
            line_end=end_index,
            raw_text=raw_span,
            extraction_method="ctet-stimulus-span-v1",
            imported_from=f"{source_path}#Q{stimulus['question_start']}-{stimulus['question_end']}",
        )
        locale = identity["locale_hint"]
        if identity["is_core"]:
            # Core sections do not have passage stimuli in these source forms.
            raise SourceError(source_path, start_index + 1, "unexpected stimulus directive in a common-core section; review parser boundary")
        stimulus_id = stable_id(
            "stim",
            form_hint["form_id"] if form_hint else exam_date,
            identity["slot_code"],
            locale,
            stimulus["question_start"],
            stimulus["question_end"],
            size=32,
        )
        parsed_stimuli.append(
            {
                "stimulus_id": stimulus_id,
                "stimulus_type": stimulus["kind"],
                "locale": locale,
                "raw_text": stimulus["raw_content"],
                "display_text": _clean_display(stimulus["raw_content"]),
                "question_start": stimulus["question_start"],
                "question_end": stimulus["question_end"],
                "source_record_id": source_record,
                "source_file_id": source_file_id,
                "source_path": source_path,
            }
        )
        for number in range(stimulus["question_start"], stimulus["question_end"] + 1):
            questions[number]["stimulus_ids"].append(stimulus_id)

    return {
        **identity,
        "path": path,
        "source_path": source_path,
        "source_file_id": source_file_id,
        "header_record_id": header_record,
        "section_header": section_header,
        "title": title,
        "part": part,
        "question_start": q_min,
        "question_end": q_max,
        "exam_date": exam_date,
        "set_code": set_code,
        "booklet_code": booklet_code,
        "questions": questions,
        "stimuli": parsed_stimuli,
        "source_line_count": len(lines),
    }


def _parse_key_legend(text: str) -> dict[str, tuple[int, ...]]:
    legend: dict[str, tuple[int, ...]] = {}
    for line in text.splitlines():
        for match in re.finditer(r"\b([A-FZ])\s*=\s*([^\n]+?)(?=\s{2,}[A-FZ]\s*=|$)", line, re.I):
            code, meaning = match.group(1).upper(), match.group(2)
            if code == "Z" and re.search(r"\b(all|saare|sabhi)\b", meaning, re.I):
                legend[code] = (1, 2, 3, 4)
                continue
            numbers = tuple(sorted({int(v) for v in re.findall(r"(?<!\d)[1-4](?!\d)", meaning)}))
            if numbers:
                legend[code] = numbers
    return legend


def _key_table_identity(header: str, q_start: int, q_end: int, source_path: str, line: int) -> tuple[str, str | None, str]:
    lower = header.lower()
    if re.match(r"^cpd\b", lower):
        return "cpd", None, "cpd"
    if re.match(r"^maths?\b", lower):
        return "mathematics", None, "mathematics"
    if re.match(r"^evs\b", lower):
        return "environmental-studies", None, "environmental-studies"

    locale = "en" if "english" in lower or re.search(r"\beng(?:-|lish)", lower) else "hi" if "hindi" in lower else None
    if locale is None:
        raise SourceError(source_path, line, f"cannot determine key-table locale from heading {header!r}")
    if "language i & ii" in lower or "language i and ii" in lower:
        return "language-1+2", locale, "language-1+2"
    if re.search(r"language\s+i\b|eng-1|hindi-1", lower):
        return "language-1", locale, "language-1"
    if re.search(r"language\s+ii\b|eng-2|hindi-2", lower):
        return "language-2", locale, "language-2"
    raise SourceError(source_path, line, f"cannot determine language slot from key heading {header!r} ({q_start}-{q_end})")


def _parse_key_file(path: Path, stage: dict[str, Any], form_id: str) -> dict[str, Any]:
    source_file_id, _, text = add_source_file(stage, path)
    lines = lines_with_endings(text)
    bodies = [line_body(line) for line in lines]
    source_path = path.relative_to(ROOT).as_posix()
    legend = _parse_key_legend(text)
    header_pattern = re.compile(r"^(.+?)\s*\(.*?Q(\d+)\s*[-–]\s*(\d+)\)\s*$", re.I)
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for index, body in enumerate(bodies):
        match = header_pattern.match(body.strip())
        if match:
            if current:
                groups.append(current)
            header = match.group(1).strip()
            q_start, q_end = int(match.group(2)), int(match.group(3))
            slot, locale, slot_code = _key_table_identity(header, q_start, q_end, source_path, index + 1)
            group_record = add_source_record(
                stage,
                source_file_id=source_file_id,
                relative_path=source_path,
                line_start=index + 1,
                line_end=index + 1,
                raw_text=lines[index],
                extraction_method="ctet-key-table-heading-v1",
                imported_from=f"{source_path}#{header}",
            )
            table_id = stable_id("akt", form_id, len(groups) + 1, header, q_start, q_end, size=28)
            current = {
                "table_id": table_id,
                "header": body.strip(),
                "label": header,
                "slot": slot,
                "slot_code": slot_code,
                "locale": locale,
                "question_start": q_start,
                "question_end": q_end,
                "source_record_id": group_record,
                "entries": [],
            }
            continue
        if current is None:
            continue
        match = re.match(r"^\s*(\d+)\.\s*([1-4A-FZ])(?:\s|$)", body, re.I)
        if not match:
            continue
        number, token = int(match.group(1)), match.group(2).upper()
        if not current["question_start"] <= number <= current["question_end"]:
            raise SourceError(source_path, index + 1, f"key Q{number} is outside table range {current['question_start']}-{current['question_end']}")
        if token in "1234":
            options = (int(token),)
        elif token in legend:
            options = legend[token]
        else:
            raise SourceError(source_path, index + 1, f"key Q{number} uses {token!r} but its option-set legend is absent")
        if not options or len(set(options)) != len(options) or any(value not in (1, 2, 3, 4) for value in options):
            raise SourceError(source_path, index + 1, f"key Q{number} has invalid expanded option set {options}")
        record_id = add_source_record(
            stage,
            source_file_id=source_file_id,
            relative_path=source_path,
            line_start=index + 1,
            line_end=index + 1,
            raw_text=lines[index],
            extraction_method="ctet-key-entry-v1",
            imported_from=f"{source_path}#Q{number}",
        )
        current["entries"].append(
            {
                "question_number": number,
                "raw_answer": token,
                "option_positions": options,
                "source_record_id": record_id,
                "line": index + 1,
            }
        )
    if current:
        groups.append(current)

    if not groups:
        raise SourceError(source_path, 1, "no answer-key table headings found")
    for group in groups:
        expected_numbers = list(range(group["question_start"], group["question_end"] + 1))
        actual_numbers = [entry["question_number"] for entry in group["entries"]]
        if actual_numbers != expected_numbers:
            missing = sorted(set(expected_numbers) - set(actual_numbers))
            duplicates = sorted({n for n in actual_numbers if actual_numbers.count(n) > 1})
            raise SourceError(
                source_path,
                group["entries"][0]["line"] if group["entries"] else None,
                f"table {group['header']!r}: expected {len(expected_numbers)} ordered answers; found {len(actual_numbers)}, missing={missing[:10]}, duplicates={duplicates[:10]}",
            )
    if sum(len(group["entries"]) for group in groups) != 210:
        raise SourceError(source_path, 1, f"expected 210 CTET key entries, found {sum(len(g['entries']) for g in groups)}")
    return {"source_file_id": source_file_id, "source_path": source_path, "legend": legend, "groups": groups}


def _expected_mirrors(form_id: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    if form_id not in config.get("forms", {}):
        raise PipelineError(f"CTET mirror-review configuration is missing form {form_id}")
    return config["forms"][form_id]


def _discover_mirrors(
    form_id: str,
    section_files: list[dict[str, Any]],
    answer_map: dict[tuple[str, str, int], tuple[int, ...]],
) -> list[dict[str, Any]]:
    by_slot_locale = {
        (section["slot_code"], section["locale_hint"]): section for section in section_files if not section["is_core"]
    }
    discovered: list[dict[str, Any]] = []
    for slot in ("language-1", "language-2"):
        en = by_slot_locale.get((slot, "en"))
        hi = by_slot_locale.get((slot, "hi"))
        if not en or not hi:
            continue
        numbers = range(max(en["question_start"], hi["question_start"]), min(en["question_end"], hi["question_end"]) + 1)
        runs: list[list[int]] = []
        for number in numbers:
            q_en = en["questions"][number]
            q_hi = hi["questions"][number]
            # Separate comprehension content must never be collapsed even if keys happen to agree.
            if q_en["stimulus_ids"] or q_hi["stimulus_ids"]:
                equal = False
            else:
                en_key = answer_map.get((slot, "en", number))
                hi_key = answer_map.get((slot, "hi", number))
                en_block = q_en["locale_blocks"].get("en")
                hi_block = q_hi["locale_blocks"].get("hi")
                equal = (
                    en_key is not None
                    and en_key == hi_key
                    and en_block is not None
                    and hi_block is not None
                    and len(en_block["options"]) == len(hi_block["options"]) == 4
                    and [o["position"] for o in en_block["options"]] == [o["position"] for o in hi_block["options"]]
                )
            if equal:
                if not runs or number != runs[-1][-1] + 1:
                    runs.append([number])
                else:
                    runs[-1].append(number)
            # A mismatch or stimulus breaks a candidate run.
        for run in runs:
            if len(run) >= 15:
                discovered.append(
                    {
                        "slot_code": slot,
                        "locale_a": "en",
                        "locale_b": "hi",
                        "question_start": run[0],
                        "question_end": run[-1],
                    }
                )
    return sorted(discovered, key=lambda item: (item["slot_code"], item["question_start"]))


def _get_key_route(group: dict[str, Any], number: int) -> tuple[str, str | None]:
    slot = group["slot"]
    if slot == "language-1+2":
        return ("language-1" if number <= 120 else "language-2", group["locale"])
    return slot, group["locale"]


def parse_ctet(stage: dict[str, Any]) -> dict[str, Any]:
    folders = sorted(path for path in ROOT.glob(CTET_FOLDER_GLOB) if path.is_dir())
    if len(folders) != 5:
        raise PipelineError(f"Expected five CTET Paper-1 folders, found {len(folders)}: {[p.as_posix() for p in folders]}")
    mirror_path = ROOT / "config" / "ctet_mirrors.json"
    mirror_file_id, _, mirror_text = add_source_file(stage, mirror_path)
    mirror_lines = lines_with_endings(mirror_text)
    mirror_record = add_source_record(
        stage,
        source_file_id=mirror_file_id,
        relative_path=mirror_path.relative_to(ROOT).as_posix(),
        line_start=1,
        line_end=len(mirror_lines),
        raw_text=mirror_text,
        extraction_method="ctet-mirror-review-config-v1",
        imported_from="config/ctet_mirrors.json",
    )
    try:
        mirror_config = json.loads(mirror_text)
    except json.JSONDecodeError as exc:
        raise SourceError("config/ctet_mirrors.json", exc.lineno, f"invalid JSON: {exc.msg}") from exc

    paper_summaries: list[dict[str, Any]] = []
    section_code_to_id = {
        "cpd": "ctet-paper-1-cpd",
        "mathematics": "ctet-paper-1-mathematics",
        "environmental-studies": "ctet-paper-1-environmental-studies",
        "language-1": "ctet-paper-1-language-1",
        "language-2": "ctet-paper-1-language-2",
    }
    for folder in folders:
        readme_path = folder / "README.md"
        readme_file_id, _, readme_text = add_source_file(stage, readme_path)
        readme_lines = lines_with_endings(readme_text)
        readme_record = add_source_record(
            stage,
            source_file_id=readme_file_id,
            relative_path=readme_path.relative_to(ROOT).as_posix(),
            line_start=1,
            line_end=len(readme_lines),
            raw_text=readme_text,
            extraction_method="ctet-paper-readme-v1",
            imported_from=readme_path.relative_to(ROOT).as_posix(),
        )
        readme_meta = _readme_metadata(readme_text)
        section_files = [
            _parse_section(folder / name, stage)
            for name in ("CPD.txt", "Maths.txt", "EVS.txt", "Eng-1.txt", "Hindi-1.txt", "Eng-2.txt", "Hindi-2.txt")
        ]
        first = section_files[0]
        form_id = f"ctet-{first['exam_date']}-set-{slug(first['set_code'])}"
        for section in section_files:
            for key in ("exam_date", "set_code", "booklet_code", "title"):
                if section[key] != first[key]:
                    raise SourceError(section["source_path"], 1, f"form metadata {key} differs from {section_files[0]['source_path']}")
        if form_id not in mirror_config.get("forms", {}):
            raise PipelineError(f"Mirror-review configuration is missing form {form_id}")

        answer_path = folder / "Answer-Key.txt"
        parsed_key = _parse_key_file(answer_path, stage, form_id)
        answer_map: dict[tuple[str, str, int], tuple[int, ...]] = {}
        for group in parsed_key["groups"]:
            for entry in group["entries"]:
                slot, locale = _get_key_route(group, entry["question_number"])
                answer_map[(slot, locale, entry["question_number"])] = entry["option_positions"]
        detected_mirrors = _discover_mirrors(form_id, section_files, answer_map)
        expected_mirrors = sorted(
            [
                {k: mirror[k] for k in ("slot_code", "locale_a", "locale_b", "question_start", "question_end")}
                for mirror in _expected_mirrors(form_id, mirror_config)
            ],
            key=lambda item: (item["slot_code"], item["question_start"]),
        )
        if detected_mirrors != expected_mirrors:
            raise PipelineError(
                f"CTET mirror candidates changed for {form_id}: detected={detected_mirrors}; reviewed={expected_mirrors}. Re-review config/ctet_mirrors.json before import."
            )
        mirror_by_slot: dict[str, set[int]] = defaultdict(set)
        for mirror in detected_mirrors:
            mirror_by_slot[mirror["slot_code"]].update(range(mirror["question_start"], mirror["question_end"] + 1))

        cycle_label = readme_meta["cycle_label"] or first["exam_date"][:4]
        session_id = f"ctet-session-{slug(cycle_label)}-{first['exam_date']}"
        exam_record = readme_record
        if not any(row["exam_id"] == "ctet" for row in stage["rows"]["exams"]):
            add_row(
                stage,
                "exams",
                {
                    "exam_id": "ctet",
                    "code": "CTET",
                    "name": "Central Teacher Eligibility Test",
                    "conducting_authority": "CBSE",
                    "source_record_id": exam_record,
                },
            )
        add_row(
            stage,
            "exam_sessions",
            {
                "session_id": session_id,
                "exam_id": "ctet",
                "session_label": cycle_label,
                "exam_date": first["exam_date"],
                "source_record_id": readme_record,
            },
        )
        total_questions = readme_meta["total_questions"] or max(s["question_end"] for s in section_files)
        if total_questions != 150:
            raise SourceError(readme_path.relative_to(ROOT).as_posix(), 1, f"expected 150 questions in the paper README, found {total_questions}")
        key_text = (answer_path).read_text(encoding="utf-8")
        key_header_file_id, _, _ = add_source_file(stage, answer_path)
        key_file_lines = lines_with_endings(key_text)
        key_version_record = add_source_record(
            stage,
            source_file_id=key_header_file_id,
            relative_path=parsed_key["source_path"],
            line_start=1,
            line_end=min(5, len(key_file_lines)),
            raw_text="".join(key_file_lines[:5]),
            extraction_method="ctet-answer-key-version-v1",
            imported_from=parsed_key["source_path"],
        )
        form_source_record = readme_record
        form_meta = {
            "form_id": form_id,
            "session_id": session_id,
            "paper_number": 1,
            "set_code": first["set_code"],
            "booklet_code": first["booklet_code"],
            "shift": readme_meta["shift"],
            "duration_minutes": readme_meta["duration_minutes"],
            "total_questions": total_questions,
            "total_marks": float(total_questions),
            "negative_marking": readme_meta["negative_marking"],
            "source_record_id": form_source_record,
        }
        add_row(stage, "paper_forms", form_meta)

        form_blueprint_id = f"bp-{form_id}-v1"
        blueprint_data = [
            {
                "slot_code": s["slot_code"],
                "section_code": s["section_code"],
                "order_index": s["order_index"],
                "question_count": s["question_end"] - s["question_start"] + 1,
                "question_start": s["question_start"],
                "question_end": s["question_end"],
                "locales": sorted(
                    {locale for q in s["questions"].values() for locale in q["locale_blocks"]}
                ),
            }
            for s in section_files
        ]
        blueprint_hash = canonical_hash({"form": form_id, "sections": blueprint_data, "mirrors": detected_mirrors})
        add_row(
            stage,
            "blueprint_versions",
            {
                "blueprint_id": form_blueprint_id,
                "exam_id": "ctet",
                "paper_number": 1,
                "version_number": 1,
                "label": f"CTET Paper I {first['exam_date']} Set {first['set_code']}",
                "expected_questions": total_questions,
                "total_marks": float(total_questions),
                "duration_minutes": readme_meta["duration_minutes"],
                "status": "active",
                "rules_json": canonical_json({"candidate_selects_one_language_per_slot": True}),
                "content_hash": blueprint_hash,
                "source_record_id": readme_record,
            },
        )
        add_row(
            stage,
            "paper_form_blueprints",
            {"form_id": form_id, "blueprint_id": form_blueprint_id, "source_record_id": readme_record},
        )
        groups: dict[str, str] = {}
        for slot in ("language-1", "language-2"):
            group_id = f"bg-{form_id}-{slot}"
            groups[slot] = group_id
            add_row(
                stage,
                "blueprint_selection_groups",
                {
                    "selection_group_id": group_id,
                    "blueprint_id": form_blueprint_id,
                    "group_code": slot,
                    "choose_min": 1,
                    "choose_max": 1,
                    "policy_code": "choose_one_locale",
                    "source_record_id": readme_record,
                },
            )
        form_sections: dict[tuple[str, str], dict[str, Any]] = {}
        sorted_sections = sorted(section_files, key=lambda s: s["order_index"])
        representative_by_slot: dict[str, dict[str, Any]] = {}
        for section in sorted_sections:
            representative_by_slot.setdefault(section["slot_code"], section)
            section_id = section_code_to_id[section["section_code"]]
            existing = next((row for row in stage["rows"]["sections"] if row["section_id"] == section_id), None)
            if existing is None:
                name_en = f"Language {section['language_slot']}" if not section["is_core"] else section["section_name_en"]
                hi_name = None
                if section["is_core"] and "/" in section["section_header"]:
                    hi_name = section["section_header"].split("/", 1)[1].strip(" )")
                add_row(
                    stage,
                    "sections",
                    {
                        "section_id": section_id,
                        "exam_id": "ctet",
                        "paper_number": 1,
                        "section_code": section["section_code"],
                        "name_en": name_en,
                        "name_hi": hi_name,
                        "source_record_id": section["header_record_id"],
                    },
                )

        blueprint_section_ids: dict[str, str] = {}
        for slot_code, section in sorted(representative_by_slot.items(), key=lambda item: item[1]["order_index"]):
            section_id = section_code_to_id[section["section_code"]]
            blueprint_section_id = f"bs-{form_id}-{slot_code}"
            blueprint_section_ids[slot_code] = blueprint_section_id
            selection_group_id = groups.get(slot_code)
            add_row(
                stage,
                "blueprint_sections",
                {
                    "blueprint_section_id": blueprint_section_id,
                    "blueprint_id": form_blueprint_id,
                    "section_id": section_id,
                    "slot_code": slot_code,
                    "order_index": section["order_index"],
                    "question_count": section["question_end"] - section["question_start"] + 1,
                    "question_start": section["question_start"],
                    "question_end": section["question_end"],
                    "required": 1,
                    "selection_group_id": selection_group_id,
                    "source_record_id": section["header_record_id"],
                },
            )
            if section["is_core"]:
                locale_sets = {
                    tuple(sorted(question["locale_blocks"])) for question in section["questions"].values()
                }
                if len(locale_sets) != 1:
                    raise SourceError(section["source_path"], 1, f"core-section locale coverage varies by question: {sorted(locale_sets)}")
                observed_locales = next(iter(locale_sets))
                locale_code = "mul" if len(observed_locales) == 2 else observed_locales[0]
                add_row(
                    stage,
                    "blueprint_section_locales",
                    {
                        "blueprint_section_id": blueprint_section_id,
                        "locale_code": locale_code,
                        "content_mode": "combined" if locale_code == "mul" else "single",
                        "candidate_selectable": 0,
                        "source_record_id": section["header_record_id"],
                    },
                )
            else:
                variants = sorted(
                    (s for s in section_files if s["slot_code"] == slot_code),
                    key=lambda item: item["locale_hint"] or "",
                )
                for variant in variants:
                    locale_code = variant["locale_hint"]
                    add_row(
                        stage,
                        "blueprint_section_locales",
                        {
                            "blueprint_section_id": blueprint_section_id,
                            "locale_code": locale_code,
                            "content_mode": "alternative",
                            "candidate_selectable": 1,
                            "source_record_id": variant["header_record_id"],
                        },
                    )
                    add_row(
                        stage,
                        "blueprint_selection_members",
                        {
                            "selection_group_id": selection_group_id,
                            "blueprint_section_id": blueprint_section_id,
                            "locale_code": locale_code,
                            "source_record_id": variant["header_record_id"],
                        },
                    )

        for section in sorted_sections:
            if section["is_core"]:
                locale_set = tuple(sorted(next(iter(section["questions"].values()))["locale_blocks"]))
                locale_code = "mul" if len(locale_set) == 2 else locale_set[0]
            else:
                locale_code = section["locale_hint"]
            form_section_id = f"fs-{form_id}-{section['slot_code']}-{locale_code}"
            add_row(
                stage,
                "paper_form_sections",
                {
                    "form_section_id": form_section_id,
                    "form_id": form_id,
                    "blueprint_section_id": blueprint_section_ids[section["slot_code"]],
                    "locale_code": locale_code,
                    "source_file_id": section["source_file_id"],
                    "source_record_id": section["header_record_id"],
                },
            )
            form_sections[(section["slot_code"], section.get("locale_hint") or locale_code)] = {
                "form_section_id": form_section_id,
                "locale_code": locale_code,
                "section": section,
            }
        add_row(
            stage,
            "blueprint_rules",
            {
                "blueprint_id": form_blueprint_id,
                "rule_code": "language-slots-must-differ",
                "parameters_json": canonical_json({"slots": ["language-1", "language-2"], "locale_comparison": "not_equal"}),
                "source_record_id": readme_record,
            },
        )

        # Classify paired English "extract" blocks as poems when the parallel Hindi direction identifies poetry.
        for section in section_files:
            if section["is_core"] or section["locale_hint"] != "en":
                continue
            paired = next((s for s in section_files if s["slot_code"] == section["slot_code"] and s.get("locale_hint") == "hi"), None)
            if not paired:
                continue
            paired_types = {(x["question_start"], x["question_end"]): x["stimulus_type"] for x in paired["stimuli"]}
            for stimulus in section["stimuli"]:
                if stimulus["stimulus_type"] == "extract" and paired_types.get((stimulus["question_start"], stimulus["question_end"])) == "poem":
                    stimulus["stimulus_type"] = "poem"

        # Create stimuli before questions so all source text is first-class and linked by explicit ranges.
        for section in section_files:
            for stimulus in section["stimuli"]:
                add_row(
                    stage,
                    "stimuli",
                    {
                        "stimulus_id": stimulus["stimulus_id"],
                        "stimulus_type": stimulus["stimulus_type"],
                        "lifecycle_status": "published",
                        "source_record_id": stimulus["source_record_id"],
                    },
                )
                add_row(
                    stage,
                    "stimulus_contents",
                    {
                        "stimulus_id": stimulus["stimulus_id"],
                        "locale_code": stimulus["locale"],
                        "content_format": "plain_text",
                        "raw_text": stimulus["raw_text"],
                        "display_text": stimulus["display_text"],
                        "instructions": None,
                        "structured_json": None,
                        "source_record_id": stimulus["source_record_id"],
                    },
                )

        # Resolve every key table to one or more source appearances before canonicalizing mirror candidates.
        routed_keys: dict[tuple[str, str | None, int], dict[str, Any]] = {}
        key_entries_for_db: list[dict[str, Any]] = []
        key_table_rows: list[dict[str, Any]] = []
        for group in parsed_key["groups"]:
            key_table_rows.append(group)
            for entry in group["entries"]:
                slot, locale = _get_key_route(group, entry["question_number"])
                key = (slot, locale, entry["question_number"])
                if key in routed_keys:
                    raise SourceError(parsed_key["source_path"], entry["line"], f"duplicate answer route for {key}")
                routed_keys[key] = {**entry, "group": group}
                key_entries_for_db.append({**entry, "group": group, "route": key})
        for section in section_files:
            for number in section["questions"]:
                route = (section["slot_code"], section.get("locale_hint"), number)
                if section["is_core"]:
                    route = (section["slot_code"], None, number)
                if route not in routed_keys:
                    raise SourceError(section["source_path"], section["questions"][number]["line_start"], f"no answer-key entry routes to Q{number} in {section['slot_code']}/{section.get('locale_hint')}")

        # Assemble canonical questions. Only dynamically detected, source-reviewed mirror runs share identity.
        appearance_lookup: dict[tuple[str, str | None, int], dict[str, Any]] = {}
        question_type_sources: dict[str, str] = {}
        canonical_question_ids: set[str] = set()
        for section in sorted_sections:
            locale_questions = section["questions"]
            for number in range(section["question_start"], section["question_end"] + 1):
                parsed_question = locale_questions[number]
                is_core = section["is_core"]
                locale_variants: list[tuple[str, dict[str, Any]]] = []
                if is_core:
                    locale_variants = sorted(parsed_question["locale_blocks"].items())
                    identity_code = section["slot_code"]
                    question_id = f"{form_id}-{identity_code}-q{number:03d}"
                    question_groups = {locale: block for locale, block in locale_variants}
                    source_record_id = parsed_question["source_record_id"]
                    appearance_routes = [(section["slot_code"], None)]
                else:
                    slot = section["slot_code"]
                    locale = section["locale_hint"]
                    mirror_numbers = mirror_by_slot.get(slot, set())
                    if number in mirror_numbers:
                        question_id = f"{form_id}-{slot}-q{number:03d}"
                    else:
                        question_id = f"{form_id}-{slot}-{locale}-q{number:03d}"
                    question_groups = {locale: parsed_question["locale_blocks"][locale]}
                    source_record_id = parsed_question["source_record_id"]
                    appearance_routes = [(slot, locale)]
                if question_id in canonical_question_ids:
                    # The second locale of a confirmed mirror contributes its content and its own appearance.
                    if is_core:
                        raise PipelineError(f"Unexpected canonical ID collision for core CTET question {question_id}")
                    if number not in mirror_by_slot.get(section["slot_code"], set()):
                        raise PipelineError(f"Unexpected duplicate CTET question identity {question_id}")
                    existing_question = next(q for q in stage["rows"]["questions"] if q["question_id"] == question_id)
                    # The prior locale created the option identities; add this locale's text/provenance.
                    for locale, block in question_groups.items():
                        if any(row["question_id"] == question_id and row["locale_code"] == locale for row in stage["rows"]["question_contents"]):
                            raise SourceError(section["source_path"], parsed_question["line_start"], f"mirror Q{number} has duplicate {locale} content")
                        add_row(
                            stage,
                            "question_contents",
                            {
                                "question_id": question_id,
                                "locale_code": locale,
                                "content_format": "plain_text",
                                "raw_stem": block["raw_stem"],
                                "display_stem": block["display_stem"],
                                "structured_json": None,
                                "source_record_id": parsed_question["source_record_id"],
                            },
                        )
                        option_rows = sorted(block["options"], key=lambda x: x["position"])
                        for option in option_rows:
                            option_id = f"{question_id}-opt{option['position']}"
                            add_row(
                                stage,
                                "option_contents",
                                {
                                    "option_id": option_id,
                                    "question_id": question_id,
                                    "locale_code": locale,
                                    "content_format": "plain_text",
                                    "raw_text": option["raw_text"],
                                    "display_text": option["display_text"],
                                    "structured_json": None,
                                    "source_record_id": parsed_question["source_record_id"],
                                },
                            )
                    review = next(
                        m for m in _expected_mirrors(form_id, mirror_config)
                        if m["slot_code"] == section["slot_code"] and m["question_start"] <= number <= m["question_end"]
                    )
                    review_id = stable_id("review", question_id, "canonical-mirror", size=28)
                    add_row(
                        stage,
                        "question_review_records",
                        {
                            "review_id": review_id,
                            "question_id": question_id,
                            "reviewed_field": "canonical_mirror",
                            "outcome": "accepted",
                            "reviewer_kind": "source-profile-review",
                            "note": review["review"],
                            "source_record_id": mirror_record,
                        },
                    )
                else:
                    canonical_question_ids.add(question_id)
                    option_count = len(next(iter(question_groups.values()))["options"])
                    if option_count != 4:
                        raise SourceError(section["source_path"], parsed_question["line_start"], f"Q{number}: expected four options, found {option_count}")
                    answer_route = appearance_routes[0]
                    answer_entry = routed_keys[(answer_route[0], answer_route[1], number)]
                    answer_mode = "multi_select" if len(answer_entry["option_positions"]) > 1 else "single_choice"
                    type_source = answer_entry["source_record_id"] if answer_mode == "multi_select" else source_record_id
                    question_type_sources.setdefault(answer_mode, type_source)
                    for locale, block in question_groups.items():
                        add_row(
                            stage,
                            "question_contents",
                            {
                                "question_id": question_id,
                                "locale_code": locale,
                                "content_format": "plain_text",
                                "raw_stem": block["raw_stem"],
                                "display_stem": block["display_stem"],
                                "structured_json": None,
                                "source_record_id": parsed_question["source_record_id"],
                            },
                        )
                    first_block = next(iter(question_groups.values()))
                    for option in sorted(first_block["options"], key=lambda x: x["position"]):
                        option_id = f"{question_id}-opt{option['position']}"
                        add_row(
                            stage,
                            "question_options",
                            {
                                "option_id": option_id,
                                "question_id": question_id,
                                "position": option["position"],
                                "original_label": option["label"],
                                "source_record_id": parsed_question["source_record_id"],
                            },
                        )
                    for locale, block in question_groups.items():
                        for option in sorted(block["options"], key=lambda x: x["position"]):
                            option_id = f"{question_id}-opt{option['position']}"
                            add_row(
                                stage,
                                "option_contents",
                                {
                                    "option_id": option_id,
                                    "question_id": question_id,
                                    "locale_code": locale,
                                    "content_format": "plain_text",
                                    "raw_text": option["raw_text"],
                                    "display_text": option["display_text"],
                                    "structured_json": None,
                                    "source_record_id": parsed_question["source_record_id"],
                                },
                            )
                    add_row(
                        stage,
                        "questions",
                        {
                            "question_id": question_id,
                            "type_code": answer_mode,
                            "lifecycle_status": "published",
                            "primary_source_record_id": source_record_id,
                            "canonical_fingerprint": canonical_hash(
                                {
                                    "locales": {
                                        loc: {
                                            "stem": block["raw_stem"],
                                            "options": [opt["raw_text"] for opt in sorted(block["options"], key=lambda x: x["position"])],
                                        }
                                        for loc, block in question_groups.items()
                                    }
                                }
                            ),
                        },
                    )
                # Create the appearance for this physical file/locale.
                if is_core:
                    locale_code = "mul" if len(parsed_question["locale_blocks"]) == 2 else next(iter(parsed_question["locale_blocks"]))
                    form_section = form_sections[(section["slot_code"], locale_code)]
                    route = (section["slot_code"], None, number)
                else:
                    locale = section["locale_hint"]
                    form_section = form_sections[(section["slot_code"], locale)]
                    route = (section["slot_code"], locale, number)
                appearance_id = f"app-{form_section['form_section_id']}-q{number:03d}"
                add_row(
                    stage,
                    "question_appearances",
                    {
                        "appearance_id": appearance_id,
                        "form_section_id": form_section["form_section_id"],
                        "question_id": question_id,
                        "question_number": number,
                        "sequence_in_section": number - section["question_start"] + 1,
                        "points": 1.0,
                        "source_record_id": parsed_question["source_record_id"],
                    },
                )
                appearance_lookup[route] = {"appearance_id": appearance_id, "question_id": question_id}
                for stimulus_id in parsed_question["stimulus_ids"]:
                    position = sum(1 for row in stage["rows"]["stimulus_question_links"] if row["stimulus_id"] == stimulus_id) + 1
                    add_row(
                        stage,
                        "stimulus_question_links",
                        {
                            "stimulus_id": stimulus_id,
                            "appearance_id": appearance_id,
                            "relation_code": "context",
                            "position": position,
                            "source_record_id": next(s["source_record_id"] for s in section["stimuli"] if s["stimulus_id"] == stimulus_id),
                        },
                    )

        for answer_mode, source_id in sorted(question_type_sources.items()):
            if any(row["type_code"] == answer_mode for row in stage["rows"]["question_types"]):
                continue
            add_row(
                stage,
                "question_types",
                {
                    "type_code": answer_mode,
                    "answer_mode": "option_set",
                    "options_min": 4,
                    "options_max": 4,
                    "allows_multiple": 1 if answer_mode == "multi_select" else 0,
                    "configuration_json": canonical_json({"option_order_is_significant": True}),
                    "source_record_id": source_id,
                },
            )

        answer_version_id = f"akv-{form_id}-cbse-final"
        authority_uri = _extract_official_key_uri(readme_text)
        add_assertion(
            stage,
            readme_record,
            "answer_key_authority_claim",
            "paper-readme",
            {
                "authority": "CBSE",
                "status": "final",
                "claim_source": "paper README",
                "authority_uri": authority_uri,
                "transcription_independently_compared_to_authority_pdf": False,
            },
        )
        add_row(
            stage,
            "answer_key_versions",
            {
                "answer_key_version_id": answer_version_id,
                "form_id": form_id,
                "version_label": "CBSE-final-as-transcribed",
                "authority_class": "exam_authority",
                "status": "final",
                "published_date": None,
                "authority_uri": authority_uri,
                "source_record_id": readme_record,
                "content_hash": canonical_hash(
                    [{"table": g["header"], "entries": [{"q": e["question_number"], "a": e["raw_answer"]} for e in g["entries"]]} for g in parsed_key["groups"]]
                ),
            },
        )
        for group in parsed_key["groups"]:
            add_row(
                stage,
                "answer_key_tables",
                {
                    "answer_key_table_id": group["table_id"],
                    "answer_key_version_id": answer_version_id,
                    "table_label": group["label"],
                    "raw_heading": group["header"],
                    "locale_code": group["locale"],
                    "slot_code": group["slot_code"],
                    "question_start": group["question_start"],
                    "question_end": group["question_end"],
                    "source_record_id": group["source_record_id"],
                },
            )
        for entry in key_entries_for_db:
            group = entry["group"]
            slot, locale = _get_key_route(group, entry["question_number"])
            if slot in ("cpd", "mathematics", "environmental-studies"):
                route = (slot, None, entry["question_number"])
            else:
                route = (slot, locale, entry["question_number"])
            appearance = appearance_lookup.get(route)
            if appearance is None:
                raise SourceError(parsed_key["source_path"], entry["line"], f"key route {route} has no parsed appearance")
            key_entry_id = stable_id("ake", answer_version_id, group["table_id"], appearance["appearance_id"], size=28)
            add_row(
                stage,
                "answer_key_entries",
                {
                    "answer_key_entry_id": key_entry_id,
                    "answer_key_table_id": group["table_id"],
                    "appearance_id": appearance["appearance_id"],
                    "question_id": appearance["question_id"],
                    "raw_answer": entry["raw_answer"],
                    "answer_mode": "option_set",
                    "scalar_answer": None,
                    "response_json": None,
                    "source_record_id": entry["source_record_id"],
                },
            )
            for position, option_position in enumerate(entry["option_positions"], 1):
                option_id = f"{appearance['question_id']}-opt{option_position}"
                add_row(
                    stage,
                    "answer_key_entry_options",
                    {
                        "answer_key_entry_id": key_entry_id,
                        "question_id": appearance["question_id"],
                        "option_id": option_id,
                        "position": position,
                        "source_record_id": entry["source_record_id"],
                    },
                )

        paper_summaries.append(
            {
                "form_id": form_id,
                "exam_date": first["exam_date"],
                "set_code": first["set_code"],
                "section_files": len(section_files),
                "question_file_appearances": sum(len(s["questions"]) for s in section_files),
                "canonical_questions": sum(
                    1 for q in stage["rows"]["questions"] if q["question_id"].startswith(form_id + "-")
                ),
                "stimuli": sum(len(s["stimuli"]) for s in section_files),
                "key_groups": len(parsed_key["groups"]),
                "key_entries": sum(len(g["entries"]) for g in parsed_key["groups"]),
                "mirrors": detected_mirrors,
            }
        )
    if set(mirror_config.get("forms", {})) != {p["form_id"] for p in paper_summaries}:
        raise PipelineError("config/ctet_mirrors.json contains a form that is absent from the discovered CTET input tree")
    return {"papers": paper_summaries}
