"""
Builds every SVG used by README.md and about-me.md into assets/cards/.

    python3 assets/build_cards.py

Needs Python 3 + Pillow (pip install pillow). Fonts, icons and photos are
embedded in each SVG so the cards render the same everywhere on GitHub.
Edit the DATA section below to change text, colours or links.
"""

import base64
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
OUT = A / "cards"
OUT.mkdir(exist_ok=True)

# ---------------------------------------------------------------- palette
INK = "#262833"
MUTED = "#6B6E7B"
BEIGE = "#F1F0EC"
SAND = "#E8DFBB"
LIME = "#E2F126"
YELLOW = "#F6C70F"
PINK = "#FF6CAE"
BLUE = "#385BEA"
TEAL = "#0D6260"
WHITE = "#FFFFFF"

# ---------------------------------------------------------------- helpers
WIDTHS = json.loads((A / "fonts" / "jost-widths.json").read_text())
_FONT_B64 = {}


def font_face(weights):
    css = []
    for w in sorted(set(weights)):
        if w not in _FONT_B64:
            _FONT_B64[w] = base64.b64encode((A / "fonts" / f"jost{w}.woff2").read_bytes()).decode()
        css.append(
            f"@font-face{{font-family:Jost;font-weight:{w};"
            f"src:url(data:font/woff2;base64,{_FONT_B64[w]}) format('woff2')}}"
        )
    return "".join(css)


def tw(text, size, weight=400):
    table = WIDTHS[str(weight)]
    return sum(table.get(c, 55) for c in text) * size / 100


def wrap(text, size, weight, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if tw(trial, size, weight) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def t(x, y, s, size, weight=400, fill=INK, anchor="start", extra=""):
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}" {extra}>{escape(s)}</text>'
    )


def img_uri(path, w, h, mode="cover", focus=(0.5, 0.5), fmt=None, quality=82, bg=None):
    """Resize an image to w x h (2x for retina) and return a data URI."""
    im = Image.open(path)
    has_alpha = im.mode in ("RGBA", "LA", "P")
    im = im.convert("RGBA" if has_alpha else "RGB")
    W, H = w * 2, h * 2
    if mode == "cover":
        scale = max(W / im.width, H / im.height)
        nw, nh = round(im.width * scale), round(im.height * scale)
        im = im.resize((nw, nh), Image.LANCZOS)
        left = min(max(0, round(nw * focus[0] - W / 2)), nw - W)
        top = min(max(0, round(nh * focus[1] - H / 2)), nh - H)
        im = im.crop((left, top, left + W, top + H))
    else:  # fit inside, keep ratio
        im.thumbnail((W, H), Image.LANCZOS)
    if bg and im.mode == "RGBA":
        base = Image.new("RGBA", im.size, bg)
        base.alpha_composite(im)
        im = base.convert("RGB")
    fmt = fmt or ("PNG" if im.mode == "RGBA" else "JPEG")
    buf = io.BytesIO()
    if fmt == "JPEG":
        im.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    else:
        im.save(buf, "PNG", optimize=True)
    mime = "image/png" if fmt == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}", im.width / 2, im.height / 2


def svg_uri(path):
    return "data:image/svg+xml;base64," + base64.b64encode(Path(path).read_bytes()).decode()


def face_uri(color):
    """The little avatar from the portfolio, recoloured to a single colour."""
    svg = (A / "icons" / "miniface-yellow.svg").read_text().replace("#E2F126", color)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def write(name, w, h, body, weights=(400, 500), title=""):
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>"
        f"<style>{font_face(weights)}text{{font-family:Jost,'Helvetica Neue',Helvetica,Arial,sans-serif}}</style>"
        f"{body}</svg>"
    )
    (OUT / f"{name}.svg").write_text(svg)
    print(f"  {name}.svg  {len(svg) // 1024} KB")


# ------------------------------------------------------ little decorations
def arrow_btn(cx, cy, r=19, bg=INK, fg=WHITE):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{bg}"/>'
        f'<path d="M{cx - 6} {cy} H{cx + 6} M{cx + 1} {cy - 5} L{cx + 6} {cy} L{cx + 1} {cy + 5}" '
        f'stroke="{fg}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    )


