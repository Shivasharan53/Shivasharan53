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
    h = 150
    s = svg_start(h, title) + surface(h, delay)
    s += f'<g {delay_style(delay + 100)}>'
    s += f'<circle cx="81" cy="75" r="32" fill="{PANEL_ALT}" stroke="{GOLD}" stroke-opacity=".7"/>'
    label = {"github": "GH", "linkedin": "in", "email": "@"}[key]
    s += f'<text x="81" y="83" text-anchor="middle" font-size="22" font-weight="700" class="mint">{label}</text>'
    s += f'<text x="137" y="68" font-size="21" font-weight="700" fill="{TEXT}">{esc(title)}</text>'
    s += f'<text x="137" y="97" font-size="14" class="muted">{esc(subtitle)}</text>'
    s += f'<path d="M932 75h18m-7 -7l7 7 -7 7" fill="none" stroke="{GOLD}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></g>'
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
        return 0, 0, "—", 0, []
    counts = {day: count for day, count in rows}
    total = sum(counts.values())
    active = sum(count > 0 for count in counts.values())
    weekdays, monthly = Counter(), Counter()
    for day, count in rows:
        weekdays[day.strftime("%A")] += count
        monthly[day.strftime("%Y-%m")] += count
    busiest = weekdays.most_common(1)[0][0] if weekdays else "—"
    today = date.today()
    cursor = today if counts.get(today, 0) else today - timedelta(days=1)
    streak = 0
    while counts.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    months = []
    for key, value in sorted(monthly.items())[-12:]:
        year, month = map(int, key.split("-"))
        months.append((calendar.month_abbr[month], value))
    return total, active, busiest, streak, months

def render_activity(data, rows):
    h = 400
    total, active, busiest, streak, months = calculate_metrics(rows)
    s = svg_start(h, "GitHub activity summary") + surface(h, 1120)
    s += f'<g {delay_style(1220)}>'
    s += f'<text x="38" y="48" font-size="13" letter-spacing="3" class="gold">GITHUB ACTIVITY</text>'
    s += f'<text x="38" y="85" font-size="25" font-weight="700" fill="{TEXT}">Small steps. Consistent progress.</text>'
    if rows:
        stats = [("CONTRIBUTIONS", f"{total:,}", MINT), ("ACTIVE DAYS", f"{active:,}", MINT),
                 ("CURRENT STREAK", f"{streak} days", MINT), ("BUSIEST WEEKDAY", busiest, GOLD)]
    else:
        stats = [("CONTRIBUTIONS", "—", MINT), ("ACTIVE DAYS", "—", MINT),
                 ("CURRENT STREAK", "—", MINT), ("BUSIEST WEEKDAY", "—", GOLD)]
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

def main():
    CARDS.mkdir(parents=True, exist_ok=True)
    data = load_data()
    rows = normalized_days(data)
    render_hero()
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

