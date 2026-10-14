# PYQ booklets — CTET & UTET, Paper I

Printable, mobile-friendly previous-year question papers, one HTML booklet per paper,
arranged year-wise. Common sections are printed in English and Hindi side by side;
language sections are printed in the medium they were set in.

```text
pyq-booklets/
  index.html              index of all booklets (grouped by exam and year)
  ctet/                   CTET Paper I booklets (5 papers)
  utet/                   UTET Paper I booklets (6 papers)
  build_booklets.py       generator (reads the repository database)
```

## Source

All questions, options, passages and answers come from
`data/xtet-question-bank.json` (the repository question database). Nothing is typed by hand.
Regenerate after the database changes:

```bash
python3 pyq-booklets/build_booklets.py
```

## Answer keys

- **CTET** booklets use the official final answer key. All 630 CTET answers for the
  Common and Language sections of Sets I (2021), A (2023) and E (2026) were checked
  against the `Answer-Key.txt` files in this repository with no mismatches.
- **UTET** booklets use a **provisional** key from the repository database. It is not an
  official key and has not been checked against one. Each booklet says so on its cover and
  in its answer key.

## Known limits

- The database holds only some language media for UTET: Language I (Hindi) and
  Language II (English). Language I (English), Sanskrit and Urdu are not in it, so those
  booklets do not contain them.
- The CTET 2023 Set A common sections (Child Development and Pedagogy, Mathematics,
  Environmental Studies) are Hindi-only in the source, and the booklet says so.
- Language sections list only the answer-relevant medium. A candidate attempts one
  language; the booklet prints both media where the paper does.
- Fonts load from Google Fonts. Offline, the page falls back to Georgia.