def float_y(inner, dist=6, dur=5, delay=0):
    return (
        f'<g>{inner}<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;0 {-dist};0 0" dur="{dur}s" begin="{delay}s" repeatCount="indefinite" '
        f'calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></g>'
    )


def spin(inner, cx, cy, dur=30, swing=None):
    if swing:  # gentle rocking instead of a full turn
        vals = f"0 {cx} {cy};{swing} {cx} {cy};0 {cx} {cy}"
        return (
            f'<g>{inner}<animateTransform attributeName="transform" type="rotate" values="{vals}" '
            f'dur="{dur}s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></g>'
        )
    return (
        f'<g>{inner}<animateTransform attributeName="transform" type="rotate" '
        f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/></g>'
    )


def burst(cx, cy, r, color, width=2.5):
    lines = []
    for ang in (0, 45, 100, 140):
        lines.append(
            f'<line x1="{cx}" y1="{cy - r}" x2="{cx}" y2="{cy + r}" transform="rotate({ang} {cx} {cy})"/>'
        )
    return f'<g stroke="{color}" stroke-width="{width}" stroke-linecap="round">{"".join(lines)}</g>'


def triangle(x, y, s, color, rot=0):
    pts = f"{x},{y} {x + s},{y + s * 0.35} {x + s * 0.25},{y + s}"
    return f'<polygon points="{pts}" fill="{color}" transform="rotate({rot} {x} {y})"/>'


def wave(x, y, length, color, amp=7, period=22, width=3, uid="w"):
    n = int(length / period) + 2
    d = f"M{x - period} {y} " + " ".join(f"q{period / 4} {-amp} {period / 2} 0 t{period / 2} 0" for _ in range(n))
    return (
        f'<clipPath id="{uid}"><rect x="{x}" y="{y - amp - width}" width="{length}" height="{2 * amp + 2 * width}"/></clipPath>'
        f'<g clip-path="url(#{uid})"><path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round">'
        f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{period} 0" dur="1.6s" repeatCount="indefinite"/>'
        f"</path></g>"
    )


def pill(x, y, label, size=12.5, fill=WHITE, color=INK, dot=None, h=26, weight=500):
    pad = 11
    dot_w = 14 if dot else 0
    w = tw(label, size, weight) + pad * 2 + dot_w
    out = f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}"/>'
    if dot:
        out += f'<circle cx="{x + pad + 4}" cy="{y + h / 2}" r="4" fill="{dot}"/>'
    out += t(f"{x + pad + dot_w:.1f}", f"{y + h / 2 + size * 0.36:.1f}", label, size, weight, color)
    return out, w


def pills(x, y, labels, **kw):
    out, cx = "", x
    for item in labels:
        label, dot = item if isinstance(item, tuple) else (item, None)
        s, w = pill(cx, y, label, dot=dot, **kw)
        out += s
        cx += w + 7
    return out


def card_frame(uid, w, h, fill, r=24, m=6):
    """Outer rounded card with a little breathing room so cards sit side by side."""
    return (
        f'<clipPath id="{uid}"><rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" rx="{r}"/></clipPath>'
        f'<rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" rx="{r}" fill="{fill}"/>'
    )


# =================================================================== DATA
PORTFOLIO = "https://jeremie.roberrini.com"

CASE_STUDIES = [
    dict(slug="gigapay-international-payments", company="Gigapay", title="Expanding to international payments",
         img="gigapay.png", panel="#DCE4FF", accent=BLUE),
    dict(slug="position-green-product-vision", company="Position Green", title="From concept to product vision",
         img="pg.png", panel="#D3EADC", accent=TEAL),
    dict(slug="snow-software-cloud-self-service", company="Snow Software", title="From on-prem to cloud self service",
         img="snow.png", panel="#D8EEF5", accent=YELLOW),
    dict(slug="nederman-industrial-hmi", company="Nederman", title="Industrial applications & HMI",
         img="nederman.png", panel="#FCE5C4", accent=PINK),
]
SMALL_STUDIES = [
    dict(slug="gigapay-customer-workflows", company="Gigapay", title="Improving customer workflows", dot=1),
    dict(slug="gigapay-design-system", company="Gigapay", title="Building a design system", dot=2),
    dict(slug="beikos-clinical-test", company="Beikos", title="From idea to clinical test", dot=3),
]

