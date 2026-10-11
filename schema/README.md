# Xtet Database Schema

Ye schema **do tarah ke content** ke liye ek hi structure use karta hai — provenance field se
farq track hota hai:

| `provenance.content_type` | Matlab | Display permission |
|---|---|---|
| `official_pyq` | CBSE ke official question paper se extracted | ⚠️ `reuse_permission` verify karna ZAROORI hai display se pehle |
| `third_party_pyq` | Kisi third-party site ke PDF se extracted | ⚠️ same — double copyright risk (CBSE + site) |
| `original_practice` | Naye, khud likhe gaye questions | ✅ free to use |

## Core fields (har question)

| Field | Type | Notes |
|---|---|---|
| `no` | int | Booklet question number (CDP: 1–30, Lang-I: 31–60, Lang-II: 61–90, Math: 91–120, EVS: 121–150) |
| `text` | `{en?, hi?, raw?}` | `raw` = unsplit bilingual text (extraction ke turant baad); `en`/`hi` = human-split clean versions |
| `options` | `{en?[], hi?[], raw?[]}` | Same logic. CTET mein hamesha 4 options |
| `answer` | `"a"\|"b"\|"c"\|"d"\|null` | Official answer key se fill karo |
| `explanation` | `{en?, hi?}` | Tumhari apni explanation (khud likhni hai — kisi book se copy mat karo) |
| `topic` | string | Syllabus topic tag |
| `difficulty` | `easy\|medium\|hard` | Optional |
| `provenance` | object | **Sabse important field** — source + permission tracking |

## Provenance fields

```json
{
  "content_type": "official_pyq | third_party_pyq | original_practice",
  "session_id": "2024-12",
  "set_code": "H",
  "source_file": "ingest/pdf/2024-12/paper1-setH.pdf",
  "source_url": "https://...",
  "page": 4,
  "reuse_permission": "granted | public_domain | unclear | not_required",
  "notes": ""
}
```

**Rule:** `content_type` = `official_pyq`/`third_party_pyq` aur `reuse_permission` = `unclear`
wale questions ko app mein PUBLICLY display mat karo jab tak permission verify na ho.
Personal/local database mein rakhna alag baat hai — ye legal risk tumhe khud assess karna hai.

## Files

- `question.schema.json` — ek question ka JSON Schema (draft-07)
- `section.schema.json` — section file (30 questions ka wrapper)
- `paper.schema.json` — paper-level metadata (session, set, sections status)

Kisi bhi JSON Schema validator se check kar sakte ho, e.g.:
`python -m pip install jsonschema && python -c "import jsonschema, json; jsonschema.validate(json.load(open('FILE')), json.load(open('schema/question.schema.json')))"`
