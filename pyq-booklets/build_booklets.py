#!/usr/bin/env python3
"""Build printable, mobile-friendly, bilingual previous-year question booklets.

Source of truth: data/xtet-question-bank.json (the repository question database).

Usage (from the repository root or anywhere):
    python3 pyq-booklets/build_booklets.py

Outputs:
    pyq-booklets/ctet/*.html   one booklet per CTET paper (year-wise)
    pyq-booklets/utet/*.html   one booklet per UTET paper (year-wise)
    pyq-booklets/index.html    index of all booklets
"""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE.parent / "data" / "xtet-question-bank.json"

ROMAN = ["I", "II", "III", "IV", "V", "VI"]

# Names for the common (bilingual) sections, keyed by section_code.
COMMON_NAMES = {
    "cpd": ("Child Development and Pedagogy", "बाल विकास व शिक्षा शास्त्र"),
    "cdp": ("Child Development and Pedagogy", "बाल विकास व शिक्षा शास्त्र"),  # UTET spelling
    "mathematics": ("Mathematics", "गणित"),
    "environmental-studies": ("Environmental Studies", "पर्यावरण अध्ययन"),
}

# Names for language sections, keyed by (slot_code, locale_code).
LANGUAGE_NAMES = {
    ("language-1", "en"): ("Language I — English", "भाषा I — अंग्रेज़ी"),
    ("language-1", "hi"): ("Language I — Hindi", "भाषा I — हिन्दी"),
    ("language-2", "en"): ("Language II — English", "भाषा II — अंग्रेज़ी"),
    ("language-2", "hi"): ("Language II — Hindi", "भाषा II — हिन्दी"),
}

EXAM_HINDI = {
    "CTET": "केंद्रीय शिक्षक पात्रता परीक्षा",
    "UTET": "उत्तराखंड शिक्षक पात्रता परीक्षा",
}

