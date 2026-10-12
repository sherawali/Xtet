# App-ready SQL query cookbook

The examples target `data/xtet-question-bank.sqlite` and require no server or ORM. They use SQLite views/tables directly; `v_official_final_answers` is the only answer view that should be presented as an official-final authority result. UTET's source-repository/provisional answers are deliberately separate. `v_form_questions` emits a row per appearance and localized content variant; for a particular stream, filter both `form_id` and `content_locale`.

Run a query in the repository with:

```sh
sqlite3 data/xtet-question-bank.sqlite "SELECT code, name FROM exams ORDER BY code;"
```

## 1. Exam/session inventory

```sql
SELECT e.code, e.name, es.session_label, es.exam_date,
       COUNT(DISTINCT pf.form_id) AS forms
FROM exams AS e
JOIN exam_sessions AS es USING (exam_id)
LEFT JOIN paper_forms AS pf USING (session_id)
GROUP BY e.exam_id, es.session_id
ORDER BY e.code, es.exam_date;
```

## 2. Forms by date and configured totals

```sql
SELECT e.code, es.exam_date, pf.form_id, pf.set_code, pf.shift,
       pf.total_questions, pf.total_marks, pf.duration_minutes
FROM paper_forms AS pf
JOIN exam_sessions AS es USING (session_id)
JOIN exams AS e USING (exam_id)
ORDER BY es.exam_date, e.code, pf.paper_number, pf.set_code;
```

## 3. Actual blueprint modules and locales for one form

```sql
SELECT form_id, slot_code, section_code, order_index, question_count,
       question_start, question_end, locale_code
FROM v_blueprint_summary
WHERE form_id = 'ctet-2024-07-07-set-a'
ORDER BY order_index, locale_code;
```

## 4. Localized questions in a selected form section

```sql
SELECT form_id, slot_code, question_number, question_id,
       content_locale, display_stem, options_json
FROM v_form_questions
WHERE form_id = 'ctet-2023-08-20-set-a'
  AND slot_code = 'language-1'
  AND content_locale = 'en'
ORDER BY question_number
LIMIT 10;
```

## 5. Canonical question with ordered localized options

```sql
SELECT question_id, locale_code, type_code, display_stem, options_json
FROM v_question_locales
WHERE question_id = 'ctet-2024-07-07-set-a-language-1-q106'
ORDER BY locale_code;
```

## 6. Multilingual full-text search

```sql
SELECT question_id, locale_code, snippet(question_search_fts, 2, '[', ']', '…', 16) AS excerpt
FROM question_search_fts
WHERE question_search_fts MATCH 'बाल OR pedagogy'
ORDER BY rank
LIMIT 20;
```

## 7. Official-final answer rows for one CTET form

```sql
SELECT form_id, question_number, raw_answer, answer_mode
FROM v_official_final_answers
WHERE form_id = 'ctet-2024-07-07-set-a'
ORDER BY table_label, question_number;
```

## 8. Complete answer-key history with authority class

```sql
SELECT form_id, authority_class, status, version_label,
       table_label, question_number, raw_answer
FROM v_answer_key_history
WHERE form_id = 'utet-p1-2024-set-d'
ORDER BY question_number;
```

## 9. Native multi-correct answers and selected option IDs

```sql
SELECT akv.form_id, qa.question_number, ake.raw_answer,
       qo.position AS correct_option_position, aeo.position AS answer_set_order,
       qo.original_label, aeo.option_id
FROM answer_key_entries AS ake
JOIN answer_key_tables AS akt USING (answer_key_table_id)
JOIN answer_key_versions AS akv USING (answer_key_version_id)
JOIN question_appearances AS qa USING (appearance_id)
JOIN answer_key_entry_options AS aeo USING (answer_key_entry_id)
JOIN question_options AS qo USING (option_id, question_id)
WHERE ake.answer_key_entry_id IN (
  SELECT answer_key_entry_id
  FROM answer_key_entry_options
  GROUP BY answer_key_entry_id
  HAVING COUNT(*) > 1
)
ORDER BY akv.form_id, qa.question_number, aeo.position;
```

## 10. Confirm non-authority UTET answers stay provisional

