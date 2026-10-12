-- Schema v1. All source/content records carry source-record provenance.
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    name TEXT NOT NULL UNIQUE,
    checksum TEXT NOT NULL CHECK (length(checksum) = 64)
) STRICT;

CREATE TABLE build_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version > 0),
    importer_version TEXT NOT NULL,
    source_manifest_hash TEXT NOT NULL CHECK (length(source_manifest_hash) = 64),
    content_hash TEXT NOT NULL CHECK (length(content_hash) = 64),
    sqlite_runtime TEXT NOT NULL,
    fts5_enabled INTEGER NOT NULL CHECK (fts5_enabled IN (0, 1))
) STRICT;

CREATE TABLE source_files (
    source_file_id TEXT PRIMARY KEY,
    relative_path TEXT NOT NULL UNIQUE,
    source_uri TEXT,
    upstream_repo TEXT,
    upstream_commit TEXT,
    media_type TEXT NOT NULL,
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    license_id TEXT,
    attribution TEXT
) STRICT;

CREATE TABLE source_records (
    source_record_id TEXT PRIMARY KEY,
    source_file_id TEXT NOT NULL REFERENCES source_files(source_file_id) ON DELETE RESTRICT,
    line_start INTEGER NOT NULL CHECK (line_start >= 1),
    line_end INTEGER NOT NULL CHECK (line_end >= line_start),
    byte_start INTEGER CHECK (byte_start IS NULL OR byte_start >= 0),
    byte_end INTEGER CHECK (byte_end IS NULL OR byte_end >= byte_start),
    extraction_method TEXT NOT NULL,
    imported_from TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    raw_sha256 TEXT NOT NULL CHECK (length(raw_sha256) = 64),
    UNIQUE (source_record_id, source_file_id),
    UNIQUE (source_file_id, line_start, line_end, extraction_method, raw_sha256)
) STRICT;

CREATE TABLE source_record_assertions (
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    assertion_key TEXT NOT NULL,
    assertion_scope TEXT NOT NULL,
    value_json TEXT NOT NULL CHECK (json_valid(value_json)),
    PRIMARY KEY (source_record_id, assertion_key, assertion_scope)
) STRICT;

CREATE TABLE exams (
    exam_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    conducting_authority TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE exam_sessions (
    session_id TEXT PRIMARY KEY,
    exam_id TEXT NOT NULL REFERENCES exams(exam_id) ON DELETE RESTRICT,
    session_label TEXT NOT NULL,
    exam_date TEXT NOT NULL CHECK (date(exam_date) IS NOT NULL),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (exam_id, session_label, exam_date)
) STRICT;

CREATE TABLE sections (
    section_id TEXT PRIMARY KEY,
    exam_id TEXT NOT NULL REFERENCES exams(exam_id) ON DELETE RESTRICT,
    paper_number INTEGER NOT NULL CHECK (paper_number > 0),
    section_code TEXT NOT NULL,
    name_en TEXT NOT NULL,
    name_hi TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (exam_id, paper_number, section_code)
) STRICT;

CREATE TABLE blueprint_versions (
    blueprint_id TEXT PRIMARY KEY,
    exam_id TEXT NOT NULL REFERENCES exams(exam_id) ON DELETE RESTRICT,
    paper_number INTEGER NOT NULL CHECK (paper_number > 0),
    version_number INTEGER NOT NULL CHECK (version_number > 0),
    label TEXT NOT NULL,
    expected_questions INTEGER NOT NULL CHECK (expected_questions > 0),
    total_marks REAL NOT NULL CHECK (total_marks >= 0),
    duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes > 0),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'retired')),
    rules_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(rules_json)),
    content_hash TEXT NOT NULL CHECK (length(content_hash) = 64),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (exam_id, paper_number, version_number, label),
    UNIQUE (blueprint_id, exam_id)
) STRICT;

CREATE TABLE blueprint_selection_groups (
    selection_group_id TEXT PRIMARY KEY,
    blueprint_id TEXT NOT NULL REFERENCES blueprint_versions(blueprint_id) ON DELETE CASCADE,
    group_code TEXT NOT NULL,
    choose_min INTEGER NOT NULL CHECK (choose_min >= 0),
    choose_max INTEGER NOT NULL CHECK (choose_max >= choose_min),
    policy_code TEXT NOT NULL,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (blueprint_id, group_code),
    UNIQUE (selection_group_id, blueprint_id)
) STRICT;

