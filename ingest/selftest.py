#!/usr/bin/env python3
"""selftest.py — End-to-end test of the ingestion pipeline using ORIGINAL content only.

Koi CBSE material use NAHI hota: practice/set-01 ke apne original CDP questions mein se
5 questions lekar ek sample PDF banata hai, phir extract_pdf.py + validate.py chala kar
poora workflow prove karta hai.

Usage:
    python ingest/selftest.py
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
SAMPLE_PDF = HERE / "pdf" / "sample-original.pdf"
SAMPLE_OUT = HERE / "out" / "sample-original.extracted.json"


def make_sample_pdf():
    """Build a small PDF from OUR OWN original questions (English only, layout test)."""
    from fpdf import FPDF

    src = json.loads((ROOT / "practice/set-01/sections/cdp.json").read_text(encoding="utf-8"))
    questions = src["questions"][:5]

    pdf = FPDF()
    pdf.add_page()
    w = pdf.epw
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(w=w, h=7, text="Child Development and Pedagogy")
    pdf.set_font("Helvetica", size=11)

    for q in questions:
        # keep sample PDF latin-1 safe (core fonts)
        text = f"{q['no']}. {q['text']['en']}".encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(w=w, h=6, text=text)
        for i, opt in enumerate(q["options"]["en"], start=1):
            opt_text = f"    ({i}) {opt}".encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(w=w, h=6, text=opt_text)
        pdf.ln(2)

    SAMPLE_PDF.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(SAMPLE_PDF))
    return len(questions)


def main():
    py = sys.executable
    n = make_sample_pdf()
    print(f"[1/3] Sample PDF generated from {n} ORIGINAL questions -> {SAMPLE_PDF}")

    r = subprocess.run(
        [py, str(HERE / "extract_pdf.py"), str(SAMPLE_PDF), "-o", str(SAMPLE_OUT),
         "--session", "selftest", "--set", "SAMPLE"],
        capture_output=True, text=True,
    )
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr)
        sys.exit("[2/3] FAIL: extraction failed")

    doc = json.loads(SAMPLE_OUT.read_text(encoding="utf-8"))
    got = len(doc["questions"])
    print(f"[2/3] Extraction produced {got} questions")
    if got != n:
        sys.exit(f"[2/3] FAIL: expected {n} questions, got {got}")

    r = subprocess.run([py, str(HERE / "validate.py"), str(SAMPLE_OUT)], capture_output=True, text=True)
    print("[3/3] Validation output:")
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr)
        sys.exit("[3/3] FAIL: validation failed")

    print("\nSELFTEST PASSED — ingestion pipeline works end-to-end (original content only).")


if __name__ == "__main__":
    main()
