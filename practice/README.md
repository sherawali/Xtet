# Practice Sets — Original, CTET Paper-I pattern par

Ye sets **original questions** hain jo maine khud likhe hain — CTET Paper-I ke exact pattern
(150 questions, 5 sections, bilingual Hindi+English, same numbering) par. Ye CBSE ke actual
papers NAHI hain; sirf practice ke liye hain. Answer keys saath mein hain.

## JSON schema (app-ready)

```json
{
  "no": 1,
  "text_en": "Question text in English",
  "text_hi": "हिन्दी में प्रश्न",
  "options_en": ["option a", "option b", "option c", "option d"],
  "options_hi": ["विकल्प अ", "विकल्प ब", "विकल्प स", "विकल्प द"]
}
```

- Section files: `set-XX/sections/<section>.json`
- Answer key: `set-XX/answer_key.json` (question no → correct option letter)
- Paper metadata + section status: `set-XX/paper.json`

## Question numbering (real CTET booklet jaisa)

| File | Section | Questions |
|---|---|---|
| `cdp.json` | Child Development and Pedagogy | 1–30 |
| `language1.json` | Language I | 31–60 |
| `language2.json` | Language II | 61–90 |
| `math.json` | Mathematics | 91–120 |
| `evs.json` | Environmental Studies | 121–150 |

## Sets

- **set-01** — "Model Paper 1" (in progress: CDP section ready, baaki sections aa rahe hain)

Ek-ek section karke add hoga; jab ek set ke saare 150 questions ready ho jayenge tabhi agla set shuru hoga.