```sql
SELECT akv.form_id, akv.authority_class, akv.status,
       COUNT(ake.answer_key_entry_id) AS answer_rows
FROM answer_key_versions AS akv
LEFT JOIN answer_key_tables AS akt USING (answer_key_version_id)
LEFT JOIN answer_key_entries AS ake USING (answer_key_table_id)
WHERE akv.form_id LIKE 'utet-p1-%'
GROUP BY akv.answer_key_version_id
ORDER BY akv.form_id;
```

## 11. One appearance with form, stream, section, and content locale

```sql
SELECT form_id, form_section_id, slot_code, section_code,
       appearance_id, question_id, question_number, locale_code,
       content_locale, display_stem
FROM v_form_questions
WHERE form_id = 'utet-p1-2024-set-d'
  AND slot_code = 'language-1'
  AND question_number = 35
ORDER BY content_locale;
```

## 12. Exact source file and line provenance for a question

```sql
SELECT q.question_id, sf.relative_path, sr.line_start, sr.line_end,
       sr.extraction_method, sr.imported_from, sr.raw_sha256, sr.raw_text
FROM questions AS q
JOIN source_records AS sr ON sr.source_record_id = q.primary_source_record_id
JOIN source_files AS sf USING (source_file_id)
WHERE q.question_id = 'ctet-2021-01-31-set-i-cpd-q001';
```

## 13. Audited stimulus ranges by form section and locale

```sql
SELECT sr.stimulus_id, st.stimulus_type, sr.locale_code,
       pfs.form_id, bs.slot_code, sr.question_start, sr.question_end,
       sr.linked_questions
FROM v_stimulus_question_ranges AS sr
JOIN stimuli AS st USING (stimulus_id)
JOIN paper_form_sections AS pfs USING (form_section_id)
JOIN blueprint_sections AS bs USING (blueprint_section_id)
ORDER BY pfs.form_id, bs.order_index, sr.question_start;
```

## 14. Stimulus content plus the linked question appearances

```sql
SELECT sc.stimulus_id, sc.locale_code, sc.display_text,
       pf.form_id, qa.question_number, qa.question_id
FROM stimulus_contents AS sc
JOIN stimuli USING (stimulus_id)
JOIN stimulus_question_links AS sl USING (stimulus_id)
JOIN question_appearances AS qa USING (appearance_id)
JOIN paper_form_sections AS pfs USING (form_section_id)
JOIN paper_forms AS pf USING (form_id)
WHERE sc.stimulus_id LIKE 'ctet-%'
ORDER BY sc.stimulus_id, sc.locale_code, qa.question_number;
```

## 15. Repository audit assertions for a UTET question

```sql
SELECT q.question_id, sf.relative_path, sr.line_start,
       sr.raw_text AS raw_audit_record
FROM question_source_audits AS qsa
JOIN source_records AS sr USING (source_record_id)
JOIN source_files AS sf USING (source_file_id)
JOIN questions AS q USING (question_id)
WHERE q.question_id = 'utet-p1-2024-cdp-q001';
```

## 16. Source tags without treating them as reviewed taxonomy

```sql
SELECT q.question_id, qst.raw_tag, sf.relative_path, sr.line_start
FROM question_source_tags AS qst
JOIN questions AS q USING (question_id)
JOIN source_records AS sr USING (source_record_id)
JOIN source_files AS sf USING (source_file_id)
WHERE q.question_id = 'utet-p1-2024-cdp-q001'
ORDER BY qst.raw_tag;
```

## 17. Current taxonomy catalog (intentionally empty at initial import)

```sql
SELECT ts.name AS taxonomy, tn.node_code, tn.name_en, tn.name_hi,
       tn.parent_node_id, tn.lifecycle_status
FROM taxonomy_nodes AS tn
JOIN taxonomy_schemes AS ts USING (taxonomy_scheme_id)
ORDER BY ts.name, tn.node_code;
```

## 18. Questions awaiting difficulty/Bloom assessment

```sql
SELECT question_id, type_code
FROM v_unrated_questions
ORDER BY question_id
LIMIT 50;
```

## 19. Localized content coverage by language

```sql
SELECT locale_code, COUNT(*) AS question_content_rows,
       COUNT(DISTINCT question_id) AS canonical_questions
FROM question_contents
GROUP BY locale_code
ORDER BY locale_code;
```