CSS = r"""
:root{--ink:#161616;--muted:#5d5d5d;--rule:#1d1d1d;--hair:#d9d6cf;--paper:#ffffff;--desk:#e9e7e1}
*{box-sizing:border-box}
html{background:var(--desk);-webkit-text-size-adjust:100%}
body{margin:0;color:var(--ink);font-family:"Noto Serif",Georgia,"Times New Roman",serif;font-size:16px;line-height:1.6}
[lang=hi]{font-family:"Noto Serif Devanagari","Noto Serif",serif;line-height:1.75}
.sheet{max-width:840px;margin:24px auto;background:var(--paper);padding:44px 52px;box-shadow:0 0 0 1px #cfccc4}
.label{font-family:"Noto Sans","Noto Sans Devanagari",Arial,sans-serif;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.print-btn{display:inline-block;margin:0 0 14px;padding:8px 14px;border:1px solid var(--ink);background:#fff;color:var(--ink);font:600 13px "Noto Sans",Arial,sans-serif;cursor:pointer}
.cover{text-align:center;border:3px double var(--rule);padding:34px 24px 26px;margin-bottom:26px}
.cover .exam{font-size:21px;font-weight:700;margin:10px 0 2px}
.cover .exam-hi{font-size:18px;margin:0 0 16px}
.cover h1{font-size:34px;margin:4px 0 4px;letter-spacing:.05em}
.cover .sub{font-size:15px;color:var(--muted);margin:0}
.cover .sub-hi{font-size:14.5px;color:var(--muted);margin:2px 0 0}
.meta{width:100%;border-collapse:collapse;margin:22px 0 0;font-size:14.5px;text-align:left}
.meta th,.meta td{border-top:1px solid var(--hair);padding:7px 10px;vertical-align:top}
.meta th{width:34%;font-family:"Noto Sans",Arial,sans-serif;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:600}
.notice{border:1px solid var(--rule);padding:12px 16px;font-size:14px;margin:0 0 22px}
.notice p{margin:4px 0}
.toc{font-size:14px;margin:0 0 6px;padding:0;list-style:none;columns:2;column-gap:28px}
.toc li{break-inside:avoid;padding:4px 0;border-bottom:1px dotted var(--hair)}
.toc a{color:var(--ink);text-decoration:none}
.part{margin-top:34px}
.part-head{border-top:3px double var(--rule);border-bottom:1px solid var(--rule);padding:10px 0 9px;margin-bottom:8px}
.part-head h2{font-size:21px;margin:3px 0 0;letter-spacing:.01em;font-weight:700}
.part-hi{font-size:16px;margin-top:2px}
.part-range{font-family:"Noto Sans",Arial,sans-serif;font-size:12.5px;color:var(--muted);margin-top:4px}
.stim{border:1px solid var(--rule);background:#fbfbf9;padding:14px 18px;margin:14px 0 4px}
.stim .label{margin-bottom:8px}
.stim-cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.stim-cols.one{grid-template-columns:1fr}
.stim p{margin:0 0 .6em;font-size:15px}
.q{padding:14px 0 15px;border-bottom:1px solid var(--hair);break-inside:avoid}
.q-no{font-family:"Noto Sans",Arial,sans-serif;font-weight:700;font-size:15px;margin-bottom:4px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:26px}
.cols.one{grid-template-columns:1fr}
.col{min-width:0}
.col+.col{border-left:1px solid var(--hair);padding-left:26px}
.stem p{margin:0 0 .4em}
.stem p:last-child{margin-bottom:0}
.opts{list-style:none;margin:8px 0 0;padding:0}
.opts li{position:relative;padding-left:2.4em;margin:4px 0;font-size:15px;line-height:1.5}
.opts .lbl{position:absolute;left:0;top:0;font-family:"Noto Sans",Arial,sans-serif;font-weight:600;font-size:14px}
.tbl{border-collapse:collapse;width:100%;font-size:14px;margin:8px 0}
.tbl th,.tbl td{border:1px solid var(--rule);padding:4px 7px;text-align:left;vertical-align:top}
.tbl th{background:#f1f0ec}
.answers{margin-top:44px;border-top:3px double var(--rule);padding-top:14px}
.answers h2{font-size:24px;margin:0 0 6px}
.answers .status{font-size:14px;color:var(--muted);margin:0 0 10px}
.key-part{margin:18px 0 0}
.key-part h3{font-size:15.5px;margin:0 0 6px;border-bottom:1px solid var(--hair);padding-bottom:4px}
.keygrid{display:grid;grid-template-columns:repeat(6,1fr);gap:3px 12px;font-size:14px;font-variant-numeric:tabular-nums}
.keygrid b{font-family:"Noto Sans",Arial,sans-serif;font-weight:600;margin-right:5px;color:var(--muted)}
.footer{margin-top:36px;padding-top:12px;border-top:1px solid var(--hair);font-size:12.5px;color:var(--muted);text-align:center;font-family:"Noto Sans",Arial,sans-serif}
.index-list{list-style:none;padding:0;margin:0}
.index-list li{display:flex;justify-content:space-between;align-items:baseline;gap:6px 16px;flex-wrap:wrap;padding:11px 0;border-bottom:1px solid var(--hair)}
.index-list a{color:var(--ink);font-weight:700;text-decoration:underline;text-underline-offset:3px}
.index-list .m{font-size:13.5px;color:var(--muted);width:100%}
.exam-h{font-size:22px;margin:30px 0 2px;letter-spacing:.02em}
.year-h{font-family:"Noto Sans",Arial,sans-serif;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:20px 0 0;font-weight:600}
@media (max-width:640px){
 html{background:#fff}
 .sheet{margin:0;padding:22px 18px;box-shadow:none;max-width:none}
 .cover h1{font-size:28px}
 .cover .exam{font-size:18px}
 .toc{columns:1}
 .cols,.stim-cols{grid-template-columns:1fr;gap:12px}
 .col+.col{border-left:0;padding-left:0;border-top:1px dashed #b9b6ad;padding-top:12px}
 .keygrid{grid-template-columns:repeat(4,1fr)}
 .meta th{width:42%}
}
@page{size:A4;margin:14mm}
@media print{
 html,body{background:#fff}
 .sheet{box-shadow:none;margin:0;padding:0;max-width:none}
 .no-print{display:none!important}
 .part{break-before:page;margin-top:0}
 .q{break-inside:avoid}
 .answers{break-before:page}
}
"""


