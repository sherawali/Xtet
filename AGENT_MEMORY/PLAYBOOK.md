# PLAYBOOK.md - Kaise karna hai (poora tarika)

Ye raha wo sab kuch jo Session 1 me sikha - tareeka, tools, methods, format, verification.
Naya paper nikalte waqt ise step-by-step follow karo.

---

## 1. Workflow (order me karo)

1. User se paper ki details lo: kaunsa exam, kaunsa paper (Paper 1/2), date, set (A/B/C/D).
2. SOURCES.md se sources kholo - pehle HTML solved paper source (theexampillar jaisa) dhoondho, phir full booklet PDF, phir official answer key.
3. Folder banao: YEAR/CTET_PaperX_Date_SetX/ (e.g. 2023/CTET_Paper1_Aug2023_SetA/).
4. Section-wise .txt files banao (format rules section 4 dekho).
5. Booklet ki instruction page zaroor padho - pata chalega ki kitne parts hain, languages kya hain, aur supplement booklet chahiye ya nahi.
6. Answer key official source se nikalo (section  5 dekho) - Answer-Key.txt banao.
7. README.md banao (paper folder me) + root README.md update karo (year-wise index).
8. Verification checklist chalao (section 6) - PASS hone par hi commit karo.
9. AGENT_MEMORY/MEMORY.md update karo + AGENT_MEMORY ko bhi commit karo.

---

## 2. Tools - kya chalta hai, kya nahi

### fetch_page (web page/PDF padhne ke liye) - PRIMARY TOOL

- HTML pages: perfect chalta hai, chunks me aata hai (hasMore/totalChunks). Aage padhne ke liye chunkIndex badhao.
- PDFs: SIRF 30 pages tak parse hota hai (hard limit). Agar PDF badi hai to...
- **r.jina.ai TRICK (Session 1 ki sabse badi learning):** URL ke aage "https://r.jina.ai/" laga do:
  - Normal: https://images.shiksha.com/mediadata/pdf/xyz.pdf (30 pages ke baad kat jata hai)
  - Trick: https://r.jina.ai/https://images.shiksha.com/mediadata/pdf/xyz.pdf (POORI PDF parse hoti hai - 49 pages, 84 pages sab chale!)
  - Chunks me milta hai (15-22 chunks) - chunkIndex se aage badho.
- PDF chunks kabhi beech sentence me kat-te hain (ek chunk "...समृद्ध हो" par khatam, agla "ती है, बल्कि..." se shuru) - chunks ko jodte waqt ye dekho.

### web_search

- Unique phrases se dhoondho (jaise passage ka ek sentence: "संगाई महोत्सव" + CTET) - clean text sources mil jate hain (testbook.com ke Q&A pages).
- depth 2 normal ke liye, depth 3 jab bahut dhoondhna ho.

### bash / git

- GitHub/git local sab chalta hai (gh auth configured hai).
- bash se INTERNET sirf github/npm/pypi tak hai - kisi aur site se PDF download KAROGE TO FAIL hoga (curl/urllib dono block hain). Time waste mat karo, fetch_page use karo.
- Chat me bheji gayi files /home/user/uploads me sync NAHI hoti (Session 1 me nahi aayi thi) - user se URL maango.

### Verification ke liye bash

