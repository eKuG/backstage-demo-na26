#!/usr/bin/env python3
"""Builds backstagecon-na-2026.pptx on the BackstageCon NA 2026 branded template (ArgoCon-deck style).

Template facts (template/backstagecon-template.pptx): 13.33x7.5in, Arial, no placeholders on branded layouts.
  L 'Title and Content' = white body + teal header bar (0-1.02in) + Backstage|CON logo top-right (9.42-12.98in)
  L 'Title Slide'       = full teal gradient + logo top-right
  L '1_Title Slide'     = full gradient (+ a stray PromCon logo we remove) -> dark statement slides
  L '2_Title Slide'     = gradient + big centred logo -> closing
Speaker notes come from content.json (written from PLAN.md/NOTES.md); screenshots from ../evidence.
"""
import os, json
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "template", "backstagecon-template.pptx")
OUT = os.path.join(HERE, "backstagecon-na-2026.pptx")
EVID = os.path.join(HERE, "..", "evidence")
EU = os.path.join(HERE, "original", "media")
C = {s["n"]: s for s in json.load(open(os.path.join(HERE, "content.json")))["slides"]}
def N(*ns): return "\n".join(C[n]["notes"] for n in ns)

# ---- palette: template teal + warm accent --------------------------------------------------------
TEAL_DK = RGBColor(0x0F, 0x4F, 0x47); TEAL = RGBColor(0x1E, 0x9E, 0x88); TEAL_LT = RGBColor(0xE6, 0xF4, 0xF0)
ORANGE = RGBColor(0xE8, 0x6A, 0x33); ORANGE_LT = RGBColor(0xFD, 0xEB, 0xE2); AMBER = RGBColor(0xFF, 0xB8, 0x5C)
INK = RGBColor(0x1F, 0x29, 0x37); MUTED = RGBColor(0x5B, 0x66, 0x76); LINE = RGBColor(0xD3, 0xDE, 0xDB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF); GREEN = RGBColor(0x2E, 0x8B, 0x57); RED = RGBColor(0xC0, 0x39, 0x2B); RED_LT = RGBColor(0xFB, 0xE7, 0xE4)
CODE_BG = RGBColor(0x14, 0x24, 0x22); CODE_FG = RGBColor(0xE6, 0xF0, 0xED); CODE_HL = AMBER; CODE_DIM = RGBColor(0x8F, 0xA8, 0xA2)
FONT, MONO = "Arial", "Courier New"

prs = Presentation(SRC)
SW, SH = prs.slide_width, prs.slide_height
L = {l.name: l for l in prs.slide_layouts}
L_CONTENT, L_TITLE, L_DARK, L_CLOSE = L["Title and Content"], L["Title Slide"], L["1_Title Slide"], L["2_Title Slide"]
for sh in list(L_DARK.shapes):                 # stray PromCon logo top-right on the dark layout
    if sh.shape_type == 13 and sh.width < Inches(5):
        sh._element.getparent().remove(sh._element)
_lst = prs.slides._sldIdLst                    # drop the template's sample slides
for el in list(_lst):
    prs.part.drop_rel(el.rId); _lst.remove(el)
I = Inches

# ---- primitives (same vocabulary as the ArgoCon deck) -------------------------------------------
def _runs(p, parts, size, color, bold=False, italic=False, mono=False):
    if isinstance(parts, str): parts = [(parts, {})]
    for txt, o in parts:
        r = p.add_run(); r.text = txt
        f = r.font; f.name = MONO if o.get("mono", mono) else FONT
        f.size = Pt(o.get("size", size)); f.bold = o.get("bold", bold); f.italic = o.get("italic", italic)
        f.color.rgb = o.get("color", color)

def text(slide, x, y, w, h, lines, size=16, color=INK, bold=False, italic=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, bg=None, mono=False, space_after=6, margin=0.1, line_spacing=None, bullets=False):
    tb = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = I(margin); tf.margin_top = tf.margin_bottom = I(min(margin, 0.08))
    tf.vertical_anchor = anchor
    if bg is not None:
        tb.fill.solid(); tb.fill.fore_color.rgb = bg
    if isinstance(lines, str): lines = [lines]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space_after)
        if line_spacing: p.line_spacing = line_spacing
        if bullets:
            pPr = p._p.get_or_add_pPr(); pPr.set("marL", str(int(I(0.25)))); pPr.set("indent", str(-int(I(0.25))))
            pPr.append(pPr.makeelement(qn("a:buChar"), {"char": "•"}))
        _runs(p, line, size, color, bold, italic, mono)
    return tb

def rect(slide, x, y, w, h, fill=None, line=None, line_w=1.0, rounded=True, radius=0.12):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, I(x), I(y), I(w), I(h))
    if rounded: shp.adjustments[0] = radius
    if fill is None: shp.fill.background()
    else: shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None: shp.line.fill.background()
    else: shp.line.color.rgb = line; shp.line.width = Pt(line_w)
    sp = shp._element.spPr; sp.append(sp.makeelement(qn("a:effectLst"), {}))
    shp.text_frame.text = ""
    return shp

