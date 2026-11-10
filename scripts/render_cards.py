#!/usr/bin/env python3
"""Render animated, image-safe SVG cards for a GitHub profile README."""
from __future__ import annotations
import base64, calendar, json, os, subprocess, tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
DATA_FILE = ROOT / "data" / "contributions.json"
CONFIG = json.loads((ROOT / "cards_config.json").read_text(encoding="utf-8"))
STATIC = os.getenv("STATIC", "").strip().lower() in {"1", "true", "yes"}
COLORS = CONFIG["colors"]
BG, PANEL, PANEL_ALT = COLORS["bg"], COLORS["panel"], COLORS["panel_alt"]
TEXT, MUTED, MINT, GOLD = COLORS["text"], COLORS["muted"], COLORS["mint"], COLORS["gold"]
FONT_FAMILY = CONFIG.get("font_family", "Arial, Helvetica, sans-serif")
WIDTH = 1000

CSS = """
@keyframes reveal { from { opacity:0; transform:translateY(14px) } to { opacity:1; transform:translateY(0) } }
@keyframes orbit { from { transform:rotate(0deg) } to { transform:rotate(360deg) } }
@keyframes grow { from { transform:scaleY(.04) } to { transform:scaleY(1) } }
@media (prefers-reduced-motion: reduce) {
 *,*::before,*::after { animation:none!important;transition:none!important;opacity:1!important;transform:none!important; }
}
"""

def esc(value):
    return escape(str(value), {'"': "&quot;"})

def delay_style(delay=0, duration=650):
    if STATIC:
        return 'opacity="1"'
    return f'style="opacity:0;animation:reveal {duration}ms cubic-bezier(.2,.7,.2,1) {delay}ms forwards"'

