# SQLite question-bank schema design

**Status:** Phase 2 design is complete and materialized by `migrations/001_initial.sql`; parser, loader, verification, and query integration tests exercise this contract. Scope is a reusable, offline SQLite database and its import/verification tooling—no application, API, sync service, hosting, or frontend.

## 1. Design goals and invariants

The database separates four concepts that must not be collapsed:

1. **Question identity** — a stable canonical item, which can have one or more localized content records.
2. **Paper appearance** — a particular occurrence of that item in a form, module, question number, and language stream.
3. **Answer-key publication** — an answer set tied to a specific version, source, authority class, and status.
4. **Source evidence** — the immutable file/line span from which an imported fact was parsed.

Core invariants:

- Do not modify source files. Keep raw source bytes in the pinned/vendor input tree and store each imported raw record/span, its SHA-256, path and line range in SQLite. Parsed/normalized display text is a separate field; it never replaces the raw value.
- Every imported content or assessment fact has a non-null, foreign-keyed provenance record. For canonical items assembled from more than one source occurrence, every appearance and locale/option source span is retained; one source is not silently discarded during a merge.
- A question can have multiple localized stems and option texts. Language choice belongs to a form module/appearance, not to the canonical question itself.
- An answer is not a column on `questions`. It is an entry in a versioned answer-key table linked to a specific appearance. Multi-correct answers are represented as a set of option foreign keys and also retain the exact raw key token.
- Only an answer-key version explicitly marked `authority_class='exam_authority'` and `status='final'` is returned by the official-answer view. The UTET source-repository answers remain provisional/non-authority until an official UBSE key is evidenced.
- Taxonomy, difficulty, Bloom level, explanations, and assets are modeled now but have no inferred assignments or fabricated content. CTET mirror and stimulus mappings are recorded per form, not generalized into parser constants.
- Imports and IDs are deterministic. Re-running the same pinned input/configuration is idempotent; a source-content or migration change changes the content-derived database version.

## 2. Entity map

```text
exams ──< exam_sessions ──< paper_forms >── paper_form_blueprints >── blueprint_versions
                                                       │                        │
                                                       │                        ├──< blueprint_sections
                                                       │                        ├──< blueprint_selection_groups/rules
                                                       │                        └──< blueprint_section_locales
                                                       └──< paper_form_sections >── question_appearances >── questions
                                                                                                      │            ├──< question_contents
                                                                                                      │            ├──< question_options ──< option_contents
                                                                                                      │            ├──< question_source_tags
                                                                                                      │            ├──< question_taxonomy_assignments
                                                                                                      │            ├──< question_assessments
                                                                                                      │            └──< explanations
                                                                                                      │
answer_key_versions ──< answer_key_tables ──< answer_key_entries ──< answer_key_entry_options
stimuli ──< stimulus_contents; stimulus_question_links >── question_appearances
assets ──< typed asset-link tables (question/option/stimulus/explanation)
source_files ──< source_records ──< every imported record/provenance link
```

`<` means one-to-many. The loader and verification stage check cross-row invariants that SQLite cannot express as a row-local `CHECK` (for example, the option count required by a question type and whether every required locale has option text).

## 3. Core tables

### Exam, sessions, forms, and data-driven blueprints