def chip(slide, x, y, w, h, label, fill=TEAL, color=WHITE, size=14, bold=True, sub=None, sub_size=11, radius=0.25, line=None):
    shp = rect(slide, x, y, w, h, fill=fill, line=line, radius=radius)
    tf = shp.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = I(0.08); tf.margin_top = tf.margin_bottom = I(0.03)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; _runs(p, label, size, color, bold)
    if sub:
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER; _runs(p2, sub, sub_size, color, False)
    return shp

def circle(slide, x, y, d, label, fill=ORANGE, color=WHITE, size=14):
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, I(x), I(y), I(d), I(d))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill; shp.line.fill.background()
    sp = shp._element.spPr; sp.append(sp.makeelement(qn("a:effectLst"), {}))
    tf = shp.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE; p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _runs(p, label, size, color, True)
    return shp

def arrow(slide, x1, y1, x2, y2, color=MUTED, w=1.75, dashed=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y1), I(x2), I(y2))
    c.line.color.rgb = color; c.line.width = Pt(w)
    ln = c.line._get_or_add_ln()
    if dashed: ln.append(ln.makeelement(qn("a:prstDash"), {"val": "dash"}))
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return c

def hline(slide, x, y, w, color=LINE, pt=1.0):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x), I(y), I(x + w), I(y))
    c.line.color.rgb = color; c.line.width = Pt(pt); return c

