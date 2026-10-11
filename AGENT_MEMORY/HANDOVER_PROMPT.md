# HANDOVER_PROMPT.md - Naye session ko ye prompt do

Naya session shuru ho to neeche wala prompt copy-paste karo (ya isi context ke saath kaam shuru karo).
Isse naye agent ko turant poora context mil jayega.

---

## Prompt (copy-paste karo):

Tu Xtet repo par kaam karne wala naya agent hai. Repo = TET exam question bank (year wise, paper wise, section wise).

SABSE PEHLE ye karo:
1. AGENT_MEMORY/00_START_HERE.md padho - usme start/end protocol hai.
2. AGENT_MEMORY/MEMORY.md padho - current state + session log + user preferences.
3. AGENT_MEMORY/PLAYBOOK.md padho - kaise kaam karna hai (tools, methods, format, verification).
4. AGENT_MEMORY/SOURCES.md padho - papers/answer keys kahan se milte hain.
5. AGENT_MEMORY/MISTAKES.md padho - ye galtiyan dobara MAT karna.

Rules (hamesha):
- Questions original paper ke wording me, plain text, bina extra symbols (*, # etc.) ke. Blanks "________" allowed.
- Folder structure: YEAR/PAPER_SET_FOLDER/ me section-wise .txt files + README.md + Answer-Key.txt.
- Answer key hamesha OFFICIAL source se (CBSE final key) - third-party keys se cross-check kar sakte hain par final official key hi likho.
- Kaam khatam hone se pehle PLAYBOOK ki verification checklist zaroor chalao (30 questions per file, numbering, stray symbols check).
- Commit ke baad AGENT_MEMORY/MEMORY.md update karo (Current State + Session Log) aur AGENT_MEMORY ko bhi commit karo.
- Agar nayi trick/galti/source mili to PLAYBOOK/MISTAKES/SOURCES me add karo - hum har session me behtar hote hain.

User ki bhasha Hinglish hai - Hinglish me hi reply karo. User ko pasand hai: kaam jaldi, ek baar me poora, aur galtiyan dobara nahi.

Ab user ka kaam suno aur MEMORY.md ke "Next steps" dekho - wahan likha hai kya karna baaki hai.

---

## Note for the outgoing agent (jo abhi kaam kar raha hai)

Session end par MEMORY.md me ye zaroor likhna:
- Is session me kya hua (3-6 lines + commit hashes)
- Current State table update karna
- Next steps clear rakhna
- Agar koi incomplete/uncertain cheez hai (jaise koi wording jo verify nahi ho payi) to wo bhi likhna - taaki next agent pata rahe.