- grep/sed/awk se counts aur numbering check karo (checklist section 6).
- awk/sed me parentheses WALE patterns carefully - "(" ko escape karo (\() warna regex group ban jata hai aur galat count aata hai. Simple grep -c '^[0-9]\+\. ' se hi kaam chalao.

---

## 3. Sources - details SOURCES.md me hain (yahan summary)

Priority order:
1. theexampillar.com - section-wise solved papers (HTML, saaf text) + official answer keys.
2. shiksha.com - full booklet PDFs (sab sets A-H) - r.jina.ai se parse karo.
3. CBSE Final Answer Key PDF (shiksha par hosted) - answer keys ka FINAL source. Page structure: p1-4 = MAIN Q1-90 (sets A-D), p5-8 = English Q91-150, p9-12 = Hindi Q91-150, phir other languages + Paper 2.
4. testbook.com/question-answer - ek-ek question ka page; unique phrase search se milta hai (clean passage text ke liye best).
5. mubeensir.blogspot.com - Google Drive links (papers + language supplements like Urdu/Marathi).

---

## 4. File Format Rules (USER KI SAKHT SHART)

- SIRF plain text. Koi markdown symbol nahi (*, #, `, >). User ne kaha tha: "bina kisi extra sign jaise * etc ke".
- Blanks original paper style: "________".
- Har question file ki shuruaat:
  Line 1: CTET Paper 1 - August 2023 - Set A  (exam + date + set)
  Line 2: Section: Hindi-1 (Language I - हिन्दी / भाषा I)
  Line 3: Part IV - Questions 91 to 120
  Line 4: Exam Date: 20 August 2023 | Paper Set: A
  Phir khaali line, phir "निर्देश :" / "Directions:" lines, phir questions.
- Question numbering ORIGINAL paper jaisi (91., 92., ... ya 1., 2., ...) - kabhi renumber mat karo.
- Options aise:
  (1) pehla option
  (2) doosra option
  (3) teesra option
  (4) chautha option
  (har option apni line me)
- Passages/poems poore likho - unke directions me "(प्र.सं. 106 से 114)" / "(Q. Nos. 106 to 114)" jaisa paper me hai.
- Match-the-following questions pipe style me:
  A. item | i. description
- Assertion-Reason me "अभिकथन (A) :" aur "तर्क (R) :" (Hindi) / "Assertion (A):" aur "Reason (R):" (English) - blank line ke saath.
- Answer-Key.txt me section-wise "N. answer" lines + multi-answer note (A=1,2 etc.).
- READMEs Hinglish me (user ko pasand hai).
- **DUAL-LANGUAGE RULE (agli baar se - user ki shart)**: CDP, Maths, EVS ke questions DUAL-language likhne hain - Hindi + English dono versions, jaisa booklet me chhapa hota hai (bilingual format). Language sections (Hindi-1/Eng-1/Hindi-2/Eng-2) SINGLE-language rahenge. (Set A ke CPD/Maths/EVS Hindi-only hain - future papers ke liye rule.) Extract karte waqt hi dono versions likho - Hindi upar/pehle jaisa booklet me ho, English neeche. Details: PDF_AND_HINDI_GUIDE.md section 6.

---

## 5. Answer Key - kaise nikale

1. CBSE Final Key PDF lo (SOURCES.md me URL hai).
2. r.jina.ai se fetch karo - chunks me Set A/B/C/D ke pages milenge.
3. Structure samjho:
   - "Set :- A PAPER-I (MAIN)" = Q1-90 (CPD+Maths+EVS). Table 4 columns: Q1-25 | Q26-50 | Q51-75 | Q76-90.
   - "Set :- A PAPER-I 01-ENGLISH" = Q91-150 (Eng-1 Q91-120 + Eng-2 Q121-150). 3 columns: Q91-115 | Q116-140 | Q141-150.
   - "Set :- A PAPER-I 02-HINDI" = Q91-150 (Hindi-1 + Hindi-2). Same column layout.
   - Baaki languages (03-SANSKRIT etc.) ke bhi pages hote hain aage.
4. Multi-answer questions ke liye legend: A=1,2 B=1,3 C=1,4 D=2,3 E=2,4 F=3,4 Z=ALL. Letter aaye to Answer-Key.txt me "A (1 aur 2 dono)" jaisa likho + note.
5. THIRD-PARTY KEYS (theexampillar etc.) se hamesha cross-check karo - Session 1 me EVS Q86-88 ki third-party key GALAT thi (official: 1,4,1). Official key hi final hai.
6. Cross-language sanity check booklet dekh kar hi karo. Language sections me passage-based question ranges alag ho sakte hain aur unke answers bhi alag ho sakte hain (Jan 2024 Set I me English/Hindi L1 Q91-105 aur L2 Q121-135 alag passages hain). Sirf wahi ranges compare karo jahan booklet se same question/translation confirm ho; har language ki final key independent official table se lo.

---

## 6. Verification Checklist (COMMIT SE PEHLE - hamesha)

Ye commands chalao (folder ke andar):

1. Har .txt me EXACTLY 30 questions:
   for f in *.txt; do echo "$f: $(grep -cE '^[0-9]+\. ' $f)"; done
2. Numbering sahi hai (CPD 1-30, Maths 31-60, EVS 61-90, Hindi-1/Eng-1 91-120, Hindi-2/Eng-2 121-150):
   grep -oE '^[0-9]+\. ' FILE | tr -d '. ' | paste -sd, -
3. Koi markdown artifact nahi (sirf blanks "________" allowed):
   grep -nE '^[*_#>`]|[*]' FILE   (blanks wali lines aayengi - wo theek hain, * nahi aana chahiye)
4. Answer-Key.txt me har section ke 30 answers:
   Total = 210 (7 sections x 30) - grep -cE '^[0-9]+\. ' Answer-Key.txt
5. Aankhon se ek baar passages/poems ke directions aur numbering dekh lo.
6. Hindi wale har block ka alag spelling/grammar pass karo: ling-vachan, idiomatic phrasing, punctuation aur technical terms dekho. Unicode/mojibake scan encoding batata hai, grammar ya source fidelity nahi. Intentional wrong-spelling distractors ko preserve karo; clean source na ho to exact wording verified hone ka claim mat karo.
7. README me section table me saari files listed hon aur Hindi-source caveat ho (agar lagu ho).

PASS -> commit (clear message ke saath). FAIL -> fix -> dobara check.

---

## 7. Is paper (CTET Paper 1 Aug 2023 Set A) ki TECH/METHODS jo use hui

- 5 sections theexampillar se (clean Hindi/English HTML).
- Eng-1 + Hindi-2 shiksha booklet PDF se via r.jina.ai (chunks 8-9 = Eng-1, 12-13 = Hindi-2).
- Hindi-2 ke gadyansh ka clean text testbook se verify kiya.
- Booklet ki garbled Hindi decode ki (MISTAKES.md me patterns hain).
- Answer key user ki di hui CBSE Final Key PDF se.
- Sabse badi jeet: r.jina.ai trick + answer-key cross-verification se 100% confident result.

## 8. Improve kaise karein (har session)

- Har nayi trick -> PLAYBOOK me.
- Har galti -> MISTAKES.md me (fix ke saath).
- Har naya source -> SOURCES.md me.
- Session log -> MEMORY.md me (short rakho).
- Goal: kam time me zyada papers, zero repeated mistakes, checklist first-time pass.

## 9. Time targets (speed + perfection dono)

- HTML source paper: 30-45 min | PDF-only (r.jina.ai + decode): 45-75 min | Max 1 hour per set.
- PDF se text + Hindi decode ka FASTEST tareeka + advanced tools + decode table: **PDF_AND_HINDI_GUIDE.md** me hai - uske bina PDF kaam mat shuru karo.
- Speed rules: chunks parallel fetch; file pehli baar me final format; key usi PDF se; checklist ek baar; chunk map MEMORY me. Details guide section 5.
