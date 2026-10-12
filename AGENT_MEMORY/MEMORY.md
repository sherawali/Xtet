# MEMORY.md - Living Memory (har session me padho + update karo)

Last updated: 2026-10-12 (Session 8 - single-file app JSON download bundle)

---

## Current State (ab kya hai)

Repo: Xtet (active Arena branch: `arena/ed8a51c8-xtet`)
Current deliverable: deterministic SQLite question-bank database, a single downloadable app JSON bundle, and parse/validate/load/verify/report/export pipeline for the five existing CTET Paper 1 texts plus pinned UTET `bank-v2` Paper 1.

- Phase 1 `docs/DATA_PROFILE.md` and Phase 2 `docs/SCHEMA.md` were completed in order before implementation.
- Pipeline implementation is complete: migrations, separate CTET/UTET parsers, JSON Schema source validation, atomic/idempotent database build, SQLite integrity/FK/unique/FTS verification, deterministic single-file JSON and NDJSON exports, data-quality report, 29 app-ready SQL examples, tests, and GitHub Actions CI.
- Verified artifact: `data/xtet-question-bank.sqlite` (26 MB), content hash `f92ebbb63338c1bc06570899dbb3376437c39a911bae4819107a49f72fe105cd`; source manifest hash `5ca08551abdba96646e9341eba59fb3c22d25c746951d45bdad87953ad4c4e7f`.
- App file: `data/xtet-question-bank.json` (12,730,793 bytes; SHA-256 `14c7204255f8341cd73ef96b5dcaf418ce8fb13f1f5c831dac8ccbc46f727d5b`), one valid JSON object with 1,830 questions, 1,950 appearances, 64 stimuli, full answer history and separate official-final answers. `python -m pipeline build` regenerates it. Intended public GitHub Raw URL: `https://raw.githubusercontent.com/sherawali/Xtet/arena/ed8a51c8-xtet/data/xtet-question-bank.json`; no custom API/CDN exists.
- `docs/APP_DOWNLOAD.md` explains the file, fields, URL, and how a rebuilt paper bank refreshes the same download.
- Verified counts: CTET 5 forms / 930 canonical questions / 1,050 appearances / 1,050 answer entries; UTET 6 forms / 900 questions / 900 appearances / 900 source-provisional answers; combined 64 stimuli / 411 links / 2,850 FTS documents. CTET official-final views contain 1,050 entries; UTET provisional rows remain excluded. One SQLite file houses both, but `exams`/sessions/forms/sections/keys are separate; CTET and UTET IDs have distinct prefixes, and a direct DB query found zero exam-prefix mismatches or question IDs reused across exams.
- Validation: 12 UTET schemas + 1,830 source records pass; all 9 integration tests pass, including CTET key spot checks, 29 SQL examples, FTS/FK/integrity, two-build determinism, and deterministic single-file JSON/NDJSON exports. Full `pipeline build`, separate `verify`, and `export` commands pass. No CTET text or upstream UTET source files were edited.
- Authority caveat: CTET keys use the final-key claims in the paper READMEs; the parser did not compare transcriptions to PDFs. August 2023 has no direct official-key URI in its README. UTET answers are independently authored source-repository values, provisional/non-authority. See `docs/DATA_QUALITY.md`.
- Delivery commits: SQLite/pipeline `9641312`, memory `aa79d19`, and app JSON `7162b95`; all pushed to `arena/ed8a51c8-xtet`. GitHub Contents API confirms the JSON download URL and file size (12,730,793 bytes). No PR was requested. Final source review showed no changes in CTET paper folders; database query found zero CTET/UTET prefix mismatches and zero question IDs reused across exams.
- User-facing handover should be Hinglish and phase-wise. The app itself is in a separate project; this repo now supplies a single JSON download file and a public Raw link, but no custom API/CDN.

### Next steps

1. No unfinished build/validation/publish steps remain. App JSON link verified by GitHub Contents API: `https://raw.githubusercontent.com/sherawali/Xtet/arena/ed8a51c8-xtet/data/xtet-question-bank.json`.
2. No PR/merge was requested. The app AI should fetch that URL; after new paper imports, run `python -m pipeline build`, test, commit, and push the updated JSON to this branch so the same link serves it.
3. For future schema/source changes: add a forward migration, retain the upstream commit/license, re-run the complete tests plus two-clean-build content-hash gate, rebuild the SQLite and app JSON artifacts/report, and update this memory.

---

## Prior CTET paper transcription history (Sessions 1-6)

Historical paper descriptions below were completed on earlier branches; they are preserved for context and do not describe the active branch/status.

### Session 6 COMPLETE: CTET 2020 cycle - January 2021 Paper 1 Set I

Folder: `2021/CTET_Paper1_Jan2021_SetI/` - all seven section files, `Answer-Key.txt`, and README are complete.

