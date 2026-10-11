# MEMORY.md - Living Memory (har session me padho + update karo)

Last updated: 2026-10-11 (Session 1 - Arena agent)

---

## Current State (ab kya hai)

Repo: Xtet (git branch: arena/b7b48f59-xtet)
Kaam: TET exam question bank - year wise, paper wise, section wise.

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

### Important facts (bhoolna mat)

- Sanskrit-1/2 is Set A booklet me NAHI hain - CBSE ki instruction #6 ke anusar Sanskrit/Urdu etc. alag "Supplement (Language) Test Booklet" me aati hain. User ko ye baat bata di gayi hai. Agar Sanskrit chahiye to supplement booklet alag se dhoondhni padegi (koi online source abhi nahi mila).
- Set A booklet me 4 language sections hote hain: Eng-1 (Q91-120), Hindi-1 (Q91-120), Eng-2 (Q121-150), Hindi-2 (Q121-150) - candidate ko har part me ek-ek language attempt karni hoti hai.
- Q91-105 Hindi-1/Eng-1 me translations hain (same answers) aur Q136-150 Hindi-2/Eng-2 me translations hain (same answers).
- ALL paragraphs/poems + questions cross-verified (Session 1 end): Eng-1 passage+poem = booklet exact ✓; Hindi-1 गद्यांश+काव्यांश+Q106-120 = theexampillar exact ✓ (typo खुदी/बुद्धि/बोधि booklet jaisa rakha, file me खुदी "खुदी नींव" sahi hai); Hindi-2 गद्यांश-1 = testbook exact ✓; Hindi-2 गद्यांश-2 (reconstruction) = answer-key aligned 100% ✓; Eng-2 passages = theexampillar clean source ✓. Saare answers CBSE key se match ✓.

### Baaki / Next steps (jab user kahe)

- Agli baar se CDP/Maths/EVS DUAL-LANGUAGE (Hindi+English) - PDF_AND_HINDI_GUIDE.md section 6 dekho. Set A ko bilingual convert karna ho to English text booklet PDF me hai (r.jina.ai chunks 0-4).
- User ko Sanskrit chahiye to: supplement booklet sources dhoondho (mubeensir.blogspot.com par Urdu/Marathi supplements mile the Dec 2022/Aug 2023 ke liye - Sanskrit wala koi link nahi mila tha).
- Baaki years/papers (Dec 2023, 2024, Paper 2, Sets B/C/D) isi PLAYBOOK se add kar sakte hain - sources SOURCES.md me hain. Sets B/C/D ki answer key to already CBSE final key PDF me hai (pages 1-12).
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

---

## User Preferences (user ko kya chahiye - hamesha yaad rakho)

- Questions ORIGINAL paper jaisa - bina kisi extra sign (jaise *, #, markdown) ke. Sirf plain text.
- Blank spaces "________" se dikhaye jate hain (original paper style) - wo allowed hain.
- Folder structure year-wise, paper set folder ke andar section-wise files.
- Section names paper ke actual sections ke hisaab se (Hindi-1, Eng-1, jaisa paper me hai).
- Hinglish me baat karna user ko pasand hai (READMEs bhi Hinglish me hain).
- **DUAL-LANGUAGE RULE (agli baar se)**: CDP, Maths, EVS ke questions DUAL-language (Hindi + English dono, jaisa booklet me chhapa hai) banane hain. Language sections (Hindi-1/Eng-1/Hindi-2/Eng-2) single-language apni bhasha me - jaise hain waise. (Set A ke current CPD/Maths/EVS Hindi-only hain - user ka instruction "agli baar dual bhasha mai" ke hisaab se future papers ke liye; agar user kahe to Set A ko bhi bilingual convert kar sakte hain.)
