# App question-data download

## The file to use

The app can download one regular JSON file:

- Repository copy: `data/xtet-question-bank.json`
- Public GitHub Raw URL: <https://raw.githubusercontent.com/sherawali/Xtet/arena/ed8a51c8-xtet/data/xtet-question-bank.json>
- File size in the current build: about 13 MB
- Format: one UTF-8 JSON object (not plain text, not one JSON record per line)

The URL serves the newest committed copy on the `arena/ed8a51c8-xtet` branch. No separate API or custom CDN is configured. When a new paper is added and the updated file is built and pushed to this branch, the same URL serves the updated question bank.

## What the JSON contains

The root object has these fields:

- `metadata`: format version, dataset content hash, source hash, exam codes, and record counts.
- `questions`: canonical question text, available languages, ordered options, and provenance.
- `appearances`: where a question occurs in a paper; each row has `exam_code` (`CTET` or `UTET`), form, section, question number, and locale.
- `stimuli`: passage/poem text and its linked appearances.
- `answer_key_history`: every imported answer version, with its authority/status fields.
- `official_final_answers`: only answer rows classified as exam-authority final. Use this list for official-final answer display/scoring. UTET source-repository answers are provisional and are intentionally not in this list.

An app can join an appearance to its question using `question_id`; it should use `exam_code` to keep CTET and UTET views separate. Questions can have multiple localized contents, so the app should select the language the learner chose.

## Refreshing after adding a paper

1. Add the paper source and any required parser/config changes.
2. Run `python -m pipeline build`. This rebuilds/verifies the SQLite database and regenerates `data/xtet-question-bank.json`.
3. Run the test suite, commit the updated JSON, then push the branch. The public Raw URL above will serve the new file.

The pipeline also writes a manifest with the JSON file's SHA-256 under `build/exports/manifest.json`; the current bundle's embedded `metadata.database_content_hash` identifies the database content version. The generated NDJSON files are optional; the app only needs the single JSON bundle if that is the chosen contract.