CREATE TABLE blueprint_sections (
    blueprint_section_id TEXT PRIMARY KEY,
    blueprint_id TEXT NOT NULL REFERENCES blueprint_versions(blueprint_id) ON DELETE CASCADE,
    section_id TEXT NOT NULL REFERENCES sections(section_id) ON DELETE RESTRICT,
    slot_code TEXT NOT NULL,
    order_index INTEGER NOT NULL CHECK (order_index > 0),
    question_count INTEGER NOT NULL CHECK (question_count > 0),
    question_start INTEGER CHECK (question_start IS NULL OR question_start > 0),
    question_end INTEGER CHECK (question_end IS NULL OR question_end >= question_start),
    required INTEGER NOT NULL CHECK (required IN (0, 1)),
    selection_group_id TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (blueprint_id, slot_code),
    UNIQUE (blueprint_id, order_index),
    UNIQUE (blueprint_section_id, blueprint_id),
    FOREIGN KEY (selection_group_id, blueprint_id)
      REFERENCES blueprint_selection_groups(selection_group_id, blueprint_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE blueprint_section_locales (
    blueprint_section_id TEXT NOT NULL REFERENCES blueprint_sections(blueprint_section_id) ON DELETE CASCADE,
    locale_code TEXT NOT NULL,
    content_mode TEXT NOT NULL CHECK (content_mode IN ('single', 'combined', 'alternative')),
    candidate_selectable INTEGER NOT NULL CHECK (candidate_selectable IN (0, 1)),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (blueprint_section_id, locale_code)
) STRICT;

CREATE TABLE blueprint_selection_members (
    selection_group_id TEXT NOT NULL REFERENCES blueprint_selection_groups(selection_group_id) ON DELETE CASCADE,
    blueprint_section_id TEXT NOT NULL,
    locale_code TEXT NOT NULL,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (selection_group_id, blueprint_section_id, locale_code),
    FOREIGN KEY (blueprint_section_id, locale_code)
      REFERENCES blueprint_section_locales(blueprint_section_id, locale_code) ON DELETE CASCADE
) STRICT;

CREATE TABLE blueprint_rules (
    blueprint_id TEXT NOT NULL REFERENCES blueprint_versions(blueprint_id) ON DELETE CASCADE,
    rule_code TEXT NOT NULL,
    parameters_json TEXT NOT NULL CHECK (json_valid(parameters_json)),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (blueprint_id, rule_code)
) STRICT;

CREATE TABLE paper_forms (
    form_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES exam_sessions(session_id) ON DELETE RESTRICT,
    paper_number INTEGER NOT NULL CHECK (paper_number > 0),
    set_code TEXT NOT NULL,
    booklet_code TEXT,
    shift INTEGER CHECK (shift IS NULL OR shift > 0),
    duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes > 0),
    total_questions INTEGER NOT NULL CHECK (total_questions > 0),
    total_marks REAL NOT NULL CHECK (total_marks >= 0),
    negative_marking REAL CHECK (negative_marking IS NULL OR negative_marking >= 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (form_id, session_id)
) STRICT;

CREATE UNIQUE INDEX uq_paper_forms_natural_key
ON paper_forms(session_id, paper_number, set_code, coalesce(shift, 0));

CREATE TABLE paper_form_blueprints (
    form_id TEXT NOT NULL REFERENCES paper_forms(form_id) ON DELETE CASCADE,
    blueprint_id TEXT NOT NULL REFERENCES blueprint_versions(blueprint_id) ON DELETE RESTRICT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (form_id, blueprint_id)
) STRICT;

CREATE TABLE paper_form_sections (
    form_section_id TEXT PRIMARY KEY,
    form_id TEXT NOT NULL REFERENCES paper_forms(form_id) ON DELETE CASCADE,
    blueprint_section_id TEXT NOT NULL REFERENCES blueprint_sections(blueprint_section_id) ON DELETE RESTRICT,
    locale_code TEXT NOT NULL,
    source_file_id TEXT NOT NULL REFERENCES source_files(source_file_id) ON DELETE RESTRICT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (form_id, blueprint_section_id, locale_code),
    UNIQUE (form_section_id, form_id)
) STRICT;

CREATE TABLE question_types (
    type_code TEXT PRIMARY KEY,
    answer_mode TEXT NOT NULL CHECK (answer_mode IN ('option_set', 'scalar', 'structured')),
    options_min INTEGER CHECK (options_min IS NULL OR options_min >= 0),
    options_max INTEGER CHECK (options_max IS NULL OR options_max >= options_min),
    allows_multiple INTEGER NOT NULL CHECK (allows_multiple IN (0, 1)),
    configuration_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(configuration_json)),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE questions (
    question_id TEXT PRIMARY KEY,
    type_code TEXT NOT NULL REFERENCES question_types(type_code) ON DELETE RESTRICT,
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('draft', 'review', 'published', 'retired')),
    primary_source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    canonical_fingerprint TEXT CHECK (canonical_fingerprint IS NULL OR length(canonical_fingerprint) = 64)
) STRICT;

CREATE TABLE question_contents (
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    locale_code TEXT NOT NULL,
    content_format TEXT NOT NULL,
    raw_stem TEXT NOT NULL,
    display_stem TEXT NOT NULL,
    structured_json TEXT CHECK (structured_json IS NULL OR json_valid(structured_json)),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (question_id, locale_code)
) STRICT;

CREATE TABLE question_options (
    option_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position > 0),
    original_label TEXT NOT NULL,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (question_id, position),
    UNIQUE (question_id, original_label),
    UNIQUE (option_id, question_id)
) STRICT;