| Table | Main fields / constraints | Purpose |
|---|---|---|
| `exams` | `exam_id` PK, unique `code`, name, conducting authority, provenance | CTET/UTET are seed data, not code branches. |
| `exam_sessions` | `session_id` PK, `exam_id` FK, session/cycle label, exam date, provenance | Separates an exam cycle/date from an individual booklet set. |
| `paper_forms` | `form_id` PK, `session_id` FK, paper number, set/booklet code, nullable shift, duration, question/mark totals, negative-marking value, form provenance | One real CTET/UTET form. Nullable source details stay null; they are not guessed. |
| `sections` | `section_id` PK, `exam_id` FK, paper number, source section code, display name, provenance | Exam-scoped subject/module catalog. |
| `blueprint_versions` | `blueprint_id` PK, exam/paper FK, integer version, expected counts/marks/duration, status, source provenance, content hash | Versioned definition of a test, independent of a specific set. A uniqueness key includes the label so form-scoped variants can use version 1 without colliding. |
| `blueprint_sections` | `blueprint_section_id` PK, `blueprint_id` and `section_id` FKs, slot/module code, order, expected count/range/marks, required flag, optional selection-group FK | The paper's ordered, data-driven module plan. A section can use a range or explicit count when the source does not provide contiguous numbers. |
| `blueprint_section_locales` | composite PK `(blueprint_section_id, locale_code)`, `content_mode`, `candidate_selectable` | Declares localized variants available in that blueprint. CTET L1/L2 have alternative `en` and `hi`; a bilingual common section has one `mul` form-module variant with `en` and `hi` content. |
| `blueprint_selection_groups` | `selection_group_id` PK, blueprint FK, `choose_min`, `choose_max`, policy code | Describes alternatives such as selecting one Language I variant. |
| `blueprint_selection_members` | composite PK `(selection_group_id, blueprint_section_id, locale_code)` | Connects each selectable locale/module to its group. |
| `blueprint_rules` | blueprint FK, stable `rule_code`, validated JSON parameters, provenance | Extensible rules such as “select exactly one language per slot” and “Language I and Language II choices must differ.” Rules are data; importer code does not hard-code one paper's languages. |
| `paper_form_blueprints` | composite PK `(form_id, blueprint_id)`, provenance | Pins each form to the blueprint version used to describe it. |
| `paper_form_sections` | `form_section_id` PK, form FK, blueprint-section FK, `locale_code` (`en`, `hi`, or `mul`), source-file FK, unique `(form_id, blueprint_section_id, locale_code)`, provenance | A realized module/stream for one form. CTET alternative English/Hindi streams are separate rows; bilingual core is one `mul` row. UTET has the locale slots actually present in its form records. |

Blueprint counts and language choices are not inferred from a universal CTET/UTET template. Form modules are generated from the inspected paper README/form metadata and stored explicitly. The verification report checks module totals, question ranges, uniqueness, candidate-choice rules, marks, and consistency with each form.

### Question identity, locale content, and appearances

| Table | Main fields / constraints | Purpose |
|---|---|---|
| `question_types` | `type_code` PK, answer mode, option policy, optional validated configuration JSON, provenance | Extensible type registry (e.g. single choice, multiple select, true/false, numeric, constructed response, matching). New types are data/schema additions, not a new hard-coded column in `questions`. |
| `questions` | stable `question_id` PK, `type_code` FK, lifecycle status, primary source-record FK, optional canonical fingerprint | Canonical question item. It has no exam-specific answer or locale field. |
| `question_contents` | composite PK `(question_id, locale_code)`, raw stem, display/search stem, content format, optional structured-block JSON, source-record FK | Localized stem/instructions. Raw text and any normalized display representation are separate. |
| `question_options` | `option_id` PK, question FK, option position, original option label, unique `(question_id, position)` and `(question_id, original_label)` | Ordered option identities independent of translated option text. |
| `option_contents` | composite PK `(option_id, locale_code)`, raw option text, display text, format/structured payload, source-record FK | Localized option content. |
| `question_appearances` | `appearance_id` PK, form-section FK, question FK, source question number, sequence, points, source-record FK, unique `(form_section_id, question_number)` | Every occurrence in every form/stream. The same canonical item may have two English/Hindi appearances when the source contains a confirmed translated mirror. |
| `question_source_tags` | question FK, exact raw source tag, source-record FK | Retains source tags as labels without pretending they are reviewed taxonomy. |
| `question_source_audits` | question FK, source-record FK, unique question/source pair | Links UTET's original audit NDJSON rows to canonical questions; audit fields remain source claims in `source_record_assertions`. |

Canonical IDs are stable and generated from source identity/configuration, not row order or current timestamps. Exact/confirmed duplicates may share a canonical `question_id`; approximate or merely similar wording is never automatically merged. CTET mirror decisions are stored in the import manifest with their evidence. Cross-paper reuse requires an explicit identity decision; it is not inferred solely from a matching stem hash.

### Stimuli, explanations, and assets

