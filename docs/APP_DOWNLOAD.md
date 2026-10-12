# App question-data download

## The files to use

The app can download two regular JSON files:

| File | Repository copy | Public GitHub Raw URL | Size |
| --- | --- | --- | --- |
| Question bank bundle | `data/xtet-question-bank.json` | <https://raw.githubusercontent.com/sherawali/Xtet/main/data/xtet-question-bank.json> | about 13.4 MB |
| Sync manifest (small) | `data/xtet-question-bank.manifest.json` | <https://raw.githubusercontent.com/sherawali/Xtet/main/data/xtet-question-bank.manifest.json> | about 4 KB |

Both are single UTF-8 JSON objects (not plain text, not one JSON record per line). The URLs serve the newest committed copy on `main`. No separate API or custom CDN is configured. When a new paper is added, the updated files must be built, tested, and merged into `main`; the same URLs then serve the updated data.

## What the JSON contains

The root object has these fields:

- `metadata`: format version, dataset content hash, source hash, importer version, exam codes, and record counts.
- `papers`: one entry per available paper/form (currently 11: 5 CTET + 6 UTET) with the display title, exam/date/set identity, declared duration and totals, section list, and per-paper appearance/answer counts. An app can render its paper picker from this array alone.
- `questions`: canonical question text, available languages, ordered options, and provenance.
- `appearances`: where a question occurs in a paper; each row has `exam_code` (`CTET` or `UTET`), form, section, question number, locale, the `stimulus_ids` that own its context text, and a denormalized `answer` convenience mirror.
- `stimuli`: passage/poem text and its linked appearances.
- `answer_key_history`: every imported answer version, with its authority/status fields.
- `official_final_answers`: only answer rows classified as exam-authority final. Use this list for official-final answer display/scoring. UTET source-repository answers are provisional and are intentionally not in this list.

An app can join an appearance to its question using `question_id`; it should use `exam_code` to keep CTET and UTET views separate. Questions can have multiple localized contents, so the app should select the language the learner chose.

Format changes are additive: `format_version` stays `1` while new fields are added, so readers must ignore unknown fields and feature-detect with a key check (`if "papers" in bundle`). `format_version` is bumped only when an existing field is removed, renamed, or retyped.

## The `papers` array

```json
{
  "form_id": "ctet-2026-02-08-set-e",
  "exam_code": "CTET",
  "exam_name": "Central Teacher Eligibility Test",
  "session_id": "ctet-session-2026-2026-02-08",
  "session_label": "2026",
  "exam_date": "2026-02-08",
  "year": 2026,
  "paper_number": 1,
  "set_code": "E",
  "booklet_code": null,
  "shift": null,
  "title": "CTET Feb 2026 Paper I (Set E)",
  "duration_minutes": 150,
  "total_questions": 150,
  "total_marks": 150.0,
  "negative_marking": 0.0,
  "appearance_count": 210,
  "official_answer_count": 210,
  "provisional_answer_count": 0,
  "question_number_min": 1,
  "question_number_max": 150,
  "locales": ["en", "hi", "mul"],
  "sections": [
    {
      "form_section_id": "fs-ctet-2026-02-08-set-e-cpd-mul",
      "section_code": "cpd",
      "name_en": "Child Development and Pedagogy",
      "name_hi": "बाल विकास व शिक्षा शास्त्र",
      "slot_code": "cpd",
      "order_index": 1,
      "locale_code": "mul",
      "question_start": 1,
      "question_end": 30,
      "declared_question_count": 30,
      "appearance_count": 30,
      "official_answer_count": 30,
      "provisional_answer_count": 0,
      "question_number_min": 1,
      "question_number_max": 30
    }
  ]
}
```

Notes:

- `title` is generated deterministically from exam code, exam date, `paper_number`, and `set_code`; apps may prefer to render their own label from the structured fields.
- `appearance_count` counts appearances, so bilingual Language I/II streams of one CTET form appear as 210 rows for a 150-question paper. `question_number_min`/`max` stay 1–150.
- `official_answer_count == 0` means the paper has no exam-authority key in this dataset (all UTET forms today: the source-repository answers are provisional).
- Unavailable source facts stay `null`; the pipeline never invents them.

## Stimulus without reverse lookups

Every appearance carries `stimulus_ids` (an array; empty when the question has no passage/poem):

```json
{"appearance_id": "app-fs-ctet-2021-01-31-set-i-language-1-en-q091",
 "stimulus_ids": ["stim-d71b573a8ea9124d3c420f8b84eec859"]}
```

Look up `stimuli[]` by `stimulus_id` and pick `contents[<locale>]`. The `stimuli[].question_appearances` list still exists for the reverse direction; in the current build each linked appearance has exactly one stimulus, and 411 of 1,950 appearances have one.

## Answers

`appearances[].answer` mirrors the key for that appearance so the app does not need an in-memory join (`null` when no key exists):

```json
{
  "answer_key_entry_id": "ake-69fc65dca1af77e09d7dfdc8106b",
  "answer_key_version_id": "akv-ctet-2021-01-31-set-i-cbse-final",
  "authority_class": "exam_authority",
  "status": "final",
  "is_official": true,
  "raw_answer": "1",
  "correct_option_positions": [1],
  "correct_option_labels": ["1"]
}
```

Rules for using it:

- `correct_option_positions` are 1-based positions inside `questions[].options` for that question — the same order the app renders. Use these to score and to highlight; ignore `correct_option_labels` for logic, use it only for display.
- `is_official` is `true` only for `authority_class == "exam_authority"` **and** `status == "final"` (CTET today). UTET mirrors are `source_repository` / `provisional` and must be labelled as provisional in the UI.
- Do not assume a single correct option and do not assume `A/B/C/D`: CTET keys print options `1–4` and UTET prints `a–d`, and the retained source keys contain multi-answer tokens (`Z`, `F`, `E`, `B`, `A`, `D`) whose rows carry 2 or 4 correct options. Always read the arrays.
- `answer_key_history` and `official_final_answers` remain the authority; the mirror is a derived convenience copy. If they ever disagree, the lists win.
- Historical/superseded key versions are not mirrored; the mirror always carries the best available row for that appearance (official final preferred, else provisional).

## Refresh/sync recipe (small manifest first)

1. `GET` `data/xtet-question-bank.manifest.json` (about 4 KB, or use `HEAD` plus the ETag). It contains `database_content_hash`, `source_manifest_hash`, `record_counts`, the paper list, and the bundle's exact `byte_size` and `sha256`.
2. Compare `database_content_hash` (or `bundle.sha256`) with the value stored after the last successful sync. If unchanged, stop — the 13.4 MB bundle is not downloaded at all. The manifest's paper list is enough to refresh the paper picker UI.
3. If it changed, `GET` `data/xtet-question-bank.json`, verify `sha256` and `byte_size` against the manifest, then persist `database_content_hash` alongside the cached bundle.
4. Send `If-None-Match` with the stored ETag on repeat requests where possible; a `304 Not Modified` also avoids the body transfer.
5. Parse the bundle off the UI thread (13 MB is roughly 1–2 s of JSON parsing on a mid-range phone). `build/exports/` also contains NDJSON variants for streaming importers, but the single JSON bundle is the supported app contract.

## Refreshing after adding a paper

1. Add the paper source and any required parser/config changes.
2. Run `python -m pipeline build`. This rebuilds/verifies the SQLite database and regenerates `data/xtet-question-bank.json`, `data/xtet-question-bank.manifest.json`, and the NDJSON/export manifest under `build/exports/`.
3. Run the test suite, commit the updated JSON and manifest, then push the branch. The public Raw URLs above will serve the new files.
