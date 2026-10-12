# Data profile: CTET and UTET Paper I inputs

**Status:** Phase 1 inspection complete. This file records observed source structure and known limits; it is not a content correction or a claim that every transcription has been compared against an official scan.

## Scope and inspection method

The CTET inputs are the five paper directories already present in this repository. For each, inspection covered all seven section `.txt` files, `Answer-Key.txt`, and `README.md` in full. The audit was structural: expected question-number ranges, option-group counts, key entries and key-table headings, language blocks, known mirror regions, and source notes. No source file was edited, rewritten, re-formatted, or retranscribed.

UTET was inspected read-only from [`sherawali/tet`](https://github.com/sherawali/tet), `bank-v2`, at commit `6792637052eb0bcddd27b9290ddd082faa725a4d`. Its question/form/appearance/stimulus data and schema files were read without changing that repository. All 12 supplied JSON Schema files passed Draft 2020-12 meta-schema checks. The 900 question rows, 900 appearance rows, six form rows, and 24 stimulus rows (1,830 records total) validated with zero schema errors against their corresponding schemas, including local `$ref` definitions. This is source-schema validation only; it is not yet validation of the target SQLite schema or importer.

## CTET inventory and structure

Each CTET paper directory contains seven section files, one answer-key file, and one README. Across the five folders this is 35 section files, five answer-key files, and five paper READMEs.

| Folder / paper | Exam date and set | Booklet / session notes recorded in README | Common sections (Q1–90) | Language-section content |
|---|---|---|---|---|
| `2021/CTET_Paper1_Jan2021_SetI` | 31 Jan 2021, Set I (CTET 2020 cycle) | Booklet `AAT-20-I` | CPD, Maths, EVS are Hindi + English | Eng-1 and Hindi-1 each Q91–120; Eng-2 and Hindi-2 each Q121–150 |
| `2023/CTET_Paper1_Aug2023_SetA` | 20 Aug 2023, Set A, morning | README identifies the CBSE booklet; no booklet code is stated | CPD, Maths, EVS are Hindi-only in these files | Both English and Hindi streams are present for Language I and II |
| `2024/CTET_Paper1_Jan2024_SetI` | 21 Jan 2024, Set I | Booklet `SAS-24-I`; README does not state a shift | CPD, Maths, EVS are Hindi + English | Eng-1 and Hindi-1 each Q91–120; Eng-2 and Hindi-2 each Q121–150 |
| `2024/CTET_Paper1_Jul2024_SetA` | 7 Jul 2024, Set A | Main booklet `JSS-24-I`; README records shift 2, 14:00–16:30 | CPD, Maths, EVS are Hindi + English | Eng-1 and Hindi-1 each Q91–120; Eng-2 and Hindi-2 each Q121–150 |
| `2026/CTET_Paper1_Feb2026_SetE` | 8 Feb 2026, Set E (Dec 2025 cycle) | Main booklet `FSC-26-I`; this is the 8 Feb sitting, not the 7 Feb forms | CPD, Maths, EVS are Hindi + English | Eng-1 and Hindi-1 each Q91–120; Eng-2 and Hindi-2 each Q121–150 |

Across all five papers, the observed section ranges are CPD Q1–30, Maths Q31–60, EVS Q61–90, Language I Q91–120, and Language II Q121–150. These ranges describe this CTET source set; the importer must not apply them to another exam or infer them from a file name alone.

### Structural count results

- Every one of the 35 section files contains all 30 question numbers expected for its section range.
- Every question has four ordered answer options in each language block present. The 12 CPD/Maths/EVS files from the four bilingual core papers contain two four-option blocks per question; the three August 2023 core files contain one Hindi four-option block per question. The 20 language-section files each contain one four-option block per question.
- Each CTET `Answer-Key.txt` contains 210 answer entries. The number is 90 common-core answers plus 120 entries for the four alternative language streams; it is not a 150-entry candidate-specific key. A candidate selects one Language I and one Language II stream.
- All five keys cover Q1–150 with their own section/language grouping. The group count is **seven** for 2021, August 2023, January 2024, and July 2024; it is **five** for February 2026. The February 2026 key alone combines each language's Language I and Language II ranges into one Q91–150 table. July 2024 still has separate Language I/II and English/Hindi groups in the supplied text key.
- Section/key headings—not file order, assumptions about seven headers, or a flat count of lines beginning with digits—are required to route answers. August 2023 lists Hindi before English in its language-key groups; the section filenames remain explicit.

### Language mirrors and reading material

The common core is represented inside each question file as English and Hindi content for 2021, January 2024, July 2024, and February 2026. August 2023's three common-core files have Hindi content only; no English translation is present in this source set and none should be invented.

English/Hindi language sections are separate streams. The following cross-file mirror regions were identified by comparing the parallel stems and option order in the two streams, checking their question numbers, and using matching key sequences as corroboration. Equal answer keys alone are not enough: unrelated passage questions sometimes happen to have the same answers.

| Paper | Language I English/Hindi mirror | Language II English/Hindi mirror | Non-mirrored reading-question ranges |
|---|---|---|---|
| January 2021 | None observed; the language streams are independent | None observed; the language streams are independent | Each language stream has its own reading content, including numbered passage lines in the English files |
| August 2023 | Q91–105 | Q136–150 | L1 Q106–120 (passage Q106–114, poem Q115–120); L2 Q121–135 (passages Q121–127 and Q128–135) |
| January 2024 | Q106–120 | Q136–150 | L1 Q91–105 and L2 Q121–135 use different English/Hindi reading content |
| July 2024 | Q106–120 | Q136–150 | L1 Q91–105 and L2 Q121–135 use different English/Hindi reading content |
| February 2026 | Q106–120 | Q136–150 | L1 Q91–105 and L2 Q121–135 use different English/Hindi reading content |

The two 15-question language-pedagogy mirrors in the later papers do not mean the whole English and Hindi sections are translations. For example, passage-based questions remain language-specific. In the January 2024 paper, the README warns against treating the comprehension passages as translations; the separate pedagogy blocks Q106–120 and Q136–150 are nevertheless parallel translations in the supplied files. In August 2023, Q135 happens to share a key answer with the adjacent mirrored range, and in February 2026 Q134–135 also share key answers across streams; those passage questions are not thereby part of the mirror. The pipeline should detect/record these regions per paper from source evidence, not encode one universal fixed range.

The reading blocks are inline in the CTET section files rather than stored in a stimulus file. The observed question ranges are:

| Paper | Language I reading blocks | Language II reading blocks |
|---|---|---|
| January 2021 | Q91–99 and Q100–105 in each language stream | Q121–128 and Q129–135 in each language stream |
| August 2023 | Q106–114 and Q115–120 in each language stream | Q121–127 and Q128–135 in each language stream |
| January 2024 | Q91–99 and Q100–105 in each language stream | Q121–128 and Q129–135 in each language stream |
| July 2024 | Q91–99 and Q100–105 in each language stream | Q121–128 and Q129–135 in each language stream |
| February 2026 | Q91–99 and Q100–105 in each language stream | Q121–128 and Q129–135 in each language stream |

The blocks include prose and poems or literary extracts as described in the per-paper READMEs. They should become first-class, locale-specific stimuli linked to the relevant question range. Some inline tables, multi-line statements, and mathematical notation are part of question content and must remain intact; this source set supplies no separate CTET image/audio asset bundle.

### CTET parsing traps, key notation, and textual quirks

- An unrestricted `^\d+\.` line count is not a question count. In the January 2021 English Language I file it finds 33 numbered lines, and in English Language II it finds 45, because numbered passage lines are mixed with the 30 question numbers. Restricting the audit to the declared question-number range yields 30 questions in each. The July 2024 English files yield 30 expected question markers each; the 33/45 case is in January 2021, not July 2024.
- Option order and the four numbered choices must be preserved. Stems may include sub-statements, continuations, or passage references; a period at the beginning of a line is not sufficient to classify it as a new question.
- Key values are single option numbers `1`–`4` or source-key multi-answer letters. The keys define A–F and Z as option sets; the source token must be kept alongside its expansion. Observed non-single answers are:

  | Paper | Key entries requiring multi-correct expansion |
  |---|---|
  | August 2023 | Maths Q40 = A = options 1 and 2 |
  | January 2024 | EVS Q80 = Z = all four options; Language I Q106 = E = options 2 and 4 in both language tables |
  | July 2024 | Maths Q35 = Z, Q48 = Z; EVS Q63 = D (2,3), Q90 = A (1,2); Language II Q136 = B (1,3) in English and Hindi |
  | February 2026 | CPD Q26 = F (3,4); English-language Q125 = F (3,4) |

  No multi-correct tokens were observed in the January 2021 key. Do not apply a letter mapping unless it is documented by that key's notation and the question's option count.
- The observed underscore placeholder runs vary by source file. Counts below are of literal runs of two or more underscores, grouped by run length; they are not a normalization instruction.

  | Paper | Literal underscore-run lengths (run length: count) |
  |---|---|
  | January 2021 | 8: 45 |
  | August 2023 | 6: 1; 8: 22; 11: 3; 12: 1 |
  | January 2024 | 8: 4; 10: 23 |
  | July 2024 | 8: 51 |
  | February 2026 | 8: 46 |

  Preserve the actual run, including non-eight-character blanks. Do not globally replace runs with `________`.
- The July 2024 Maths Q59 uses `*` as a literal unknown operator in the expression `(7 * 2) × (123) = 92496`; it is mathematical content, not a formatting marker.
- The Python UTF-8 read of the supplied section/key text succeeded; a scan found no Unicode replacement character or common mojibake markers. This is a character-level check, not a language proofread.
- Paper-specific source notes that affect confidence and must be carried into quality/provenance reporting:
  - **January 2021:** the official booklet's Hindi text layer is described as legacy-font encoded. The clean Hindi transcription was cross-checked against Studyfry, so exact Hindi wording/typography is not independently verified against a clean official scan. The README explicitly says Studyfry answers are not the authority and notes answer discrepancies; the key follows the CBSE final key.
  - **August 2023:** its README says the answer key is based on the CBSE final key and records the Maths Q40 multi-answer. It does not include a direct official PDF URL for that key.
  - **January 2024:** the README records that a manual Hindi language pass corrected wording/spelling/grammar/punctuation without changing options or key, and cautions that exact Hindi wording was not checked against a clean booklet source. Hindi-1 Q94 has intentionally incorrect spelling distractors which must remain as printed/transcribed.
  - **July 2024:** Hindi text was decoded from a legacy Chanakya-font mirror and cross-checked against third-party clean Hindi solution PDFs; the answer authority is stated to be the CBSE final key. Preserve the source's wording and `*` symbol as-is.
  - **February 2026:** the README records that matras lost in a legacy-font source were restored by grammar, while specified printed quirks were intentionally retained (including English `beehieve`, Hindi `बुद्धयोत्तेजक`, and the Q26 English/Hindi term difference). Do not “fix” these in the source or silently normalize them in the raw-text field.

The per-paper READMEs supply direct CBSE final-key links for January 2021, January 2024, July 2024, and February 2026. August 2023 is described as CBSE's official final key but has no direct key link in its README. These are source-provided citations/claims; this phase did not download or visually re-verify those PDFs.

## UTET `bank-v2` source profile

### Pinned source and records

| Input | Observed records |
|---|---:|
| `bank-v2/paper-forms/utet/paper-1/forms.ndjson` | 6 forms |
| `bank-v2/paper-forms/utet/paper-1/appearances.ndjson` | 900 appearances |
| Non-empty `bank-v2/exams/utet/paper-1/**/questions.ndjson` streams | 5 × 180 = 900 questions |
| `bank-v2/exams/utet/paper-1/language-1/{hindi}/stimuli.ndjson` and `language-2/{english}/stimuli.ndjson` | 24 stimuli |
| Corresponding `bank-v2/audits/utet-p1-*-question-audit.ndjson` files | 6 × 150 = 900 audit records |
| Corresponding `bank-v2/sources/utet-p1-*-sources.json` files | 6 source manifests |
| `bank-v2/schemas/` | 12 JSON Schema files |

The other six language question streams (English/Hindi alternatives not used in these forms, Sanskrit, and Urdu) are present but empty. Each form records 150 questions, 150 marks, 150 minutes, no negative marking, shift 1, and five 30-question modules. The six source forms are:

| Form date | Set | Source form ID |
|---|---|---|
| 6 Nov 2020 | A | `utet-p1-2020-set-a` |
| 24 Mar 2021 | C | `utet-p1-2021-set-c` |
| 26 Nov 2022 | B | `utet-p1-2022-set-b` |
| 29 Sep 2024 | D | `utet-p1-2024-set-d` |
| 24 Oct 2025 | A | `utet-p1-2025-set-a` |
| 29 Sep 2026 | A | `utet-p1-2026-set-a` |

Each form lists its modules and the 30 `appearanceIds` in each module. Appearance rows supply the question number and chosen language slot; use these form/appearance fields rather than deriving order from question IDs. The observed numbering is CPD Q1–30, Language I (Hindi) Q31–60, Language II (English) Q61–90, Maths Q91–120, and EVS Q121–150.

### UTET content shape and schema results

- The five populated streams contain 180 questions each: CPD, Maths, EVS, Language I Hindi, and Language II English. There are 900 distinct question IDs and 900 appearances, 150 per form and 30 per form/module.
- All 540 core questions (CPD/Maths/EVS) have Hindi and English prompt/option locales. The 180 Hindi Language I questions are Hindi-only; the 180 English Language II questions are English-only.
- All 900 are source type `single-choice`, have four ordered options (`a`–`d`), and contain one source answer. Every `appearance.officialOptionId` agrees with its question's `answer.optionId`; this agreement does **not** make the answer an official authority key.
- Prompt and option payloads use Markdown content blocks. No question has an asset list; the source contains no standalone image/audio assets. The 24 stimuli are 17 prose and 7 poems: 12 Hindi (6 prose, 6 poem) and 12 English (11 prose, 1 poem). A total of 111 question rows reference them (55 Hindi, 56 English); all 24 stimulus IDs are referenced and no stimulus links were broken in the inspection.
- All 900 source questions have source review flags `answerVerified`, `translationVerified`, and `mediaVerified` set true; the 900 audits also say the answer transformation and stem/options were checked and visual dependency is `none`. These are source-contributor review flags, not independent official-authority verification.
- All 900 questions have editorial difficulty `unrated`, empirical difficulty `null`, cognitive level `unrated`, and empty topic/concept ID lists. There are no source explanations or question assets. The current source taxonomy therefore gives no rated difficulty, Bloom level, or topic assignment to import.
- The source schemas declare JSON Schema Draft 2020-12 and use local references. All 12 schema files passed schema checks; 900 questions, 900 appearances, six forms, and 24 stimuli validated with zero errors. The source audit NDJSON and source manifests were counted/read but were not part of those four data-schema validation totals.

### UTET answer authority and content-provenance boundary

The UTET records embed single answers in each question and duplicate the selected option ID on the appearance. The source manifests carry `verificationStatus: "verified"` and question rows carry positive review flags, but the inspected manifest records have no official answer-key URL or key-document reference. The repository's root `LICENSE` identifies the material as an independently authored question bank, not affiliated with or endorsed by UBSE/CBSE, and not derived verbatim from an examination authority. The `sourceType: "pyq"` label is therefore a source claim, not proof of a verbatim official-paper transcription.

Accordingly, the imported answer values may be preserved as a **source-repository / provisional, non-authority answer version** with their raw provenance and review flags. They must not be exposed by the target's official-final-answer view or described as an official UBSE key. Until an official UTET final key and question-paper provenance are supplied, the official-authority answer view for UTET remains empty/unresolved. This keeps the source content available for review without violating the rule against promoting third-party answers to authority.

The UTET repository is licensed CC BY 4.0. Any vendored source rows or derived extracts must retain attribution to “TET Question Bank contributors” (2026), link the license, and indicate changes. The CTET folders in this repository have no root license/rights notice in the inspected tree; their contents and redistribution status must not be assigned a new license by this pipeline.

## Import implications and completed pipeline gates

1. Preserve each raw source file/NDJSON line and record its file path, line range (or NDJSON line number), extraction method, source snapshot/commit, and `imported_from`. Derived parsed text must never overwrite raw text.
2. Build CTET question boundaries from the paper's expected section range and validated four-option groups; do not count every numbered line. Store reading passages/poems as locale-specific stimuli and link by audited question ranges rather than regexing numbered passage lines.
3. Treat language-choice slots and answer-key headings as data. The importer supports separate language tables and February 2026's combined Q91–150 per-language tables, preserving raw multi-answer tokens and expanded option identities.
4. Version answer keys and distinguish authority. CTET keys are imported as the final CBSE keys described by the paper READMEs (without re-comparison to PDFs, per scope); UTET answers from this source remain provisional/non-authority pending official UBSE-key evidence.
5. The target pipeline gates passed: CTET 5 forms / 930 canonical questions / 1,050 optional-stream appearances / 1,050 key entries; UTET 6 forms / 900 questions / 900 appearances / 900 provisional answer entries. Combined database: 1,830 questions, 1,950 appearances, 64 stimuli, 411 links, 1,968 correct-option links, 109 SHA-256-inventoried sources, and 2,850 localized FTS documents. The single-file app JSON bundle (`data/xtet-question-bank.json`) is deterministic and contains 1,830 questions, 1,950 appearances, 64 stimuli, answer-key history, and a separate official-final list.
6. UTET's 12 pinned schemas and all 1,830 question/form/appearance/stimulus records validated with zero errors. SQLite `integrity_check`, `foreign_key_check`, key-authority boundary, unique/option-locale/link checks, FTS5 integrity, all 29 app SQL examples, two-clean-build content-hash equality, deterministic JSON/NDJSON export hashes, and CI workflow tests passed. See [`docs/DATA_QUALITY.md`](DATA_QUALITY.md), [`docs/PIPELINE.md`](PIPELINE.md), and [`docs/QUERIES.md`](QUERIES.md).
7. This work is structural parsing/validation only. No CTET source text, key token, whitespace, spelling, or wording was revised or compared against official scans; README quality caveats remain authoritative context. No authority claim is added for UTET.
