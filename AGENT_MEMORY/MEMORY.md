# MEMORY.md - Living Memory (har session me padho + update karo)

Last updated: 2026-10-12 (Session 4 - CTET July 2024 Paper 1 Set A, COMPLETE)

---

## Current State (ab kya hai)

Repo: Xtet (current Arena branch: arena/3d996047-xtet)
Kaam: TET exam question bank - year wise, paper wise, section wise.

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

### Baaki / Next steps (jab user kahe)

- CTET January 2024 Paper 1 Set I and its manual Hindi language QA are complete; content/README commit `2394b47`. Exact Hindi source wording remains unverified until a clean scan/transcript is available. For the next paper, follow the user's choice and use PLAYBOOK.md plus PDF_AND_HINDI_GUIDE.md. Keep CDP/Maths/EVS bilingual and each language section single-language.
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
- Commits: `6c1a22e` (paper + root README) + Hindi-spelling polish & AGENT_MEMORY update wala commit.
- Agli baar ke liye leads (agar language text dobara chahiye ho): prepp ka HTML quiz page "CTET 2024 Paper 1 Question Paper (07-Jul-2024)" (210 Q list + per-question pages - option order ka cross-check try kiya ja sakta hai, par confirm karna baaki hai); SET-D ka pyqonline text PDF; prepp CDN ke language supplement PDFs (Set A Sanskrit etc.).


---

## User Preferences (user ko kya chahiye - hamesha yaad rakho)

- Questions ORIGINAL paper jaisa - bina kisi extra sign (jaise *, #, markdown) ke. Sirf plain text.
- Blank spaces "________" se dikhaye jate hain (original paper style) - wo allowed hain.
- Folder structure year-wise, paper set folder ke andar section-wise files.
- Section names paper ke actual sections ke hisaab se (Hindi-1, Eng-1, jaisa paper me hai).
- Hinglish me baat karna user ko pasand hai (READMEs bhi Hinglish me hain).
- **DUAL-LANGUAGE RULE (agli baar se)**: CDP, Maths, EVS ke questions DUAL-language (Hindi + English dono, jaisa booklet me chhapa hai) banane hain. Language sections (Hindi-1/Eng-1/Hindi-2/Eng-2) single-language apni bhasha me - jaise hain waise. (Set A ke current CPD/Maths/EVS Hindi-only hain - user ka instruction "agli baar dual bhasha mai" ke hisaab se future papers ke liye; agar user kahe to Set A ko bhi bilingual convert kar sakte hain.)
