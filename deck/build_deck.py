#!/usr/bin/env python3
"""Builds deck/backstagecon-na-2026-v2.pptx from original/backstagecon-na-2026.pptx + content.json + evidence/*.png.
Slides 1-3 untouched (speaker edits those). Keeps selected original slides, rewrites text in place,
adds NEW/SHOT slides on the deck's own layouts, reorders via sldIdLst."""
import json, copy, os, sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "original", "backstagecon-na-2026.pptx")
OUT = os.path.join(HERE, "backstagecon-na-2026-v2.pptx")
EVID = os.path.join(HERE, "..", "evidence")
content = {s["n"]: s for s in json.load(open(os.path.join(HERE, "content.json")))["slides"]}

prs = Presentation(SRC)
SW, SH = prs.slide_width, prs.slide_height
orig = list(prs.slides)  # index 0 = slide 1
L_TITLE_CONTENT = prs.slide_layouts[0]   # 'Title and Content'
L_TITLE_ONLY = prs.slide_layouts[0]      # same layout as the EU content slides; body placeholder removed per slide

# ---- style (matches the CNCF template: dark text on white, teal-ish accent) ----
INK = RGBColor(0x1F, 0x29, 0x37); MUTED = RGBColor(0x5B, 0x66, 0x76); ACCENT = RGBColor(0x00, 0x7A, 0xA3)
CODE_BG = RGBColor(0x1E, 0x1E, 0x24); CODE_FG = RGBColor(0xE6, 0xED, 0xF3)
FONT = "Arial"; MONO = "Courier New"

def set_title(slide, text):
    t = slide.shapes.title
    if t is None:
        for sh in slide.placeholders:
            if sh.placeholder_format.type in (1, 3):  # TITLE, CENTER_TITLE
                t = sh; break
    if t is None:
        return
    tf = t.text_frame
    p = tf.paragraphs[0]
    for r in p.runs[1:]: r._r.getparent().remove(r._r)
    if p.runs: p.runs[0].text = text
    else: p.add_run().text = text
    for extra in tf.paragraphs[1:]: extra._p.getparent().remove(extra._p)

def body_placeholder(slide):
    for sh in slide.placeholders:
        if sh.placeholder_format.type == 7 or sh.placeholder_format.idx == 1:  # BODY
            return sh
    return None

def fill_body(ph, lines, size=20):
    tf = ph.text_frame; tf.word_wrap = True
    first = tf.paragraphs[0]
    for extra in tf.paragraphs[1:]: extra._p.getparent().remove(extra._p)
    for i, line in enumerate(lines):
        p = first if i == 0 else tf.add_paragraph()
        for r in list(p.runs): r._r.getparent().remove(r._r)
        bold = line.startswith("**") and line.endswith("**")
        r = p.add_run(); r.text = line.strip("*") if bold else line
        r.font.size = Pt(size); r.font.bold = bold; r.font.name = FONT; r.font.color.rgb = INK
        p.space_after = Pt(8)

def add_textbox(slide, x, y, w, h, lines, size=16, color=INK, bold_first=False, mono=False, bg=None, anchor_top=True):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.15); tf.margin_top = tf.margin_bottom = Inches(0.1)
    if bg is not None:
        tb.fill.solid(); tb.fill.fore_color.rgb = bg
    tf.vertical_anchor = MSO_ANCHOR.TOP if anchor_top else MSO_ANCHOR.MIDDLE
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        bold = (bold_first and i == 0) or (line.startswith("**") and line.endswith("**"))
        r = p.add_run(); r.text = line.strip("*") if (line.startswith("**") and line.endswith("**")) else line
        r.font.size = Pt(size); r.font.name = MONO if mono else FONT; r.font.bold = bold; r.font.color.rgb = color
        p.space_after = Pt(2 if mono else 6)
    return tb

def add_table(slide, x, y, w, h, header, rows, size=13):
    shp = slide.shapes.add_table(len(rows) + 1, len(header), x, y, w, h)
    tbl = shp.table
    for c, hd in enumerate(header):
        cell = tbl.cell(0, c); cell.text = hd
        for p in cell.text_frame.paragraphs:
            for r in p.runs: r.font.bold = True; r.font.size = Pt(size); r.font.name = FONT; r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.fill.solid(); cell.fill.fore_color.rgb = ACCENT
    for ri, row in enumerate(rows, 1):
        for c, val in enumerate(row):
            cell = tbl.cell(ri, c); cell.text = str(val)
            for p in cell.text_frame.paragraphs:
                for r in p.runs: r.font.size = Pt(size); r.font.name = FONT; r.font.color.rgb = INK
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(0xF4, 0xF6, 0xF8) if ri % 2 else RGBColor(0xFF, 0xFF, 0xFF)
    return shp

def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text or ""

def new_slide(layout):
    return prs.slides.add_slide(layout)

