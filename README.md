# Xtet

TET exam ke question bank - year wise, paper wise, section wise.

## Structure

2021/
  CTET_Paper1_Jan2021_SetI/    (CTET 2020 cycle, Paper 1, 31 January 2021, Set I)
    CPD.txt        - Questions 1-30 (Child Development & Pedagogy, Hindi + English)
    Maths.txt      - Questions 31-60 (Mathematics, Hindi + English)
    EVS.txt        - Questions 61-90 (Environmental Studies, Hindi + English)
    Eng-1.txt      - Questions 91-120 (Language I - English)
    Hindi-1.txt    - Questions 91-120 (Language I - Hindi)
    Eng-2.txt      - Questions 121-150 (Language II - English)
    Hindi-2.txt    - Questions 121-150 (Language II - Hindi)
    Answer-Key.txt - CBSE Official Final Answer Key (Q1-150)

2023/
  CTET_Paper1_Aug2023_SetA/    (CTET Paper 1, 20 August 2023, Set A)
    CPD.txt        - Questions 1-30 (Child Development & Pedagogy)
    Maths.txt      - Questions 31-60 (Mathematics)
    EVS.txt        - Questions 61-90 (Environmental Studies)
    Hindi-1.txt    - Questions 91-120 (Language I - Hindi)
    Eng-1.txt      - Questions 91-120 (Language I - English)
    Eng-2.txt      - Questions 121-150 (Language II - English)
    Hindi-2.txt    - Questions 121-150 (Language II - Hindi)
    Answer-Key.txt - CBSE Final Answer Key (Q1-150)

2024/
  CTET_Paper1_Jan2024_SetI/     (CTET Paper 1, 21 January 2024, Set I)
    CPD.txt        - Questions 1-30 (Hindi + English)
    Maths.txt      - Questions 31-60 (Hindi + English)
    EVS.txt        - Questions 61-90 (Hindi + English)
    Hindi-1.txt    - Questions 91-120 (Language I - Hindi)
    Eng-1.txt      - Questions 91-120 (Language I - English)
    Eng-2.txt      - Questions 121-150 (Language II - English)
    Hindi-2.txt    - Questions 121-150 (Language II - Hindi)
    Answer-Key.txt - CBSE Official Final Answer Key (Q1-150)

  CTET_Paper1_Jul2024_SetA/     (CTET Paper 1, 07 July 2024, Set A)
    CPD.txt        - Questions 1-30 (Hindi + English)
    Maths.txt      - Questions 31-60 (Hindi + English)
    EVS.txt        - Questions 61-90 (Hindi + English)
    Hindi-1.txt    - Questions 91-120 (Language I - Hindi)
    Eng-1.txt      - Questions 91-120 (Language I - English)
    Eng-2.txt      - Questions 121-150 (Language II - English)
    Hindi-2.txt    - Questions 121-150 (Language II - Hindi)
    Answer-Key.txt - CBSE Official Final Answer Key (Q1-150)

2026/
  CTET_Paper1_Feb2026_SetE/     (CTET Paper 1, 08 February 2026, Set E - December 2025 session)
    CPD.txt        - Questions 1-30 (Hindi + English)
    Maths.txt      - Questions 31-60 (Hindi + English)
    EVS.txt        - Questions 61-90 (Hindi + English)
    Hindi-1.txt    - Questions 91-120 (Language I - Hindi)
    Eng-1.txt      - Questions 91-120 (Language I - English)
    Eng-2.txt      - Questions 121-150 (Language II - English)
    Hindi-2.txt    - Questions 121-150 (Language II - Hindi)
    Answer-Key.txt - CBSE Official Final Answer Key (Q1-150)

Har paper folder me README.md me paper set aur sections ka note hota hai.
Set A aur Set I ki language availability unke alag-alag README files mein di gayi hai.
CTET December 2025 session ka Paper 1 February 2026 mein hua (08 Feb 2026, Set E yahan hai).

## SQLite question-bank database

Verified question-bank data is available as SQLite (`data/xtet-question-bank.sqlite`), as one app-downloadable JSON file (`data/xtet-question-bank.json`), and as a small sync manifest (`data/xtet-question-bank.manifest.json`, about 4 KB) that carries the content hash and paper list so an app can skip re-downloading an unchanged bundle. The JSON combines the five CTET Paper 1 text sets and six pinned UTET Paper 1 forms; each appearance identifies its exam, so CTET and UTET remain separate. It includes a `papers` list (title, exam/date/set identity, section ranges, answer counters), localized questions, options, stimuli, provenance, answer-key history, and a separate official-final answer list. Each appearance also carries `stimulus_ids` and a derived `answer` mirror (official-final or provisional, with 1-based correct-option positions) for direct app use. UTET repository answers remain provisional and are not included in the official-final list. UTET source/license attribution is preserved under `data/utet/`.

- App data file and download notes: [`docs/APP_DOWNLOAD.md`](docs/APP_DOWNLOAD.md).
- Build/verify/export: see [`docs/PIPELINE.md`](docs/PIPELINE.md).
- Schema decisions: [`docs/SCHEMA.md`](docs/SCHEMA.md); observed source profile: [`docs/DATA_PROFILE.md`](docs/DATA_PROFILE.md).
- Quality gates and verified counts: [`docs/DATA_QUALITY.md`](docs/DATA_QUALITY.md).
- 29 example app-ready SQL queries: [`docs/QUERIES.md`](docs/QUERIES.md).
- Rebuild commands (Python 3.11+, pinned requirements): `python -m pipeline build`, then `python -m pipeline verify`. The build refreshes the SQLite and app JSON files; deterministic NDJSON exports are also written under `build/exports/`.

No app code is included in this repository; its data file and download instructions are ready for the app AI to use.

## AGENT_MEMORY (AI agents ke liye)

Jo bhi AI agent is repo par kaam kare, SABSE PEHLE AGENT_MEMORY/00_START_HERE.md padhe - usme start/end protocol hai.
Current state + session log: AGENT_MEMORY/MEMORY.md
Kaise karna hai (tools, sources, verification): AGENT_MEMORY/PLAYBOOK.md, SOURCES.md, MISTAKES.md
Naye session ka ready prompt: AGENT_MEMORY/HANDOVER_PROMPT.md
Session ke end me AGENT_MEMORY zaroor update karein.