APPS = [
    dict(key="okay-weather", name="Okay Weather", icon="weather.png", tint="#ECE8FF", blob="#D6CCFF",
         line="Honest forecasts and a rain-aware widget", chips=["Web", "Android"]),
    dict(key="sundial", name="Sundial", icon="sundial.png", tint="#E1EAF6", blob=YELLOW,
         line="A sun-path clock for your home screen", chips=["Android", "Open source"]),
    dict(key="workout-journal", name="Workout Journal", icon="workout.png", tint="#FFE6EF", blob="#FFC2D8",
         line="A calm, simple workout log for the gym", chips=["Web", "Offline"]),
    dict(key="grateful", name="Grateful", icon="grateful.png", tint="#FAEDE9", blob="#F6CFC4",
         line="One good thing a day, a gratitude journal", chips=["Web", "Private"]),
    dict(key="little-stories", name="Little Stories", icon="stories.png", tint="#FFF2C6", blob="#FFD66B",
         line="A private journal of the people in your life", chips=["Web", "Offline"]),
    dict(key="nts", name="NTS Downloader", icon="nts.png", tint="#F3F8CF", blob=LIME,
         line="Save NTS radio episodes as tagged MP3s", chips=["Web", "Music"]),
    dict(key="smart-cv", name="Smart CV", icon="smartcv.png", tint="#E7E9FF", blob="#FFC2E0",
         line="An editable CV that prints clean", chips=["Web", "Tool"]),
]

RESOURCES = [
    dict(key="about", title="About me", line="Dancing, running, cooking, and the person behind the pixels",
         tint="#FFDDEB", chip="about-me.md"),
    dict(key="photos", title="Photos", line="Portraits for CVs, talks and LinkedIn, free to use",
         tint="#FFF2C6", chip="photos/"),
    dict(key="cv", title="CV & cover letter", line="UX designer and product owner versions, as PDF",
         tint="#DCE4FF", chip="cv/"),
    dict(key="links", title="Links", line="Guides, Figma kits and little tools I made",
         tint="#EEF6C8", chip="links.md"),
]

SOCIALS = [
    ("linkedin", "LinkedIn", "#0A66C2"),
    ("medium", "Medium", INK),
    ("dribbble", "Dribbble", "#EA4C89"),
    ("behance", "Behance", "#1769FF"),
    ("figma", "Figma", "#A259FF"),
    ("instagram", "Instagram", "#E1306C"),
    ("lovable", "Lovable", PINK),
]

JOURNEY = [
    ("Réunion", "born on a tropical island", YELLOW),
    ("Bordeaux", "economics school", PINK),
    ("Paris", "international trade degree", BLUE),
    ("London", "client management", LIME),
    ("Amsterdam", "switched to UX at Ironhack", PINK),
    ("Stockholm", "Snow Software, Gigapay", YELLOW),
    ("Malmö", "Position Green, Nederman", TEAL),
]

POLAROIDS = [
    dict(name="marathon", src="malmo-marathon.jpg", cap=["42.2 km in Malmö,", "still smiling somehow"], focus=(0.38, 0.34), rot=-3, tape=LIME),
    dict(name="kizomba", src="kizomba-festival.jpg", cap=["Kizomba festival", "nights in Albania"], focus=(0.55, 0.32), rot=2.5, tape=PINK),
    dict(name="dance", src="dance.png", cap=["Salsa & bachata,", "my weekly reset"], focus=(0.6, 0.45), rot=-1.5, tape=YELLOW),
    dict(name="bbq", src="bbq.png", cap=["BBQ with friends,", "spicy food guaranteed"], focus=(0.5, 0.55), rot=2, tape="#9BB5FF"),
    dict(name="forest", src="forest.png", cap=["Forest walks,", "poking at every plant"], focus=(0.55, 0.45), rot=-2.5, tape=LIME),
    dict(name="museum", src="museum-rings.jpg", cap=["Bread rings or sausages?", "The debate continues"], focus=(0.5, 0.45), rot=1.5, tape=PINK),
    dict(name="rainbow", src="bus-stop-rainbow.jpg", cap=["Swedish rain jacket,", "accidental rainbow"], focus=(0.55, 0.42), rot=-2, tape=YELLOW),
    dict(name="work-event", src="work-event.jpg", cap=["Pastry in one hand,", "feedback in the other"], focus=(0.45, 0.4), rot=2, tape="#9BB5FF"),
    dict(name="gala", src="position-green-gala.jpg", cap=["Position Green gala", "with the team"], focus=(0.5, 0.5), rot=-1.5, tape=LIME, wide=True),
]


