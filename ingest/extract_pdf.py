#!/usr/bin/env python3
"""extract_pdf.py — Best-effort MCQ extraction from a CTET-style PDF.

TUM apne downloaded PDF par chalaoge (personal copy). Output schema/question.schema.json
ke mutabik section-file JSON hota hai, marked needs_review=true.

Usage:
    python ingest/extract_pdf.py <input.pdf> [-o out.json] [--session 2024-12] [--set H]

Important:
- Extraction best-effort hai: bilingual (hi/en) split, option cleanup aur section
  boundaries ka human review zaroori hai.
- Ye tool koi reuse right GRANT NAHI karta. Output mein provenance.reuse_permission
  default "unclear" set hota hai. App mein display karne se pehle permission verify karo.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber missing. Run: pip install -r ingest/requirements.txt")

SECTION_HINTS = [
    ("cdp", ["child development and pedagogy", "बाल विकास एवं शिक्षण शास्त्र", "बाल विकास तथा शिक्षण"]),
    ("math", ["mathematics", "गणित"]),
    ("evs", ["environmental studies", "पर्यावरण अध्ययन", "पर्यावरणीय अध्ययन"]),
    ("language", ["language-i", "language-ii", "language i", "language ii", "भाषा-1", "भाषा-2", "भाषा -1", "भाषा -2"]),
]

Q_RE = re.compile(r"^\s*(?:Q\.?\s*|प्रश्न\s*)?(\d{1,3})\s*[.)]\s*(.+)$")
OPT_RE = re.compile(r"^\s*\(([1-4]|[a-dA-D])\)\s*(.+)$")


def detect_section(line: str):
    low = line.lower()
    for sid, keys in SECTION_HINTS:
        if any(k in low for k in keys):
            return sid
    return None


def extract(pdf_path: Path):
    questions = []
    current = None
    current_section = "unknown"
    expected = 1

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue

                sec = detect_section(line)
                if sec and len(line) < 120:
                    current_section = sec
                    continue

                m = Q_RE.match(line)
                if m:
                    no = int(m.group(1))
                    if no == 1 or no == expected:
                        if current:
                            questions.append(current)
                        current = {
                            "no": no,
                            "raw": m.group(2).strip(),
                            "options_raw": [],
                            "page": page.page_number,
                            "section_id": current_section,
                        }
                        expected = no + 1
                        continue

                om = OPT_RE.match(line)
                if om and current is not None:
                    current["options_raw"].append(om.group(2).strip())
                    continue

                if current is not None:
                    # continuation line -> attach to question text (review later)
                    current["raw"] += " " + line

    if current:
        questions.append(current)
    return questions


def to_schema(questions, source, session, set_code):
    doc = {
        "section_id": "unknown",
        "paper_id": None,
        "kind": "extracted_pyq",
        "extraction": {
            "source_file": str(source),
            "tool": "extract_pdf.py v1",
            "needs_review": True,
        },
        "questions": [],
    }
    sections = {q["section_id"] for q in questions}
    if len(sections) == 1 and sections != {"unknown"}:
        doc["section_id"] = next(iter(sections))

    for q in questions:
        opts = q["options_raw"][:4] if len(q["options_raw"]) >= 4 else q["options_raw"]
        doc["questions"].append(
            {
                "no": q["no"],
                "text": {"raw": q["raw"]},
                "options": {"raw": opts},
                "answer": None,
                "explanation": None,
                "topic": None,
                "difficulty": None,
                "provenance": {
                    "content_type": "official_pyq",
                    "session_id": session,
                    "set_code": set_code,
                    "source_file": str(source),
                    "source_url": None,
                    "page": q.get("page"),
                    "reuse_permission": "unclear",
                    "notes": "Machine-extracted; human review + hi/en split required.",
                },
            }
        )
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", help="input PDF file (aapki apni downloaded copy)")
    ap.add_argument("-o", "--out", help="output JSON path (default: <pdf>.extracted.json)")
    ap.add_argument("--session", help="session id, e.g. 2024-12")
    ap.add_argument("--set", help="set code, e.g. H")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        sys.exit(f"PDF not found: {pdf_path}")

    questions = extract(pdf_path)
    doc = to_schema(questions, pdf_path, args.session, args.set)

    out = Path(args.out) if args.out else pdf_path.with_suffix(".extracted.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(doc['questions'])} questions -> {out}")
    print("Next: review + hi/en split, then run ingest/validate.py", out.name)


if __name__ == "__main__":
    main()
