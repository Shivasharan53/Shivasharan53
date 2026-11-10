#!/usr/bin/env python3
"""
Render animated GitHub profile SVG cards.
Usage:
  python scripts/render_cards.py
  STATIC=1 python scripts/render_cards.py

Inputs:
  data/contributions.json (refreshed by .github/workflows/profile-cards.yml)
  cards_config.json (profile text, repo links, palette and optional portrait)
"""
from __future__ import annotations
import base64, calendar, json, os, re, shutil, subprocess
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cards"
DATA = ROOT / "data" / "contributions.json"
CFG = json.loads((ROOT / "cards_config.json").read_text(encoding="utf-8"))
STATIC = os.getenv("STATIC", "").strip().lower() in {"1", "true", "yes"}
C = CFG["colors"]
BG, PANEL, PANEL2, TEXT, MUTED, MINT, GOLD = (C[k] for k in ("bg","panel","panel2","text","muted","mint","gold"))
FONT = CFG.get("font_family", "Arial, Helvetica, sans-serif")
WIDTH = 1000
CSS = """
@keyframes rise { from { opacity:0; transform:translateY(18px) } to { opacity:1; transform:translateY(0) } }
@keyframes draw { from { stroke-dashoffset:1200 } to { stroke-dashoffset:0 } }
@keyframes glow { 0%,100% { opacity:.45 } 50% { opacity:1 } }
@keyframes drift { from { transform:translateX(-12px) } to { transform:translateX(12px) } }
"""
def esc(v): return escape(str(v))
def anim_attrs(delay=0, duration=700):
    if STATIC: return 'opacity="1"'
    return f'style="opacity:0;animation:rise {duration}ms cubic-bezier(.2,.7,.2,1) {delay}ms forwards"'
def svg_start(h, title):
    css = "" if STATIC else CSS + "@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;opacity:1!important;transform:none!important;stroke-dashoffset:0!important}}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{h}" viewBox="0 0 {WIDTH} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title><defs>
