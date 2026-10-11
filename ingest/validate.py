#!/usr/bin/env python3
"""validate.py — Structural validation of Xtet section/question JSON files.

Usage:
    python ingest/validate.py file1.json [file2.json ...]

Exit code: 0 = all clean, 1 = errors found.

Checks:
- unique + continuous question numbering
- non-empty text, >= 4 options
- valid answer letters, valid provenance fields
- WARNs on missing Hindi translation and on PYQ content with unclear reuse permission
"""
import json
import sys
from pathlib import Path

VALID_CONTENT_TYPES = {"official_pyq", "third_party_pyq", "original_practice"}
VALID_PERMS = {"granted", "public_domain", "unclear", "not_required"}
VALID_ANSWERS = {"a", "b", "c", "d", None}
TEXT_KEYS = ("en", "hi", "raw")


def validate_file(path: str):
    errors, warnings = [], []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    questions = data.get("questions", [])

    if not questions:
        errors.append("no questions found in file")
        return errors, warnings

    seen = []
    for q in questions:
        no = q.get("no")
        if no in seen:
            errors.append(f"q{no}: duplicate question number")
        seen.append(no)

        text = q.get("text", {}) or {}
        if not any(text.get(k) for k in TEXT_KEYS):
            errors.append(f"q{no}: empty text (need en/hi/raw)")
        if text.get("en") and not text.get("hi"):
            warnings.append(f"q{no}: English present but Hindi missing")
        if text.get("raw") and not (text.get("en") or text.get("hi")):
            warnings.append(f"q{no}: text not yet split into hi/en (raw only)")

        opts = q.get("options", {}) or {}
        flat = opts.get("en") or opts.get("raw") or opts.get("hi") or []
        if len(flat) < 4:
            errors.append(f"q{no}: fewer than 4 options ({len(flat)})")
        elif len(flat) > 4:
            warnings.append(f"q{no}: more than 4 options ({len(flat)})")

        ans = q.get("answer")
        if ans not in VALID_ANSWERS:
            errors.append(f"q{no}: invalid answer value '{ans}'")

        prov = q.get("provenance") or {}
        if not prov:
            errors.append(f"q{no}: missing provenance (required for permission tracking)")
        else:
            ct = prov.get("content_type")
            rp = prov.get("reuse_permission")
            if ct not in VALID_CONTENT_TYPES:
                errors.append(f"q{no}: bad provenance.content_type '{ct}'")
            if rp not in VALID_PERMS:
                errors.append(f"q{no}: bad provenance.reuse_permission '{rp}'")
            if ct in {"official_pyq", "third_party_pyq"} and rp == "unclear":
                warnings.append(f"q{no}: PYQ content with UNCLEAR reuse permission — verify before displaying in app")

    nums = sorted(seen)
    if nums != list(range(nums[0], nums[0] + len(nums))):
        errors.append(f"question numbers not continuous: got {nums[:6]}...")

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python ingest/validate.py <file.json> [more.json ...]")

    rc = 0
    for f in sys.argv[1:]:
        try:
            errs, warns = validate_file(f)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {f}: {e}")
            rc = 1
            continue
        status = "OK  " if not errs else "FAIL"
        if errs:
            rc = 1
        print(f"{status} {f} — {len(errs)} error(s), {len(warns)} warning(s)")
        for e in errs[:15]:
            print(f"  ERROR: {e}")
        for w in warns[:15]:
            print(f"  warn:  {w}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