- Official booklet code `AAT-20-I`; CTET 2020 cycle exam held on 31 January 2021. User selected this paper after explicitly asking not to overlap with the other session's Dec-2025/Feb-2026 paper work.
- Transcribed CPD Q1-30, Maths Q31-60, EVS Q61-90 bilingually; English and Hindi Language I/II are separate streams for Q91-150. Added each language part's IMPORTANT eligibility notice and kept the booklet's English-before-Hindi order in the 2021 index.
- Official source booklet and CBSE Official Final Answer Key URLs are in the folder README and SOURCES.md. Hindi text layer is legacy-font encoded; clean Hindi wording received Studyfry cross-check only, with the source limitation documented. Studyfry is not answer authority.
- `Answer-Key.txt` uses Set I MAIN for Q1-90, `01-ENGLISH` for English Q91-150, and `02-HINDI` for Hindi Q91-150. All seven answer vectors matched the official key. Studyfry discrepancies at EVS Q90, English Language II Q145 and Hindi Language I Q106 are recorded in README and MISTAKES.md.
- Verification passed: 30 questions and four options per language per section; 210 answers across seven key sections; UTF-8/Devanagari, plain-text and blank-marker scans; `git diff --check`. Final content/source review completed. Paper commit: `52a0951`; memory follow-ups: `95d382f` and `dfbdabf`; branch pushed. PR #7 is being prepared for merge after syncing the latest `origin/main` and preserving the separate Feb-2026/Dec-2025 paper work.

### Session 5 COMPLETE: CTET Feb 2026 Paper 1 Set E (December 2025 session)

Folder: 2026/CTET_Paper1_Feb2026_SetE/ - POORA COMPLETE (CPD, Maths, EVS, Eng-1, Hindi-1, Eng-2, Hindi-2, Answer-Key, README).

- Paper: CTET December 2025 session (21st edition) - exam 08-02-2026, Paper 1, Set E; booklet code `FSC-26-I`; 150 Q / 150 min; negative marking nahi. (User "2025 ka paper" keh rahe the - 2025 me koi CTET session nahi hua, Dec-2025 session ka exam Feb 2026 me hua; wahi target tha.)
- "Do paper" ka matlab is cycle me Paper 1 + Paper 2 dono hain; abhi sirf Paper 1 kiya. Paper 2 baad me add kar sakte hain.
- Question text source: prepp CDN ka 48-page text-layer booklet (`ctet-2026-paper-1-question-paper-pdf-feb-08-2026-1775556035.pdf`, r.jina.ai, 15 chunks). Chunk map: c0-c3 = cover + CDP Q1-30 + Maths start; c3-c5 = Maths Q31-60; c5-c8 = EVS Q61-90; c8 = Part IV English notice + Q91-96 (Tarawati/Roopa); c9 = Q96-105 (Kalahandi extract) + Part IV Hindi header/passage start; c10 = Hindi Q91-99 + verse Q100-105 + Hindi pedagogy Q106-117; c11 = Hindi Q117-120 + Part V English Q121-135; c12 = English Q136-150 + Part V Hindi notice/passage + Q121-135; c13 = Hindi Q136-150 + back cover. (c14 = instructions page.)
- Official final answer key (84 pages) se Set E ke 3 tables: page 36 = `Set :- E PAPER-I- MAIN` (Q1-90), page 40 = `Set :- E PAPER-I- 01-English` (Q91-150), page 44 = `Set :- E PAPER-I- 02-Hindi` (Q91-150). Page pattern: B/C/D/E ke MAIN = 33/34/35/36, 01-English = 37/38/39/40, 02-Hindi = 41/42/43/44. Multi answers: MAIN Q26 = F; 01-English Q125 = F (son/relative).
- **Built-in cross-check (naya trick)**: Q106-120 aur Q136-150 (bhasha shikshashastra) dono language tables me IDENTICAL hote hain - English aur Hindi keys exactly match hui (do independent tables se poora verify). Agar mismatch aaye to transcription me galti hai.
- Hindi sections legacy Chanakya text se decode kiye (jaise July/Jan me). Kuch matras encoding me lost hoti hain ("बनना" vs "बनने") - grammar + third-party clean text se validate kiya (askfilo ka Hindi-2 passage = exact match; testbook "कीरम काँटे"; poem ka canonical text search se "सीमित पग डग" confirm).
- Verification: 30 Q per file, numbering, blanks sab 8-underscore `________` standard, 210 key entries (script se generate ki - typo-proof), markdown/stray-symbol scan clean, Devanagari/Latin script scan clean, Hindi QA pass hua. Answer-Key.txt me note: official Feb-2026 key me har language ka ek hi table Q91-150 (Part IV+V) cover karta hai.
- Commits: `4f7d6a5` (paper + READMEs + Answer-Key + root index) aur `624b940` (ye AGENT_MEMORY update).

### Session 4 COMPLETE: CTET July 2024 Paper 1 Set A

Folder: 2024/CTET_Paper1_Jul2024_SetA/ - POORA COMPLETE (CPD, Maths, EVS, Eng-1, Hindi-1, Eng-2, Hindi-2, Answer-Key, README).