## 20. Localized option text for one question

```sql
SELECT qo.position, qo.original_label, oc.locale_code,
       oc.display_text, oc.structured_json
FROM question_options AS qo
JOIN option_contents AS oc USING (option_id)
WHERE qo.question_id = 'utet-p1-2024-cdp-q001'
ORDER BY qo.position, oc.locale_code;
```

## 21. Key-entry coverage by form and authority

```sql
SELECT akv.form_id, akv.authority_class, akv.status,
       COUNT(DISTINCT ake.appearance_id) AS covered_appearances,
       COUNT(DISTINCT akt.answer_key_table_id) AS source_tables
FROM answer_key_versions AS akv
LEFT JOIN answer_key_tables AS akt USING (answer_key_version_id)
LEFT JOIN answer_key_entries AS ake USING (answer_key_table_id)
GROUP BY akv.answer_key_version_id
ORDER BY akv.form_id;
```

## 22. Candidate language-choice groups and members

```sql
SELECT pf.form_id, bsg.group_code, bsg.choose_min, bsg.choose_max,
       bsm.locale_code, bs.slot_code, bs.question_count
FROM blueprint_selection_groups AS bsg
JOIN blueprint_versions AS bv USING (blueprint_id)
JOIN paper_form_blueprints AS pfb USING (blueprint_id)
JOIN paper_forms AS pf USING (form_id)
JOIN blueprint_selection_members AS bsm USING (selection_group_id)
JOIN blueprint_sections AS bs USING (blueprint_section_id)
WHERE pf.form_id = 'ctet-2023-08-20-set-a'
ORDER BY bsg.group_code, bsm.locale_code;
```

## 23. Confirmed canonical translation mirrors with multiple appearances

```sql
SELECT q.question_id, COUNT(DISTINCT qa.appearance_id) AS appearances,
       group_concat(DISTINCT pfs.locale_code) AS appearance_locales,
       group_concat(DISTINCT bs.slot_code) AS slots
FROM questions AS q
JOIN question_appearances AS qa USING (question_id)
JOIN paper_form_sections AS pfs USING (form_section_id)
JOIN blueprint_sections AS bs USING (blueprint_section_id)
WHERE q.question_id LIKE 'ctet-2024-07-07-set-a-language-%'
GROUP BY q.question_id
HAVING COUNT(DISTINCT qa.appearance_id) > 1
ORDER BY q.question_id;
```

## 24. Vendored source license/attribution inventory

```sql
SELECT license_id, attribution, upstream_repo, upstream_commit,
       COUNT(*) AS file_count, SUM(byte_size) AS bytes
FROM source_files
GROUP BY license_id, attribution, upstream_repo, upstream_commit
ORDER BY license_id, upstream_commit;
```

## 25. Bilingual core content for one canonical question

```sql
SELECT question_id, locale_code, display_stem, options_json
FROM v_question_locales
WHERE question_id = 'ctet-2024-07-07-set-a-cpd-q001'
ORDER BY locale_code;
```

## 26. Example Hindi full-text search

```sql
SELECT question_id, locale_code,
       snippet(question_search_fts, 2, '⟦', '⟧', '…', 12) AS context
FROM question_search_fts
WHERE question_search_fts MATCH 'शिक्षा OR भाषा'
ORDER BY rank
LIMIT 15;
```

## 27. Build and source snapshot metadata

```sql
SELECT schema_version, importer_version, source_manifest_hash,
       content_hash, sqlite_runtime, fts5_enabled
FROM build_metadata
WHERE singleton = 1;
```

## 28. Editorial assessment inventory (should be empty until reviewed)

```sql
SELECT difficulty_band, bloom_level, assessment_status,
       COUNT(*) AS assessments
FROM question_assessments
GROUP BY difficulty_band, bloom_level, assessment_status
ORDER BY difficulty_band, bloom_level;
```

## 29. Expanded official-final correct options

```sql
SELECT form_id, question_number, raw_answer,
       correct_option_position, correct_option_label, option_id
FROM v_official_final_answer_options
WHERE form_id = 'ctet-2024-07-07-set-a'
ORDER BY question_number, correct_option_position;
```