| Table | Main fields / constraints | Purpose |
|---|---|---|
| `stimuli` | `stimulus_id` PK, extensible `stimulus_type`, status, provenance | Passage, poem, table, image, audio, case study, or other reusable stimulus. |
| `stimulus_contents` | composite PK `(stimulus_id, locale_code)`, raw/display text, format, structured blocks/instructions, provenance | Localized stimulus content. |
| `stimulus_question_links` | composite PK `(stimulus_id, appearance_id)`, relation/order, source-record FK | Links each stimulus to every question appearance that uses it. A range view exposes audited first/last question numbers; individual links are retained to support non-contiguous future cases and UTET's explicit `stimulusId` references. |
| `explanations` | `explanation_id` PK, question FK, locale, raw/display body, status, author/source type, provenance | Optional, versionable explanation content. No explanation is inferred from the answer key. |
| `assets` | `asset_id` PK, media type, relative path/URI, SHA-256, byte size, MIME type, license/attribution, status, provenance | Checksummed image/audio/other external assets; binary data is not embedded as application logic. |
| `asset_locales` | composite PK `(asset_id, locale_code)`, alt text/caption, provenance | Localized accessible descriptions. |
| Typed asset links | `question_assets`, `option_assets`, `stimulus_assets`, `explanation_assets`; each has direct FKs, role/order and provenance | Avoids a weak polymorphic `owner_type/owner_id` reference and keeps FK integrity. |

CTET passage text is split into `stimuli` using its audited inline line/question ranges. UTET stimulus IDs and locale-specific Markdown blocks are imported as source records. Tables, sub-statements, underscores, Unicode, option order, and whitespace are not discarded when generating a search/display field.

### Versioned answer keys and native multi-correct answers

| Table | Main fields / constraints | Purpose |
|---|---|---|
| `answer_key_versions` | `answer_key_version_id` PK, form FK, version label, authority class, status, publication/effective date, cited authority URI/text, source provenance, content hash | Stores provisional, final, revised, and superseded keys as immutable versions. `authority_class` distinguishes `exam_authority`, `source_repository`, and `editorial`. |
| `answer_key_tables` | `answer_key_table_id` PK, version FK, raw heading, locale/module, declared question range, source-record FK | Preserves the actual table/group layout, including the February 2026 Q91–150 per-language layout. |
| `answer_key_entries` | `answer_key_entry_id` PK, table FK, appearance/question FKs, raw source token, answer mode, optional scalar/structured response, source-record FK, unique `(answer_key_table_id, appearance_id)` | One key answer for one appearance in one key version. The exact token (`1`–`4`, `A`–`F`, `Z`, or future value) is never thrown away. |
| `answer_key_entry_options` | composite FK to answer entry/question and option/question; unique option per entry; explicit answer-set order | One-to-many option set for single or multi-correct choice keys. The option FK retains the printed option position; the link's `position` is only the order within the correct set. Composite FKs prevent selecting an option belonging to a different question. |

A partial unique index permits at most one current final key with `authority_class='exam_authority'` per form. Superseded versions remain queryable. The official view filters only on that class and final status; it never substitutes the newest provisional key. A verifier rejects a `final` authority version with missing/invalid option links, duplicate answers, uncovered required appearances, or key-question mismatches.

**Source policy for this load:** CTET answer-key files are labeled as CBSE official-final-key transcriptions by their paper READMEs; that attribution and the available official links are stored as provenance. The UTET repository embeds answers but does not supply an official UBSE key citation and disclaims examination-authority affiliation. Those answers are preserved only as `source_repository` + `provisional` and are excluded from official-answer results until authority evidence is imported.

### Provenance and review assertions

| Table | Main fields / constraints | Purpose |
|---|---|---|
| `source_files` | `source_file_id` PK, repository/path, pinned commit or local source ID, media type, byte size, SHA-256, license/attribution, source URI | Immutable file inventory. Input bytes remain in the repository/vendor tree; hashes detect drift. |
| `source_records` | `source_record_id` PK, source-file FK, 1-based inclusive start/end lines, optional byte offsets, extraction method, `imported_from`, raw exact text/JSON line, record SHA-256 | Exact raw record/span used by the importer. For NDJSON, one record is one original line; for CTET, it may be a whole question/options block, key entry, or stimulus span. |
| Provenance FKs | Every factual row above carries a non-null `source_record_id` (or a typed link to one); each FK points to a valid `source_records` row | Provides file/line/extraction/import provenance without an unchecked polymorphic pointer. When one fact has multiple sources, additional typed provenance links are retained. |
| `source_record_assertions` | source-record FK, assertion code/value, assertion scope, source provenance | Preserves upstream `verified`, `answerVerified`, `translationVerified`, `mediaVerified`, and audit claims as claims from that source—not as official status. |
| Typed review tables | Subject-specific `question_review_records`, `stimulus_review_records`, `appearance_review_records`, `form_review_records`, and `answer_key_review_records`, each with direct subject/provenance FKs, reviewer/source, field, outcome, and note | Adds future human review without an unchecked polymorphic target pointer or overwriting source facts. Current source review claims stay distinguishable from our own reviews. |

