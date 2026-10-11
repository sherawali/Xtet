# AGENT_MEMORY - START HERE

Agar tum ek naye AI agent ho jo abhi is repo par kaam karne aaye ho, to SABSE PEHLE ye karo:

## Session Start Protocol (har baar)

1. Ye file (00_START_HERE.md) padhi ja rahi hai - good.
2. Ab AGENT_MEMORY/MEMORY.md padho - usme "Current State" aur "Session Log" hai - tumhe pata chalega kya hua, kya baaki hai.
3. AGENT_MEMORY/PLAYBOOK.md padho - kaise kaam karna hai, kaunse tools chalte hain, kaunse nahi.
4. AGENT_MEMORY/SOURCES.md padho - question papers aur answer keys kahan se milte hain.
5. AGENT_MEMORY/MISTAKES.md padho - pehle ki galtiyan DOBARA mat karna.
6. Zarurat ho to AGENT_MEMORY/HANDOVER_PROMPT.md se ready-made context prompt lo.

## Session End Protocol (har baar, bhoolna mat)

1. AGENT_MEMORY/MEMORY.md UPDATE karo:
   - "Current State" section = ab kya ban gaya, kya baaki hai, next steps kya hain
   - "Session Log" me is session ki 3-6 lines add karo (kya kiya, commit hashes)
2. Agar koi nayi galti hui ya nayi trick mili to AGENT_MEMORY/MISTAKES.md aur PLAYBOOK.md me add karo.
3. Agar naye sources mile to SOURCES.md me add karo.
4. Aakhir me git commit karo (AGENT_MEMORY ke changes bhi repo ka hissa hain).

## Ye folder ke files

| File | Kya hai |
| --- | --- |
| 00_START_HERE.md | Ye file - start/end protocol |
| MEMORY.md | Living memory - current state + session log (har session me padho + update karo) |
| HANDOVER_PROMPT.md | Naye session/agent ko dene ka ready prompt |
| PLAYBOOK.md | Poora tarika - kaise karna hai, tools, format rules, verification checklist |
| SOURCES.md | Question paper + answer key sources (URLs, kya kaam karta hai, kya nahi) |
| MISTAKES.md | Galtiyan jo hui hain + unke fixes - ye dobara nahi honi chahiye |

## Ek line me maqsad

Xtet repo = TET exam ke question bank (year wise, paper wise, section wise, bina extra symbols ke).
Har paper PERFECT nikalna hai - questions original wording me, sections sahi, answer key official source se, aur verification checklist pass karke hi commit karna hai.
Hum har session me behtar hote jayenge - kam time me zyada kaam, zero repeated mistakes.