<linearGradient id="accent" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{MINT}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="{TEXT}" stroke-opacity=".035"/></pattern>
<style>{css} text{{font-family:{FONT}}} .muted{{fill:{MUTED}}} .mint{{fill:{MINT}}} .gold{{fill:{GOLD}}}</style>
</defs><rect width="1000" height="{h}" rx="26" fill="{BG}"/><rect width="1000" height="{h}" rx="26" fill="url(#grid)"/>'''
def end(): return "</svg>\n"
def card_bg(h, inset=0):
    return f'<rect x="{inset}" y="{inset}" width="{1000-2*inset}" height="{h-2*inset}" rx="24" fill="{PANEL}" stroke="{MINT}" stroke-opacity=".24"/>'
def save(name, content):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(content + end(), encoding="utf-8")

def font_embed():
    # Optional local TTF can be supplied in assets/fonts/profile.ttf.
    font = ROOT / "assets" / "fonts" / "profile.ttf"
    if not font.exists(): return ""
    subset = ROOT / "cards" / "profile-subset.woff"
    subset.parent.mkdir(exist_ok=True)
    try:
        subprocess.run(["pyftsubset", str(font), f"--output-file={subset}",
                        "--flavor=woff", "--unicodes=U+0000-00FF"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        payload = base64.b64encode(subset.read_bytes()).decode("ascii")
        return f"@font-face{{font-family:Profile;src:url(data:font/woff;base64,{payload}) format('woff');font-weight:100 900}}"
    except (OSError, subprocess.CalledProcessError):
        print("pyftsubset unavailable; keeping brand fallback Arial.")
        return ""

def load_data():
    if not DATA.exists():
        return {"days": [], "weeks": [], "current_streak": 0, "longest_streak": 0,
                "total_contributions": 0, "as_of": "No contribution data yet"}
    obj = json.loads(DATA.read_text(encoding="utf-8"))
    # Accept GraphQL-shaped cache or the normalized data file.
    return obj

def normalize_days(data):
    raw = data.get("days", [])
    if raw and isinstance(raw[0], dict) and "date" in raw[0]:
        return [(x["date"], int(x.get("count", x.get("contributionCount", 0)))) for x in raw]
    weeks = data.get("weeks", [])
    result = []
    for week in weeks:
        for d in week.get("contributionDays", []):
            result.append((d["date"], int(d.get("contributionCount", 0))))
    return sorted(result)

def metrics(days, data):
    today = date.today()
    dct = {date.fromisoformat(d): n for d,n in days}
    monthly = defaultdict(int)
    for d,n in days:
        dt = date.fromisoformat(d)
        monthly[dt.strftime("%b")] += n
    active = sum(n > 0 for _,n in days)
    total = sum(n for _,n in days)
    weekdays = Counter()
    for d,n in days:
        if n: weekdays[date.fromisoformat(d).strftime("%A")] += n
    busiest = weekdays.most_common(1)[0][0] if weekdays else "—"
    # Count current streak from today, allowing yesterday when today has no activity.
    cursor = today if dct.get(today,0) else today - timedelta(days=1)
    streak = 0
    while dct.get(cursor,0) > 0:
        streak += 1
        cursor -= timedelta(days=1)
    current = int(data.get("current_streak", streak)) if data.get("current_streak") is not None else streak
    return monthly, total, active, busiest, current

def hero():
    h=300
    s=svg_start(h,"Shivasharanappa | Generative AI Engineer Intern")
    s+=card_bg(h)
    s+=f'<circle cx="820" cy="150" r="104" fill="{MINT}" opacity=".065"/><circle cx="820" cy="150" r="78" fill="none" stroke="url(#accent)" stroke-width="2" stroke-dasharray="5 9" {"" if STATIC else ""}>'
    if not STATIC: s+='<animateTransform attributeName="transform" type="rotate" from="0 820 150" to="360 820 150" dur="30s" repeatCount="indefinite"/>'
    s+='</circle>'
    s+=f'<text x="58" y="68" font-size="15" letter-spacing="4" class="gold" {anim_attrs(0)}>GENERATIVE AI · PYTHON · SOFTWARE</text>'
    s+=f'<text x="58" y="137" font-size="46" font-weight="700" fill="{TEXT}" {anim_attrs(180)}>{esc(CFG["name"])}</text>'
    s+=f'<text x="60" y="181" font-size="23" class="mint" {anim_attrs(340)}>{esc(CFG["role"])}</text>'
    s+=f'<text x="60" y="222" font-size="17" class="muted" {anim_attrs(500)}>{esc(CFG["tagline"])}</text>'
    portrait=CFG.get("portrait_url","").strip()
    if portrait:
        s+=f'<clipPath id="portraitClip"><circle cx="820" cy="150" r="58"/></clipPath><image href="{esc(portrait)}" x="762" y="92" width="116" height="116" preserveAspectRatio="xMidYMid slice" clip-path="url(#portraitClip)"/>'
    else:
        s+=f'<path d="M820 96L834 136L874 150L834 164L820 204L806 164L766 150L806 136Z" fill="url(#accent)"/><circle cx="820" cy="150" r="8" fill="{BG}"/>'
    s+=f'<text x="60" y="273" font-size="12" letter-spacing="2" class="muted">PDA COLLEGE OF ENGINEERING · COMPUTER SCIENCE &amp; DESIGN</text>'
    save("hero.svg",s)

def tile(name,title,subtitle,href,delay):
    s=svg_start(150,title)
    s+=f'<a xlink:href="{esc(href)}"><rect x="4" y="4" width="992" height="142" rx="20" fill="{PANEL}" stroke="{MINT}" stroke-opacity=".24"/>'
    s+=f'<circle cx="82" cy="75" r="34" fill="{PANEL2}" stroke="{GOLD}" stroke-opacity=".7"/>'
    label={"github":"GH","linkedin":"in","email":"@"}.get(name,"↗")
    s+=f'<text x="82" y="83" text-anchor="middle" font-size="23" font-weight="700" class="mint">{label}</text>'
    s+=f'<text x="142" y="67" font-size="23" font-weight="700" fill="{TEXT}">{esc(title)}</text><text x="142" y="98" font-size="15" class="muted">{esc(subtitle)}</text>'
    s+=f'<text x="932" y="87" text-anchor="middle" font-size="24" class="gold">↗</text></a>'
    return s+end()

def activity(data):
    days=normalize_days(data)
    monthly,total,active,busiest,streak=metrics(days,data)
    months=list(monthly.items())[-12:]
    if not months: months=[(m,0) for m in calendar.month_abbr[1:]]
    maxv=max([v for _,v in months]+[1])
    h=390
    s=svg_start(h,"GitHub monthly contributions and activity")
    s+=card_bg(h)
    s+=f'<text x="38" y="48" font-size="14" letter-spacing="3" class="gold">CONTRIBUTION OVERVIEW</text><text x="38" y="86" font-size="25" font-weight="700" fill="{TEXT}">Consistency, one commit at a time.</text>'
    for i,(label,value) in enumerate([("CONTRIBUTIONS",total),("ACTIVE DAYS",active),("CURRENT STREAK",f"{streak} days"),("BUSIEST DAY",busiest)]):
        x=38+i*236
        s+=f'<rect x="{x}" y="112" width="218" height="82" rx="15" fill="{PANEL2}"/>'
        s+=f'<text x="{x+17}" y="141" font-size="11" letter-spacing="1.5" class="muted">{label}</text><text x="{x+17}" y="174" font-size="24" font-weight="700" fill="{MINT if i!=3 else GOLD}">{esc(value)}</text>'
    base=324
    for i,(label,value) in enumerate(months):
        x=55+i*76
        bh=int(86*value/maxv)
        s+=f'<rect x="{x}" y="{base-86}" width="42" height="86" rx="8" fill="{PANEL2}"/>'
        if bh:
            s+=f'<rect x="{x}" y="{base-bh}" width="42" height="{bh}" rx="7" fill="url(#accent)" {"" if STATIC else f"style=\"transform-box:fill-box;transform-origin:bottom;animation:rise 650ms ease {650+i*55}ms both\""} />'
        s+=f'<text x="{x+21}" y="{base+22}" font-size="12" text-anchor="middle" class="muted">{esc(label)}</text>'
    s+=f'<text x="38" y="372" font-size="12" class="muted">Monthly contributions · Updated {esc(data.get("as_of","daily"))}</text>'
    save("activity.svg",s)

def repo_card(project,delay,name):
    h=178
    s=svg_start(h,project["name"])
    s+=card_bg(h)
    s+=f'<text x="38" y="42" font-size="12" letter-spacing="2" class="gold">FEATURED PROJECT</text>'
    s+=f'<text x="38" y="83" font-size="27" font-weight="700" fill="{TEXT}" {anim_attrs(delay)}>{esc(project["name"])}</text>'
    s+=f'<text x="38" y="116" font-size="16" class="muted">{esc(project["description"])}</text>'
    s+=f'<rect x="38" y="136" width="150" height="28" rx="14" fill="{MINT}" fill-opacity=".12" stroke="{MINT}" stroke-opacity=".45"/>'
    s+=f'<text x="113" y="155" text-anchor="middle" font-size="12" class="mint">VIEW REPOSITORY ↗</text>'
    s+=f'<a xlink:href="{esc(project["url"])}"><rect x="22" y="18" width="956" height="144" rx="18" fill="transparent"/></a>'
    save(name,s)

def contribution_graph(data):
    days=normalize_days(data)
    h=220
    s=svg_start(h,"GitHub contribution heatmap")
    s+=card_bg(h)
    s+=f'<text x="38" y="43" font-size="13" letter-spacing="2" class="gold">CONTRIBUTION GRAPH</text>'
    if not days:
        s+=f'<text x="38" y="110" font-size="17" class="muted">Contribution history will appear after the first daily sync.</text>'
    else:
        parsed=[(date.fromisoformat(d),n) for d,n in days]
        first=parsed[0][0]
        # Align to Sunday; each column is a week.
        offset=(first.weekday()+1)%7
        maxv=max([v for _,v in parsed]+[1])
        for idx,(dt,n) in enumerate(parsed):
            col=(idx+offset)//7; row=(idx+offset)%7
            x=38+col*13; y=72+row*17
            level=0 if n==0 else min(4,1+int(4*n/maxv))
            fills=[PANEL2,"#24463f","#356d5c","#4b9a7e",MINT]
            s+=f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{fills[level]}"/>'
        s+=f'<text x="38" y="204" font-size="11" class="muted">Less</text>'
        for i,col in enumerate(["#24463f","#356d5c","#4b9a7e",MINT]):
            s+=f'<rect x="{75+i*20}" y="195" width="11" height="11" rx="2" fill="{col}"/>'
        s+=f'<text x="170" y="205" font-size="11" class="muted">More · {len(days)} days shown</text>'
    save("contributions.svg",s)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    font_css=font_embed()
    global FONT
    if font_css:
        FONT="Profile, "+FONT
    data=load_data()
    hero()
    for key,title,sub,url in [
        ("github","GitHub","Explore my code and projects",CFG["links"]["github"]),
        ("linkedin","LinkedIn","Connect and follow my journey",CFG["links"]["linkedin"]),
        ("email","Email","Get in touch",CFG["links"]["email"]),
    ]:
        (OUT/f"{key}.svg").write_text(tile(key,title,sub,url,0),encoding="utf-8")
    activity(data)
    for p,delay,filename in zip(CFG["featured_repos"],[850,1050,1250],["repo-speech.svg","repo-fruit.svg","repo-python.svg"]):
        repo_card(p,delay,filename)
    contribution_graph(data)
    print(f"Rendered cards in {OUT} ({'STATIC' if STATIC else 'animated'} mode).")

if __name__=="__main__":
    main()