Source lines use one-based inclusive numbering. `raw_text` is captured without trimming or Unicode normalization; line-ending and full-file integrity are also checked against `source_files.sha256`. The `imported_from` value identifies the exact source path/record or pinned upstream ID, while `extraction_method` names the parser rule/config version.

### Taxonomy and difficulty/Bloom metadata

| Table | Main fields / constraints | Purpose |
|---|---|---|
| `taxonomy_schemes` | scheme ID, exam/paper scope, name/version, provenance | Supports multiple exam syllabi/taxonomies. |
| `taxonomy_nodes` | node ID, scheme FK, parent FK, stable code, kind, localized names, active status, provenance; unique `(scheme_id, code)` | Hierarchical topic/subtopic/concept catalog. Parent cycles and incompatible scopes are verifier errors. |
| `question_taxonomy_assignments` | question/node FKs, method (`human`, `source`, `model`), confidence, review status, provenance, unique assignment key | Tags each item with who/what supplied the classification and its evidence. Seeded empty; no source tag is treated as a reviewed topic. |
| `question_assessments` | assessment ID, question FK, nullable difficulty value/band, nullable Bloom level, method/sample/confidence/status, provenance | Supports editorial or empirical ratings and future updates. No unrated source question receives an invented level. |

The UTET source's `unrated` values are preserved as source assertions. The target rating and taxonomy tables start empty unless a source provides a genuine classification or a reviewer adds one with provenance.

## 4. SQLite integrity, indexes, FTS5, and app-ready views

### Constraints and indexes

- Use `STRICT` tables, primary keys, `NOT NULL`, domain `CHECK` constraints, composite foreign keys, and unique indexes wherever SQLite can express the rule.
- Enable `PRAGMA foreign_keys=ON` on every connection. Required post-load checks are `PRAGMA foreign_key_check` and `PRAGMA integrity_check`.
- Enforce unique question positions/labels per question, unique form-section question numbers, unique answer per key version/appearance, unique option membership per answer, and unique blueprint module order/locale assignments.
- Add a partial unique index for one official-final key version per form; ordinary provisional/source versions remain allowed.
- Add indexes for form/session lookup, `(form_section_id, question_number)`, question/locale content, key version/form/status, stimulus links, taxonomy node assignments, and provenance source path/hash.
- Cross-row checks run in the verifier: expected option counts per type, complete localized options, allowed locales, section/blueprint totals, one answer per required appearance for a complete key version, multi-answer option bounds, stimuli ranges, and no orphan source rows.

### FTS5

Build a normal `question_search_documents` table with one row per `(question_id, locale_code)` and flattened prompt, ordered options, linked stimulus text, and any approved explanation. Maintain `question_search_fts` as an FTS5 external-content index with insert/update/delete triggers. Locale and stable IDs are unindexed columns for result filtering/joins; Unicode/Devanagari tokenization is tested against the supported SQLite build. Rebuild and integrity-check the FTS index in the verification stage. Raw source text is not rewritten to suit the tokenizer.

### Views

The initial app-ready views are:

- `v_question_locales`: one localized canonical question with `options_json` containing ordered option IDs, labels, and localized display text.
- `v_form_questions`: form, blueprint slot, appearance number, stream and content locale, localized question stem, and ordered localized `options_json`. Bilingual content is emitted once per available content locale; clients should select the desired `content_locale`.
- `v_stimulus_question_ranges`: stimulus, locale, and audited min/max question range plus linked appearances.
- `v_official_final_answers`: one row per answer entry from only authority-class `exam_authority`, status `final`; source-repository/provisional UTET values cannot leak into it. It exposes the entry ID for joins to native option links.
- `v_official_final_answer_options`: official-final answers expanded to one row per correct option, ordered by its explicit option position.
- `v_answer_key_history`: version/table/entry history expanded to one row per correct option (raw token, option ID/label, authority, status, and answer-source record).
- `v_blueprint_summary`: module order, counts, language availability/choice rules, form totals.
- `v_question_provenance` and `v_unrated_questions`: audit and content-coverage views.