- Paper: CTET July 2024 (19th CTET), Paper 1, Set A; exam 07-07-2024; booklet code JSS-24-I; Paper-I shift 2:00-4:30 PM.
- Question text ka BEST source: prepp CDN ka poora 48-page text-layer booklet (`JSS_24_I_Paper_I_Eng_Hin_AAAA_df9531e82c9d92ed0b91bc08c0d69085.pdf`, r.jina.ai prefix zaroori, 14 chunks). English saaf; Hindi legacy Chanakya encoding - par PADHNE LAYAK hai (word-by-word decode ho jata hai), isi se Hindi sections transcribe kiye.
- Official final answer key `2024080797.pdf` se Set A ki dono language tables: page 5 = `Set :- A PAPER-I 01-ENGLISH`, page 9 = `Set :- A PAPER-I 02-HINDI`. (Set B/C/D ki tables bhi usi PDF mein; P2 key = 2024080769.pdf.)
- Hindi wording cross-check: adda247 clean Hindi PDFs (12155708/12155709) - par unka question numbering SHIFTED aur option order badla hua hai; option/question order HAMESHA booklet se liya (MISTAKES #10 dekho).
- Verification pass hua: 30 Q per file, numbering, blanks `________`, 210 key entries, Devanagari/UTF-8 scan, Hindi grammar pass, README status table + source caveat.
- Session commit (paper + README): `6c1a22e` (_Add CTET July 2024 Paper 1 Set A_); uske baad ek chhota polish commit - Hindi spelling ko booklet ke hisaab se align kiya (सम्प्रेषणात्मक, मूल्याँकन) + AGENT_MEMORY update.

### Completed

2023/CTET_Paper1_Aug2023_SetA/ - CTET Paper 1, 20 August 2023, Set A - POORA COMPLETE:

| File | Content | Status |
| --- | --- | --- |
| CPD.txt | Q1-30 Child Development & Pedagogy | done |
| Maths.txt | Q31-60 Mathematics | done |
| EVS.txt | Q61-90 Environmental Studies | done |
| Hindi-1.txt | Q91-120 Language I Hindi (gadyansh Q106-114, kavyansh Q115-120) | done |
| Eng-1.txt | Q91-120 Language I English (Geeta Garud passage Q106-114, "Gather ye rosebuds" poem Q115-120) | done |
| Eng-2.txt | Q121-150 Language II English (2 passages) | done |
| Hindi-2.txt | Q121-150 Language II Hindi (2 gadyansh: kshama/dharam Q121-127, Sangai festival Q128-135) | done |
| Answer-Key.txt | CBSE Final Answer Key Q1-150 (7 sections, section-wise) | done |
| README.md | Paper set + section table + Sanskrit note | done |

Root README.md me year-wise index hai + AGENT_MEMORY ka pointer.

Git commits is paper ke:
- b953562 - pehle 5 sections (CPD, Maths, EVS, Hindi-1, Eng-2) + READMEs
- 807f014 - Eng-1 + Hindi-2 add kiye
- 0977f4c - Answer-Key.txt add kiya

2024/CTET_Paper1_Jan2024_SetI/ - CTET Paper 1, 21 January 2024, Set I - POORA PAPER ADD KIYA:

| File | Content | Status |
| --- | --- | --- |
| CPD.txt | Q1-30, Hindi + English | done |
| Maths.txt | Q31-60, Hindi + English | done |
| EVS.txt | Q61-90, Hindi + English | done |
| Eng-1.txt | Q91-120, Language I English | done |
| Hindi-1.txt | Q91-120, Language I Hindi | done |
| Eng-2.txt | Q121-150, Language II English | done |
| Hindi-2.txt | Q121-150, Language II Hindi | done |
| Answer-Key.txt | CBSE Official Final Key, 7 sections / 210 entries | done |
| README.md | Paper notes, section table, sources, set-specific language notes | done |

Root README.md year-wise index 2024 ke Set I folder ke saath update hua. AGENT_MEMORY ke PDF/Hindi workflow, sources aur mistakes bhi update hue.

2026/CTET_Paper1_Feb2026_SetE/ - CTET Paper 1, 08 February 2026, Set E (December 2025 session ki 21st edition) - POORA COMPLETE:

| File | Content | Status |
| --- | --- | --- |
| CPD.txt | Q1-30 Child Development & Pedagogy, Hindi + English | done |
| Maths.txt | Q31-60 Mathematics, Hindi + English | done |
| EVS.txt | Q61-90 Environmental Studies, Hindi + English | done |
| Eng-1.txt | Q91-120 Language I English (Tarawati/Roopa passage Q91-99, Kalahandi extract Q100-105) | done |
| Hindi-1.txt | Q91-120 Language I Hindi (Chanakya-type ahankar gadyansh Q91-99, Sumitra Nandan Pant-style "धन्यवाद" kavita Q100-105) | done |
| Eng-2.txt | Q121-150 Language II English (2 passages: boy-with-gash Q121-128, patriarch/tribes Q129-135) | done |
| Hindi-2.txt | Q121-150 Language II Hindi (2 gadyansh: satta/raja Q121-128, Hindi vs sthaaniya bhasha Q129-135) | done |
| Answer-Key.txt | CBSE Official Final Key Q1-150 (CPD/Maths/EVS + Language English + Language Hindi = 210 entries) | done |
| README.md | Paper set + section table + sources + official-key notation | done |

Root README.md me 2026/ ka year-wise index entry add hua.

Note: Hindi-1 Q100-105 kavita = Shivmangal Singh 'Suman' ki "धन्यवाद/आभार" (poem search se confirm). Hindi-1 passage = Chanakya-parampara ka ahankar/pratishtha gadyansh.

### Important facts (bhoolna mat)

- Sanskrit-1/2 is Set A booklet me NAHI hain - CBSE ki instruction #6 ke anusar Sanskrit/Urdu etc. alag "Supplement (Language) Test Booklet" me aati hain. User ko ye baat bata di gayi hai. Agar Sanskrit chahiye to supplement booklet alag se dhoondhni padegi (koi online source abhi nahi mila).
- Set A booklet me 4 language sections hote hain: Eng-1 (Q91-120), Hindi-1 (Q91-120), Eng-2 (Q121-150), Hindi-2 (Q121-150) - candidate ko har part me ek-ek language attempt karni hoti hai.
- Aug 2023 Set A me Q91-105 Hindi-1/Eng-1 aur Q136-150 Hindi-2/Eng-2 translations hain (same answers); ye Set A-specific hai, dusre papers ke liye assume na karein.
- ALL paragraphs/poems + questions cross-verified (Session 1 end): Eng-1 passage+poem = booklet exact ✓; Hindi-1 गद्यांश+काव्यांश+Q106-120 = theexampillar exact ✓ (typo खुदी/बुद्धि/बोधि booklet jaisa rakha, file me खुदी "खुदी नींव" sahi hai); Hindi-2 गद्यांश-1 = testbook exact ✓; Hindi-2 गद्यांश-2 (reconstruction) = answer-key aligned 100% ✓; Eng-2 passages = theexampillar clean source ✓. Saare answers CBSE key se match ✓.
- January 2024 work is the December 2023 CTET cycle's official January exam, Paper 1, booklet code I (`SAS-24-I`). Main sections Q1-90 are bilingual; language sections are single-language files. The source booklet is English-Hindi; other language supplements are separate.
- English and Hindi language sections are not assumed to be translations: Set I has different passages and independently keyed answer tables for Q91-105 and Q121-135.
- January 2024 `Answer-Key.txt` follows the official CBSE final key. Notation: `E` = options 2 and 4; `Z` = all options. Math Q32's printed working is `1030`; Q54 is 1/12 kg packets from 7 1/2 kg salt (15/2 kg in the worked calculation; CBSE key option 4). Oswaal/Testbook were text cross-checks only, never key authority.
- Validation run: 30 numbered questions and options (1)-(4) in each of seven section files, 210 answer-key entries, plain-text scan and `git diff --check` passed.
- Hindi QA (Session 3): CPD, Maths, EVS, Hindi-1 and Hindi-2 Hindi blocks were manually proofread for Unicode/Devanagari script, spelling, grammar, punctuation, agreement and terminology. Clear language issues were corrected; numbering, option order, and official key were left unchanged. Hindi-1 Q94's deliberately misspelled spelling-test distractors were preserved. UTF-8/script and structural scans passed. Source PDFs' Hindi text layers remain legacy-font garbled, so exact booklet wording is still not independently verified; do not claim source-level word-for-word verification.

### Historical CTET paper backlog (not active unless user requests that paper)

- CTET 2020 cycle (31 January 2021), Paper 1 Set I is complete in `2021/CTET_Paper1_Jan2021_SetI/`; content, source notes and verification are complete on `arena/0a9a02c8-xtet`; commits `52a0951` (paper) and `95d382f` (memory update) are pushed. Keep it separate from the other session's Dec-2025 cycle (Feb-2026 exam) work. The source's Hindi text layer is legacy-font encoded, so exact Hindi wording remains subject to the caveat in that paper's README.
- CTET January 2024 Paper 1 Set I and its manual Hindi language QA are complete; content/README commit `2394b47`. Exact Hindi source wording remains unverified until a clean scan/transcript is available. For the next paper, follow the user's choice and use PLAYBOOK.md plus PDF_AND_HINDI_GUIDE.md. Keep CDP/Maths/EVS bilingual and each language section single-language.
- **Feb 2026 Paper 2** (same Dec-2025 cycle) kabhi bhi add kar sakte hain: official page https://ctet.nic.in/question-paper-feb-2026/ (P2 07Feb sets W/X/Y/Z, 08Feb sets G/H/I/J) + official final key (same 84-page PDF me P2 tables aage hain; P2 08Feb key alag PDF bhi hai - SOURCES.md dekho). Paper 2 me bhi CDP/Maths(Science+Maths)/EVS-ish structure same nahi hota - booklet structure pehle padhna.
- Feb 2026 Paper 1 ke baaki sets (07Feb: S/T/U/V; 08Feb: B/C/D) aur 01-March-2026 session (P1 sets K-N) bhi isi PDF-source series me mil sakte hain (ctet.nic.in question-paper page par).
- Set A ko bilingual convert karna ho to English text booklet PDF me hai (r.jina.ai chunks 0-4); only do it if user asks.
- User ko Sanskrit chahiye to supplement booklet sources dhoondho (mubeensir.blogspot.com par Urdu/Marathi supplements mile the Dec 2022/Aug 2023 ke liye - Sanskrit wala koi link nahi mila tha).
- Baaki years/papers, Paper 2, Sets B/C/D isi PLAYBOOK se add kar sakte hain - sources SOURCES.md me hain. Sets B/C/D ki answer key CBSE final key PDF me hai (pages 1-12).
- **Speed target**: next paper 30-60 min me (recipe ready hai) - PDF_AND_HINDI_GUIDE.md section 5.
- Har naye paper ke baad ye MEMORY.md update karna hai.

---

## Session Log (naya session add karte jao)

### Session 1 - 2026-10-11 - CTET Paper 1 Aug 2023 Set A complete

- User ne kaha "ctet ke paper hai kya?" - repo me papers dhoondhe, phir CTET Paper 1 Aug 2023 Set A nikalne ka kaam mila.
- Pehle theexampillar.com se 5 sections nikale (CPD, Maths, EVS, Hindi-1, Eng-2) - commit b953562.
- User ne poocha "hindi 1 eng 1 hindi 2 eng 2 sanskrit hai kya?" + shiksha ka full booklet PDF link diya.
- shiksha PDF ki Hindi garbled thi + fetch_page ki 30-page limit thi - r.jina.ai trick se poori 49-page parse ki. Eng-1 (chunk 8-9) aur Hindi-2 (chunk 12-13) nikale. Hindi-2 ke gadyansh ka clean text testbook.com se mila ("सुख कहाँ होता है" search). Commit 807f014.
- User ne answer key maangi - user ki di hui shiksha link (CBSE Final Key PDF) se Q1-150 ki key verify + add ki. Ek correction mila: EVS Q86-88 ki purani web-key galat thi. Commit 0977f4c.
- User ne AGENT_MEMORY folder banane ko kaha - ye sab files usi ka natija hai.
- User ne kaha AGENT_MEMORY me aur add karo: PDF/Hindi ka fastest tareeka + advanced tools + future papers DUAL-language (CDP/Maths/EVS bilingual) + sab kuch cross-check karo (esp. paragraphs/poems). Result: PDF_AND_HINDI_GUIDE.md bana, saare paragraphs/poems clean sources se verified (sab MATCH), dual-language rule record hua. (Ye update.)
- PDF chunk map (dobara fetch na karein): shiksha booklet 15 chunks - c0-4: CDP/Maths/EVS (bilingual), c8-9: Eng-1 (c9 me passage+poem+Q106-120), c11-12: Eng-2, c12-13: Hindi-2. CBSE key PDF 22 chunks - c0: Q1-90 all sets, c1: English Q91-150, c2: Hindi Q91-150.
- User confirmation: dual-language rule AGLI PAPER se ("agle se") - Set A ko bilingual convert nahi karna. Sab kuch repo par merge: PR #1 MERGED into main (merge commit 5c0c172, 2026-10-11).

### Session 2 - 2026-10-12 - CTET January 2024 Paper 1 Set I

- Memory/playbook review ke baad user ne official January 2024 exam, Paper 1, Set I (`SAS-24-I`) select kiya. Prepp/Careers360 Set I booklet mirrors + official CBSE final answer key sources record kiye.
- `2024/CTET_Paper1_Jan2024_SetI/` me CPD, Maths, EVS (Hindi+English), Eng-1, Hindi-1, Eng-2, Hindi-2, Answer-Key, README add kiye. Root README and source/Hindi guidance update ki.
- English-Hindi language sections ko translations assume nahi kiya; Set I passages/key tables alag rakhe. Shift details conflicting hone se README me omit kiye.
- Q32 ke stacked `1030` working aur Maths Q54 ke printed 1/12 kg, 7 1/2 kg values third-party text sources se cross-check kiye (worked calculation 15/2 × 12 = 90); answer key phir bhi official CBSE se li.
- Validation: har section me 30 questions/four options; answer key me 210 entries; `git diff --check` pass. Hindi PDF extraction legacy-font encoded thi, isliye exact Hindi typography/wording par residual manual-review caveat record ki.
- Paper/document commit: `8d540b9` (`Add CTET January 2024 Paper 1 Set I`).

### Session 3 - 2026-10-12 - Hindi QA for CTET January 2024 Set I

- User asked for a full Hindi script/rendering, spelling and grammar review across the five Hindi-containing files. Manually reviewed all Hindi blocks in CPD, Maths, EVS, Hindi-1 and Hindi-2; corrected clear spelling, agreement and awkward phrasing while preserving question/option order and answer-key choices.
- Preserved Hindi-1 Q94's intentionally incorrect spelling distractors. Added README note explaining what the review covers and the source limitation.
- UTF-8/Devanagari scan, question numbering, four-option counts, 210 answer-key entries and `git diff --check` all passed. The official key was not edited.
- Prepp/Careers360 PDFs still have garbled legacy-font Hindi text layers; no clean Set I Hindi transcript was found. This was a language-level proofread, not exact source-level verification. Updated PLAYBOOK, PDF/Hindi guide and MISTAKES with the separate QA workflow.
- Content/README commit: `2394b47` (`Proofread Hindi in CTET January 2024 Set I`).

---

### Session 4 - 2026-10-12 - CTET July 2024 Paper 1 Set A (COMPLETE)

- User ne kaha "Memory's folder dekho aage bado" - memory padhi, next paper = CTET July 2024 Paper 1 Set A chuna (Jan 2024 Set I ke baad ka agla session, user ke "same year ka doosra paper" instruction ke mutabik).
- Source hunt: Shiksha/Prepp ke scan mirrors image-only nikle. adda247 ka text-layer mirror (sites/22/2026/01/15152514, 48 pages, "Haridwar Paper I Eng+Hin AAAA.pmd") mila - English saaf, Hindi legacy Chanakya. Baad me prepp CDN ka BEHTAR text-layer booklet mila (`JSS_24_I_Paper_I_Eng_Hin_AAAA_...pdf`, 14 chunks) - isi se saara content liya.
- CPD/Maths/EVS (Q1-90) dual-language likhe. Maths Q37 extraction boundary par chhoot gaya tha - booklace chunk 1 se recover kiya ("One crore is : ...").
- Language sections: Eng-1, Eng-2 alag files mein; Hindi-1, Hindi-2 booklet ke legacy Hindi text se decode karke likhe (Chanakya mapping consistent hai - padhna possible hai). Third-party (adda247/booklace) sirf cross-check ke liye.
- **Pakda gaya error:** Hindi-1 Q97 ke options 3/4 adda247 ke order par likhe the - booklet ka order ulta hai. Booklet se fix kiya ("शुद्ध विचार, अच्छे कर्म" official key Q97 = 3 ke saath match). Baaki sab Hindi questions ka option order booklet se verified + har official digit ka semantic check kiya (sab pass).
- Answer-Key.txt official key PDF (`2024080797.pdf`, 29/07/2024) se: Set A MAIN Q1-90 (page 1-4), `Set :- A 01-ENGLISH` (page 5), `Set :- A 02-HINDI` (page 9). Semantic verification se confirm hua ki 01-ENGLISH = English sections ki stream, 02-HINDI = Hindi sections ki stream (Q121-135 dono streams mein alag; Q106-120 aur Q136-150 dono stream mein identical).
- Verification: 30 Q per file, numbering sahi, blanks `________`, 210 key entries, chhote blanks (6/9/10 underscore) ko 8-underscore standard kiya (CPD/EVS/Hindi), markdown/`*` scan clean (Q59 ka `*` original notation hai), Devanagari scan OK.
- Session learning: (1) prepp CDN booklet = is paper ka best source; (2) legacy Hindi text padhne layak hai - blindly garbled maankar third-party order mat lo; (3) official key ke pages set-wise + language-wise (01-ENGLISH/02-HINDI) hote hain - semantic check se stream assignment confirm karo.
- Hindi spelling polish: booklet ki spelling ke hisaab se `सम्प्रेषणात्मक` (na ki "संप्रेषणात्मक") aur `मूल्याँकन` align kiye (Hindi-1 + Hindi-2), phir AGENT_MEMORY (MEMORY/SOURCES/MISTAKES/PLAYBOOK) update.
- Commits: `6c1a22e` (paper + root README), `a5ac702` (Hindi spelling polish + AGENT_MEMORY). Branch `arena/3d996047-xtet` push kiya, PR #4 MERGED into main (merge commit `560907c`, 2026-10-12). Working tree clean.
- Agli baar ke liye leads (agar language text dobara chahiye ho): prepp ka HTML quiz page "CTET 2024 Paper 1 Question Paper (07-Jul-2024)" (210 Q list + per-question pages - option order ka cross-check try kiya ja sakta hai, par confirm karna baaki hai); SET-D ka pyqonline text PDF; prepp CDN ke language supplement PDFs (Set A Sanskrit etc.).

### Session 5 - 2026-10-12 - CTET Feb 2026 Paper 1 Set E (COMPLETE)

- User ne kaha: "Memory etc pado 2025 ka paper par kaam shuru karo... agar is saal do paper hue ho dono ek ek karke add karo; pickle task se related commits bhi dekhna; jo seekho wo memory me add karna, TAB merge karna."
- 2025 me koi CTET session nahi hua (July + Dec dono skip) - isliye target hua CTET Dec-2025 session ka Paper 1, jo exam 08-02-2026 ko hua (21st edition, Set E, booklet `FSC-26-I`). User ne option me confirm kiya. "Do paper" = isi cycle ke P1 + P2; abhi sirf P1 kiya, P2 baaki.
- Sources: ctet.nic.in ka Feb-2026 question-paper page (Drive links HTTP 500 fail) → prepp CDN ka 48-page text-layer booklet mirror (r.jina.ai, 15 chunks, chunk map SOURCES.md #9) + CBSE official final key PDF (84 pages, 30 chunks; Set E tables pages 36/40/44). Third-party (testbook/askfilo/prepp) sirf wording/semantics cross-check ke liye.
- Transcription: CPD/Maths/EVS (Q1-90) bilingual; Eng-1/Hindi-1/Eng-2/Hindi-2 single-language. Hindi legacy Chanakya text decode kiya - jahan matras encoding me lost thi (e.g. "बनना/बनने") wahan grammar + third-party clean text se validate kiya (askfilo ka Hindi-2 passage EXACT match; testbook "कीरम काँटे"; poem ka canonical text "सीमित पग डग"). Printed quirks preserve (Q61 "beehieve", Q13 "बुद्धयोत्तेजक", Q26 English "assimilation" vs Hindi "समायोजन").
- Answer-Key.txt: official key ke 3 E-tables se 210 entries (MAIN 90 + 01-English 60 + 02-Hindi 60), python script se generate + asserts. **Naya verification trick**: Q106-120 aur Q136-150 English vs Hindi tables me identical nikle (30/30 match) - isse dono tables ki transcription confirm hui.
- Pickle task (c983b097) analysis: branch Initial commit se forked (4 session purani base), papers/memory ko metadata-hub + JSON schema se replace karne wala approach, aur `sessions/README.md` me galat section mapping. Unmerged chhoda; lessons MISTAKES #11 me.
- Memory me pehle jo B-02-Hindi key adhoori thi (Q99/Q110-112/Q124-150) usko chunk 3+4 dobara fetch karke poori verify ki - Q99 = 1 nikla (pehle "4" ka shak tha). Key-table reading ka grouping lesson MISTAKES #12 me.
- Verification pass: 30 Q/file, numbering, blanks sab `________` (8-underscore) standard, 210 key entries, markdown/stray-symbol + script scans clean, Hindi QA pass, README (folder) + root index update.
- Commits: `4f7d6a5` (paper + Answer-Key + READMEs + root index), `624b940` (AGENT_MEMORY update: SOURCES #9, MISTAKES #11-13, PLAYBOOK #11, PDF_AND_HINDI_GUIDE note, MEMORY Session 5 + preferences). Branch `arena/27af2acc-xtet` push → PR → merge (memory update ke BAAD - user ki is baar ki shart).

### Session 6 - 2026-10-12 - CTET 2020 cycle, January 2021 Paper 1 Set I

- User ne pehle 2026 par kaam kaha aur doosri session ke 2025 kaam se overlap na karne ko bola; memory docs read karne ke baad final selection CTET 2020 cycle Paper 1 Set I (`AAT-20-I`, exam 31 January 2021) hua. Alag session ka Dec-2025 cycle (Feb-2026 exam) untouched.
- `2021/CTET_Paper1_Jan2021_SetI/` me CPD (1-30), Maths (31-60), EVS (61-90), Eng-1/Hindi-1 (91-120), Eng-2/Hindi-2 (121-150), CBSE Official Final Answer Key aur README add kiye; root README, SOURCES.md aur MISTAKES.md update kiye.
- Official booklet URL `2022040421.pdf`; final key URL `2022033154.pdf`. Booklet code `AAT-20-I`. Official key mapping: Set I MAIN Q1-90, `01-ENGLISH` English Q91-150, `02-HINDI` Hindi Q91-150. Seven answer vectors verified against the official tables; Studyfry discrepancies: EVS Q90 (CBSE 3 vs Studyfry 4), English Language II Q145 (CBSE 3 vs Studyfry 2), Hindi Language I Q106 (CBSE 2 vs Studyfry 1).
- CDP/Maths/EVS are bilingual; each language section is single-language. English appears before Hindi within Parts IV/V. Added the IMPORTANT English/Hindi eligibility note to all four files; README notes Language II must differ from Language I and language streams are not assumed to be translations.
- Hindi booklet text layer is legacy-font encoded; Studyfry was used as wording cross-check only. Exact Hindi source typography/wording caveat and third-party key differences are documented in the paper README. No clean official Hindi scan/transcript was obtained.
- Validation: all seven section files have 30 questions and four options per language, Answer-Key has 7 sections/210 entries, all vector checks passed, blank markers are eight underscores, UTF-8/Devanagari/plain-text scans passed, and `git diff --check` passed. Manually reviewed section content/source notes and the answer-key mapping. Paper commit: `52a0951` (`Add CTET 2020 cycle January 2021 Paper 1 Set I`); memory follow-ups: `95d382f` and `dfbdabf`. Branch `arena/0a9a02c8-xtet` was pushed. While preparing PR #7, latest `origin/main` (including the separate Feb-2026/Dec-2025 session) was merged into this branch; MEMORY/SOURCES conflicts were resolved without dropping either paper. SOURCES #9 is Feb 2026 and #10 is January 2021. PR #7 merge requested by user.

---

### Session 7 - 2026-10-12 - CTET/UTET SQLite question-bank pipeline

- User request: build an extensible SQLite database and deterministic parse/validate/load/verify/report/export pipeline from the five existing CTET Paper 1 text sets and six UTET Paper 1 forms in `sherawali/tet` `bank-v2`, with documentation, CI, report, artifact, and memory update. Followed the required order: completed Phase 1 `docs/DATA_PROFILE.md`, presented Phase 2 `docs/SCHEMA.md` summary, then implemented.
- Vendored a scoped, unmodified UTET snapshot at commit `6792637052eb0bcddd27b9290ddd082faa725a4d`; recorded CC BY 4.0 attribution/change notice. Its embedded answer fields remain `source_repository`/`provisional`, outside the official-final view. CTET raw source files remained unmodified; key text was structurally parsed only.
- Implemented migration, CTET parser with configured mirror drift checks/stimuli/multi-key expansion, UTET schema/parser/audit import, provenance staging, atomic clean rebuild, SQLite integrity/FK/FTS/content-hash verification, data-quality report and deterministic NDJSON exports. Added `docs/PIPELINE.md`, `docs/QUERIES.md` (29 executable SQL examples), `docs/DATA_QUALITY.md`, `.github/workflows/question-bank.yml`, and root README database instructions.
- Built `data/xtet-question-bank.sqlite` (26 MB); content hash `f92ebbb63338c1bc06570899dbb3376437c39a911bae4819107a49f72fe105cd`; source manifest hash `5ca08551abdba96646e9341eba59fb3c22d25c746951d45bdad87953ad4c4e7f`. Counts: CTET 930 canonical questions / 1,050 appearances / 1,050 official-final key entries; UTET 900 questions / 900 appearances / 900 provisional source answer entries; combined 64 stimuli / 411 links / 2,850 FTS documents.
- Validation passed: 12 UTET schemas; 9 integration tests; 29 SQL examples; exact CTET multi-answer spot-checks; CTET/UTET counts; clean two-build content-hash equality; deterministic exports; `PRAGMA integrity_check`; zero FK violations; FTS5 integrity/search; official-vs-provisional boundary; full `pipeline build`, `verify`, `export`, Python compile, and `git diff --check`. GitHub Actions workflow added. CTET paper folders remained unchanged; DB query found zero CTET/UTET prefix mismatches and zero question IDs reused across exams.
- Commit/push: `9641312` (`Build deterministic CTET and UTET SQLite bank`) on `arena/ed8a51c8-xtet`; push succeeded. No PR opened because none was requested.

---

### Session 8 - 2026-10-12 - Single-file app JSON download

- User said they did not want technical explanations and asked to make the question data downloadable for their separate app; app-code changes will be handled by another AI. Keep replies plain Hinglish.
- Added a single, regular JSON bundle at `data/xtet-question-bank.json` in addition to SQLite/NDJSON. `pipeline build` now regenerates it; deterministic bundle has metadata/content version plus questions, appearances (with `exam_code`), stimuli, complete answer history, and a separate official-final answers array. Size 12,730,793 bytes; SHA-256 `14c7204255f8341cd73ef96b5dcaf418ce8fb13f1f5c831dac8ccbc46f727d5b`; DB content hash unchanged at `f92ebbb63338c1bc06570899dbb3376437c39a911bae4819107a49f72fe105cd`.
- Added `docs/APP_DOWNLOAD.md` with public GitHub Raw URL: `https://raw.githubusercontent.com/sherawali/Xtet/arena/ed8a51c8-xtet/data/xtet-question-bank.json`. No custom API/CDN or separate app project is present. GitHub Contents API confirms this exact `download_url` and 12,730,793-byte size.
- Updated exporter, CLI full-build flow, README, pipeline/data-profile docs, PLAYBOOK, and integration tests. Full build, verify, export, py_compile, and all 9 integration tests passed; bundle checked as valid JSON with 1,830 questions, 1,950 appearances, 64 stimuli, 1,950 answer-history rows, 1,050 official-final rows, and both exam codes.
- Commit/push succeeded: `7162b95` (`Add downloadable single-file question bank JSON`) on `arena/ed8a51c8-xtet`. Working tree check pending after memory update; no PR requested.

---

## User Preferences (user ko kya chahiye - hamesha yaad rakho)

- Questions ORIGINAL paper jaisa - bina kisi extra sign (jaise *, #, markdown) ke. Sirf plain text.
- Blank spaces "________" se dikhaye jate hain (original paper style) - wo allowed hain.
- Folder structure year-wise, paper set folder ke andar section-wise files.
- Section names paper ke actual sections ke hisaab se (Hindi-1, Eng-1, jaisa paper me hai).
- Hinglish me baat karna user ko pasand hai (READMEs bhi Hinglish me hain).
- **Memory update ke BAAD hi merge karna** (Session 5 me user ne explicitly kaha: "same jo tu abhi silega (seekhega) usko memory mai add jaroor karna tab merge karna taaki har baar aur better ho sake"). Ritual: paper commit → AGENT_MEMORY update commit → PR → merge. Memory update hone se pehle merge NAHI.
- Purane "pickle" jaisi galtiyan dobara nahi (MISTAKES #11) - papers/AGENT_MEMORY ko koi restructure replace nahi karega.
- **DUAL-LANGUAGE RULE (agli baar se)**: CDP, Maths, EVS ke questions DUAL-language (Hindi + English dono, jaisa booklet me chhapa hai) banane hain. Language sections (Hindi-1/Eng-1/Hindi-2/Eng-2) single-language apni bhasha me - jaise hain waise. (Set A ke current CPD/Maths/EVS Hindi-only hain - user ka instruction "agli baar dual bhasha mai" ke hisaab se future papers ke liye; agar user kahe to Set A ko bhi bilingual convert kar sakte hain.)
