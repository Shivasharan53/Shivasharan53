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


def render_dashboard(data, rows):
    """Render a single, compact developer dashboard for the profile README."""
    width, height = 1320, 930
    total, active, busiest, streak, months, busiest_count = calculate_metrics(rows)
    repo_count = int(CONFIG.get("repo_count", 0))
    avatar_url = CONFIG.get("avatar_url", "").strip()
    bg, panel, panel2 = "#0b1017", "#131c27", "#192533"
    text_color, muted = "#edf4f8", "#8ea1b5"
    green, cyan, purple, gold = "#39df91", "#42c8d5", "#9a8cff", "#f3c969"
    s = [f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
 width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Shivasharanappa developer dashboard">
<title>Shivasharanappa | Generative AI Engineer Dashboard</title>
<defs>
 <linearGradient id="dashBg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#080d14"/><stop offset="1" stop-color="#111b2a"/>
 </linearGradient>
 <linearGradient id="dashPanel" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#1a2735"/><stop offset="1" stop-color="#111a25"/>
 </linearGradient>
 <linearGradient id="dashTop" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#39df91"/><stop offset=".55" stop-color="#42c8d5"/><stop offset="1" stop-color="#9a8cff"/>
 </linearGradient>
 <linearGradient id="dashGreen" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#65f3ae"/><stop offset="1" stop-color="#138b62"/>
 </linearGradient>
 <filter id="dashShadow" x="-25%" y="-25%" width="155%" height="175%">
  <feGaussianBlur in="SourceAlpha" stdDeviation="7" result="blur"/>
  <feOffset in="blur" dx="0" dy="7" result="off"/>
  <feComponentTransfer in="off" result="shadow"><feFuncA type="linear" slope=".38"/></feComponentTransfer>
  <feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge>
 </filter>
 <filter id="dashGlow" x="-80%" y="-80%" width="260%" height="260%">
  <feGaussianBlur stdDeviation="9" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
 </filter>
 <pattern id="dashGrid" width="26" height="26" patternUnits="userSpaceOnUse">
  <path d="M26 0H0V26" fill="none" stroke="#9bb6cb" stroke-opacity=".035" stroke-width="1"/>
 </pattern>
 <clipPath id="avatarClip"><circle cx="150" cy="164" r="49"/></clipPath>
 <style>text{{font-family:Inter,Arial,Helvetica,sans-serif}}.muted{{fill:#8ea1b5}}</style>
</defs>
<rect width="1320" height="930" rx="28" fill="url(#dashBg)"/>
<rect width="1320" height="930" rx="28" fill="url(#dashGrid)"/>
<circle cx="1110" cy="110" r="170" fill="#2e9f83" opacity=".055" filter="url(#dashGlow)"/>
<circle cx="180" cy="765" r="150" fill="#6250b4" opacity=".06" filter="url(#dashGlow)"/>
''']
    def txt(x, y, value, size=12, color=text_color, weight=400, spacing=0, anchor="start"):
        s.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" letter-spacing="{spacing}" text-anchor="{anchor}">{esc(value)}</text>')
    def panel(x, y, w, h, accent=green, radius=19):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="url(#dashPanel)" stroke="{accent}" stroke-opacity=".26" filter="url(#dashShadow)"/>')
        s.append(f'<path d="M{x+radius} {y+1}H{x+w-radius}" stroke="{accent}" stroke-opacity=".6" stroke-width="2" stroke-linecap="round"/>')
    def small_panel(x, y, w, h, accent=green):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="13" fill="{panel2}" stroke="{accent}" stroke-opacity=".28"/>')
        s.append(f'<path d="M{x+13} {y+1}H{x+w-13}" stroke="{accent}" stroke-opacity=".42" stroke-width="1.4"/>')
    def chip(x, y, label, color=green, w=125):
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="25" rx="12" fill="{color}" fill-opacity=".10" stroke="{color}" stroke-opacity=".45"/>')
        txt(x+w/2, y+16.5, label, 10.3, color, 700, .25, "middle")
    def section_title(x, y, label, subtitle=""):
        txt(x, y, label, 11, green, 700, 2.1)
        if subtitle:
            txt(x, y+18, subtitle, 10, muted, 400, .2)

    # Top application bar
    s.append('<rect x="24" y="18" width="1272" height="46" rx="14" fill="#101923" stroke="#263747"/>')
    s.append('<circle cx="49" cy="41" r="13" fill="url(#dashTop)"/>')
    txt(49, 45.5, "S", 13, "#07131a", 800, 0, "middle")
    txt(72, 45, "SHIVA  /  DEVELOPER DASHBOARD", 11, text_color, 700, 1.7)
    s.append('<circle cx="1134" cy="41" r="4" fill="#39df91" filter="url(#dashGlow)"/>')
    txt(1147, 45, "PROFILE OVERVIEW", 10, muted, 700, 1.3)
    txt(1270, 45, "2026", 10, purple, 700, 1, "end")

    # Left profile panel
    panel(24, 82, 252, 390, green)
    txt(47, 112, "PROFILE", 10, green, 700, 2)
    s.append('<circle cx="150" cy="164" r="56" fill="#253c48" stroke="url(#dashTop)" stroke-width="3" filter="url(#dashGlow)"/>')
    s.append('<circle cx="150" cy="164" r="49" fill="#1c2a3c"/>')
    s.append('<image x="101" y="115" width="98" height="98" href="avatar.png" xlink:href="avatar.png" preserveAspectRatio="xMidYMid slice" clip-path="url(#avatarClip)"/>')
    txt(150, 245, CONFIG.get("name", "Shivasharanappa").upper(), 17, text_color, 800, .6, "middle")
    txt(150, 268, "GENERATIVE AI ENGINEER INTERN", 9.6, purple, 700, .75, "middle")
    txt(150, 291, "Pragyan AI", 12, muted, 500, .2, "middle")
    s.append('<path d="M47 310H253" stroke="#344454"/>')
    txt(48, 334, "EDUCATION", 9.5, gold, 700, 1.4)
    txt(48, 354, "B.E. · Computer Science & Design", 10.5, text_color, 600)
    txt(48, 372, "PDA College of Engineering", 10, muted, 400)
    small_panel(43, 390, 102, 40, green)
    small_panel(155, 390, 102, 40, cyan)
    txt(94, 407, str(repo_count), 16, green, 800, 0, "middle")
    txt(94, 420, "REPOSITORIES", 8, muted, 700, .8, "middle")
    txt(206, 407, f"{total:,}", 16, cyan, 800, 0, "middle")
    txt(206, 420, "CONTRIBUTIONS", 8, muted, 700, .8, "middle")
    txt(150, 454, "GITHUB  ·  LINKEDIN  ·  EMAIL", 8.5, muted, 700, 1, "middle")

    # Center activity and metrics
    panel(294, 82, 644, 390, cyan)
    section_title(318, 111, "GITHUB ACTIVITY", "A snapshot of the last 365 days")
    metric_data = [
        ("CONTRIBUTIONS", f"{total:,}", green),
        ("ACTIVE DAYS", str(active), cyan),
        ("PUBLIC REPOS", str(repo_count), purple),
    ]
    for i, (label, value, accent) in enumerate(metric_data):
        x = 315 + i*201
        small_panel(x, 143, 185, 76, accent)
        txt(x+15, 166, label, 8.7, muted, 700, .8)
        txt(x+15, 202, value, 25, accent, 800)
        s.append(f'<circle cx="{x+159}" cy="181" r="8" fill="{accent}" fill-opacity=".16"/>')
        s.append(f'<circle cx="{x+159}" cy="181" r="3.5" fill="{accent}"/>')

    txt(319, 250, "MONTHLY CONTRIBUTIONS", 9.5, muted, 700, 1.3)
    month_counts = Counter()
    for day, count in rows:
        month_counts[day.strftime("%Y-%m")] += count
    month_keys = sorted(month_counts)[-6:]
    if not month_keys:
        month_keys = [date.today().strftime("%Y-%m")]
        month_counts[month_keys[0]] = 0
    max_month = max([month_counts[k] for k in month_keys] + [1])
    baseline = 354
    for i, key in enumerate(month_keys):
        x = 340 + i*93
        value = month_counts[key]
        bar_h = max(3, round(63*value/max_month)) if value else 3
        s.append(f'<rect x="{x}" y="{baseline-64}" width="45" height="64" rx="7" fill="#253444"/>')
        s.append(f'<rect x="{x}" y="{baseline-bar_h}" width="45" height="{bar_h}" rx="7" fill="url(#dashGreen)"/>')
        txt(x+22.5, baseline-bar_h-7, str(value), 8.8, green if value else muted, 600, 0, "middle")
        mlabel = date(int(key[:4]), int(key[5:7]), 1).strftime("%b")
        txt(x+22.5, baseline+15, mlabel, 9.2, muted, 500, 0, "middle")

    txt(319, 392, "CONTRIBUTION MAP  ·  LAST 365 DAYS", 9.2, muted, 700, 1.15)
    if rows:
        first = rows[0][0]
        offset = (first.weekday()+1) % 7
        for i, (day, count) in enumerate(rows):
            col, row = (i+offset)//7, (i+offset)%7
            x, y = 319 + col*9.1, 402 + row*9
            color = "#1d2b37" if count == 0 else ("#145c48" if count < 4 else "#17845b" if count < 10 else "#29b976" if count < 22 else "#65edaa")
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="6.8" height="6.8" rx="1.8" fill="{color}"/>')
    txt(319, 465, f"Updated {data.get('as_of', 'daily sync')}  ·  {active} active days", 8.6, muted, 400)

    # Right stack panel
    panel(956, 82, 340, 390, purple)
    section_title(980, 111, "CORE TOOLKIT", "Technologies used across projects")
    tools = [
        ("PYTHON", "SQL"), ("PYSPARK", "POWER BI"),
        ("LANGCHAIN", "FAISS"), ("STREAMLIT", "FASTAPI"),
        ("PANDAS", "NUMPY"), ("GROQ", "HUGGING FACE"),
    ]
    for i, pair in enumerate(tools):
        yy = 151 + i*42
        chip(980, yy, pair[0], green if i%2==0 else cyan, 137)
        chip(1137, yy, pair[1], purple if i%2==0 else gold, 137)
    s.append('<path d="M980 414H1272" stroke="#344454"/>')
    txt(980, 438, "FOCUS", 9, gold, 700, 1.4)
    txt(1030, 438, "LLMs  ·  RAG  ·  ML  ·  COMPUTER VISION", 9.2, muted, 600, .1)

    # About panel
    panel(24, 493, 388, 382, purple)
    section_title(48, 524, "ABOUT ME", "Curious mind. Practical builder.")
    txt(48, 580, "Computer Science & Design graduate", 13, text_color, 700)
    txt(48, 603, "from PDA College of Engineering.", 12, muted, 400)
    txt(48, 642, "Currently a Generative AI Engineer", 12, text_color, 600)
    txt(48, 663, "Intern at Pragyan AI.", 12, muted, 400)
    txt(48, 702, "I enjoy building useful applications", 11.5, muted, 400)
    txt(48, 722, "across LLMs, data and computer vision.", 11.5, muted, 400)
    chip(48, 765, "GENAI", green, 86)
    chip(146, 765, "DATA", cyan, 86)
    chip(244, 765, "COMPUTER VISION", purple, 145)

    # Experience and education panel
    panel(426, 493, 400, 382, gold)
    section_title(450, 524, "EXPERIENCE & EDUCATION", "Learning through practical work")
    s.append('<circle cx="456" cy="566" r="4" fill="#39df91"/>')
    txt(472, 570, "Generative AI Engineer Intern", 12, text_color, 700)
    txt(472, 591, "Pragyan AI", 10.5, green, 700)
    txt(472, 609, "GenAI applications · LLMs · Python", 9.5, muted, 400)
    s.append('<circle cx="456" cy="638" r="4" fill="#42c8d5"/>')
    txt(472, 642, "Big Data Analytics Intern", 12, text_color, 700)
    txt(472, 663, "Krugna Technologies", 10.5, cyan, 700)
    txt(472, 681, "Python · PySpark · SQL · Power BI", 9.5, muted, 400)
    s.append('<path d="M450 704H801" stroke="#344454"/>')
    txt(450, 731, "EDUCATION", 9.5, gold, 700, 1.6)
    txt(450, 754, "B.E. · Computer Science & Design", 10.5, text_color, 600)
    txt(450, 772, "PDA College of Engineering", 9.5, muted, 400)
    txt(450, 806, "Diploma · Mechanical Engineering", 10.5, text_color, 600)
    txt(450, 824, "Government Polytechnic, Gulbarga", 9.5, muted, 400)
    txt(450, 853, "Degree completed  ·  Diploma completed in 2023", 8.2, muted, 400)

    # Project showcase panel
    panel(840, 493, 456, 382, green)
    section_title(864, 524, "SELECTED PROJECTS", "A few things I have built")
    projects = [
        ("NammaClean AI", "Waste classification with MobileNetV2"),
        ("Live Market Sales Analysis", "Market data analysis and forecasting"),
        ("Document Voice Studio", "Document-to-text and voice workflows"),
        ("SmartLoan India", "Loan discovery and EMI calculations"),
        ("CampusScope", "College information discovery"),
        ("PragyanAI Image Studio", "AI-powered image editing tools"),
    ]
    for i, (name, desc) in enumerate(projects):
        y = 545 + i*49
        accent = green if i%3==0 else cyan if i%3==1 else purple
        s.append(f'<rect x="860" y="{y}" width="416" height="43" rx="10" fill="#1a2936" stroke="{accent}" stroke-opacity=".23"/>')
        s.append(f'<rect x="860" y="{y}" width="4" height="43" rx="2" fill="{accent}"/>')
        txt(876, y+17, name, 10.8, text_color, 700)
        txt(876, y+33, desc, 8.7, muted, 400)
        txt(1257, y+26, "↗", 15, accent, 700, 0, "middle")

    txt(28, 907, "INNOVATE  ·  BUILD  ·  INSPIRE", 9, muted, 700, 2)
    txt(1290, 907, "GITHUB PROFILE  /  SHIVASHARAN53", 9, muted, 700, 1.1, "end")
    save_card("dashboard.svg", "\n".join(s))

def main():
    CARDS.mkdir(parents=True, exist_ok=True)
    data = load_data()
    rows = normalized_days(data)
    render_dashboard(data, rows)
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

