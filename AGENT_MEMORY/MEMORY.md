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

### Baaki / Next steps (jab user kahe)

- User ko Sanskrit chahiye to: supplement booklet sources dhoondho (mubeensir.blogspot.com par Urdu/Marathi supplements mile the Dec 2022/Aug 2023 ke liye - Sanskrit wala koi link nahi mila tha).
- Baaki years/papers (Dec 2023, 2024, Paper 2, Sets B/C/D) isi PLAYBOOK se add kar sakte hain - sources SOURCES.md me hain. Sets B/C/D ki answer key to already CBSE final key PDF me hai (pages 1-12).
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

---

## User Preferences (user ko kya chahiye - hamesha yaad rakho)

- Questions ORIGINAL paper jaisa - bina kisi extra sign (jaise *, #, markdown) ke. Sirf plain text.
- Blank spaces "________" se dikhaye jate hain (original paper style) - wo allowed hain.
- Folder structure year-wise, paper set folder ke andar section-wise files.
- Section names paper ke actual sections ke hisaab se (Hindi-1, Eng-1, jaisa paper me hai).
- Hinglish me baat karna user ko pasand hai (READMEs bhi Hinglish me hain).
