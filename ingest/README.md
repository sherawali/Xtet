# Ingestion Workflow

Tumhare paas maujood CTET Paper-I PDFs se structured JSON database banane ka process.

## Setup (ek baar)

```bash
python3 -m venv .venv
.venv/bin/pip install -r ingest/requirements.txt
```

## Workflow

### 1. PDFs collect karo (khud download karo)

Official/third-party links `sessions/*/meta.json` aur `sources/sources.json` mein hain.
PDFs ko yahan rakho (ye folders gitignore hain — copyrighted material repo mein commit nahi hota):

```
ingest/pdf/<session_id>/<paper>-<set>.pdf
# e.g. ingest/pdf/2024-12/paper1-setH.pdf
```

### 2. Extract

```bash
.venv/bin/python ingest/extract_pdf.py ingest/pdf/2024-12/paper1-setH.pdf \
    -o ingest/out/2024-12/paper1-setH.json --session 2024-12 --set H
```

Output best-effort hota hai (`needs_review: true`):

- `text.raw` mein bilingual text ek saath hota hai → **human review karke `text.hi` / `text.en` mein split karo**
- `options.raw` → `options.hi` / `options.en` mein split karo
- Section boundaries check karo
- Answer key se `answer` field fill karo
- `provenance.reuse_permission` ko `unclear` se aage update karo jab verification ho

### 3. Validate

```bash
.venv/bin/python ingest/validate.py ingest/out/2024-12/paper1-setH.json
```

Errors block karte hain; warnings (missing Hindi, unclear permission) track karo.

### 4. Pipeline test karo (bina kisi copyrighted content ke)

```bash
.venv/bin/python ingest/selftest.py
```

Ye repo ke **apne original** practice questions se sample PDF bana ke poora
extract → validate flow test karta hai.

## Legal flag (important)

Extracted PYQ content mein `provenance.reuse_permission` default **`unclear`** hota hai.
CTET Information Bulletins question contents ki disclosure/transmission ko expressly prohibit
karte hain aur website par koi open reuse license nahi mila. Jab tak permission verify na ho:

- ✅ Personal/local database mein rakh sakte ho
- ❌ App mein public display/redistribution mat karo

`original_practice` content par ye restriction nahi hai.
