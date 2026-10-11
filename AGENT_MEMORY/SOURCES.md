# SOURCES.md - Question Papers aur Answer Keys kahan se milte hain

Sab URLs Session 1 me test kiye gaye hain (2026-10-11). Kaam karte hain - ye confirmed hai.

---

## 1. theexampillar.com - Solved Papers (sabse pehle yahan dekho)

Section-wise HTML me questions + official answer key ke saath. Text saaf hota hai (Hindi bhi).

URL pattern:
- https://theexampillar.com/ctet-exam-20-aug-2023-paper-i-cdp-answer-key/
- https://theexampillar.com/ctet-exam-20-aug-2023-paper-i-mathematics-answer-key/
- https://theexampillar.com/ctet-exam-20-aug-2023-paper-i-evs-answer-key/
- https://theexampillar.com/ctet-exam-20-aug-2023-paper-i-language-i-hindi-answer-key/
- https://theexampillar.com/ctet-exam-20-aug-2023-paper-i-language-ii-english-answer-key/

Notes:
- Long sections paginated hoti hain: /2/ /3/ laga ke agla page.
- Har page par "Show Answer/Hide" hota hai - answers neeche hote hain.
- Ye site HAR language cover nahi karti - Aug 2023 Paper 1 me sirf Hindi L1 + Eng L2 thi. Eng-1/Hindi-2 nahi mili thi yahan.
- Inki answer key mostly sahi thi par 100% nahi - CBSE final key se hi final lo (MISTAKES.md dekho).

## 2. shiksha.com - Full Booklet PDFs (sab sets)

Article (sab sets ke links is page par hain):
https://www.shiksha.com/sarkari-exams/teaching/articles/ctet-2023-question-paper-pdf-paper-1-paper-2-all-sets-blogId-131853

Direct PDF links (CTET Aug 2023):
- Paper 1 Set A: https://images.shiksha.com/mediadata/pdf/1698734064phpnugAtI.pdf
- Paper 1 Set B: https://images.shiksha.com/mediadata/pdf/1698734076phpsuNsEa.pdf
- Paper 1 Set C: https://images.shiksha.com/mediadata/pdf/1698734092php0Erneb.pdf
- Paper 1 Set D: https://images.shiksha.com/mediadata/pdf/1698734107phpv0dbIK.pdf
- Paper 2 Set E: https://images.shiksha.com/mediadata/pdf/1698734126phpNtLNxv.pdf
- Paper 2 Set F: https://images.shiksha.com/mediadata/pdf/1698734138phpyGN6XY.pdf
- Paper 2 Set G: https://images.shiksha.com/mediadata/pdf/1698734152phpzc9m1q.pdf
- Paper 2 Set H: https://images.shiksha.com/mediadata/pdf/1698734165php2K2ZDe.pdf

IMPORTANT:
- Direct fetch_page se SIRF 30 pages parse hoti hain. r.jina.ai lagao (PLAYBOOK.md dekho).
- Booklet ki Hindi TEXT LAYER garbled hai (font corruption) - English saaf hai. Hindi ke liye patterns MISTAKES.md me hain + clean sources (testbook) dhoondho.
- Set A booklet = 48 pages: instructions + CDP + Maths + EVS + Part IV (Eng-1 then Hindi-1) + Part V (Eng-2 then Hindi-2). Booklet order: Part IV me ENGLISH pehle, phir Hindi; Part V me bhi ENGLISH pehle.

## 3. CBSE Final Answer Key PDF (ANSWER KEY KA FINAL SOURCE)

https://images.shiksha.com/mediadata/pdf/1705312468phpFFopP0.pdf

(Title: "CTET AUG-2023 Final KEY EXAM-20/08/2023" - 84 pages)
Ye r.jina.ai se parse hoti hai (22 chunks). Structure:

- Pages 1-4: Set A/B/C/D PAPER-I (MAIN) = Q1-90. Columns: Q1-25 | Q26-50 | Q51-75 | Q76-90.
- Pages 5-8: Set A/B/C/D PAPER-I 01-ENGLISH = Q91-150 (Eng-1 Q91-120 + Eng-2 Q121-150). Columns: Q91-115 | Q116-140 | Q141-150.
- Pages 9-12: Set A/B/C/D PAPER-I 02-HINDI = Q91-150 (Hindi-1 + Hindi-2). Same columns.
- Uske baad: 03-SANSKRIT, 04-URDU etc. languages + PAPER-II keys.

Legend (multi-correct): A=1,2 B=1,3 C=1,4 D=2,3 E=2,4 F=3,4 Z=ALL.

CBSE ki official page bhi hai: https://ctet.nic.in/previous-year-final-answer-key/ ("CTET Aug23 Answer Key P1/P2").

## 4. testbook.com - Per-question Q&A pages (clean text ke liye)

Google par unique phrase search karo - jaise:
- "सुख कहाँ होता है" testbook -> Set A Hindi-2 Q123 ka exact page mil gaya tha (clean gadyansh ke saath!)
- "संगाई महोत्सव" CTET -> festival passage wale questions

URL format: https://testbook.com/question-answer/<question-title-slug>
Ye pages passage + question + options + detailed solution dete hain. Garbled PDF ki Hindi verify karne ke liye BEST.

## 5. mubeensir.blogspot.com - Google Drive links (papers + supplements)

https://mubeensir.blogspot.com/p/questionpapers-in-hindi-english-with.html

- Har session ke paper PDFs (Drive links, fetch_page se parse hote hain).
- Dec 2022 ke liye alag "HINDI 2 ENG 1 LANGUAGE" PDFs bhi hain - matlab language-wise booklets bhi mil sakti hain.
- URDU/MARATHI supplement booklets ke links hain (Aug 2023 ke liye bhi). SANSKRIT supplement ka link NAHI mila tha.

## 6. CBSE answer key page (old keys / other sessions)

https://ctet.nic.in/previous-year-final-answer-key/ - year-wise official keys.

---

## Sources jo TRY kiye par kaam nahi aaye

- jagranjosh.com - sirf download links dete hain, questions nahi.
- adda247 - galat session ka paper milta hai (Dec 2024 vs Aug 2023) - dhyan se dekho.
- scribd - answer keys hain par questions nahi; login wall.
- bash se direct download (curl/wget/urllib) - network block hai - FAIL.