# ================================================================ BUILDERS
def banner():
    W, H = 840, 300
    photo, _, _ = img_uri(ROOT / "photos" / "jeremie-roberrini-cutout.png", 340, 340, fmt="JPEG", quality=86, bg=BEIGE)
    body = (
        f'<clipPath id="bn"><rect width="{W}" height="{H}" rx="28"/></clipPath>'
        f'<g clip-path="url(#bn)"><rect width="{W}" height="{H}" fill="{BEIGE}"/>'
        + spin(burst(22, 300, 62, TEAL, 2.2), 22, 300, dur=40)
        + float_y(f'<circle cx="468" cy="70" r="9" fill="{PINK}"/>', 8, 5)
        + float_y(f'<circle cx="790" cy="240" r="6" fill="{BLUE}"/>', 6, 4, 1)
        + f'<image href="{photo}" x="505" y="-8" width="340" height="340"/>'
        + "</g>"
    )
    s, _ = pill(44, 38, "Hej, salut, hi!", size=13, fill=WHITE, dot=YELLOW)
    body += s
    body += t(42, 120, "Jeremie Roberrini", 54, 300)
    body += t(44, 166, "Product Designer", 36, 300)
    body += t(45, 200, "In Malmö, open to all of Europe", 15.5, 400, MUTED)
    body += pills(44, 226, [("UX strategy", LIME), ("Design systems", YELLOW), ("Accessibility", PINK), ("Little apps", BLUE)], size=12.5)
    write("banner", W, H, body, (300, 400, 500), "Jeremie Roberrini, Product Designer in Malmö")


def feature_cards():
    W, H = 420, 220
    face = face_uri(WHITE)
    # Portfolio
    body = card_frame("pf", W, H, INK)
    body += '<g clip-path="url(#pf)">'
    body += float_y(triangle(330, 26, 46, LIME, 8), 6, 6)
    body += f'<circle cx="400" cy="200" r="64" fill="{BLUE}"/>'
    body += wave(220, 192, 120, YELLOW, uid="pfw")
    body += "</g>"
    body += f'<circle cx="368" cy="128" r="30" fill="{WHITE}" opacity=".08"/>'
    body += f'<image href="{face}" x="334" y="94" width="68" height="68"/>'
    body += t(30, 48, "PORTFOLIO", 12, 500, LIME, extra='letter-spacing="2"')
    body += t(30, 92, "Design portfolio", 30, 400, WHITE)
    body += t(30, 120, "Case studies, process and outcomes", 15, 400, "#B9BBC6")
    body += t(30, 182, "jeremie.roberrini.com", 14, 500, LIME)
    write("start-portfolio", W, H, body, (400, 500), "Design portfolio, jeremie.roberrini.com")

    # Commonplace
    body = card_frame("cp", W, H, YELLOW)
    body += '<g clip-path="url(#cp)">'
    body += spin(burst(372, 60, 52, TEAL, 2.2), 372, 60, dur=36)
    body += float_y(f'<circle cx="360" cy="176" r="22" fill="{WHITE}"/>', 6, 5)
    body += f'<rect x="300" y="140" width="34" height="34" rx="8" fill="{PINK}" transform="rotate(14 317 157)"/>'
    body += "</g>"
    body += t(30, 48, "COMMONPLACE", 12, 500, INK, extra='letter-spacing="2"')
    body += t(30, 92, "Things I made & collect", 30, 400, INK)
    body += t(30, 120, "Guides, Figma kits, articles and tools", 15, 400, "#5B4A12")
    body += t(30, 182, "jeremie.roberrini.com/commonplace", 14, 500, INK)
    write("start-commonplace", W, H, body, (400, 500), "Commonplace: guides, Figma kits, articles and tools")