def make_font_css():
    """Subset optional licensed TTF/OTF and embed WOFF as a base64 data URI."""
    candidates = [
        ROOT / "assets" / "fonts" / "profile.ttf",
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    font = next((item for item in candidates if item.exists()), None)
    if font is None:
        return ""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "profile-subset.woff"
            subprocess.run(
                ["pyftsubset", str(font), f"--output-file={out}", "--flavor=woff",
                 "--unicodes=U+0000-00FF", "--layout-features=*"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            )
            encoded = base64.b64encode(out.read_bytes()).decode("ascii")
        return ("@font-face{font-family:ProfileEmbedded;"
                f"src:url(data:font/woff;base64,{encoded}) format('woff');"
                "font-style:normal;font-weight:100 900;font-display:swap}")
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Font subsetting skipped; using Arial fallback: {exc}")
        return ""

EMBEDDED_FONT = make_font_css()
ACTIVE_FONT = "ProfileEmbedded, " + FONT_FAMILY if EMBEDDED_FONT else FONT_FAMILY

def svg_start(height, title):
    style = "" if STATIC else CSS
    return f"""<svg xmlns="http://www.w3.org/2000/svg"
 xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{height}"
 viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title><defs>
 <linearGradient id="brand" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{MINT}"/><stop offset="1" stop-color="{GOLD}"/>
 </linearGradient>
 <pattern id="quiet-grid" width="32" height="32" patternUnits="userSpaceOnUse">
  <path d="M32 0H0V32" fill="none" stroke="{TEXT}" stroke-opacity=".025"/>
 </pattern>
 <style>{EMBEDDED_FONT}{style}
 text{{font-family:{ACTIVE_FONT}}}
 .muted{{fill:{MUTED}}}.mint{{fill:{MINT}}}.gold{{fill:{GOLD}}}
 </style>
</defs>
<rect width="1000" height="{height}" rx="26" fill="{BG}"/>
<rect width="1000" height="{height}" rx="26" fill="url(#quiet-grid)"/>
"""

def surface(height, delay=0):
    return (f'<g {delay_style(delay)}><rect x="1" y="1" width="998" height="{height-2}" rx="24" '
            f'fill="{PANEL}" stroke="{MINT}" stroke-opacity=".22"/></g>')

def save_card(filename, markup):
    CARDS.mkdir(parents=True, exist_ok=True)
    (CARDS / filename).write_text(markup + "</svg>\n", encoding="utf-8")

def render_hero():
    h = 310
    s = svg_start(h, "Shivasharanappa | Generative AI Engineer")
    s += surface(h)
    s += (f'<circle cx="817" cy="154" r="112" fill="{MINT}" opacity=".045"/>'
          f'<circle cx="817" cy="154" r="83" fill="none" stroke="{GOLD}" '
          'stroke-opacity=".45" stroke-width="1.5"/>')
    orbit = "" if STATIC else 'style="transform-box:fill-box;transform-origin:center;animation:orbit 36s linear infinite"'
    s += (f'<g {orbit}><circle cx="817" cy="154" r="61" fill="none" stroke="{MINT}" '
          'stroke-width="2" stroke-dasharray="4 10"/>'
          f'<circle cx="817" cy="93" r="5" fill="{GOLD}"/></g>')
    s += f'<text x="58" y="65" font-size="13" letter-spacing="3.5" class="gold" {delay_style(0)}>GENERATIVE AI  /  PYTHON  /  SOFTWARE</text>'
    s += f'<text x="56" y="137" font-size="47" font-weight="700" fill="{TEXT}" {delay_style(140)}>{esc(CONFIG["name"])}</text>'
    s += f'<text x="59" y="181" font-size="22" class="mint" {delay_style(280)}>{esc(CONFIG["role"])}</text>'
    s += f'<text x="59" y="222" font-size="16" class="muted" {delay_style(420)}>{esc(CONFIG["tagline"])}</text>'
    s += f'<text x="59" y="270" font-size="11" letter-spacing="1.8" class="muted" {delay_style(560)}>COMPUTER SCIENCE &amp; DESIGN  ·  PDA COLLEGE OF ENGINEERING</text>'
    portrait = CONFIG.get("portrait_url", "").strip()
    if portrait:
        s += ('<defs><clipPath id="portrait"><circle cx="817" cy="154" r="49"/></clipPath></defs>'
              f'<image href="{esc(portrait)}" x="768" y="105" width="98" height="98" '
              'preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait)"/>')
    else:
        s += (f'<path d="M817 119L829 142L852 154L829 166L817 189L805 166L782 154L805 142Z" '
              f'fill="url(#brand)"/><circle cx="817" cy="154" r="7" fill="{BG}"/>')
    save_card("hero.svg", s)


def render_link_tile(key, title, subtitle, delay):
    # Compact canvas keeps text legible at README width=32.5%.
    h, w = 112, 340
    style = "" if STATIC else CSS
    s = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title><defs><style>{EMBEDDED_FONT}{style}
text{{font-family:{ACTIVE_FONT}}}.muted{{fill:{MUTED}}}.mint{{fill:{MINT}}}.gold{{fill:{GOLD}}}
@media(prefers-reduced-motion:reduce){{animate,animateTransform{{display:none!important}}}}
</style></defs><rect x="1" y="1" width="338" height="110" rx="19" fill="{PANEL}" stroke="{MINT}" stroke-opacity=".22"/>"""
    s += f'<g {delay_style(delay + 100)}>'
    s += f'<circle cx="49" cy="56" r="26" fill="{PANEL_ALT}" stroke="{GOLD}" stroke-opacity=".7"/>'
    label = {"github": "GH", "linkedin": "in", "email": "@"}[key]
    s += f'<text x="49" y="62" text-anchor="middle" font-size="17" font-weight="700" class="mint">{label}</text>'
    s += f'<text x="91" y="49" font-size="16" font-weight="700" fill="{TEXT}">{esc(title)}</text>'
    s += f'<text x="91" y="72" font-size="10.5" class="muted">{esc(subtitle)}</text>'
    s += f'<path d="M304 56h17m-7 -7l7 7 -7 7" fill="none" stroke="{GOLD}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></g>'
    save_card(f"{key}.svg", s)
def load_data():
    if not DATA_FILE.exists():
        return {"days": [], "as_of": "Awaiting first sync"}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def normalized_days(data):
    rows = []
    for item in data.get("days", []):
        rows.append((date.fromisoformat(item["date"]), int(item.get("count", 0))))
    if not rows:
        for week in data.get("weeks", []):
            for item in week.get("contributionDays", []):
                rows.append((date.fromisoformat(item["date"]), int(item["contributionCount"])))
    return sorted(rows, key=lambda pair: pair[0])


def calculate_metrics(rows):
    if not rows:
        return 0, 0, "—", 0, [], 0
    counts = {day: count for day, count in rows}
    total = sum(counts.values())
    active = sum(count > 0 for count in counts.values())
    monthly = Counter()
    for day, count in rows:
        monthly[day.strftime("%Y-%m")] += count
    busiest_date, busiest_count = max(rows, key=lambda item: (item[1], item[0]))
    busiest = f"{busiest_date.strftime('%d %b')} · {busiest_count}" if busiest_count else "—"
    today = date.today()
    cursor = today if counts.get(today, 0) else today - timedelta(days=1)
    streak = 0
    while counts.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    months = []
    for key, value in sorted(monthly.items())[-12:]:
        _, month = map(int, key.split("-"))
        months.append((calendar.month_abbr[month], value))
    return total, active, busiest, streak, months, busiest_count

def render_about():
    """Render the profile's About Me card in the existing brand style."""
    h = 238
    about = CONFIG.get("about", {})
    heading = about.get("heading", "Curious mind. Practical builder.")
    paragraphs = about.get("paragraphs", [
        "I'm a Computer Science and Design graduate from PDA College of Engineering.",
        "Currently a Generative AI Engineer Intern at Pragyan AI.",
        "I explore Generative AI, LLMs, Python, machine learning and computer vision.",
        "I enjoy learning by building practical applications and solving real problems.",
    ])
    focus = about.get("focus", ["GENERATIVE AI", "MACHINE LEARNING", "COMPUTER VISION"])
    s = svg_start(h, "About Shivasharanappa")
    s += surface(h, 980)
    s += f'<g {delay_style(1080)}>'
    s += f'<text x="38" y="45" font-size="12" letter-spacing="2.8" class="gold">ABOUT ME</text>'
    s += f'<text x="38" y="83" font-size="25" font-weight="700" fill="{TEXT}">{esc(heading)}</text>'
    for index, line in enumerate(paragraphs[:4]):
        s += f'<text x="38" y="{123 + index*27}" font-size="14.5" class="muted" {delay_style(1160 + index*100)}>{esc(line)}</text>'
    s += f'<rect x="728" y="52" width="232" height="145" rx="16" fill="{PANEL_ALT}" stroke="{MINT}" stroke-opacity=".3"/>'
    s += f'<text x="750" y="82" font-size="11" letter-spacing="1.8" class="gold">AREAS I EXPLORE</text>'
    for index, label in enumerate(focus[:3]):
        y = 112 + index*27
        s += f'<circle cx="754" cy="{y-4}" r="4" fill="{MINT}"/>'
        s += f'<text x="769" y="{y}" font-size="12.5" fill="{TEXT}">{esc(label)}</text>'
    s += '</g>'
    save_card("about.svg", s)


def render_experience_education():
    """Render experience and education in two matching profile panels."""
    h = 370
    section = CONFIG.get("experience_education", {})
    experiences = section.get("experience", [])
    education = section.get("education", [])
    s = svg_start(h, "Experience and education") + surface(h, 1420)
    s += f'<g {delay_style(1520)}>'
    s += f'<text x="38" y="46" font-size="12" letter-spacing="2.8" class="gold">MY JOURNEY</text>'
    s += f'<text x="38" y="83" font-size="25" font-weight="700" fill="{TEXT}">Experience &amp; Education</text>'
    s += f'<rect x="34" y="108" width="452" height="226" rx="17" fill="{PANEL_ALT}" fill-opacity=".72" stroke="{MINT}" stroke-opacity=".24"/>'
    s += f'<rect x="514" y="108" width="452" height="226" rx="17" fill="{PANEL_ALT}" fill-opacity=".72" stroke="{GOLD}" stroke-opacity=".24"/>'
    s += f'<text x="58" y="142" font-size="12" letter-spacing="1.8" class="mint">EXPERIENCE</text>'
    s += f'<text x="538" y="142" font-size="12" letter-spacing="1.8" class="gold">EDUCATION</text>'
    for index, item in enumerate(experiences[:2]):
        y = 181 + index * 92
        s += f'<circle cx="63" cy="{y-5}" r="5" fill="{MINT}"/>'
        s += f'<text x="81" y="{y}" font-size="15" font-weight="700" fill="{TEXT}">{esc(item.get("title", ""))}</text>'
        s += f'<text x="81" y="{y+22}" font-size="12.5" class="mint">{esc(item.get("organization", ""))}</text>'
        s += f'<text x="81" y="{y+43}" font-size="11.5" class="muted">{esc(item.get("details", ""))}</text>'
    for index, item in enumerate(education[:2]):
        y = 181 + index * 92
        s += f'<circle cx="543" cy="{y-5}" r="5" fill="{GOLD}"/>'
        s += f'<text x="561" y="{y}" font-size="15" font-weight="700" fill="{TEXT}">{esc(item.get("title", ""))}</text>'
        s += f'<text x="561" y="{y+22}" font-size="12.5" class="gold">{esc(item.get("organization", ""))}</text>'
        s += f'<text x="561" y="{y+43}" font-size="11.5" class="muted">{esc(item.get("details", ""))}</text>'
    s += '</g>'
    save_card("experience-education.svg", s)


def render_learning():
    """Render current learning areas without implying unearned certificates."""
    section = CONFIG.get("learning", {})
    cards = section.get("areas", [])
    h = 310
    s = svg_start(h, "Currently learning and building") + surface(h, 1750)
    s += f'<g {delay_style(1850)}>'
    s += f'<text x="38" y="43" font-size="12" letter-spacing="2.8" class="gold">LEARNING &amp; BUILDING</text>'
    s += f'<text x="38" y="81" font-size="25" font-weight="700" fill="{TEXT}">{esc(section.get("heading", "Curious today. Better tomorrow."))}</text>'
    s += f'<text x="38" y="108" font-size="13.5" class="muted">Exploring ideas through hands-on practice and practical projects.</text>'
    for index, item in enumerate(cards[:3]):
        x = 34 + index * 312
        accent = MINT if index != 1 else GOLD
        s += f'<rect x="{x}" y="132" width="292" height="121" rx="15" fill="{PANEL_ALT}" stroke="{accent}" stroke-opacity=".34"/>'
        s += f'<text x="{x+18}" y="160" font-size="10.5" letter-spacing="1.5" fill="{accent}">{esc(item.get("label", ""))}</text>'
        s += f'<text x="{x+18}" y="188" font-size="17" font-weight="700" fill="{TEXT}">{esc(item.get("title", ""))}</text>'
        for line_index, line in enumerate(item.get("details", [])[:3]):
            y = 211 + line_index * 17
            s += f'<circle cx="{x+22}" cy="{y-4}" r="2.8" fill="{accent}"/>'
            s += f'<text x="{x+33}" y="{y}" font-size="11.5" class="muted">{esc(line)}</text>'
    note = section.get("note", "Certificates and achievements will be added here as they are completed and verified.")
    s += f'<text x="38" y="285" font-size="11.5" class="muted">{esc(note)}</text>'
    s += '</g>'
    save_card("learning.svg", s)

def render_activity(data, rows):
    h = 400
    total, active, busiest, streak, months, busiest_count = calculate_metrics(rows)
    s = svg_start(h, "GitHub activity summary") + surface(h, 1120)
    s += f'<g {delay_style(1220)}>'
    s += f'<text x="38" y="48" font-size="13" letter-spacing="3" class="gold">GITHUB ACTIVITY</text>'
    s += f'<text x="38" y="85" font-size="25" font-weight="700" fill="{TEXT}">Small steps. Consistent progress.</text>'
    if rows:
        stats = [("CONTRIBUTIONS", f"{total:,}", MINT), ("ACTIVE DAYS", f"{active:,}", MINT),
                 ("CURRENT STREAK", f"{streak} day" if streak == 1 else f"{streak} days", MINT), ("BUSIEST DAY · COUNT", busiest, GOLD)]
    else:
        stats = [("CONTRIBUTIONS", "—", MINT), ("ACTIVE DAYS", "—", MINT),
                 ("CURRENT STREAK", "—", MINT), ("BUSIEST DAY · COUNT", "—", GOLD)]
    for i, (label, value, accent) in enumerate(stats):
        x = 38 + i * 236
        s += f'<rect x="{x}" y="111" width="218" height="82" rx="14" fill="{PANEL_ALT}"/>'
        s += f'<text x="{x+16}" y="140" font-size="10.5" letter-spacing="1.2" class="muted">{label}</text>'
        size = 22 if len(value) > 12 else 25
        s += f'<text x="{x+16}" y="174" font-size="{size}" font-weight="700" fill="{accent}">{esc(value)}</text>'
    s += f'<text x="38" y="232" font-size="12" letter-spacing="1.8" class="muted">MONTHLY CONTRIBUTIONS · LAST 12 MONTHS</text>'
    if rows:
        max_value = max([v for _, v in months] + [1])
        base, left, slot = 344, 52, 75
        for i, (label, value) in enumerate(months):
            x = left + i * slot
            bar_h = max(2, round(82 * value / max_value)) if value else 0
            s += f'<rect x="{x}" y="{base-82}" width="38" height="82" rx="7" fill="{PANEL_ALT}"/>'
            if value:
                transform = "" if STATIC else f'style="transform-box:fill-box;transform-origin:bottom;animation:grow 700ms ease {1850+i*45}ms both"'
                s += f'<rect x="{x}" y="{base-bar_h}" width="38" height="{bar_h}" rx="7" fill="url(#brand)" {transform}/>'
            s += f'<text x="{x+19}" y="{base+21}" font-size="11" text-anchor="middle" class="muted">{label}</text>'
    else:
        s += f'<text x="38" y="300" font-size="15" class="muted">Monthly activity will appear after the first contribution sync.</text>'
    s += f'<text x="38" y="385" font-size="11" class="muted">Latest 365 days · Updated {esc(data.get("as_of", "daily sync"))}</text>'
    s += "</g>"
    save_card("activity.svg", s)

def render_project(project, filename, delay):
    h = 178
    s = svg_start(h, project["name"]) + surface(h, delay)
    s += f'<g {delay_style(delay + 100)}>'
    s += f'<text x="38" y="42" font-size="11" letter-spacing="2.2" class="gold">FEATURED PROJECT</text>'
    s += f'<text x="38" y="84" font-size="27" font-weight="700" fill="{TEXT}">{esc(project["name"])}</text>'
    s += f'<text x="38" y="116" font-size="15" class="muted">{esc(project["description"])}</text>'
    s += f'<rect x="38" y="137" width="154" height="27" rx="13" fill="{MINT}" fill-opacity=".10" stroke="{MINT}" stroke-opacity=".48"/>'
    s += f'<text x="108" y="155" text-anchor="middle" font-size="11" class="mint">OPEN PROJECT</text>'
    s += f'<circle cx="927" cy="87" r="28" fill="{PANEL_ALT}" stroke="{GOLD}" stroke-opacity=".55"/>'
    s += f'<path d="M915 87h24m-9 -9l9 9 -9 9" fill="none" stroke="{MINT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    s += '</g>'
    save_card(filename, s)

def render_contributions(rows):
    h = 230
    s = svg_start(h, "GitHub contribution graph") + surface(h, 2920)
    s += f'<g {delay_style(3020)}>'
    s += f'<text x="38" y="43" font-size="13" letter-spacing="2.5" class="gold">CONTRIBUTION GRAPH</text>'
    if not rows:
        s += f'<text x="38" y="118" font-size="16" class="muted">Your contribution history will appear after the first daily sync.</text>'
    else:
        first = rows[0][0]
        offset = (first.weekday() + 1) % 7
        max_count = max([count for _, count in rows] + [1])
        for i, (day, count) in enumerate(rows):
            col, row = (i + offset) // 7, (i + offset) % 7
            x, y = 38 + col * 13, 76 + row * 14
            opacity = 0.08 if count == 0 else min(1.0, 0.22 + 0.78 * count / max_count)
            s += f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{MINT}" fill-opacity="{opacity:.2f}"/>'
        s += f'<text x="38" y="211" font-size="10.5" class="muted">LESS</text>'
        for i, opacity in enumerate((0.08, 0.28, 0.48, 0.72, 1.0)):
            s += f'<rect x="{82+i*18}" y="201" width="11" height="11" rx="2" fill="{MINT}" fill-opacity="{opacity}"/>'
        s += f'<text x="184" y="211" font-size="10.5" class="muted">MORE · LAST 365 DAYS</text>'
    s += "</g>"
    save_card("contributions.svg", s)



def widget_text(x, y, value, size=12, color="#edf4f8", weight=400, anchor="start", spacing=0):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}" letter-spacing="{spacing}">{esc(value)}</text>'


def widget_start(width, height, title, subtitle, accent="#39df91"):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
 width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<defs>
 <linearGradient id="wbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#111d2a"/><stop offset="1" stop-color="#0b121c"/></linearGradient>
 <linearGradient id="wtop" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="#9a8cff"/></linearGradient>
 <linearGradient id="wglass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity=".10"/><stop offset="1" stop-color="#ffffff" stop-opacity=".025"/></linearGradient>
 <filter id="wshadow" x="-25%" y="-25%" width="160%" height="180%"><feGaussianBlur in="SourceAlpha" stdDeviation="5" result="b"/><feOffset dy="6" dx="1" result="o"/><feComponentTransfer in="o" result="s"><feFuncA type="linear" slope=".48"/></feComponentTransfer><feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
 <filter id="wglow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="20" fill="url(#wbg)" stroke="#405366" stroke-opacity=".75"/>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="19" fill="url(#wglass)"/>
<path d="M22 2H{width-22}" stroke="url(#wtop)" stroke-width="2.5" stroke-linecap="round" opacity=".95"/>
{widget_text(22, 31, title.upper(), 10.5, accent, 700, spacing=1.5)}
{widget_text(22, 49, subtitle, 9.5, "#91a5b8", 400)}
'''


def widget_metric(x, y, w, label, value, accent):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="59" rx="11" fill="#1b2a39" stroke="{accent}" stroke-opacity=".34"/>']
    out.append(f'<path d="M{x+11} {y+1}H{x+w-11}" stroke="{accent}" stroke-opacity=".55" stroke-width="1.5"/>')
    out.append(widget_text(x+11, y+19, label.upper(), 7.8, "#91a5b8", 700, spacing=.7))
    out.append(widget_text(x+11, y+46, value, 19, accent, 800))
    return "".join(out)


def render_widget_profile():
    w, h = 280, 348
    accent, cyan, purple = "#39df91", "#42c8d5", "#9a8cff"
    s = widget_start(w, h, "Profile", "DEVELOPER IDENTITY", accent)
    s += '<circle cx="140" cy="116" r="59" fill="#243b49" stroke="#39df91" stroke-width="2.5" filter="url(#wglow)"/>'
    s += '<circle cx="140" cy="116" r="51" fill="#172638"/>'
    avatar = CONFIG.get("avatar_url", "").strip()
    s += '<defs><clipPath id="profileAvatar"><circle cx="140" cy="116" r="49"/></clipPath></defs>'
    if avatar:
        s += f'<image x="91" y="67" width="98" height="98" href="{esc(avatar)}" xlink:href="{esc(avatar)}" preserveAspectRatio="xMidYMid slice" clip-path="url(#profileAvatar)"/>'
    else:
        s += widget_text(140, 125, "SP", 27, "#ffffff", 800, "middle")
    s += widget_text(140, 199, CONFIG.get("name", "Shivasharanappa"), 16, "#f4f7fb", 800, "middle")
    s += widget_text(140, 221, "GENERATIVE AI ENGINEER INTERN", 8.5, purple, 700, "middle", .8)
    s += widget_text(140, 240, "Pragyan AI", 10.5, "#b8c8d6", 500, "middle")
    s += '<path d="M22 258H258" stroke="#34495d"/>'
    s += widget_metric(20, 273, 112, "Repositories", str(CONFIG.get("repo_count", 0)), accent)
    # contribution count is added by the activity card, so keep this tile factual and static-free.
    s += widget_metric(145, 273, 115, "Speciality", "GenAI", cyan)
    s += '</svg>'
    save_card("widget-profile.svg", s)


def render_widget_activity(data, rows):
    w, h = 620, 348
    accent, cyan, purple, gold = "#39df91", "#42c8d5", "#9a8cff", "#f3c969"
    total, active, busiest, streak, months, busiest_count = calculate_metrics(rows)
    s = widget_start(w, h, "GitHub activity", "LIVE PROFILE SNAPSHOT · LAST 365 DAYS", cyan)
    stats = [
        ("Contributions", f"{total:,}", accent),
        ("Active days", str(active), cyan),
        ("Current streak", f"{streak}d", purple),
        ("Repositories", str(CONFIG.get("repo_count", 0)), gold),
    ]
    for i, (label, value, color) in enumerate(stats):
        s += widget_metric(18+i*148, 68, 137, label, value, color)
    s += widget_text(22, 159, "MONTHLY CONTRIBUTIONS", 9.5, "#b8c8d6", 700, spacing=1.1)
    monthly = Counter()
    for day, count in rows:
        monthly[day.strftime("%Y-%m")] += count
    keys = sorted(monthly)[-6:]
    if not keys:
        keys = [date.today().strftime("%Y-%m")]
        monthly[keys[0]] = 0
    maxv = max([monthly[k] for k in keys] + [1])
    base = 286
    for i, key in enumerate(keys):
        x = 42+i*91
        val = monthly[key]
        bh = max(3, round(85*val/maxv)) if val else 3
        s += f'<rect x="{x}" y="{base-88}" width="48" height="88" rx="8" fill="#203244"/>'
        s += f'<rect x="{x}" y="{base-bh}" width="48" height="{bh}" rx="8" fill="url(#wtop)"/>'
        s += widget_text(x+24, base-bh-8, str(val), 8.5, accent if val else "#91a5b8", 700, "middle")
        label = date(int(key[:4]), int(key[5:7]), 1).strftime("%b")
        s += widget_text(x+24, base+17, label, 9, "#91a5b8", 500, "middle")
    s += widget_text(22, 329, f"Updated {data.get('as_of', 'daily sync')} · busiest day: {busiest}", 8.5, "#91a5b8")
    s += '</svg>'
    save_card("widget-activity.svg", s)


def render_widget_toolkit():
    w, h = 320, 348
    accent, cyan, purple, gold = "#39df91", "#42c8d5", "#9a8cff", "#f3c969"
    s = widget_start(w, h, "Core toolkit", "TECHNOLOGIES USED IN MY PROJECTS", purple)
    tools = [
        ("PYTHON", "SQL"), ("PYSPARK", "POWER BI"),
        ("LANGCHAIN", "FAISS"), ("STREAMLIT", "FASTAPI"),
        ("PANDAS", "NUMPY"), ("GROQ", "HUGGING FACE"),
    ]
    colors = [accent, cyan, purple, gold, accent, cyan]
    for i, pair in enumerate(tools):
        y = 76+i*39
        for j, label in enumerate(pair):
            x = 18+j*145
            color = colors[i] if j == 0 else (purple if i%2 == 0 else gold)
            s += f'<rect x="{x}" y="{y}" width="135" height="27" rx="9" fill="#1c2b3a" stroke="{color}" stroke-opacity=".48" filter="url(#wshadow)"/>'
            s += f'<path d="M{x+8} {y+1}H{x+127}" stroke="{color}" stroke-opacity=".55"/>'
            s += widget_text(x+67.5, y+18, label, 8.3, "#edf4f8", 700, "middle", .4)
    s += '<path d="M20 319H300" stroke="#35495d"/>'
    s += widget_text(20, 337, "LLMs  ·  RAG  ·  ML  ·  COMPUTER VISION", 8.2, "#b8c8d6", 600)
    s += '</svg>'
    save_card("widget-toolkit.svg", s)


def render_widget_about():
    w, h = 400, 226
    accent, cyan, purple = "#9a8cff", "#42c8d5", "#39df91"
    s = widget_start(w, h, "About me", "A QUICK INTRODUCTION", accent)
    lines = [
        ("Computer Science & Design graduate", 82, "#edf4f8", 600),
        ("PDA College of Engineering", 103, "#91a5b8", 400),
        ("Generative AI Engineer Intern at Pragyan AI", 139, "#edf4f8", 600),
        ("Building practical applications with Python,", 171, "#91a5b8", 400),
        ("LLMs, machine learning and computer vision.", 190, "#91a5b8", 400),
    ]
    for value, y, color, weight in lines:
        s += widget_text(22, y, value, 10.8, color, weight)
    s += f'<rect x="22" y="204" width="91" height="15" rx="7" fill="{purple}" fill-opacity=".17"/>'
    s += widget_text(67.5, 215, "PRACTICAL BUILDER", 7.2, purple, 700, "middle", .5)
    s += '</svg>'
    save_card("widget-about.svg", s)


def render_widget_experience():
    w, h = 420, 226
    accent, cyan, gold = "#39df91", "#42c8d5", "#f3c969"
    s = widget_start(w, h, "Experience", "INTERNSHIPS & HANDS-ON WORK", accent)
    s += '<circle cx="28" cy="84" r="4" fill="#39df91"/>'
    s += widget_text(43, 87, "Generative AI Engineer Intern", 10.5, "#edf4f8", 700)
    s += widget_text(43, 105, "Pragyan AI", 9.5, accent, 700)
    s += widget_text(43, 122, "Building practical Generative AI applications", 8.6, "#91a5b8")
    s += '<circle cx="28" cy="150" r="4" fill="#42c8d5"/>'
    s += widget_text(43, 153, "Big Data Analytics Intern", 10.5, "#edf4f8", 700)
    s += widget_text(43, 171, "Krugna Technologies", 9.5, cyan, 700)
    s += widget_text(43, 188, "Python · PySpark · SQL · Power BI", 8.6, "#91a5b8")
    s += '</svg>'
    save_card("widget-experience.svg", s)


def render_widget_education():
    w, h = 390, 226
    accent, gold = "#f3c969", "#9a8cff"
    s = widget_start(w, h, "Education", "ACADEMIC BACKGROUND", accent)
    s += '<path d="M24 87H365" stroke="#34495d"/>'
    s += widget_text(24, 82, "B.E. · Computer Science & Design", 10.2, "#edf4f8", 700)
    s += widget_text(24, 102, "PDA College of Engineering", 9.2, "#91a5b8")
    s += '<path d="M24 128H365" stroke="#34495d"/>'
    s += widget_text(24, 154, "Diploma · Mechanical Engineering", 10.2, "#edf4f8", 700)
    s += widget_text(24, 174, "Government Polytechnic, Gulbarga", 9.2, "#91a5b8")
    s += widget_text(24, 205, "Diploma completed in 2023", 8.2, gold, 700)
    s += '</svg>'
    save_card("widget-education.svg", s)


def render_widget_project(filename, title, category, description, accent):
    w, h = 390, 145
    s = widget_start(w, h, title, category, accent)
    s += f'<rect x="18" y="66" width="354" height="58" rx="12" fill="#1b2a39" stroke="{accent}" stroke-opacity=".35" filter="url(#wshadow)"/>'
    s += f'<path d="M30 67H360" stroke="{accent}" stroke-opacity=".55"/>'
    s += widget_text(32, 91, title, 11, "#edf4f8", 700)
    s += widget_text(32, 110, description, 8.6, "#91a5b8")
    s += f'<path d="M340 88h17m-7 -7l7 7 -7 7" stroke="{accent}" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
    s += '</svg>'
    save_card(filename, s)


def render_widget_contributions(rows):
    w, h = 1260, 172
    accent = "#39df91"
    s = widget_start(w, h, "Contribution map", "YOUR GITHUB CONTRIBUTIONS · LAST 365 DAYS", accent)
    if rows:
        first = rows[0][0]
        offset = (first.weekday()+1) % 7
        for i, (day, count) in enumerate(rows):
            col, row = (i+offset)//7, (i+offset)%7
            x, y = 24+col*22.6, 74+row*12.5
            color = "#1b2937" if count == 0 else ("#15533f" if count < 4 else "#17875e" if count < 10 else "#2dbd7e" if count < 22 else "#77f0b4")
            s += f'<rect x="{x:.1f}" y="{y:.1f}" width="15" height="9" rx="2" fill="{color}"/>'
        month_label = None
        for i, (day, count) in enumerate(rows):
            if day.day <= 7 and day.strftime("%b") != month_label:
                col = (i+offset)//7
                x = 24+col*22.6
                s += widget_text(x, 65, day.strftime("%b").upper(), 7.5, "#91a5b8", 600)
                month_label = day.strftime("%b")
        s += widget_text(24, 163, "LESS", 7.5, "#91a5b8", 700)
        for i, col in enumerate(("#1b2937", "#15533f", "#17875e", "#2dbd7e", "#77f0b4")):
            s += f'<rect x="{65+i*16}" y="153" width="10" height="9" rx="2" fill="{col}"/>'
        s += widget_text(155, 163, "MORE", 7.5, "#91a5b8", 700)
    else:
        s += widget_text(24, 100, "Contribution history will appear after the next sync.", 11, "#91a5b8")
    s += '</svg>'
    save_card("widget-contributions.svg", s)


def render_widget_cards(data, rows):
    render_widget_profile()
    render_widget_activity(data, rows)
    render_widget_toolkit()
    render_widget_about()
    render_widget_experience()
    render_widget_education()
    render_widget_project("widget-project-nammaclean.svg", "NammaClean AI", "COMPUTER VISION", "Waste classification with MobileNetV2", "#39df91")
    render_widget_project("widget-project-market.svg", "Live Market Sales Analysis", "DATA ANALYTICS", "Market data analysis project", "#42c8d5")
    render_widget_project("widget-project-voice.svg", "Document Voice Studio", "AI APPLICATION", "Document, text and voice workflows", "#9a8cff")
    render_widget_project("widget-project-loan.svg", "SmartLoan India", "PYTHON APPLICATION", "Loan information and EMI calculations", "#f3c969")
    render_widget_project("widget-project-campus.svg", "CampusScope", "COLLEGE DISCOVERY", "College information platform", "#42c8d5")
    render_widget_project("widget-project-imagestudio.svg", "PragyanAI Image Studio", "IMAGE PROCESSING", "Creative image processing tools", "#9a8cff")
    render_widget_contributions(rows)

def main():
    CARDS.mkdir(parents=True, exist_ok=True)
    data = load_data()
    rows = normalized_days(data)
    render_widget_cards(data, rows)
    render_hero()
    render_about()
    render_experience_education()
    render_learning()
    render_link_tile("github", "GitHub", "Explore my code and projects", 700)
    render_link_tile("linkedin", "LinkedIn", "Connect and follow my journey", 820)
    render_link_tile("email", "Email", "Get in touch", 940)
    render_activity(data, rows)
    for i, (project, filename) in enumerate(zip(
        CONFIG["featured_repos"], ["repo-speech.svg", "repo-fruit.svg", "repo-python.svg"]
    )):
        render_project(project, filename, 2150 + i * 260)
    render_contributions(rows)
    print(f"Rendered {len(list(CARDS.glob('*.svg')))} SVG cards ({'STATIC' if STATIC else 'animated'} mode).")

if __name__ == "__main__":
    main()