# ---------------------------------------------------------------- text helpers

def bi(en: str, hi: str) -> str:
    """Bilingual label: English followed by Hindi on a separate span."""
    return f'{html.escape(en)} <span lang="hi">/ {html.escape(hi)}</span>'


def inline(raw: str | None) -> str:
    """Escape one-line display text, keeping its line breaks."""
    if not raw:
        return ""
    text = html.escape(raw.strip(), quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return "<br>".join(line.rstrip() for line in text.split("\n"))


def block(raw: str | None) -> str:
    """Render multi-paragraph display text (paragraphs, poems, pipe tables)."""
    if not raw:
        return ""
    text = html.escape(raw.replace("\r", "").strip(), quote=False)
    out: list[str] = []
    for chunk in re.split(r"\n\s*\n", text):
        lines = [ln.rstrip() for ln in chunk.split("\n") if ln.strip()]
        if not lines:
            continue
        if all(ln.lstrip().startswith("|") for ln in lines):
            out.append(table_html(lines))
        else:
            body = "<br>".join(re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", ln) for ln in lines)
            out.append(f"<p>{body}</p>")
    return "".join(out)


def table_html(lines: list[str]) -> str:
    rows: list[list[str]] = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue  # markdown separator row
        rows.append(cells)
    if not rows:
        return ""
    head, body = rows[0], rows[1:]
    out = ['<table class="tbl"><thead><tr>']
    out += [f"<th>{c}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def option_label(opt: dict) -> str:
    return str(opt.get("original_label") or opt.get("position"))


def answer_text(app: dict) -> str:
    labels = (app.get("answer") or {}).get("correct_option_labels") or []
    return " & ".join(f"({lb})" for lb in labels) if labels else "—"


# ---------------------------------------------------------------- rendering

def stimulus_block(stim: dict, loc: str, rng_label: str) -> str:
    content = stim.get("contents", {})
    if loc == "mul":
        locales = [lc for lc in ("en", "hi") if lc in content]
    else:
        locales = [loc] if loc in content else list(content)[:1]
    kind = "Poem / कविता" if stim.get("stimulus_type") == "poem" else "Passage / गद्यांश"
    cols = []
    for lc in locales:
        c = content[lc]
        cols.append(f'<div class="col" lang="{lc}">{block(c.get("display_text") or c.get("display_stem"))}</div>')
    one = " one" if len(cols) == 1 else ""
    return (
        '<aside class="stim">'
        f'<div class="label">{kind} · {rng_label}</div>'
        f'<div class="stim-cols{one}">{"".join(cols)}</div>'
        "</aside>"
    )


def present_locales(q: dict) -> list[str]:
    """Locales in which this question is actually printed (en first, then hi)."""
    return [lc for lc in ("en", "hi") if lc in q["contents"]]


def question_block(app: dict, q: dict, loc: str) -> str:
    qno = app["question_number"]
    opts = sorted(q["options"], key=lambda o: o["position"])
    locales = present_locales(q) or [loc]

    def column(lc: str) -> str:
        c = q["contents"].get(lc, {})
        stem = block(c.get("display_stem") or c.get("display_text"))
        items = "".join(
            f'<li><span class="lbl">({html.escape(option_label(o))})</span> '
            f'{inline((o["contents"].get(lc) or {}).get("display_text"))}</li>'
            for o in opts
        )
        return f'<div class="col" lang="{lc}"><div class="stem">{stem}</div><ol class="opts">{items}</ol></div>'

    cols = "".join(column(lc) for lc in locales)
    one = " one" if len(locales) == 1 else ""
    return (
        f'<article class="q" id="q{qno}-{loc}">'
        f'<div class="q-no">{qno}.</div>'
        f'<div class="cols{one}">{cols}</div>'
        "</article>"
    )


def build_paper(p: dict, Q: dict, S: dict, apps: dict) -> tuple[str, str, dict]:
    exam = p["exam_code"]
    form = p["form_id"]
    secs = sorted(p["sections"], key=lambda s: s["order_index"])
    # A candidate answers each question number once; language sections exist in
    # two media (one is chosen), so count distinct question numbers.
    first_by_number: dict[int, dict] = {}
    for s in secs:
        for a in apps.get(s["form_section_id"], []):
            first_by_number.setdefault(a["question_number"], a)
    all_apps = list(first_by_number.values())
    official = bool(all_apps) and all(a["answer"].get("status") == "final" for a in all_apps)
    total_marks = sum(float(a.get("points") or 0) for a in all_apps)
    dt = datetime.strptime(p["exam_date"], "%Y-%m-%d")
    date_en = f"{dt.day} {dt.strftime('%B %Y')}"

    slot_roman: dict[str, str] = {}
    slot_locales: dict[str, set[str]] = defaultdict(set)
    for s in secs:
        slot_locales[s["slot_code"]].add(s["locale_code"])
    has_two_medium = any(len(v) > 1 for k, v in slot_locales.items() if k.startswith("language"))
    has_language = any(k.startswith("language") for k in slot_locales)

    def section_locales(s: dict) -> set[str]:
        found: set[str] = set()
        for a in apps.get(s["form_section_id"], []):
            found.update(present_locales(Q[a["question_id"]]) if a["question_id"] in Q else [])
        return found

    common_notes_en: list[str] = []
    common_notes_hi: list[str] = []
    for s in secs:
        if s["section_code"] not in COMMON_NAMES:
            continue
        name_en, name_hi = COMMON_NAMES[s["section_code"]]
        langs = section_locales(s)
        if langs == {"en", "hi"}:
            continue
        if langs == {"hi"}:
            common_notes_en.append(f"{name_en} is printed in Hindi only in this paper.")
            common_notes_hi.append(f"{name_hi} इस प्रश्न-पत्र में केवल हिन्दी में दिया गया है।")
        elif langs == {"en"}:
            common_notes_en.append(f"{name_en} is printed in English only in this paper.")
            common_notes_hi.append(f"{name_hi} इस प्रश्न-पत्र में केवल अंग्रेज़ी में दिया गया है।")

    parts: list[str] = []
    toc: list[str] = []
    key_parts: list[str] = []
    seen_stim: set[str] = set()
    problems: list[str] = []

    for s in secs:
        slot = s["slot_code"]
        if slot not in slot_roman:
            slot_roman[slot] = ROMAN[len(slot_roman)]
        roman = slot_roman[slot]
        loc = s["locale_code"]
        if s["section_code"] in COMMON_NAMES:
            en_t, hi_t = COMMON_NAMES[s["section_code"]]
            langs = section_locales(s)
            if langs == {"en", "hi"}:
                loc_note_en, loc_note_hi = "English & Hindi", "अंग्रेज़ी व हिन्दी"
            elif langs == {"hi"}:
                loc_note_en, loc_note_hi = "Hindi", "हिन्दी"
            else:
                loc_note_en, loc_note_hi = "English", "अंग्रेज़ी"
        else:
            en_t, hi_t = LANGUAGE_NAMES[(slot, loc)]
            loc_note_en, loc_note_hi = ("English medium", "अंग्रेज़ी माध्यम") if loc == "en" else ("Hindi medium", "हिन्दी माध्यम")
        sec_id = f"sec-{roman}-{loc}"
        start, end = s["question_start"], s["question_end"]
        rng_en = f"Questions {start}–{end}"
        rng_hi = f"प्रश्न {start}–{end}"
        toc.append(
            f'<li><a href="#{sec_id}">Part {roman} · {html.escape(en_t)}</a> '
            f'<span class="label">{start}–{end}</span></li>'
        )

        sec_apps = sorted(apps.get(s["form_section_id"], []), key=lambda a: a["question_number"])
        if len(sec_apps) != s.get("declared_question_count", len(sec_apps)):
            problems.append(f"{form} {roman} {loc}: {len(sec_apps)} rows vs declared {s.get('declared_question_count')}")

        parts.append(f'<section class="part" id="{sec_id}">')
        parts.append(
            '<header class="part-head">'
            f'<div class="label">Part {roman} · {html.escape(loc_note_en)} <span lang="hi">/ {html.escape(loc_note_hi)}</span></div>'
            f"<h2>{html.escape(en_t)}</h2>"
            f'<div class="part-hi" lang="hi">भाग {roman} · {html.escape(hi_t)}</div>'
            f'<div class="part-range">{rng_en} &nbsp;·&nbsp; <span lang="hi">{rng_hi}</span></div>'
            "</header>"
        )

        key_rows: list[str] = []
        for app in sec_apps:
            q = Q.get(app["question_id"])
            if q is None:
                problems.append(f"missing question {app['question_id']}")
                continue
            for sid in app.get("stimulus_ids") or []:
                if sid in seen_stim or sid not in S:
                    continue
                seen_stim.add(sid)
                refs = sorted({
                    r["question_number"] for r in S[sid].get("question_appearances", [])
                    if r.get("form_id") == form and r.get("locale_code") in (loc, "mul")
                })
                if not refs:
                    refs = [app["question_number"]]
                if len(refs) > 1:
                    rng = f"Questions {refs[0]}–{refs[-1]} · प्रश्न {refs[0]}–{refs[-1]}"
                else:
                    rng = f"Question {refs[0]} · प्रश्न {refs[0]}"
                parts.append(stimulus_block(S[sid], loc, rng))
            parts.append(question_block(app, q, loc))
            key_rows.append(
                f'<span><b>{app["question_number"]}</b>{html.escape(answer_text(app))}</span>'
            )
        parts.append("</section>")
        key_parts.append(
            '<div class="key-part">'
            f'<h3>Part {roman} · {html.escape(en_t)} <span lang="hi">/ {html.escape(hi_t)}</span> · {rng_en}</h3>'
            f'<div class="keygrid">{"".join(key_rows)}</div>'
            "</div>"
        )

    # Notices (bilingual).
    notices: list[str] = []
    if any(section_locales(s) == {"en", "hi"} for s in secs if s["section_code"] in COMMON_NAMES):
        notices.append(
            "<p>" + bi(
                "Common sections printed in both English and Hindi appear side by side, question by question.",
                "दोनों भाषाओं में छपे सामान्य खंडों में प्रत्येक प्रश्न अंग्रेज़ी और हिन्दी में साथ-साथ दिया गया है।",
            ) + "</p>"
        )
    for en_note, hi_note in zip(common_notes_en, common_notes_hi):
        notices.append(f"<p>{bi(en_note, hi_note)}</p>")
    if has_language and has_two_medium:
        notices.append(
            "<p>" + bi(
                "Language I and Language II are printed in both media. A candidate attempts only the language opted for.",
                "भाषा I और भाषा II दोनों माध्यमों में दिए गए हैं। अभ्यर्थी केवल चुनी हुई भाषा के प्रश्न हल करता है।",
            ) + "</p>"
        )
    elif has_language:
        notices.append(
            "<p>" + bi(
                "This booklet prints the language sections that are available in the repository database for this paper.",
                "यह पुस्तिका इस प्रश्न-पत्र के लिए डेटाबेस में उपलब्ध भाषा-खंड ही दिखाती है।",
            ) + "</p>"
        )
    if official:
        status_en = "Official final answer key."
        status_hi = "आधिकारिक अंतिम उत्तर-कुंजी।"
    else:
        status_en = "Provisional answer key from the repository database. It is not an official answer key."
        status_hi = "डेटाबेस स्रोत की अनंतिम उत्तर-कुंजी। यह आधिकारिक उत्तर-कुंजी नहीं है।"
    notices.append(f"<p>{bi(status_en, status_hi)}</p>")

    marks = int(total_marks) if float(total_marks).is_integer() else total_marks
    meta_rows = [
        (bi("Examination", "परीक्षा"), f"{html.escape(p.get('exam_name') or exam)}"),
        (bi("Exam date", "परीक्षा तिथि"), date_en),
        (bi("Paper / Set", "प्रश्न-पत्र / सेट"), f"Paper I · Set {html.escape(p['set_code'])}"),
    ]
    if p.get("booklet_code"):
        meta_rows.append((bi("Booklet code", "बुकलेट कोड"), html.escape(p["booklet_code"])))
    meta_rows.append((bi("Total questions", "कुल प्रश्न"), str(len(all_apps))))
    meta_rows.append((bi("Maximum marks", "अधिकतम अंक"), str(marks)))
    if p.get("duration_minutes"):
        meta_rows.append((bi("Duration", "अवधि"), f"{p['duration_minutes']} minutes / मिनट"))
    neg = p.get("negative_marking")
    if neg is not None:
        meta_rows.append((bi("Negative marking", "ऋणात्मक अंकन"), "None / नहीं" if not neg else str(neg)))
    meta_rows.append((bi("Answer key", "उत्तर-कुंजी"), bi(
        "Official final" if official else "Provisional", "आधिकारिक अंतिम" if official else "अनंतिम"
    )))
    meta_html = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in meta_rows)

    ex_hi = EXAM_HINDI.get(exam, "")
    cover = (
        '<header class="cover">'
        f'<div class="label">{html.escape(p.get("exam_name") or exam)}</div>'
        f'<div class="exam-hi" lang="hi">{html.escape(ex_hi)}</div>'
        f"<h1>Paper I</h1>"
        f'<p class="sub">Previous Year Question Paper · {html.escape(exam)} {dt.year}</p>'
        f'<p class="sub-hi" lang="hi">पूर्व वर्ष प्रश्न-पत्र · प्रश्न-पत्र I</p>'
        f'<table class="meta">{meta_html}</table>'
        "</header>"
    )
    notice_html = f'<section class="notice no-print-keep">{"".join(notices)}</section>'
    toc_html = f'<nav aria-label="Parts"><ul class="toc">{"".join(toc)}</ul></nav>'
    answers_html = (
        '<section class="answers" id="answers">'
        f'<h2>{bi("Answer Key", "उत्तर-कुंजी")}</h2>'
        f'<p class="status">{bi(status_en, status_hi)}</p>'
        f'{"".join(key_parts)}'
        "</section>"
    )
    footer = (
        '<div class="footer">'
        f"{html.escape(exam)} Paper I · Set {html.escape(p['set_code'])} · {date_en} · "
        "Built from data/xtet-question-bank.json"
        "</div>"
    )
    title = f"{exam} Paper I · {date_en} · Set {p['set_code']}"
    body = (
        '<div class="sheet">'
        '<button class="print-btn no-print" onclick="window.print()">Print / Save as PDF · प्रिंट / PDF</button>'
        f"{cover}{notice_html}{toc_html}{''.join(parts)}{answers_html}{footer}"
        "</div>"
    )
    doc = page(title, body)
    summary = {
        "exam": exam, "year": dt.year, "date": date_en, "set": p["set_code"],
        "official": official, "questions": len(all_apps),
        "parts": [(roman, en) for roman, en in [(v, k) for k, v in slot_roman.items()]],
    }
    return doc, make_name(exam, dt, p["set_code"]), dict(summary, problems=problems)


def make_name(exam: str, dt: datetime, set_code: str) -> str:
    return f"{exam.lower()}-{dt.year}-{dt.strftime('%b').lower()}-set-{set_code.lower()}.html"


def page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n"
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;700'
        "&family=Noto+Serif+Devanagari:wght@400;700"
        '&family=Noto+Sans:wght@400;600;700&display=swap" rel="stylesheet">\n'
        f"<style>{CSS}</style>\n"
        "</head>\n<body>\n"
        f"{body}\n"
        "</body>\n</html>\n"
    )


def build_index(entries: list[dict]) -> str:
    rows: list[str] = []
    for exam in ("CTET", "UTET"):
        items = sorted((e for e in entries if e["exam"] == exam), key=lambda e: (e["year"], e["date_sort"]))
        if not items:
            continue
        rows.append(f'<h2 class="exam-h">{html.escape(exam)} · Paper I</h2>')
        rows.append(f'<div class="label" style="margin-top:2px">{bi(EXAM_HINDI[exam], "प्रश्न-पत्र I")}</div>')
        by_year: dict[int, list[dict]] = defaultdict(list)
        for e in items:
            by_year[e["year"]].append(e)
        for year in sorted(by_year):
            rows.append(f'<div class="year-h">{year}</div><ul class="index-list">')
            for e in by_year[year]:
                key = "Official final key" if e["official"] else "Provisional key"
                rows.append(
                    f'<li><a href="{e["path"]}">{html.escape(exam)} Paper I · Set {html.escape(e["set"])} · {html.escape(e["date"])}</a>'
                    f'<span class="m">{e["questions"]} questions · {key} · '
                    f'{html.escape(", ".join(e["parts"]))}</span></li>'
                )
            rows.append("</ul>")
    body = (
        '<div class="sheet">'
        '<header class="cover">'
        '<div class="label">Previous Year Question Papers</div>'
        '<h1>CTET &amp; UTET</h1>'
        '<p class="sub">Paper I · year-wise booklets · English and Hindi</p>'
        '<p class="sub-hi" lang="hi">पूर्व वर्ष प्रश्न-पत्र · वर्षवार पुस्तिकाएँ · अंग्रेज़ी व हिन्दी</p>'
        "</header>"
        f"{''.join(rows)}"
        '<div class="footer">Built from data/xtet-question-bank.json · run pyq-booklets/build_booklets.py to regenerate</div>'
        "</div>"
    )
    return page("CTET & UTET Paper I — Previous Year Question Papers", body)


def main() -> None:
    db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    Q = {q["question_id"]: q for q in db["questions"]}
    S = {s["stimulus_id"]: s for s in db["stimuli"]}
    apps: dict[str, list[dict]] = defaultdict(list)
    for a in db["appearances"]:
        apps[a["form_section_id"]].append(a)

    for sub in ("ctet", "utet"):
        for old in (HERE / sub).glob("*.html"):
            old.unlink()
    (HERE / "index.html").unlink(missing_ok=True)

    entries: list[dict] = []
    for p in db["papers"]:
        doc, name, info = build_paper(p, Q, S, apps)
        folder = HERE / p["exam_code"].lower()
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(doc, encoding="utf-8")
        dt = datetime.strptime(p["exam_date"], "%Y-%m-%d")
        entries.append({
            "exam": p["exam_code"], "year": info["year"], "date": info["date"],
            "date_sort": p["exam_date"], "set": info["set"], "official": info["official"],
            "questions": info["questions"], "path": f"{p['exam_code'].lower()}/{name}",
            "parts": [v for v in dict.fromkeys(
                COMMON_NAMES[s["section_code"]][0] if s["section_code"] in COMMON_NAMES
                else LANGUAGE_NAMES[(s["slot_code"], s["locale_code"])][0]
                for s in sorted(p["sections"], key=lambda s: s["order_index"])
            )],
        })
        status = "official" if info["official"] else "provisional"
        print(f"{p['exam_code']} {info['date']} set {info['set']}: {info['questions']} questions, {status} key -> {folder.name}/{name}")
        for prob in info["problems"]:
            print(f"  WARNING: {prob}")

    (HERE / "index.html").write_text(build_index(entries), encoding="utf-8")
    print(f"index -> {HERE.name}/index.html")


if __name__ == "__main__":
    main()