def case_cards():
    W, H = 420, 300
    for i, c in enumerate(CASE_STUDIES):
        uid = f"cs{i}"
        px, py, pw, ph = 18, 18, W - 36, 186
        src = A / "projects" / c["img"]
        iw = pw - 70
        uri, rw, rh = img_uri(src, iw, 400, mode="fit", fmt="JPEG", quality=84, bg=c["panel"])
        body = card_frame(uid, W, H, BEIGE)
        body += (
            f'<clipPath id="{uid}p"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16"/></clipPath>'
            f'<g clip-path="url(#{uid}p)"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="{c["panel"]}"/>'
            + float_y(f'<circle cx="{px + 30}" cy="{py + 34}" r="10" fill="{c["accent"]}"/>', 5, 5, i * 0.7)
            + f'<circle cx="{px + pw - 30}" cy="{py + 30}" r="12" fill="none" stroke="{WHITE}" stroke-width="5"/>'
            + f'<g filter="url(#{uid}s)"><image href="{uri}" x="{px + (pw - rw) / 2:.1f}" y="{py + 26}" width="{rw:.1f}" height="{rh:.1f}"/></g>'
            + "</g>"
            f'<filter id="{uid}s" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#262833" flood-opacity=".12"/></filter>'
        )
        lines = wrap(c["title"], 19, 500, 300)[:2]
        top = 230 if len(lines) == 2 else 238
        body += t(30, top, c["company"].upper(), 11.5, 500, MUTED, extra='letter-spacing="1.6"')
        for j, ln in enumerate(lines):
            body += t(30, top + 25 + j * 23, ln, 19, 500)
        body += arrow_btn(372, 252)
        write(f"case-{i + 1}", W, H, body, (500,), f"{c['company']}: {c['title']}")

    # small ones + "see all"
    W, H = 420, 140
    for i, c in enumerate(SMALL_STUDIES):
        uid = f"ss{i}"
        dot = svg_uri(A / "icons" / f"project-dot{c['dot']}.svg")
        body = card_frame(uid, W, H, BEIGE)
        body += f'<circle cx="70" cy="70" r="42" fill="{WHITE}"/><image href="{dot}" x="32" y="32" width="76" height="76"/>'
        body += t(130, 56, c["company"].upper(), 11.5, 500, MUTED, extra='letter-spacing="1.6"')
        lines = wrap(c["title"], 19, 500, 210)
        for j, ln in enumerate(lines[:2]):
            body += t(130, 82 + j * 23, ln, 19, 500)
        body += arrow_btn(374, 70)
        write(f"case-small-{i + 1}", W, H, body, (500,), f"{c['company']}: {c['title']}")

    body = card_frame("sa", W, H, INK)
    body += '<g clip-path="url(#sa)">' + float_y(triangle(250, 80, 60, LIME, -10), 6, 6) + wave(150, 118, 90, YELLOW, uid="saw") + "</g>"
    body += t(30, 60, "All case studies", 22, 500, WHITE)
    body += t(30, 86, "jeremie.roberrini.com/projects", 13.5, 400, "#B9BBC6")
    body += arrow_btn(374, 70, bg=LIME, fg=INK)
    write("case-all", W, H, body, (400, 500), "See all case studies")


def app_cards():
    W, H = 420, 150
    for i, a in enumerate(APPS):
        uid = f"ap{i}"
        icon, _, _ = img_uri(A / "icons" / a["icon"], 84, 84, fmt="PNG")
        body = card_frame(uid, W, H, a["tint"])
        body += f'<g clip-path="url(#{uid})">' + float_y(
            f'<circle cx="{W - 30}" cy="22" r="46" fill="{a["blob"]}" opacity=".9"/>', 7, 6, i * 0.5) + "</g>"
        body += (
            f'<clipPath id="{uid}i"><rect x="26" y="33" width="84" height="84" rx="22"/></clipPath>'
            f'<rect x="26" y="33" width="84" height="84" rx="22" fill="{WHITE}"/>'
            f'<image href="{icon}" x="26" y="33" width="84" height="84" clip-path="url(#{uid}i)"/>'
        )
        body += t(128, 56, a["name"], 21, 500)
        lines = wrap(a["line"], 14, 400, 215)
        for j, ln in enumerate(lines[:2]):
            body += t(128, 78 + j * 18, ln, 14, 400, MUTED)
        body += pills(128, 78 + len(lines[:2]) * 18 - 2, a["chips"], size=11, h=22, fill=WHITE)
        body += arrow_btn(380, 75, r=18)
        write(f"app-{a['key']}", W, H, body, (400, 500), f"{a['name']}: {a['line']}")

    body = card_frame("hub", W, H, INK)
    body += '<g clip-path="url(#hub)">'
    body += float_y(f'<circle cx="300" cy="40" r="12" fill="{PINK}"/>', 6, 5)
    body += spin(burst(250, 120, 34, LIME, 2), 250, 120, dur=30)
    body += "</g>"
    body += t(30, 62, "roberrini.com", 22, 500, WHITE)
    body += t(30, 88, "All my little apps in one place", 14, 400, "#B9BBC6")
    body += arrow_btn(380, 75, r=18, bg=LIME, fg=INK)
    write("app-hub", W, H, body, (400, 500), "roberrini.com: all my little apps")