def build_new(spec):
    s = new_slide(L_TITLE_ONLY)
    set_title(s, spec["title"])
    # remove any stray non-title placeholders
    for ph in list(s.placeholders):
        if ph.placeholder_format.type not in (1, 3): ph._element.getparent().remove(ph._element)
    body = spec.get("body") or []; code = spec.get("code"); table = spec.get("table")
    left_w = SW - Inches(1.2)
    top = Inches(1.55)
    if code and body:
        add_textbox(s, Inches(0.6), top, Inches(5.6), SH - top - Inches(0.6), body, size=16)
        add_textbox(s, Inches(6.5), top, SW - Inches(7.1), SH - top - Inches(0.6), code.splitlines(), size=12, color=CODE_FG, mono=True, bg=CODE_BG)
    elif code:
        add_textbox(s, Inches(0.6), top, left_w, SH - top - Inches(0.6), code.splitlines(), size=13, color=CODE_FG, mono=True, bg=CODE_BG)
    elif table:
        if body: add_textbox(s, Inches(0.6), top, left_w, Inches(0.8), body, size=16); top += Inches(0.9)
        rows = table["rows"]; add_table(s, Inches(0.6), top, left_w, Inches(0.45) * (len(rows) + 1), table["header"], rows, size=13 if len(table["header"]) > 3 else 14)
    else:
        add_textbox(s, Inches(0.6), top, left_w, SH - top - Inches(0.6), body, size=20 if len(body) <= 4 else 18)
    set_notes(s, spec["notes"]); return s

def build_shot(spec, img):
    s = new_slide(L_TITLE_ONLY)
    set_title(s, spec["title"])
    for ph in list(s.placeholders):
        if ph.placeholder_format.type not in (1, 3): ph._element.getparent().remove(ph._element)
    top = Inches(1.45); maxw = SW - Inches(1.0); maxh = SH - top - Inches(1.15)
    if img and os.path.exists(img):
        from PIL import Image
        iw, ih = Image.open(img).size; scale = min(maxw / iw, maxh / ih)
        w, h = int(iw * scale), int(ih * scale)
        s.shapes.add_picture(img, int((SW - w) / 2), top, w, h)
    else:
        add_textbox(s, Inches(0.6), top, maxw, maxh, [f"[screenshot missing: {os.path.basename(img) if img else '?'}]"], size=18, color=MUTED)
    if spec.get("caption"):
        add_textbox(s, Inches(0.6), SH - Inches(1.05), maxw, Inches(0.85), [spec["caption"]], size=13, color=MUTED)
    set_notes(s, spec["notes"]); return s

SHOTS = {16: "tempo-waterfall-layer0.jpg", 21: "dash-adoption.jpg", 22: "dash-friction.jpg", 23: "dash-plugins.jpg", 25: "pyroscope-flamegraph.jpg"}
KEEP = {6: 5, 7: 7, 8: 17, 9: 23, 10: 24, 14: 15, 24: 14, 27: 27, 31: 28}   # new n -> original slide number
ORDER = []  # list of slide objects in final order
ORDER_EXTRA_AFTER = {}
ORDER += [orig[0], orig[1], orig[2]]
for n in range(4, 32):
    spec = content[n]; kind = spec["kind"]
    if kind == "KEEP-REWRITE":
        s = orig[3]; set_title(s, spec["title"]); ph = body_placeholder(s)
        if ph is not None: fill_body(ph, spec["body"], size=22)
        set_notes(s, spec["notes"]); ORDER.append(s)
    elif kind == "KEEP":
        s = orig[KEEP[n] - 1]
        if n == 7:  # orig 9 follows: the "siloed view" diagram from Amsterdam
            extra = orig[8]; set_notes(extra, "[0:20] And this is the picture we drew last time: every plugin logs and counts its own way, nothing correlates, nobody sees a request end to end. We fixed the backend half of that in Amsterdam. Hold the thought: fragmented is also what adoption data looks like today.")
            ORDER_EXTRA_AFTER[id(s)] = extra
        if n == 10 and spec.get("body"):   # callout on the built-in meters slide
            add_textbox(s, Inches(7.0), Inches(5.6), Inches(5.8), Inches(1.4), spec["body"], size=15, color=ACCENT, bold_first=True)
        set_notes(s, spec["notes"]); ORDER.append(s)
    elif kind == "NEW":
        ORDER.append(build_new(spec))
    elif kind == "SHOT":
        ORDER.append(build_shot(spec, os.path.join(EVID, SHOTS.get(n, ""))))

# splice extra kept slides
_o = []
for sl in ORDER:
    _o.append(sl)
    if id(sl) in ORDER_EXTRA_AFTER: _o.append(ORDER_EXTRA_AFTER[id(sl)])
ORDER = _o
# ---- reorder + drop unused originals ----
sldIdLst = prs.slides._sldIdLst
rid_to_el = {el.rId: el for el in list(sldIdLst)}
part_to_rid = {prs.part.related_part(rid): rid for rid in rid_to_el}
keep_rids = [part_to_rid[s.part] for s in ORDER]
for el in list(sldIdLst):
    sldIdLst.remove(el)
for rid in keep_rids:
    sldIdLst.append(rid_to_el[rid])
for rid in rid_to_el:
    if rid not in keep_rids:
        prs.part.drop_rel(rid)
prs.save(OUT)
print("wrote", OUT, "slides:", len(prs.slides))