CREATE TABLE option_contents (
    option_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    locale_code TEXT NOT NULL,
    content_format TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    display_text TEXT NOT NULL,
    structured_json TEXT CHECK (structured_json IS NULL OR json_valid(structured_json)),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (option_id, locale_code),
    FOREIGN KEY (option_id, question_id)
      REFERENCES question_options(option_id, question_id) ON DELETE CASCADE
) STRICT;

CREATE TABLE question_appearances (
    appearance_id TEXT PRIMARY KEY,
    form_section_id TEXT NOT NULL REFERENCES paper_form_sections(form_section_id) ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE RESTRICT,
    question_number INTEGER NOT NULL CHECK (question_number > 0),
    sequence_in_section INTEGER NOT NULL CHECK (sequence_in_section > 0),
    points REAL NOT NULL DEFAULT 1 CHECK (points >= 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (form_section_id, question_number),
    UNIQUE (form_section_id, sequence_in_section),
    UNIQUE (appearance_id, question_id)
) STRICT;

CREATE TABLE question_source_tags (
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    raw_tag TEXT NOT NULL,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (question_id, raw_tag, source_record_id)
) STRICT;

CREATE TABLE question_source_audits (
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (question_id, source_record_id)
) STRICT;

CREATE TABLE stimuli (
    stimulus_id TEXT PRIMARY KEY,
    stimulus_type TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('draft', 'review', 'published', 'retired')),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE stimulus_contents (
    stimulus_id TEXT NOT NULL REFERENCES stimuli(stimulus_id) ON DELETE CASCADE,
    locale_code TEXT NOT NULL,
    content_format TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    display_text TEXT NOT NULL,
    instructions TEXT,
    structured_json TEXT CHECK (structured_json IS NULL OR json_valid(structured_json)),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (stimulus_id, locale_code)
) STRICT;

CREATE TABLE stimulus_question_links (
    stimulus_id TEXT NOT NULL REFERENCES stimuli(stimulus_id) ON DELETE CASCADE,
    appearance_id TEXT NOT NULL REFERENCES question_appearances(appearance_id) ON DELETE CASCADE,
    relation_code TEXT NOT NULL DEFAULT 'context',
    position INTEGER NOT NULL CHECK (position > 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (stimulus_id, appearance_id),
    UNIQUE (stimulus_id, position)
) STRICT;

CREATE TABLE stimulus_review_records (
    review_id TEXT PRIMARY KEY,
    stimulus_id TEXT NOT NULL REFERENCES stimuli(stimulus_id) ON DELETE CASCADE,
    reviewed_field TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reviewer_kind TEXT NOT NULL,
    note TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE answer_key_versions (
    answer_key_version_id TEXT PRIMARY KEY,
    form_id TEXT NOT NULL REFERENCES paper_forms(form_id) ON DELETE RESTRICT,
    version_label TEXT NOT NULL,
    authority_class TEXT NOT NULL CHECK (authority_class IN ('exam_authority', 'source_repository', 'editorial')),
    status TEXT NOT NULL CHECK (status IN ('provisional', 'final', 'superseded', 'retracted')),
    published_date TEXT CHECK (published_date IS NULL OR date(published_date) IS NOT NULL),
    authority_uri TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    content_hash TEXT NOT NULL CHECK (length(content_hash) = 64),
    UNIQUE (form_id, version_label),
    UNIQUE (answer_key_version_id, form_id)
) STRICT;

CREATE UNIQUE INDEX uq_one_exam_authority_final_key_per_form
ON answer_key_versions(form_id)
WHERE authority_class = 'exam_authority' AND status = 'final';

CREATE TABLE answer_key_tables (
    answer_key_table_id TEXT PRIMARY KEY,
    answer_key_version_id TEXT NOT NULL REFERENCES answer_key_versions(answer_key_version_id) ON DELETE CASCADE,
    table_label TEXT NOT NULL,
    raw_heading TEXT NOT NULL,
    locale_code TEXT,
    slot_code TEXT,
    question_start INTEGER NOT NULL CHECK (question_start > 0),
    question_end INTEGER NOT NULL CHECK (question_end >= question_start),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (answer_key_table_id, answer_key_version_id)
) STRICT;

CREATE TABLE answer_key_entries (
    answer_key_entry_id TEXT PRIMARY KEY,
    answer_key_table_id TEXT NOT NULL REFERENCES answer_key_tables(answer_key_table_id) ON DELETE CASCADE,
    appearance_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    raw_answer TEXT NOT NULL,
    answer_mode TEXT NOT NULL CHECK (answer_mode IN ('option_set', 'scalar', 'structured')),
    scalar_answer TEXT,
    response_json TEXT CHECK (response_json IS NULL OR json_valid(response_json)),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (answer_key_table_id, appearance_id),
    UNIQUE (answer_key_entry_id, question_id),
    FOREIGN KEY (appearance_id, question_id)
      REFERENCES question_appearances(appearance_id, question_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE answer_key_entry_options (
    answer_key_entry_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    option_id TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position > 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (answer_key_entry_id, option_id),
    UNIQUE (answer_key_entry_id, position),
    FOREIGN KEY (answer_key_entry_id, question_id)
      REFERENCES answer_key_entries(answer_key_entry_id, question_id) ON DELETE CASCADE,
    FOREIGN KEY (option_id, question_id)
      REFERENCES question_options(option_id, question_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE explanations (
    explanation_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    locale_code TEXT NOT NULL,
    content_format TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    display_text TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'review', 'published', 'retired')),
    author_kind TEXT NOT NULL,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (question_id, locale_code, explanation_id)
) STRICT;

CREATE TABLE assets (
    asset_id TEXT PRIMARY KEY,
    media_type TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    license_id TEXT,
    attribution TEXT,
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('draft', 'review', 'published', 'retired')),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE asset_locales (
    asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE CASCADE,
    locale_code TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    caption TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (asset_id, locale_code)
) STRICT;

CREATE TABLE question_assets (
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    role TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position > 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (question_id, asset_id, role)
) STRICT;

CREATE TABLE option_assets (
    option_id TEXT NOT NULL REFERENCES question_options(option_id) ON DELETE CASCADE,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    role TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position > 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (option_id, asset_id, role)
) STRICT;

CREATE TABLE stimulus_assets (
    stimulus_id TEXT NOT NULL REFERENCES stimuli(stimulus_id) ON DELETE CASCADE,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    role TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position > 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (stimulus_id, asset_id, role)
) STRICT;

CREATE TABLE explanation_assets (
    explanation_id TEXT NOT NULL REFERENCES explanations(explanation_id) ON DELETE CASCADE,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    role TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position > 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (explanation_id, asset_id, role)
) STRICT;

CREATE TABLE taxonomy_schemes (
    taxonomy_scheme_id TEXT PRIMARY KEY,
    exam_id TEXT NOT NULL REFERENCES exams(exam_id) ON DELETE RESTRICT,
    paper_number INTEGER,
    name TEXT NOT NULL,
    version_label TEXT NOT NULL,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (exam_id, paper_number, name, version_label)
) STRICT;

CREATE TABLE taxonomy_nodes (
    taxonomy_node_id TEXT PRIMARY KEY,
    taxonomy_scheme_id TEXT NOT NULL REFERENCES taxonomy_schemes(taxonomy_scheme_id) ON DELETE CASCADE,
    parent_node_id TEXT,
    node_code TEXT NOT NULL,
    node_kind TEXT NOT NULL CHECK (node_kind IN ('topic', 'subtopic', 'concept', 'skill', 'standard')),
    name_en TEXT NOT NULL,
    name_hi TEXT,
    lifecycle_status TEXT NOT NULL CHECK (lifecycle_status IN ('draft', 'active', 'retired')),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (taxonomy_scheme_id, node_code),
    UNIQUE (taxonomy_node_id, taxonomy_scheme_id),
    FOREIGN KEY (parent_node_id, taxonomy_scheme_id)
      REFERENCES taxonomy_nodes(taxonomy_node_id, taxonomy_scheme_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE question_taxonomy_assignments (
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    taxonomy_node_id TEXT NOT NULL REFERENCES taxonomy_nodes(taxonomy_node_id) ON DELETE RESTRICT,
    assignment_method TEXT NOT NULL CHECK (assignment_method IN ('source', 'human', 'model', 'import_rule')),
    confidence REAL CHECK (confidence IS NULL OR confidence BETWEEN 0.0 AND 1.0),
    review_status TEXT NOT NULL CHECK (review_status IN ('unreviewed', 'accepted', 'rejected')),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    PRIMARY KEY (question_id, taxonomy_node_id, assignment_method, source_record_id)
) STRICT;

CREATE TABLE question_assessments (
    assessment_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    difficulty_band TEXT CHECK (difficulty_band IS NULL OR difficulty_band IN ('very_easy', 'easy', 'medium', 'hard', 'very_hard')),
    difficulty_value REAL CHECK (difficulty_value IS NULL OR difficulty_value BETWEEN 0.0 AND 1.0),
    difficulty_method TEXT,
    bloom_level TEXT CHECK (bloom_level IS NULL OR bloom_level IN ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')),
    confidence REAL CHECK (confidence IS NULL OR confidence BETWEEN 0.0 AND 1.0),
    assessment_status TEXT NOT NULL CHECK (assessment_status IN ('unrated', 'editorial', 'empirical', 'reviewed')),
    sample_size INTEGER CHECK (sample_size IS NULL OR sample_size >= 0),
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT,
    UNIQUE (question_id, assessment_id)
) STRICT;

CREATE TABLE question_review_records (
    review_id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    reviewed_field TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reviewer_kind TEXT NOT NULL,
    note TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE appearance_review_records (
    review_id TEXT PRIMARY KEY,
    appearance_id TEXT NOT NULL REFERENCES question_appearances(appearance_id) ON DELETE CASCADE,
    reviewed_field TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reviewer_kind TEXT NOT NULL,
    note TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE form_review_records (
    review_id TEXT PRIMARY KEY,
    form_id TEXT NOT NULL REFERENCES paper_forms(form_id) ON DELETE CASCADE,
    reviewed_field TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reviewer_kind TEXT NOT NULL,
    note TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE answer_key_review_records (
    review_id TEXT PRIMARY KEY,
    answer_key_version_id TEXT NOT NULL REFERENCES answer_key_versions(answer_key_version_id) ON DELETE CASCADE,
    reviewed_field TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reviewer_kind TEXT NOT NULL,
    note TEXT,
    source_record_id TEXT NOT NULL REFERENCES source_records(source_record_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE question_search_documents (
    search_doc_id INTEGER PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    locale_code TEXT NOT NULL,
    stem TEXT NOT NULL,
    options TEXT NOT NULL,
    explanations TEXT NOT NULL,
    stimuli TEXT NOT NULL,
    UNIQUE (question_id, locale_code)
) STRICT;

CREATE INDEX idx_exam_sessions_exam_date ON exam_sessions(exam_id, exam_date);
CREATE INDEX idx_paper_forms_session ON paper_forms(session_id, paper_number, set_code);
CREATE INDEX idx_blueprint_sections_blueprint_order ON blueprint_sections(blueprint_id, order_index);
CREATE INDEX idx_paper_form_sections_form_locale ON paper_form_sections(form_id, locale_code);
CREATE INDEX idx_question_appearances_question ON question_appearances(question_id);
CREATE INDEX idx_question_appearances_number ON question_appearances(form_section_id, question_number);
CREATE INDEX idx_question_contents_locale ON question_contents(locale_code, question_id);
CREATE INDEX idx_answer_key_versions_form_status ON answer_key_versions(form_id, status, authority_class);
CREATE INDEX idx_answer_key_entries_appearance ON answer_key_entries(appearance_id, answer_key_table_id);
CREATE INDEX idx_stimulus_links_appearance ON stimulus_question_links(appearance_id);
CREATE INDEX idx_question_taxonomy_node ON question_taxonomy_assignments(taxonomy_node_id, question_id);
CREATE INDEX idx_source_records_file_lines ON source_records(source_file_id, line_start, line_end);
CREATE INDEX idx_source_files_sha256 ON source_files(sha256);

CREATE VIEW v_question_locales AS
SELECT q.question_id, q.type_code, q.lifecycle_status, qc.locale_code,
       qc.display_stem, qc.content_format,
       (SELECT json_group_array(json_object(
           'option_id', ordered.option_id,
           'position', ordered.position,
           'label', ordered.original_label,
           'text', ordered.display_text
       ))
        FROM (
           SELECT qo.option_id, qo.position, qo.original_label, oc.display_text
           FROM question_options AS qo
           JOIN option_contents AS oc ON oc.option_id = qo.option_id
           WHERE qo.question_id = q.question_id AND oc.locale_code = qc.locale_code
           ORDER BY qo.position
        ) AS ordered) AS options_json
FROM questions AS q
JOIN question_contents AS qc USING (question_id);

CREATE VIEW v_form_questions AS
SELECT pf.form_id, pf.set_code, pf.paper_number,
       pfs.form_section_id, bs.slot_code, s.section_code, pfs.locale_code,
       qa.appearance_id, qa.question_id, qa.question_number, qa.sequence_in_section,
       qc.locale_code AS content_locale, qc.display_stem,
       (SELECT json_group_array(json_object(
           'option_id', ordered.option_id,
           'position', ordered.position,
           'label', ordered.original_label,
           'text', ordered.display_text
       ))
        FROM (
           SELECT qo.option_id, qo.position, qo.original_label, oc.display_text
           FROM question_options AS qo
           JOIN option_contents AS oc ON oc.option_id = qo.option_id
           WHERE qo.question_id = qa.question_id AND oc.locale_code = qc.locale_code
           ORDER BY qo.position
        ) AS ordered) AS options_json,
       q.type_code, qa.points
FROM paper_forms AS pf
JOIN paper_form_sections AS pfs USING (form_id)
JOIN blueprint_sections AS bs USING (blueprint_section_id)
JOIN sections AS s USING (section_id)
JOIN question_appearances AS qa USING (form_section_id)
JOIN questions AS q USING (question_id)
JOIN question_contents AS qc USING (question_id);

CREATE VIEW v_official_final_answers AS
SELECT akv.form_id, akv.answer_key_version_id, akv.authority_uri,
       akt.table_label, ake.answer_key_entry_id,
       ake.appearance_id, ake.question_id, qa.question_number,
       ake.raw_answer, ake.answer_mode, ake.scalar_answer,
       ake.source_record_id AS answer_source_record_id
FROM answer_key_versions AS akv
JOIN answer_key_tables AS akt USING (answer_key_version_id)
JOIN answer_key_entries AS ake USING (answer_key_table_id)
JOIN question_appearances AS qa USING (appearance_id)
WHERE akv.authority_class = 'exam_authority'
  AND akv.status = 'final';

CREATE VIEW v_official_final_answer_options AS
SELECT official.form_id, official.answer_key_version_id,
       official.answer_key_entry_id, official.appearance_id,
       official.question_id, official.question_number, official.raw_answer,
       aeo.position AS answer_set_order, qo.position AS correct_option_position,
       aeo.option_id, qo.original_label AS correct_option_label
FROM v_official_final_answers AS official
JOIN answer_key_entry_options AS aeo USING (answer_key_entry_id)
JOIN question_options AS qo USING (option_id, question_id)
ORDER BY official.form_id, official.question_number, qo.position;

CREATE VIEW v_answer_key_history AS
SELECT akv.form_id, akv.answer_key_version_id, akv.version_label,
       akv.authority_class, akv.status, akv.authority_uri,
       akt.answer_key_table_id, akt.table_label, akt.raw_heading,
       ake.answer_key_entry_id, ake.appearance_id, ake.question_id,
       qa.question_number, ake.raw_answer, ake.answer_mode, ake.scalar_answer,
       aeo.position AS answer_set_order, qo.position AS correct_option_position,
       aeo.option_id, qo.original_label AS correct_option_label,
       ake.source_record_id AS answer_source_record_id
FROM answer_key_versions AS akv
JOIN answer_key_tables AS akt USING (answer_key_version_id)
JOIN answer_key_entries AS ake USING (answer_key_table_id)
JOIN question_appearances AS qa USING (appearance_id)
LEFT JOIN answer_key_entry_options AS aeo USING (answer_key_entry_id)
LEFT JOIN question_options AS qo USING (option_id, question_id);

CREATE VIEW v_stimulus_question_ranges AS
SELECT sl.stimulus_id, sc.locale_code, qa.form_section_id,
       MIN(qa.question_number) AS question_start,
       MAX(qa.question_number) AS question_end,
       COUNT(*) AS linked_questions
FROM stimulus_question_links AS sl
JOIN question_appearances AS qa USING (appearance_id)
JOIN stimulus_contents AS sc USING (stimulus_id)
GROUP BY sl.stimulus_id, sc.locale_code, qa.form_section_id;

CREATE VIEW v_blueprint_summary AS
SELECT pf.form_id, exam.code AS exam_code, pf.paper_number, pf.set_code,
       bs.slot_code, s.section_code, bs.order_index, bs.question_count,
       bs.question_start, bs.question_end, pfs.locale_code
FROM paper_forms AS pf
JOIN exam_sessions AS es USING (session_id)
JOIN exams AS exam USING (exam_id)
JOIN paper_form_sections AS pfs USING (form_id)
JOIN blueprint_sections AS bs USING (blueprint_section_id)
JOIN sections AS s USING (section_id);

CREATE VIEW v_unrated_questions AS
SELECT q.question_id, q.type_code
FROM questions AS q
LEFT JOIN question_assessments AS qa USING (question_id)
WHERE qa.assessment_id IS NULL OR qa.assessment_status = 'unrated';

CREATE VIEW v_question_provenance AS
SELECT q.question_id, sf.relative_path, sr.line_start, sr.line_end,
       sr.extraction_method, sr.imported_from, sr.raw_sha256
FROM questions AS q
JOIN source_records AS sr ON sr.source_record_id = q.primary_source_record_id
JOIN source_files AS sf USING (source_file_id);

CREATE VIRTUAL TABLE question_search_fts USING fts5(
  question_id UNINDEXED,
  locale_code UNINDEXED,
  stem,
  options,
  explanations,
  stimuli,
  content='question_search_documents',
  content_rowid='search_doc_id',
  tokenize='unicode61 remove_diacritics 0'
);

CREATE TRIGGER question_search_documents_ai AFTER INSERT ON question_search_documents BEGIN
  INSERT INTO question_search_fts(rowid, question_id, locale_code, stem, options, explanations, stimuli)
  VALUES (new.search_doc_id, new.question_id, new.locale_code, new.stem, new.options, new.explanations, new.stimuli);
END;
CREATE TRIGGER question_search_documents_ad AFTER DELETE ON question_search_documents BEGIN
  INSERT INTO question_search_fts(question_search_fts, rowid, question_id, locale_code, stem, options, explanations, stimuli)
  VALUES ('delete', old.search_doc_id, old.question_id, old.locale_code, old.stem, old.options, old.explanations, old.stimuli);
END;
CREATE TRIGGER question_search_documents_au AFTER UPDATE ON question_search_documents BEGIN
  INSERT INTO question_search_fts(question_search_fts, rowid, question_id, locale_code, stem, options, explanations, stimuli)
  VALUES ('delete', old.search_doc_id, old.question_id, old.locale_code, old.stem, old.options, old.explanations, old.stimuli);
  INSERT INTO question_search_fts(rowid, question_id, locale_code, stem, options, explanations, stimuli)
  VALUES (new.search_doc_id, new.question_id, new.locale_code, new.stem, new.options, new.explanations, new.stimuli);
END;