def resource_illustration(key):
    if key == "about":
        face = face_uri(INK)
        return (
            float_y(f'<circle cx="68" cy="75" r="42" fill="{PINK}"/>', 4, 5)
            + f'<image href="{face}" x="38" y="45" width="60" height="60"/>'
            + f'<circle cx="104" cy="40" r="7" fill="{YELLOW}"/>'
        )
    if key == "photos":
        uri, _, _ = img_uri(ROOT / "photos" / "jeremie-roberrini-portrait.jpg", 56, 56, focus=(0.53, 0.3))
        return (
            f'<g transform="rotate(-10 60 76)"><rect x="32" y="44" width="62" height="70" rx="4" fill="{WHITE}" stroke="#E8D9A0"/></g>'
            f'<g transform="rotate(7 76 74)"><rect x="44" y="36" width="66" height="76" rx="4" fill="{WHITE}" stroke="#E8D9A0"/>'
            f'<clipPath id="ph"><rect x="49" y="41" width="56" height="56" rx="2"/></clipPath>'
            f'<image href="{uri}" x="49" y="41" width="56" height="56" clip-path="url(#ph)"/></g>'
            + float_y(f'<circle cx="34" cy="38" r="6" fill="{PINK}"/>', 4, 4)
        )
    if key == "cv":
        lines = "".join(
            f'<rect x="50" y="{58 + k * 10}" width="{36 - (k % 2) * 12}" height="4" rx="2" fill="#C7D1F5"/>' for k in range(4)
        )
        return (
            f'<rect x="38" y="34" width="62" height="82" rx="8" fill="{WHITE}"/>'
            f'<circle cx="54" cy="47" r="7" fill="{BLUE}"/>' + lines
            + float_y(
                f'<circle cx="98" cy="104" r="15" fill="{LIME}"/>'
                f'<path d="M91 104 l5 5 l9 -10" stroke="{INK}" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
                4, 4)
        )
    if key == "links":
        return (
            f'<g fill="none" stroke-width="7" stroke-linecap="round">'
            f'<rect x="28" y="56" width="50" height="30" rx="15" stroke="{TEAL}" transform="rotate(-30 53 71)"/>'
            f'<rect x="58" y="62" width="50" height="30" rx="15" stroke="{BLUE}" transform="rotate(-30 83 77)"/></g>'
            + float_y(f'<circle cx="104" cy="40" r="7" fill="{PINK}"/>', 4, 4)
        )
    return ""


def resource_cards():
    W, H = 420, 150
    for r in RESOURCES:
        uid = f"rs{r['key']}"
        body = card_frame(uid, W, H, r["tint"])
        body += resource_illustration(r["key"])
        body += t(140, 56, r["title"], 21, 500)
        lines = wrap(r["line"], 14, 400, 200)
        for j, ln in enumerate(lines[:2]):
            body += t(140, 78 + j * 18, ln, 14, 400, MUTED)
        s, _ = pill(140, 78 + len(lines[:2]) * 18 - 2, r["chip"], size=11, h=22)
        body += s + arrow_btn(380, 75, r=18)
        write(f"repo-{r['key']}", W, H, body, (400, 500), f"{r['title']}: {r['line']}")


def social_pills():
    H = 44
    for key, label, color in SOCIALS:
        w = tw(label, 15, 500) + 60
        body = (
            f'<rect x="1" y="1" width="{w - 2:.1f}" height="{H - 2}" rx="{(H - 2) / 2}" fill="{WHITE}" stroke="#D9D7CF" stroke-width="1.5"/>'
            f'<circle cx="23" cy="22" r="6" fill="{color}"/>' + t(37, 27.5, label, 15, 500)
        )
        write(f"social-{key}", round(w), H, body, (500,), label)


