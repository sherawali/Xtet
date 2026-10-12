# HANDOVER_PROMPT.md - Naye session ke liye

Naya session shuru ho to neeche wala prompt copy-paste karo (ya isi context ke saath kaam shuru karo).

---

## Prompt (copy-paste karo)

Tu Xtet repo par kaam karne wala naya agent hai. Repo mein CTET paper ke original text files, verified SQLite question bank, aur app ke liye ek downloadable JSON bundle hai.

### Sabse pehle padho
1. `AGENT_MEMORY/00_START_HERE.md` - start/end protocol.
2. `AGENT_MEMORY/MEMORY.md` - current state, session log, user preferences.
3. `AGENT_MEMORY/PLAYBOOK.md` - workflow aur verification.
4. `AGENT_MEMORY/SOURCES.md` - source/answer-key records.
5. `AGENT_MEMORY/MISTAKES.md` - purani galtiyan dobara na karna.

### Abhi ke real deliverables
- SQLite database: `data/xtet-question-bank.sqlite`.
- App ke liye ek single JSON file: `data/xtet-question-bank.json` (about 13.4 MB).
- Chhoti sync file (about 4 KB): `data/xtet-question-bank.manifest.json` - content hash, papers list, aur bundle ka byte size/SHA-256; app pehle isse check karke bada bundle download karna skip kar sakti hai. Contract/sync recipe: `docs/APP_DOWNLOAD.md`.
- Download URLs (merge ke baad stable `main` branch): `https://raw.githubusercontent.com/sherawali/Xtet/main/data/xtet-question-bank.json` aur `.../data/xtet-question-bank.manifest.json`.
- `python -m pipeline build` SQLite, quality report, JSON bundle aur manifest regenerate karta hai. Detailed exports `build/exports/` mein hain.
- JSON mein CTET aur UTET dono hain. Root `papers` list (11 forms) se paper picker turant ban jata hai; `appearances` ke `exam_code` se exam alag hota hai; har appearance me `stimulus_ids` aur derived `answer` mirror hai (`is_official` se CTET final vs UTET provisional pata chalta hai). Authority lists `official_final_answers` / `answer_key_history` hi rehti hain; mirror sirf convenience hai. Bundle changes additive hain, isliye `format_version` 1 hai - app unknown fields ignore kare aur key-presence se feature detect kare.
- Counts: CTET 930 canonical questions / 1,050 appearances; UTET 900 questions / 900 appearances. Yeh sample/demo nahi, source data se bana deliverable hai.
- App project is repo mein nahi hai. User ne kaha hai ki app code kisi doosre AI se update karwayenge. Isliye app integration tabhi implement karo jab user app repo de ya specifically bole. Raw link ready hai; custom API/CDN nahi hai.

### Agle session ke liye kaam / behtari
1. PR #8 is session mein `main` mein merge hua (`10b3f49e...`); GitHub Actions pass hue. Confirm `MEMORY.md` current status aur stable app Raw URL.
2. Agar user app-side integration maange aur app repo de, JSON download ko us app ke current flow ke saath integrate/test karo: download failure, JSON parse failure, language selection, CTET/UTET filter, refresh/cache, aur app version display. App ko tab tak “integrated” mat bolo jab tak app repo mein test na ho.
3. Naye CTET/UTET papers tabhi add karo jab user source/paper bataye. Source inspect/profile karo, parser/config/schema update karo, phir `python -m pipeline build`, `verify`, full tests, export aur determinism gates chalao. Build/push ke baad `main` Raw URL wahi rahega aur naya JSON serve karega.
4. UTET ko official answers ke roop mein tab tak promote mat karo jab tak official UBSE key/source citation na mile. August 2023 CTET README mein direct key URI missing hai. `docs/DATA_QUALITY.md` ke caveats preserve karo.
5. Database/schema ke changes mein forward migration add karo; applied migration rewrite mat karo. CTET source `.txt` read-only/source of truth hain. Pinned UTET upstream snapshot bhi read-only rakho.

### Hamesha ke rules
- User se Hinglish mein, simple bhasha mein baat karo; kaam phase-wise karo aur chhota progress update do. User technical terms nahi samajhna chahta—seedha batao unhe kya karna hai.
- CTET ke paper text, spelling, whitespace, answers, ya layout ko bina explicit permission edit/retranscribe/re-verify mat karo. Raw provenance preserve karo.
- Official key hi final authority hai; third-party/embedded UTET values provisional rakho. Multi-correct answers ko expand karke preserve karo.
- Existing manual-paper workflow ke liye folder layout `YEAR/PAPER_SET_FOLDER/` aur original paper format follow karo; all section/key/source checks run karo.
- Nayi galti ho to `MISTAKES.md`; naya verified source ho to `SOURCES.md`; workflow seekh ho to `PLAYBOOK.md` update karo.
- Session ke end par `MEMORY.md` ka Current State + Session Log + Next steps update karo. Verification ke bina commit nahi.
- Hamesha current Arena branch par hi kaam karo; branch switch/push nahi. GitHub PR ke liye `gh` use karo. User ne explicitly merge na kaha ho toh PR merge mat karo.

Ab user ka naya kaam suno aur `MEMORY.md` ke Next steps dekho. Agar koi unfinished/uncertain baat ho toh chhupao mat.

---

## Outgoing agent note

Session end par `MEMORY.md` mein 3-6 line session log, current branch/commit/PR status, tests, aur pending caveats likho. `HANDOVER_PROMPT.md` ko tabhi update karo jab next session ke liye naya important state ya concrete next step ho.