def picture(slide, path, x, y, w, h, caption=None, frame=True):
    if os.path.exists(path):
        iw, ih = Image.open(path).size; s = min(I(w) / iw, I(h) / ih)
        pw, ph = int(iw * s), int(ih * s); px, py = int(I(x) + (I(w) - pw) / 2), int(I(y))
        if frame:
            rect(slide, px / 914400 - 0.04, py / 914400 - 0.04, pw / 914400 + 0.08, ph / 914400 + 0.08, fill=WHITE, line=LINE, radius=0.03)
        pic = slide.shapes.add_picture(path, px, py, pw, ph); bottom = (py + ph) / 914400
    else:
        rect(slide, x, y, w, h, fill=TEAL_LT, line=LINE, radius=0.03)
        text(slide, x, y, w, h, [f"[screenshot: {os.path.basename(path)}]"], size=14, color=MUTED, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        pic = None; bottom = y + h
    if caption:
        text(slide, x, bottom + 0.08, w, 0.5, caption, size=12, color=MUTED, align=PP_ALIGN.CENTER)
    return pic

def ev(name): return os.path.join(EVID, name)
def eu(name): return os.path.join(EU, name)

def table(slide, x, y, w, header, rows, col_w=None, size=12, row_h=0.5, header_fill=TEAL_DK):
    shp = slide.shapes.add_table(len(rows) + 1, len(header), I(x), I(y), I(w), I(row_h * (len(rows) + 1)))
    tbl = shp.table
    if col_w:
        for i, cw in enumerate(col_w): tbl.columns[i].width = I(cw)
    for c, hd in enumerate(header):
        cell = tbl.cell(0, c); cell.fill.solid(); cell.fill.fore_color.rgb = header_fill
        tf = cell.text_frame; tf.paragraphs[0].text = ""; _runs(tf.paragraphs[0], hd, size, WHITE, True)
        cell.margin_left = cell.margin_right = I(0.08); cell.margin_top = cell.margin_bottom = I(0.04)
    for r, row in enumerate(rows, 1):
        for c, val in enumerate(row):
            cell = tbl.cell(r, c); cell.fill.solid(); cell.fill.fore_color.rgb = TEAL_LT if r % 2 else WHITE
            tf = cell.text_frame; tf.word_wrap = True; tf.paragraphs[0].text = ""
            _runs(tf.paragraphs[0], val, size, INK, bold=(c == 0))
            cell.margin_left = cell.margin_right = I(0.08); cell.margin_top = cell.margin_bottom = I(0.04)
    return shp

def code(slide, x, y, w, h, lines, size=11.5, hl=()):
    tb = text(slide, x, y, w, h, [""], size=size, bg=CODE_BG, margin=0.18)
    tf = tb.text_frame; tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(0); p.line_spacing = 1.05
        col = CODE_HL if i in hl else (CODE_DIM if line.strip().startswith("#") else CODE_FG)
        _runs(p, line if line else " ", size, col, bold=(i in hl), mono=True)
    return tb

def notes(slide, txt): slide.notes_slide.notes_text_frame.text = txt.strip()

def stat(slide, x, y, w, number, label, color=ORANGE, nsize=54, lsize=13, lcolor=MUTED):
    text(slide, x, y, w, 0.95, number, size=nsize, color=color, bold=True, margin=0, space_after=0)
    text(slide, x, y + 0.95, w, 0.9, label, size=lsize, color=lcolor, margin=0, space_after=0)

def source(slide, txt): text(slide, 0.4, 7.05, 12.5, 0.35, txt, size=9.5, color=MUTED, margin=0, space_after=0)

def callout(slide, x, y, w, h, head, body, fill=TEAL_LT, head_color=TEAL_DK, size=11.5):
    rect(slide, x, y, w, h, fill=fill)
    text(slide, x + 0.2, y + 0.08, w - 0.4, 0.45, head, size=15, color=head_color, bold=True, space_after=0)
    text(slide, x + 0.2, y + 0.5, w - 0.4, h - 0.6, body, size=size, color=INK, space_after=0)

def content_slide(title):
    s = prs.slides.add_slide(L_CONTENT)
    text(s, 0.3, -0.15, 9.0, 1.36, title, size=26, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    return s

def dark_slide(): return prs.slides.add_slide(L_DARK)

# =================================================================================================
# 1. TITLE
s = prs.slides.add_slide(L_TITLE)
text(s, 0.69, 1.75, 11.9, 1.2, "Treating Backstage Like a Product", size=46, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
text(s, 0.72, 2.95, 11.5, 0.8, "Observability with OpenTelemetry", size=32, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
text(s, 0.8, 4.05, 11.5, 0.6, "Ekansh Gupta", size=28, color=WHITE, italic=True, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
text(s, 0.8, 4.6, 11.5, 0.5, "Software Engineer, Bindplane (Dynatrace)", size=18, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
text(s, 0.8, 6.3, 11.5, 0.5, "Everything in this talk runs on this laptop.", size=16, color=AMBER, italic=True, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
notes(s, """[0:00] Hi, I'm Ekansh. I build telemetry pipelines at Bindplane, which is part of Dynatrace now. Last March, in Amsterdam, Shivay and I stood on the BackstageCon stage and instrumented Backstage with OpenTelemetry. This talk is the sequel, and it starts with the question we could not answer back then.
Everything you will see runs on this laptop: a Backstage 1.56, a Collector, and a kernel. If it breaks it is mine, not the conference Wi-Fi. Before any slides, I want to read you three numbers from the dashboard that has been running during lunch.""")

# 2. HOOK (dark): three numbers
s = dark_slide()
text(s, 0.9, 0.85, 11.6, 0.9, "Before any slides, three numbers from a running portal.", size=36, color=WHITE, bold=True, space_after=0)
for x, num, lab in [(0.9, "100%", "of runs of one template fail.\nEvery single one."),
                    (5.0, "104", "lookups in one hour of catalog entities\nthat do not exist."),
                    (9.1, "307", "TechDocs pages requested in one hour\nthat were never built.")]:
    rect(s, x, 2.1, 3.6, 2.55, fill=None, line=RGBColor(0x7F, 0xC8, 0xB9), radius=0.15)
    stat(s, x + 0.25, 2.25, 3.2, num, lab, color=AMBER, nsize=56, lsize=14, lcolor=WHITE)
text(s, 0.9, 5.15, 11.6, 0.8, [[("Backstage emitted ", {}), ("none", {"color": AMBER}), (" of these numbers. Everything on that dashboard came from OpenTelemetry.", {})]], size=24, color=WHITE, bold=True, space_after=0)
text(s, 0.9, 6.1, 11.6, 0.6, "Let's build it again from zero, in twenty minutes, on this laptop.", size=18, color=WHITE, italic=True, space_after=0)
notes(s, N(11))

# 3. AMSTERDAM
s = content_slide("Amsterdam, March 2026: 'is it up?'")
picture(s, eu("s09_179.png"), 0.4, 1.4, 6.9, 3.85, caption="The picture we drew last time: every plugin logs and counts its own way, nothing correlates")
x = 7.6
for head, body in [("instrumentation.js, loaded with --require", "NodeSDK + auto-instrumentations before any other import"),
                   ("Twelve built-in meters", "catalog_entities_count, scaffolder.task.duration, backend_tasks..."),
                   ("A forced 500, a trace, an alert", "The 'plugin returned 500, here is the span' demo")]:
    rect(s, x, 1.4 + 0, 5.35, 0.0001)  # spacer no-op
for i, (head, body) in enumerate([("instrumentation.js + --require", "NodeSDK and auto-instrumentations, loaded before any other import"),
                                  ("Twelve built-in meters", "catalog_entities_count, scaffolder.task.duration, backend_tasks.*"),
                                  ("A forced 500, a trace, an alert", "'the plugin returned 500, here is the span' in Grafana")]):
    y = 1.4 + i * 1.08
    circle(s, 7.6, y + 0.1, 0.42, str(i + 1), fill=TEAL, size=14)
    text(s, 8.15, y, 4.8, 0.95, [[(head + "  ", {"bold": True}), (body, {"color": MUTED, "size": 12.5})]], size=14, color=INK, space_after=0)
rect(s, 0.4, 5.75, 12.55, 1.15, fill=ORANGE_LT)
text(s, 0.65, 5.8, 12.1, 1.05, [[("The question we could not answer: ", {"bold": True, "color": ORANGE}), ("is anyone using the portal, where do they get stuck, and which plugin burns the budget? That dashboard could tell you a request failed. It could not tell you whether the portal was worth running.", {})]], size=15, color=INK, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
notes(s, N(5, 8))

# 4. WHAT BACKSTAGE EMITS NATIVELY
s = content_slide("What Backstage emits natively: one slide")
meters = ["# catalog", "catalog_entities_count{kind}", "catalog_registered_locations_count", "catalog_relations_count",
          "catalog.processed.entities.count{result}", "catalog.processing.duration", "catalog.processing.queue.delay", "catalog.stitching.*",
          "# scaffolder", "scaffolder.task.count{template,result}", "scaffolder.task.duration", "scaffolder.step.count / .duration",
          "# scheduler", "backend_tasks.task.runs.count / .duration"]
code(s, 0.4, 1.4, 6.3, 5.0, meters, size=12.5, hl=(1, 9))
text(s, 0.4, 6.5, 6.3, 0.4, "Backstage 1.56; all via @opentelemetry/api; nothing starts the SDK for you.", size=11, color=MUTED, space_after=0)
text(s, 7.1, 1.4, 5.85, 0.5, "Nothing for the things a product team asks about", size=16, color=TEAL_DK, bold=True, space_after=0)
for i, (lab, sub) in enumerate([("HTTP per plugin", "no request count, no latency, no error ratio"),
                                ("Search", "no query count, no zero-result rate"),
                                ("TechDocs", "no page views, no 404s"),
                                ("Permissions", "allow / deny decisions are not metered"),
                                ("Users", "no sign-ins, no active users, no sessions")]):
    y = 2.0 + i * 0.72
    circle(s, 7.15, y + 0.06, 0.4, "✕", fill=RED, size=13)
    text(s, 7.7, y, 5.2, 0.7, [[(lab + "  ", {"bold": True}), (sub, {"color": MUTED, "size": 12})]], size=14, color=INK, space_after=0)
rect(s, 7.1, 5.75, 5.85, 1.15, fill=TEAL_LT)
text(s, 7.3, 5.8, 5.5, 1.05, [[("The wiring itself: ", {"bold": True, "color": TEAL_DK}), ("Mithun Banerjee's lightning talk at 5:15 today is the copy-paste version of instrumentation.js. I am skipping it. Today is about what to do with the data.", {})]], size=13, color=INK, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
notes(s, N(10, 9))

# 5. THESIS (dark)
s = dark_slide()
text(s, 0.9, 0.8, 11.6, 1.5, [[("A portal is a ", {}), ("product", {"color": AMBER}), (".", {})], "Measure it like one."], size=44, color=WHITE, bold=True, space_after=2)
cards = [("Adoption", "Who uses it, for what, how often. Active users, page views per plugin, templates run, hours saved."),
         ("Friction", "Where people get stuck. Failed template runs, zero-result searches, links to entities that no longer exist."),
         ("Reliability per plugin", "Which plugin burns the error budget. RED per plugin, slowest routes, the database behind each one.")]
x = 0.9
for head, body in cards:
    rect(s, x, 2.75, 3.75, 2.55, fill=None, line=RGBColor(0x7F, 0xC8, 0xB9), radius=0.15)
    text(s, x + 0.25, 2.9, 3.3, 0.6, head, size=22, color=AMBER, bold=True, space_after=0)
    text(s, x + 0.25, 3.55, 3.3, 1.7, body, size=14, color=WHITE, space_after=0)
    x += 3.93
text(s, 0.9, 5.65, 11.6, 1.3, [
    [("Spotify measures time to the tenth merged PR and search success. ", {}), ("Insights", {"bold": True}), (" and Red Hat's ", {}), ("Adoption Insights", {"bold": True}), (" exist, but they are plugins with their own database.", {})],
    [("Today: the same answers from ", {}), ("OpenTelemetry you already run", {"bold": True, "color": AMBER}), (", with no new database and no product metric emitted by Backstage.", {})],
], size=16, color=WHITE, space_after=6)
notes(s, N(12))

# 6. FOUR LAYERS
s = content_slide("Four layers, each gives what the others cannot")
layers = [("Kernel", "OBI, eBPF", "Traces with Postgres per table, RED, Node event loop, GC and heap, network flows. Works on plugins you do not own.", "one privileged container\nzero code, no restart"),
          ("Runtime", "Node SDK", "In-process spans (express, pg), winston logs stamped with trace ids, Backstage's own twelve meters.", "one env var\nNODE_OPTIONS=--require ..."),
          ("Product", "Auditor service", "Who did what, and did it work: entity lookups by user, template runs by template, failures.", "one config line\nseverityLogLevelMappings.low: info"),
          ("User", "AnalyticsApi", "navigate, click, search with result count, create with time saved. The adoption numbers.", "~90 lines, no SDK\none fetch every 2 s")]
x = 0.4
for i, (lab, head, body, foot) in enumerate(layers):
    rect(s, x, 1.45, 3.0, 5.45, fill=TEAL_LT)
    chip(s, x + 0.2, 1.65, 1.6, 0.45, f"{i}  ·  {lab}", fill=ORANGE if i == 0 else TEAL, size=12, radius=0.4)
    text(s, x + 0.2, 2.25, 2.65, 0.6, head, size=18, color=TEAL_DK, bold=True, space_after=0)
    text(s, x + 0.2, 2.9, 2.65, 2.9, body, size=13.5, color=INK, space_after=0)
    hline(s, x + 0.2, 5.95, 2.6)
    text(s, x + 0.2, 6.05, 2.65, 0.8, foot, size=10.5, color=MUTED, mono=True, space_after=0)
    x += 3.18
notes(s, N(13))

# 7. LAYER 0: OBI
s = content_slide("Layer 0: OBI 1.0, zero code, no restart")
compose = ["obi:", "  image: otel/ebpf-instrument:v1.0.0   # released 2026-10-30", "  privileged: true", "  pid: host",
           "  environment:", "    OTEL_EBPF_OPEN_PORT: \"7007,5432\"", "    OTEL_EBPF_METRICS_FEATURES: application,application_runtime,network",
           "    OTEL_EXPORTER_OTLP_ENDPOINT: http://otelcol:4318", "  volumes: [/sys/kernel/tracing:/sys/kernel/tracing, /sys/fs/cgroup:/sys/fs/cgroup]"]
code(s, 0.4, 1.4, 7.6, 3.0, compose, size=11.5, hl=(1, 5))
text(s, 0.4, 4.5, 7.6, 0.35, "What OBI logged when Backstage started:", size=12, color=MUTED, space_after=0)
code(s, 0.4, 4.85, 7.6, 2.05, ["instrumenting process cmd=/usr/local/bin/node pid=1395", "    type=nodejs service=backstage", "Script successfully injected  component=nodejs.Injector",
                               "# Backstage read: OTEL_SERVICE_NAME from its own env, nothing else"], size=11.5, hl=(2,))
callout(s, 8.3, 1.4, 4.65, 1.75, "Injected through the inspector",
        "SIGUSR1 opens the inspector, one Runtime.evaluate installs an AsyncLocalStorage bridge. Async-context propagation is marked Stable; event-loop, GC and heap metrics are experimental.")
callout(s, 8.3, 3.27, 4.65, 1.75, "What you get for free",
        "HTTP server and client spans (TLS included: static OpenSSL uprobes), Postgres statements per table, RED metrics with http.route, nodejs.eventloop.*, v8js.*, TCP flows.")
callout(s, 8.3, 5.14, 4.65, 1.76, "What you do not get", "Business attributes: template, entity, user. Logs as a signal. Header propagation on this linuxkit 7.0 kernel, and never into TLS egress.", fill=ORANGE_LT, head_color=ORANGE)
notes(s, N(14, 15))

# 8. WATERFALL
s = content_slide("One scaffolder POST, 17 spans, zero code")
picture(s, ev("tempo-waterfall-layer0.jpg"), 0.4, 1.4, 12.55, 5.0, caption="Tempo, layer 0 on the rig: the POST, the internal catalog call for the template, SELECT final_entities, INSERT tasks and task_events, each with the Postgres server span underneath")
notes(s, N(16))

# 9. LAYER 1: ONE ENV VAR
s = content_slide("Layer 1: one environment variable")
env = ["NODE_OPTIONS=--require @opentelemetry/auto-instrumentations-node/register", "OTEL_EXPORTER_OTLP_ENDPOINT=http://otelcol:4318",
       "OTEL_TRACES_EXPORTER=otlp", "OTEL_METRICS_EXPORTER=otlp", "OTEL_LOGS_EXPORTER=otlp", "OTEL_METRIC_EXPORT_INTERVAL=10000",
       "# runtime-node is OBI's job here; fs/dns/net are noise", "OTEL_NODE_DISABLED_INSTRUMENTATIONS=runtime-node,fs,dns,net"]
code(s, 0.4, 1.4, 7.6, 3.1, env, size=10.5, hl=(0,))
text(s, 0.4, 4.6, 7.6, 0.4, "Measured on the rig: container restart to ready in ~3 s; first meters in Prometheus within 10 s.", size=12, color=MUTED, space_after=0)
rect(s, 0.4, 5.05, 7.6, 1.85, fill=ORANGE_LT)
text(s, 0.6, 5.12, 7.2, 1.7, [[("Gotcha. ", {"bold": True, "color": ORANGE}), ("The winston instrumentation only ships log records when ", {}), ("@opentelemetry/winston-transport", {"mono": True, "size": 12}), (" is installed in the app. Without it you get trace ids in your log lines and nothing in Loki. Same story for the auditor's events.", {})]], size=13.5, color=INK, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
text(s, 8.3, 1.4, 4.65, 0.5, "Within ten seconds", size=16, color=TEAL_DK, bold=True, space_after=0)
for i, (head, body) in enumerate([("Backstage's own meters", "scaffolder.task.count by template and result, catalog_entities_count by kind, scheduler runs"),
                                  ("Logs with trace ids", "every winston line carries trace_id and span_id; audit events arrive as structured records"),
                                  ("In-process spans", "express middleware, pg queries with the statement, undici calls, all nested under OBI's request")]):
    y = 1.95 + i * 1.65
    circle(s, 8.35, y + 0.08, 0.42, str(i + 1), fill=TEAL, size=14)
    text(s, 8.9, y, 4.05, 1.55, [[(head, {"bold": True})], [(body, {"color": MUTED, "size": 12})]], size=14, color=INK, space_after=2)
notes(s, N(17))

# 10. COLLECTOR 1/3
s = content_slide("Product metrics are born in the Collector")
# flow row
for x, w, lab, sub, col in [(0.4, 2.3, "OBI · SDK · browser", "spans, logs, events", TEAL), (3.1, 2.4, "transform (OTTL)", "/api/<plugin> → backstage.plugin", ORANGE),
                            (5.9, 2.2, "span_metrics", "RED per plugin + route", ORANGE), (8.5, 2.2, "count", "audit + analytics logs", ORANGE), (11.1, 1.85, "Prometheus", "+ Loki + Tempo", TEAL)]:
    chip(s, x, 1.5, w, 0.95, lab, fill=col, sub=sub, size=13, sub_size=10, radius=0.15)
for x1, x2 in [(2.7, 3.08), (5.5, 5.88), (8.1, 8.48), (10.7, 11.08)]:
    arrow(s, x1 + 0.02, 1.97, x2 - 0.02, 1.97, color=TEAL_DK, w=2)
ottl = ["processors:", "  transform/plugin:", "    trace_statements:",
        "      - set(span.attributes[\"backstage.plugin\"], span.attributes[\"url.path\"])", "          where IsMatch(span.attributes[\"url.path\"], \"^/api/[A-Za-z0-9_-]+\")",
        "      - replace_pattern(span.attributes[\"backstage.plugin\"], \"^/api/([A-Za-z0-9_-]+).*$\", \"$$1\")",
        "connectors:", "  span_metrics:", "    dimensions:", "      - name: http.request.method", "      - name: http.response.status_code",
        "      - name: backstage.plugin", "      - name: http.route"]
code(s, 0.4, 2.75, 8.2, 4.15, ottl, size=9.5, hl=(5, 11))
callout(s, 8.9, 2.75, 4.05, 2.0, "One fact, one dimension", "Every backend plugin lives under /api/<pluginId>/. One regex turns that into a label on every span and, through span_metrics, on every RED series.")
callout(s, 8.9, 4.9, 4.05, 2.0, "Same metric, any layer", "In layer 0 the spans come from OBI, in layer 1 from the SDK. The dashboard does not care which; the Collector filters the duplicate.")
notes(s, N(18))

# 11. COLLECTOR 2/3: AUDIT
s = content_slide("Audit events become counters")
rec = ["# one winston record per audit event (Backstage >= 1.36)", "{ \"isAuditEvent\": true,", "  \"plugin\": \"scaffolder\", \"eventId\": \"task\",", "  \"status\": \"succeeded\",        # initiated | succeeded | failed",
       "  \"actor\": { \"actorId\": \"user:default/guest\", ... },", "  \"meta\":  { \"actionType\": \"create\",", "             \"templateRef\": \"template:default/paved-road-service\" } }"]
code(s, 0.4, 1.4, 6.2, 2.6, rec, size=9.5, hl=(3, 6))
cnt = ["connectors:", "  count:", "    logs:", "      backstage.audit.events:", "        conditions: ['attributes[\"isAuditEvent\"] == true']",
       "        attributes:", "          - key: plugin", "          - key: eventId", "          - key: status", "          - key: backstage.actor      # from actor.actorId",
       "          - key: backstage.template   # from meta.templateRef"]
code(s, 6.8, 1.4, 6.15, 3.65, cnt, size=10, hl=(4, 9, 10))
callout(s, 0.4, 4.15, 6.2, 1.3, "Turn them on first", "Severity 'low' maps to debug by default and the info-level logger drops it. One line: backend.auditor.severityLogLevelMappings.low: info.")
callout(s, 0.4, 5.6, 6.2, 1.3, "actorId is a person", "user:default/guest is PII once it is a Prometheus label. Hash it in the Collector (one OTTL SHA256 line) or drop it before it leaves the host.", fill=ORANGE_LT, head_color=ORANGE)
text(s, 6.8, 5.2, 6.15, 1.7, [
    [("What that buys you: ", {"bold": True, "color": TEAL_DK}), ("template runs by template and status, ", {}), ("who", {"bold": True}), (" ran them, entity lookups by query type, and the ghost lookups: fetches of entities that no longer exist.", {})],
    [("No code in Backstage knows these metrics exist.", {"italic": True, "color": MUTED})],
], size=13.5, color=INK, space_after=6)
notes(s, N(19))

# 12. COLLECTOR 3/3: BROWSER
s = content_slide("The browser talks OTLP: 90 lines, no SDK")
ts = ["captureEvent(event: AnalyticsEvent) {", "  const attrs = {", "    'backstage.analytics.action': event.action,     // navigate | click | search | create",
      "    'backstage.plugin': event.context.pluginId,", "    'enduser.id': this.userRef,                      // from identityApi", "    'session.id': this.sessionId,",
      "  };", "  if (event.value !== undefined) attrs['backstage.analytics.value'] = event.value;",
      "  if (event.action === 'search') attrs['backstage.search.zero_results'] = String(event.value === 0);", "  this.queue.push(otlpLogRecord(event, attrs));  // flushed every 2 s to :4318/v1/logs", "}"]
code(s, 0.4, 1.4, 8.2, 4.1, ts, size=9.5, hl=(2, 8))
text(s, 0.4, 5.6, 8.2, 1.3, [
    [("Registered with ", {}), ("AnalyticsImplementationBlueprint", {"mono": True, "size": 12.5}), (" from @backstage/plugin-app-react. No OTel SDK in the browser: the module writes OTLP/JSON by hand and POSTs it.", {})],
    [("Requested in backstage#25045 in 2024, closed not-planned. It is sixty lines.", {"italic": True, "color": MUTED})],
], size=13.5, color=INK, space_after=6)
callout(s, 8.9, 1.4, 4.05, 1.7, "Collector side", "otlp receiver http with cors.allowed_origins for the portal origin. count connector turns actions into backstage_analytics_events_total.")
callout(s, 8.9, 3.25, 4.05, 1.7, "search carries the result count", "value == 0 becomes backstage.search.zero_results = true. The zero-result rate is one PromQL division.")
callout(s, 8.9, 5.1, 4.05, 1.8, "create carries time saved", "The scaffolder emits create with value = minutes from backstage.io/time-saved. Sum it in Loki: hours saved per template.")
notes(s, N(20))

# 13-15. DASHBOARD ROWS
for title, img, cap, n in [
    ("Adoption: who uses the portal, and for what", "dash-adoption.jpg", "Dashboard row 1 on the rig: active users, page views, searches, templates run, hours saved, plugin usage, who runs templates (audit), template popularity", 21),
    ("Friction: where people get stuck", "dash-friction.jpg", "Dashboard row 2 on the rig: 100% failure on the stock GitHub template, p95 by template, slowest steps, zero-result searches, ghost lookups, TechDocs 404s", 22),
    ("Plugins as products: RED per plugin", "dash-plugins.jpg", "Dashboard row 3 on the rig: requests/s, error ratio and p95 per plugin, slowest routes, and the service graph with one Postgres database node per plugin", 23),
]:
    s = content_slide(title)
    picture(s, ev(img), 0.4, 1.4, 12.55, 5.0, caption=cap)
    notes(s, N(n))

# 16. FOURTH SIGNAL
s = content_slide("Fourth signal: a CPU profile, no agent")
picture(s, ev("pyroscope-flamegraph.jpg"), 0.4, 1.4, 8.3, 5.5, caption="Pyroscope 2.4, OTel eBPF profiler distro 0.164: JS frames symbolized next to kernel frames")
callout(s, 8.95, 1.4, 4.0, 2.2, "Profiles are OTel's fourth signal", "Public alpha since March. The eBPF profiler runs as a Collector distro, exports OTLP profiles, Pyroscope ingests them natively.")
callout(s, 8.95, 3.75, 4.0, 1.75, "V8 frames, not just native", "Ignition, Sparkplug and TurboFan frames resolve to function names: net.Socket.write, ajv compileSchema, processTicksAndRejections.")
callout(s, 8.95, 5.65, 4.0, 1.25, "Limit", "Asynchronous stack traces are not built; you see where CPU goes, not which request asked for it.", fill=ORANGE_LT, head_color=ORANGE)
notes(s, N(24, 25))

# 17. DEMO CUE (dark)
s = dark_slide()
text(s, 0.9, 0.9, 11.6, 0.9, "Demo: four beats, one laptop", size=38, color=WHITE, bold=True, space_after=0)
beats = [("A", "Layer 0: the kernel", "make layer0  →  OBI log 'Script successfully injected'  →  Tempo waterfall of a scaffolder POST  →  RED by plugin", "zero code"),
         ("B", "Layer 1: one env var", "make layer1  →  ~3 s restart  →  scaffolder.task.count by template appears  →  a log line with trace_id", "~10 s"),
         ("C", "Product metrics", "run a template in the UI  →  the create event lands with time saved  →  audit counters: who ran what", "~20 s"),
         ("D", "Plugins as products", "RED table per plugin  →  slowest routes  →  service graph with one database per plugin  →  flame graph", "dashboard")]
y = 2.05
for letter, head, body, t in beats:
    rect(s, 0.9, y, 11.6, 1.05, fill=None, line=RGBColor(0x7F, 0xC8, 0xB9), radius=0.15)
    circle(s, 1.1, y + 0.25, 0.55, letter, fill=ORANGE, color=WHITE, size=18)
    text(s, 1.9, y + 0.06, 8.9, 0.45, head, size=18, color=WHITE, bold=True, space_after=0)
    text(s, 1.9, y + 0.5, 8.9, 0.5, body, size=12.5, color=WHITE, space_after=0)
    text(s, 10.6, y + 0.3, 1.8, 0.45, t, size=13, color=AMBER, bold=True, align=PP_ALIGN.RIGHT, space_after=0)
    y += 1.2
notes(s, N(26, 27))

# 18. TRADE-OFFS
s = content_slide("Trade-offs: what bit us on the rig")
rows = [("Two sources of the same span", "OBI and the SDK both emit HTTP spans; RED doubles", "pick an owner per layer; filter the other in the Collector (telemetry.distro.name)"),
        ("Kernel caveats", "linuxkit 7.0 disabled OBI header propagation; TLS egress never carries context", "accept leaf spans for GitHub calls; mount /sys/kernel/tracing; read the OBI log"),
        ("Audit events are debug by default", "severity 'low' is dropped by the info-level logger", "backend.auditor.severityLogLevelMappings.low: info"),
        ("actorId is PII", "user refs become Prometheus labels", "hash with one OTTL SHA256 statement, or keep actors in Loki only"),
        ("Looking costs money", "~250 spans/s, ~150 log records/s on an 8 rps portal", "put the Collector's own export rate on the dashboard; sample traces, never the counters")]
table(s, 0.4, 1.45, 12.55, ["What", "Why it bites", "What we did"], rows, col_w=[2.9, 4.6, 5.05], size=13, row_h=0.85)
notes(s, N(28))

# 19. SLOs
s = content_slide("Starter SLOs for a developer portal")
t = C[29]["table"]
table(s, 0.4, 1.45, 12.55, t["header"], [tuple(r) for r in t["rows"]], col_w=[5.0, 7.55] if len(t["header"]) == 2 else None, size=13.5, row_h=0.72)
text(s, 0.4, 6.5, 12.55, 0.45, "Proposed, not published: no Backstage SLOs exist in the docs, Spotify's Insights or the CNCF talks we could find.", size=11.5, color=MUTED, italic=True, space_after=0)
notes(s, N(29))

# 20. TAKE IT HOME
s = content_slide("Take it home")
rect(s, 0.4, 1.45, 7.6, 5.45, fill=TEAL_LT)
text(s, 0.65, 1.6, 7.1, 0.5, "Everything you saw, on your laptop", size=18, color=TEAL_DK, bold=True, space_after=0)
code(s, 0.65, 2.15, 7.1, 1.9, ["git clone https://github.com/eKuG/backstage-demo-na26", "make build && make up   # Backstage + OBI + Collector + Grafana", "make load               # synthetic developers, ~8 rps",
                               "make layer1             # SDK on; make layer0 = SDK off"], size=11)
text(s, 0.65, 4.2, 7.1, 2.6, [
    "Collector config with the three derivations, the 36-panel dashboard, the AnalyticsApi module",
    "Three templates that tell the friction story: paved road, stock GitHub (fails), slow pipeline",
    "Pinned: Backstage 1.56.0 · OBI v1.0.0 · Collector contrib 0.164.0 · Pyroscope 2.4 · Grafana 13",
], size=13, color=INK, bullets=True, space_after=6)
rect(s, 8.3, 1.45, 4.65, 5.45, fill=WHITE, line=LINE)
picture(s, ev("repo-qr.png"), 8.75, 1.75, 3.75, 3.75, frame=False)
text(s, 8.4, 5.6, 4.45, 0.45, "github.com/eKuG/backstage-demo-na26", size=12.5, color=TEAL_DK, bold=True, align=PP_ALIGN.CENTER, mono=True, space_after=0)
text(s, 8.4, 6.1, 4.45, 0.7, "Mithun Banerjee, 5:15 today: the setup.\nOBI internals deep dive: Tuesday.", size=12, color=MUTED, align=PP_ALIGN.CENTER, space_after=0)
notes(s, N(30))

# 21. CLOSE
s = prs.slides.add_slide(L_CLOSE)
text(s, 0.0, 6.3, 13.33, 0.6, "Thank you  ·  Questions?", size=24, color=WHITE, bold=True, align=PP_ALIGN.CENTER, space_after=0)
notes(s, N(31) + "\nLikely questions: OBI vs SDK overhead (2.3% vs 6% CPU on the rig); does this work on Kubernetes (OBI as DaemonSet, same config); where do hashed actors live (Loki, not Prometheus); what about the new frontend system (AnalyticsImplementationBlueprint is the new-system API).")

# ---- BACKUP -------------------------------------------------------------------------------------
s = dark_slide()
text(s, 0.9, 2.6, 11.6, 1.0, "Backup: the demo, frame by frame", size=40, color=WHITE, bold=True, space_after=0)
text(s, 0.9, 3.7, 11.6, 0.8, "Captured on the rehearsal rig. Shown only if the live run misbehaves.", size=18, color=WHITE, italic=True, space_after=0)
notes(s, "Backup section. Skip unless the demo fails; then narrate these in order, same beats.")
for title, img, cap in [
    ("Beat C: a template run from the UI", ev("backstage-template-run.jpg"), "Paved Road Service: fetch, provision (simulated), done. The frontend emits create with value 240 (PT4H) the moment the task is created."),
    ("Beat D: the runtime row and the flame graph", ev("dash-runtime.jpg"), "Event loop utilization and p99 delay from OBI's injected agent, GC by type, heap by space, the flame graph, Postgres ops per plugin database, Collector export rate."),
    ("Amsterdam: who monitors the monitor?", eu("s17_232.png"), "The slide that opened the question last March."),
]:
    s = content_slide(title)
    picture(s, img, 0.4, 1.4, 12.55, 4.95)
    text(s, 0.4, 6.45, 12.55, 0.5, cap, size=13, color=MUTED, align=PP_ALIGN.CENTER, space_after=0)
    notes(s, cap)

prs.save(OUT)
print("wrote", OUT, "slides:", len(prs.slides))