def journey():
    W, H = 840, 270
    xs = [62 + i * 119 for i in range(len(JOURNEY))]
    ys = [140 if i % 2 == 0 else 170 for i in range(len(JOURNEY))]
    d = f"M{xs[0]} {ys[0]} " + " ".join(
        f"C{(xs[i - 1] + xs[i]) / 2} {ys[i - 1]} {(xs[i - 1] + xs[i]) / 2} {ys[i]} {xs[i]} {ys[i]}" for i in range(1, len(xs))
    )
    body = f'<rect width="{W}" height="{H}" rx="28" fill="{BEIGE}"/>'
    body += t(30, 44, "7 cities · 4 countries · 2 languages", 15, 500)
    body += t(W - 30, 44, "one coffee culture at a time", 13, 400, MUTED, "end")
    body += (
        f'<path d="{d}" stroke="{INK}" stroke-opacity=".35" stroke-width="2.5" fill="none" stroke-dasharray="2 9" stroke-linecap="round">'
        f'<animate attributeName="stroke-dashoffset" from="22" to="0" dur="1.4s" repeatCount="indefinite"/></path>'
        f'<circle r="6" fill="{PINK}"><animateMotion dur="9s" repeatCount="indefinite" path="{d}"/></circle>'
    )
    for i, (city, note, color) in enumerate(JOURNEY):
        x, y = xs[i], ys[i]
        last = i == len(JOURNEY) - 1
        if last:
            body += (
                f'<circle cx="{x}" cy="{y}" r="13" fill="{color}" opacity=".35">'
                f'<animate attributeName="r" values="13;22;13" dur="2.4s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values=".35;0;.35" dur="2.4s" repeatCount="indefinite"/></circle>'
            )
        body += f'<circle cx="{x}" cy="{y}" r="13" fill="{color}"/><circle cx="{x}" cy="{y}" r="5" fill="{WHITE}"/>'
        up = i % 2 == 0
        ty = y - 52 if up else y + 40
        body += t(x, ty, city, 16.5, 500, anchor="middle")
        for j, ln in enumerate(wrap(note, 12.5, 400, 108)[:2]):
            body += t(x, ty + 18 + j * 15, ln, 12.5, 400, MUTED, "middle")
    write("journey", W, H, body, (400, 500), "Réunion, Bordeaux, Paris, London, Amsterdam, Stockholm, Malmö")


def polaroids():
    for p in POLAROIDS:
        wide = p.get("wide", False)
        pw, ph = (408, 240) if wide else (248, 240)
        W, H = pw + 72, 372
        fx, fy = 36, 34
        uri, _, _ = img_uri(A / "about" / p["src"], pw, ph, focus=p["focus"], fmt="JPEG", bg=WHITE)
        cx, cy = W / 2, H / 2
        body = (
            f'<filter id="sh" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#262833" flood-opacity=".18"/></filter>'
            f'<g transform="rotate({p["rot"]} {cx} {cy})">'
            f'<rect x="{fx - 16}" y="{fy - 16}" width="{pw + 32}" height="{ph + 104}" rx="6" fill="{WHITE}" filter="url(#sh)"/>'
            f'<image href="{uri}" x="{fx}" y="{fy}" width="{pw}" height="{ph}" preserveAspectRatio="xMidYMid slice"/>'
        )
        for j, ln in enumerate(p["cap"]):
            body += t(cx, fy + ph + 38 + j * 23, ln, 17, 400, INK, "middle")
        body += (
            f'<rect x="{cx - 38}" y="{fy - 28}" width="76" height="24" fill="{p["tape"]}" opacity=".85" '
            f'transform="rotate({-p["rot"] * 2} {cx} {fy - 16})"/></g>'
        )
        write(f"polaroid-{p['name']}", W, H, body, (400,), " ".join(p["cap"]))


if __name__ == "__main__":
    print("Building cards into", OUT.relative_to(ROOT))
    banner()
    feature_cards()
    case_cards()
    app_cards()
    resource_cards()
    social_pills()
    journey()
    polaroids()
