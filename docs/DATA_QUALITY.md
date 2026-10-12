# Data quality report

**Database:** `data/xtet-question-bank.sqlite`<br>
**Content hash:** `f92ebbb63338c1bc06570899dbb3376437c39a911bae4819107a49f72fe105cd`<br>
**Source manifest hash:** `5ca08551abdba96646e9341eba59fb3c22d25c746951d45bdad87953ad4c4e7f`<br>
**SQLite runtime:** `3.40.1` (FTS5/JSON1 enabled)<br>
**Verification:** SQLite integrity, foreign keys, FTS5 integrity, counts, answer-key boundaries, and content hash passed.

## Imported inventory

| Exam | Forms | Canonical questions | Question appearances | Answer-key entries |
|---|---:|---:|---:|---:|
| CTET | 5 | 930 | 1050 | 1050 |
| UTET | 6 | 900 | 900 | 900 |

The database contains **109 source files**, **4959 source records**, **2850 localized question-content rows**, **7320 options**, **64 stimuli**, and **411 stimulus-to-appearance links**.

## Form-level structural counts

| Exam | Form | Date | Set | Configured questions | Imported appearances | Key entries |
|---|---|---|---|---:|---:|---:|
| CTET | `ctet-2021-01-31-set-i` | 2021-01-31 | I | 150 | 210 | 210 |
| CTET | `ctet-2023-08-20-set-a` | 2023-08-20 | A | 150 | 210 | 210 |
| CTET | `ctet-2024-01-21-set-i` | 2024-01-21 | I | 150 | 210 | 210 |
| CTET | `ctet-2024-07-07-set-a` | 2024-07-07 | A | 150 | 210 | 210 |
| CTET | `ctet-2026-02-08-set-e` | 2026-02-08 | E | 150 | 210 | 210 |
| UTET | `utet-p1-2020-set-a` | 2020-11-06 | A | 150 | 150 | 150 |
| UTET | `utet-p1-2021-set-c` | 2021-03-24 | C | 150 | 150 | 150 |
| UTET | `utet-p1-2022-set-b` | 2022-11-26 | B | 150 | 150 | 150 |
| UTET | `utet-p1-2024-set-d` | 2024-09-29 | D | 150 | 150 | 150 |
| UTET | `utet-p1-2025-set-a` | 2025-10-24 | A | 150 | 150 | 150 |
| UTET | `utet-p1-2026-set-a` | 2026-09-29 | A | 150 | 150 | 150 |

CTET imports **210 file appearances and 210 key rows per form** because all four optional language streams are retained. Candidate-facing form configuration still specifies 150 questions and requires one locale per language slot. UTET has 150 appearances and 150 embedded source-answer rows per form.

## Answer authority and multi-correct expansions

| Exam | Form | Authority class | Status | Authority URI recorded |
|---|---|---|---|---|
| CTET | `ctet-2021-01-31-set-i` | exam_authority | final | <https://cdnbbsr.s3waas.gov.in/s3443dec3062d0286986e21dc0631734c9/uploads/2022/03/2022033154.pdf> |
| CTET | `ctet-2023-08-20-set-a` | exam_authority | final | Not linked in source README |
| CTET | `ctet-2024-01-21-set-i` | exam_authority | final | <https://cdnbbsr.s3waas.gov.in/s3443dec3062d0286986e21dc0631734c9/uploads/2024/02/2024021954.pdf> |
| CTET | `ctet-2024-07-07-set-a` | exam_authority | final | <https://cdnbbsr.s3waas.gov.in/s3443dec3062d0286986e21dc0631734c9/uploads/2024/08/2024080797.pdf> |
| CTET | `ctet-2026-02-08-set-e` | exam_authority | final | <https://cdnbbsr.s3waas.gov.in/s3443dec3062d0286986e21dc0631734c9/uploads/2026/04/20260401449979389.pdf> |
| UTET | `utet-p1-2020-set-a` | source_repository | provisional | Not linked in source README |
| UTET | `utet-p1-2021-set-c` | source_repository | provisional | Not linked in source README |
| UTET | `utet-p1-2022-set-b` | source_repository | provisional | Not linked in source README |
| UTET | `utet-p1-2024-set-d` | source_repository | provisional | Not linked in source README |
| UTET | `utet-p1-2025-set-a` | source_repository | provisional | Not linked in source README |
| UTET | `utet-p1-2026-set-a` | source_repository | provisional | Not linked in source README |

**Official-final view rows:** 1050. **UTET provisional source-repository answer rows kept out of that view:** 900.
The parser expanded multi-correct source letters into **1968 correct-option links** across **1950 answer entries**; source tokens remain stored verbatim.

The CTET `Answer-Key.txt` values are imported as the official-final versions described by the corresponding paper READMEs. This is a structural parse, not a re-comparison against the linked CBSE PDF. Forms without a direct official-key URI in source metadata: `ctet-2023-08-20-set-a`. The UTET repository's embedded answers are explicitly `source_repository`/`provisional`; no official UBSE key was evidenced in the pinned manifest/audit sources.

## Locale, stimuli, annotations, and provenance

| Question locale | Content rows |
|---|---:|
| en | 1380 |
| hi | 1470 |

- **Stimuli:** 64 total; all have at least one linked question appearance. Inline CTET reading blocks and UTET stimulus rows are separate entities.
- **Source audits:** 900 UTET audit records are linked to their canonical questions.
- **Assets/explanations:** 0 assets and 0 explanations are imported; source inputs provide no relevant files/content in this scope.
- **Taxonomy/difficulty/Bloom:** 0 taxonomy nodes, 0 assignments, and 0 assessments. These remain intentionally empty/unrated.
- **FTS5:** 2850 localized search documents; `integrity-check` passed and sample multilingual search returned 102 rows.
- **Raw provenance:** every imported source file is SHA-256 fingerprinted. Extracted question/key/audit records retain raw source text, file path, line range, extraction method, `imported_from`, and (for UTET) pinned commit/license/attribution metadata.

## Source license and limitations

- `Unassigned / not asserted`: 48 source files.
- `CC-BY-4.0`: 61 source files.
- CTET source files are not assigned a license by this pipeline; paper READMEs include source-quality notes, including legacy-font transcription/review limitations. Raw text remains unchanged and no editorial correction is applied.
- UTET source is pinned to `sherawali/tet` commit `6792637052eb0bcddd27b9290ddd082faa725a4d`, CC BY 4.0, attributed to TET Question Bank contributors (2026). Its `verified` flags are repository-level assertions, not an official UBSE endorsement.
- No content-level re-verification against exam authority scans/PDFs was performed. Validation gates cover source/schema structure, database constraints, linkage, answer expansion, deterministic content hashing, and search integrity.

## Validation summary

- `PRAGMA integrity_check`: ok
- `PRAGMA foreign_key_check`: 0 violations
- FTS5 integrity: ok
- Content hash re-computation: `f92ebbb63338c1bc06570899dbb3376437c39a911bae4819107a49f72fe105cd`

To regenerate: `python -m pipeline report --db data/xtet-question-bank.sqlite --output docs/DATA_QUALITY.md`.