These are read-only SQLite interfaces for a future client. They do not imply an API or require a server.

## 5. Migrations, deterministic loading, and content versioning

- Store forward-only migration metadata in `schema_migrations` (`version`, stable name, SQL checksum). Apply each migration in a transaction; refuse changed checksums for an already-applied version.
- Create each clean build in a temporary SQLite file. Run migrations, import each stage in a transaction, run all verification checks and `PRAGMA optimize`, close the file, then atomically replace the deliverable. A failed stage leaves the prior database untouched.
- Idempotence is achieved by deterministic rebuild-from-source: stable keys/unique constraints reject duplicates, and a fresh database is reconciled from the complete current stage instead of mutating an older build in place. Removed source rows therefore disappear only in a newly validated replacement build.
- `build_metadata` stores schema version, importer version, source-manifest hash, normalized-content hash, SQLite runtime, and FTS5 capability. The content hash is SHA-256 over sorted relative-path/source-file hashes, migration checksums, importer version, and canonical sorted relational content (including generated search documents). Timestamps and machine-specific absolute paths are excluded.
- Reproducibility acceptance is content-hash and normalized-row equality under two clean rebuilds, not reliance on SQLite page-layout bytes being identical across SQLite runtimes. The verifier requires FTS5 and JSON1 and records the SQLite runtime/version.
- The UTET input snapshot is pinned to its upstream commit and vendored with its attribution/license; CTET input paths are read in place. Both inputs are hashed before parsing. Generated database/output files are not used as inputs to their own content hash.

## 6. Source-to-schema mapping

### CTET

- Create exam/session/form and blueprint/module rows from each paper folder's README, section file headers, and answer-key group headings. Preserve absent shifts/booklet details as null.
- Parse each section using its expected range and four-option structure, with source line spans. A bilingual core question yields one appearance and `en` + `hi` content; August 2023 core yields one Hindi content locale only.
- English/Hindi language streams are distinct `paper_form_sections`. Confirmed mirrored questions share a canonical question ID and localized text while keeping both source appearances/provenance. Independent comprehension questions stay separate.
- Convert inline passages/poems into locale-specific `stimuli` and link their explicit question appearances. Keep structured tables and inline math in the raw question content unless an audited parser can preserve their structure without loss.
- Parse key headings/ranges into `answer_key_tables`; store each original value and line span. Expand A–F/Z only using the applicable key legend, and retain the source token and selected option IDs.

### UTET

- Import each pinned `forms.ndjson` form and its module/appearance IDs; validate the 30-item module counts and source `questionNumber` ranges.
- Map question locales, Markdown prompt/option blocks, ordered options, stimulus IDs, raw `answer`, source tags, difficulty/cognitive-level fields, and all upstream review flags. Keep the answer in a source-repository/provisional answer-key version, not the official view.
- Import `stimuli.ndjson` as first-class locale content. Keep audit/source-manifest rows as source provenance/assertions; do not re-label the repository's independent question bank as an official paper transcription.

## 7. Explicit choices and boundaries

1. **No answer on the canonical question row.** This permits provisional, final, and revised answers to coexist without overwriting content or misrepresenting authority.
2. **Provisional UTET answers remain queryable but not authoritative.** This follows the source license/disclaimer and the absence of an official UBSE key citation in the inspected files.
3. **Canonicalization is conservative.** Confirmed translation mirrors can share identity; near-duplicates and matching-key-only pairs cannot. The input-derived mirror manifest stores per-paper evidence.
4. **Raw and normalized content coexist.** Search/display cleanup, Markdown-to-text flattening, or line parsing never changes raw source values.
5. **Blueprints are data.** Question ranges, locales, alternative language choices, form order, marks, and selection rules are stored in rows; code validates them but does not assume CTET numbering or one permanent section layout.
6. **No inferred taxonomy or ratings.** Empty taxonomy/assessment tables are a supported and reportable state; future labels must carry their own provenance.
7. **Licensing is source-scoped.** UTET rows require CC BY 4.0 attribution and change indication. The CTET input tree has no inspected license statement, so the database does not grant one.

Implementation is materialized in the SQL migration, deterministic staging/load/verify/export pipeline, and CI. Integration tests cover nullable source metadata, bilingual content, confirmed translated appearances, separate and combined language-key layouts, multi-correct expansion, provisional non-authority UTET answers, all 29 app-query examples, and clean-rebuild content-hash equality.
