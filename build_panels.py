#!/usr/bin/env python3
"""
Renders the animated panels for github.com/ankitorleaveit.

Run with no arguments and it uses the baked-in values below.
Run with GH_TOKEN set (as the GitHub Action does) and it pulls the live
numbers - contributions, streaks, repo and follower counts, and the real
contribution calendar - straight from the GitHub GraphQL API first.

    python scripts/build_panels.py            # offline, baked-in data
    GH_TOKEN=ghp_xxx python scripts/build_panels.py

Writes scan.svg, stack.svg, activity.svg, telemetry.svg, badges.svg to the
repository root. No third-party services involved.
"""
import json, os, sys, urllib.request, datetime

USER = os.environ.get("GH_USER", "ankitorleaveit")
OUT_DIR = os.environ.get("OUT_DIR", ".")

# --------------------------------------------------------------- static facts
D = {
    "handle":    USER,
    "name":      "Ankit Bhuyan",
    "bio":       "I code stuff.",
    "role":      "tech geek // builder",
    "base":      "India :: UTC +05:30",
    "status":    "building / learning / shipping",
    "languages": "Java, CSS, OOP",
    "platforms": "Android, iOS, Windows",
    "cloud":     "Google Cloud, AWS",
    "focus":     "AI / ML",
    "links":     "g.dev/anxhvr, in/ankkkuuu",
    "email":     "ankitbhuyans@gmail.com",
    # --- numbers below are refreshed from the API when GH_TOKEN is present ---
    "since":         "24 Feb 2022",
    "since_year":    2022,
    "contributions": 279,
    "streak":        3,
    "repos":         2,
    "followers":     4,
    "achievements":  5,
    "matrix":        None,   # list[list[int]] - 7 rows x N cols of daily counts
}

GQL = """
query($login:String!) {
  user(login:$login) {
    name bio location createdAt
    followers { totalCount }
    repositories(privacy:PUBLIC, ownerAffiliations:OWNER) { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}"""


def fetch_live():
    """Fill D from the GraphQL API. Silently keeps the defaults on any failure."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("no GH_TOKEN - using baked-in values")
        return
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": GQL, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": f"{USER}-profile-scan"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            u = json.load(r)["data"]["user"]
    except Exception as e:                                  # noqa: BLE001
        print(f"live fetch failed ({e}) - using baked-in values")
        return

    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]

    best = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        best = max(best, run)

    created = datetime.datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    D.update({
        "name":          u.get("name") or D["name"],
        "bio":           u.get("bio") or D["bio"],
        "since":         created.strftime("%-d %b %Y"),
        "since_year":    created.year,
        "contributions": cal["totalContributions"],
        "streak":        best,
        "repos":         u["repositories"]["totalCount"],
        "followers":     u["followers"]["totalCount"],
    })

    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"][-26:]
    D["matrix"] = [[w["contributionDays"][r]["contributionCount"]
                    if r < len(w["contributionDays"]) else 0
                    for w in weeks] for r in range(7)]
    print(f"live: {D['contributions']} contributions, streak {D['streak']}, "
          f"{D['repos']} repos, {D['followers']} followers")


import math, random


# ------------------------------------------------------------------ palette
BG      = "#04100c"
PANEL   = "#07160f"
INNER   = "#0a2219"
BORDER  = "#124d38"
ACCENT  = "#2ee6a6"
ACCENT2 = "#69ffc4"
DIM     = "#1e7a5c"
TEXT    = "#a9f5d8"
LABEL   = "#3fbf92"
CYAN    = "#5ad1ff"
AMBER   = "#ffc46b"
ROSE    = "#ff7ad9"
MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

EASE = "0.4 0 0.2 1"
OUT  = "0.16 1 0.3 1"


def kt(*v):
    return ";".join(f"{x:.4f}" for x in v)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def grid(A, W, H, cid):
    A(f'<g clip-path="url(#{cid})"><g stroke="#0c3527" stroke-width="1" opacity="0.45">')
    A('<animateTransform attributeName="transform" type="translate" values="0 0;-25 25" '
      'dur="9s" repeatCount="indefinite"/>')
    for x in range(-25, W + 50, 25):
        A(f'<line x1="{x}" y1="0" x2="{x}" y2="{H+25}"/>')
    for y in range(-25, H + 50, 25):
        A(f'<line x1="-25" y1="{y}" x2="{W+25}" y2="{y}"/>')
    A('</g></g>')


def shell(A, W, H):
    A(f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>')
    grid(A, W, H, "shellClip")
    A(f'<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" rx="13.5" fill="none" '
      f'stroke="{BORDER}" stroke-width="1.5">'
      f'<animate attributeName="stroke-opacity" values="0.6;1;0.6" dur="4.5s" calcMode="spline" '
      f'keySplines="{EASE};{EASE}" repeatCount="indefinite"/></rect>')


def titlebar(A, W, tabs, right_label):
    A(f'<rect x="1" y="1" width="{W-2}" height="38" rx="13" fill="#061a13"/>')
    A(f'<rect x="1" y="26" width="{W-2}" height="13" fill="#061a13"/>')
    A(f'<line x1="1" y1="39" x2="{W-1}" y2="39" stroke="{BORDER}"/>')
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        A(f'<circle cx="{22 + i*20}" cy="20" r="5.5" fill="{c}" opacity="0.55">'
          f'<animate attributeName="opacity" values="0.55;1;0.55" dur="3s" begin="{i*0.35}s" '
          f'calcMode="spline" keySplines="{EASE};{EASE}" repeatCount="indefinite"/></circle>')
    x = 92
    for i, (name, active) in enumerate(tabs):
        w = 8 * len(name) + 26
        A(f'<rect x="{x}" y="7" width="{w}" height="25" rx="6" '
          f'fill="{INNER if active else "none"}" stroke="{BORDER if active else "none"}" '
          f'stroke-width="1"/>')
        A(f'<text x="{x + w/2}" y="24" text-anchor="middle" font-family="{MONO}" font-size="11.5" '
          f'fill="{ACCENT2 if active else DIM}">{esc(name)}</text>')
        if active:
            A(f'<rect x="{x+8}" y="30" width="{w-16}" height="2" rx="1" fill="{ACCENT}">'
              f'<animate attributeName="opacity" values="0.5;1;0.5" dur="2.6s" calcMode="spline" '
              f'keySplines="{EASE};{EASE}" repeatCount="indefinite"/></rect>')
        x += w + 8
    A(f'<circle cx="{W-72}" cy="20" r="4" fill="{ACCENT2}">'
      f'<animate attributeName="opacity" values="1;0.15;1" dur="1.6s" calcMode="spline" '
      f'keySplines="{EASE};{EASE}" repeatCount="indefinite"/></circle>')
    A(f'<text x="{W-58}" y="24" font-family="{MONO}" font-size="10.5" fill="{DIM}">{right_label}</text>')


def panel(A, x, y, w, h, cycle, delay=0.0, label=None, right=None, ticks=True):
    per = 2 * (w + h)
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{PANEL}" opacity="0.9"/>')
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" stroke="{BORDER}" '
      f'stroke-width="1.2" stroke-dasharray="{per}">'
      f'<animate attributeName="stroke-dashoffset" values="{per};0;0;{per}" '
      f'keyTimes="0;0.055;0.955;1" calcMode="spline" keySplines="{OUT};0 0 1 1;{EASE}" '
      f'dur="{cycle}s" begin="{delay}s" repeatCount="indefinite"/></rect>')
    if ticks:
        for j, (cx, cy, sx, sy) in enumerate(((x, y, 1, 1), (x+w, y, -1, 1),
                                              (x, y+h, 1, -1), (x+w, y+h, -1, -1))):
            A(f'<path d="M{cx} {cy+sy*11} L{cx} {cy} L{cx+sx*11} {cy}" fill="none" '
              f'stroke="{ACCENT}" stroke-width="1.6" opacity="0">'
              f'<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.06;0.95;1" '
              f'calcMode="spline" keySplines="{OUT};0 0 1 1;{EASE}" dur="{cycle}s" '
              f'begin="{delay + j*0.07:.2f}s" repeatCount="indefinite"/></path>')
    if label:
        A(f'<text x="{x+18}" y="{y+26}" font-family="{MONO}" font-size="11.5" letter-spacing="2" '
          f'fill="{ACCENT}">{label}</text>')
    if right:
        A(f'<text x="{x+w-18}" y="{y+26}" text-anchor="end" font-family="{MONO}" font-size="10.5" '
          f'fill="{DIM}">{esc(right)}</text>')
    if label or right:
        A(f'<line x1="{x+18}" y1="{y+36}" x2="{x+w-18}" y2="{y+36}" stroke="{ACCENT}" '
          f'opacity="0.5" stroke-dasharray="{w-36}">'
          f'<animate attributeName="stroke-dashoffset" values="{w-36};0;0;{w-36}" '
          f'keyTimes="0;0.07;0.95;1" calcMode="spline" keySplines="{OUT};0 0 1 1;{EASE}" '
          f'dur="{cycle}s" begin="{delay}s" repeatCount="indefinite"/></line>')


def typed(A, uid, x, y, cycle, t0, dur, chars, chw, size, parts, caret=True, caret_col=ACCENT2):
    """parts = [(text, colour)] rendered as one monospace line that types itself in."""
    width = chars * chw + 2
    t1 = t0 + dur
    times = kt(0, t0, t1, 0.945, 1)
    A(f'<clipPath id="{uid}"><rect x="{x}" y="{y-size}" height="{size*1.5:.0f}" width="{width:.0f}">'
      f'<animate attributeName="width" values="0;0;{width:.0f};{width:.0f};0" keyTimes="{times}" '
      f'dur="{cycle}s" repeatCount="indefinite"/></rect></clipPath>')
    spans = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in parts)
    A(f'<text x="{x}" y="{y}" xml:space="preserve" font-family="{MONO}" font-size="{size}" '
      f'clip-path="url(#{uid})">{spans}</text>')
    if caret:
        A(f'<rect y="{y-size+1}" width="{chw*0.9:.1f}" height="{size+2}" fill="{caret_col}" '
          f'x="{x}" opacity="0">'
          f'<animate attributeName="x" values="{x};{x};{x+width:.0f};{x+width:.0f};{x}" '
          f'keyTimes="{times}" dur="{cycle}s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0;0;0.9;0;0" '
          f'keyTimes="{kt(0, t0, t1, min(t1+0.015, 0.94), 1)}" dur="{cycle}s" '
          f'repeatCount="indefinite"/></rect>')


def countup(A, x, y, target, cycle, t0, dur, size, colour):
    """Odometer: eased frames swapped with discrete opacity windows."""
    frames, n = [], 14
    for k in range(n + 1):
        p = k / n
        eased = 1 - (1 - p) ** 3
        frames.append(int(round(target * eased)))
    seen, uniq = set(), []
    for f in frames:
        if f not in seen or f == frames[-1]:
            uniq.append(f); seen.add(f)
    m = len(uniq)
    A(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="{size}" '
      f'font-weight="bold" fill="{colour}" opacity="1">'
      f'<animate attributeName="opacity" values="1;0;0" keyTimes="0;0.002;1" '
      f'dur="{cycle}s" calcMode="discrete" repeatCount="indefinite"/>{uniq[-1]}</text>')
    for k, val in enumerate(uniq):
        a = t0 + (dur * k / m)
        b = t0 + (dur * (k + 1) / m) if k < m - 1 else 0.95
        A(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="{size}" '
          f'font-weight="bold" fill="{colour}" opacity="0">'
          f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
          f'keyTimes="{kt(0, a, min(a+0.003, 0.99), min(b, 0.993), min(b+0.003, 0.996), 1)}" '
          f'dur="{cycle}s" calcMode="discrete" repeatCount="indefinite"/>{val}</text>')



def starfield(A, x, y, w, h, cid, layers=3):
    """Parallax dust drifting behind the instrument panel."""
    for L in range(layers):
        random.seed(200 + L)
        speed = 26 + L * 22
        dots = [(random.uniform(0, w), random.uniform(0, h), 0.6 + L * 0.35) for _ in range(16)]
        A(f'<g clip-path="url(#{cid})" opacity="{0.2 + L*0.12:.2f}">'
          f'<animateTransform attributeName="transform" type="translate" '
          f'values="0 0;{-w} 0" dur="{speed}s" repeatCount="indefinite"/>')
        for copy in (0, 1):
            for (dx, dy, r) in dots:
                A(f'<circle cx="{x + dx + copy*w:.1f}" cy="{y + dy:.1f}" r="{r:.1f}" '
                  f'fill="{ACCENT}"/>')
        A('</g>')


def crt(A, W, H, cid, cycle):
    """Scanlines, a rolling band, a power-on flash and a chromatic tear."""
    A(f'<g clip-path="url(#{cid})">')
    A(f'<g opacity="0.05" stroke="#000" stroke-width="1.6">')
    for y in range(0, H, 3):
        A(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>')
    A('</g>')
    A(f'<rect x="0" y="0" width="{W}" height="90" fill="url(#crtband)" opacity="0.5">'
      f'<animate attributeName="y" values="{-90};{H}" dur="7.5s" repeatCount="indefinite"/></rect>')
    # horizontal tear that jumps a few times per cycle
    for k, t in enumerate((0.33, 0.62, 0.86)):
        yy = 90 + k * 170
        A(f'<rect x="0" y="{yy}" width="{W}" height="14" fill="{ACCENT}" opacity="0">'
          f'<animate attributeName="opacity" values="0;0.12;0;0" '
          f'keyTimes="0;{t:.3f};{t+0.006:.3f};1" dur="{cycle}s" calcMode="discrete" '
          f'repeatCount="indefinite"/>'
          f'<animateTransform attributeName="transform" type="translate" values="0 0;9 0;0 0" '
          f'keyTimes="0;{t:.3f};1" dur="{cycle}s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    # power-on: a hairline that blooms open at the top of every cycle
    A(f'<g transform="translate(0 {H/2})">'
      f'<rect x="0" y="-1.5" width="{W}" height="3" fill="{ACCENT2}" opacity="0">'
      f'<animateTransform attributeName="transform" type="scale" values="1 0.2;1 1;1 60" '
      f'keyTimes="0;0.25;1" dur="0.55s" calcMode="spline" keySplines="{OUT};{EASE}" '
      f'repeatCount="indefinite" begin="0s"/>'
      f'<animate attributeName="opacity" values="0.95;0.55;0" keyTimes="0;0.35;1" dur="0.55s" '
      f'repeatCount="indefinite"/></rect></g>')
    A('</g>')


DEFS_COMMON = f'''
  <linearGradient id="crtband" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{ACCENT2}" stop-opacity="0"/>
    <stop offset="50%" stop-color="{ACCENT2}" stop-opacity="0.05"/>
    <stop offset="100%" stop-color="{ACCENT2}" stop-opacity="0"/>
  </linearGradient>
  <filter id="bloom" x="-70%" y="-70%" width="240%" height="240%">
    <feGaussianBlur stdDeviation="3" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>'''


# ==================================================================== scan.svg
def build_scan(path):
    W, H, CYCLE, ROT = 1000, 612, 20.0, 14.0
    random.seed(7)
    out = []
    A = out.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'role="img" aria-label="Animated profile scan console for Ankit Bhuyan (ankitorleaveit)">')
    A('<title>./profile-scan --target ankitorleaveit --live</title>')
    A(f'''<defs>{DEFS_COMMON}
  <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{ACCENT2}" stop-opacity="0.5"/>
    <stop offset="40%" stop-color="{ACCENT}" stop-opacity="0.14"/>
    <stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="glow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.2"/>
    <stop offset="65%" stop-color="{ACCENT}" stop-opacity="0.05"/>
    <stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="vignette" cx="42%" cy="38%" r="68%">
    <stop offset="0%" stop-color="{PANEL}" stop-opacity="0"/>
    <stop offset="55%" stop-color="{PANEL}" stop-opacity="0.10"/>
    <stop offset="82%" stop-color="#04120d" stop-opacity="0.6"/>
    <stop offset="100%" stop-color="#020a07" stop-opacity="0.93"/>
  </radialGradient>
  <linearGradient id="terminator" x1="0" y1="0" x2="1" y2="0.35">
    <stop offset="0%" stop-color="#020a07" stop-opacity="0.72"/>
    <stop offset="38%" stop-color="#020a07" stop-opacity="0.1"/>
    <stop offset="100%" stop-color="#020a07" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="scanline" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{ACCENT2}" stop-opacity="0"/>
    <stop offset="50%" stop-color="{ACCENT2}" stop-opacity="0.85"/>
    <stop offset="100%" stop-color="{ACCENT2}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="barfill" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{DIM}"/><stop offset="60%" stop-color="{ACCENT}"/>
    <stop offset="100%" stop-color="{ACCENT2}"/>
  </linearGradient>
  <linearGradient id="rainfade" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#fff" stop-opacity="0"/>
    <stop offset="35%" stop-color="#fff" stop-opacity="1"/>
    <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="shellClip"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  <clipPath id="orbClip"><circle cx="226" cy="248" r="132"/></clipPath>
  <clipPath id="rainClip"><rect x="453" y="51" width="530" height="394" rx="10"/></clipPath>
  <mask id="rainMask"><rect x="453" y="51" width="530" height="394" fill="url(#rainfade)"/></mask>
</defs>''')

    shell(A, W, H)
    titlebar(A, W, [("scan.sh", True), ("dossier.json", False), ("contact.md", False)], "LIVE")

    panel(A, 16, 50, 420, 396, CYCLE, 0.10, "VISUAL_MAP", "SECTOR 0x1F")
    panel(A, 452, 50, 532, 396, CYCLE, 0.28, "SUBJECT_DOSSIER", "v3.0")
    panel(A, 16, 456, 420, 124, CYCLE, 0.40, "BOOT_LOG", "tail -f")
    panel(A, 452, 456, 532, 124, CYCLE, 0.52, "COUNTERS", f'since {D["since"]}')

    # ---------------------------------------------------------- globe
    A('<clipPath id="lpClip"><rect x="16" y="50" width="420" height="396" rx="10"/></clipPath>')
    starfield(A, 16, 50, 420, 396, "lpClip")
    CX, CY, R, CW, CH = 226, 248, 132, 10.0, 11.5
    A(f'<circle cx="{CX}" cy="{CY}" r="{R+30}" fill="url(#glow)">'
      f'<animate attributeName="opacity" values="0.7;1;0.7" dur="5.5s" calcMode="spline" '
      f'keySplines="{EASE};{EASE}" repeatCount="indefinite"/></circle>')
    A(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="#05130e"/>')

    A(f'<g clip-path="url(#orbClip)" font-family="{MONO}" font-size="10.5" text-anchor="middle">')
    for r in range(int((2 * R) / CH) + 1):
        y = CY - R + r * CH + 5
        dy = (y - CY) / R
        if abs(dy) > 0.985:
            continue
        hw = R * math.sqrt(max(0.0, 1 - dy * dy))
        n = max(4, int(round((2 * hw) / CW)))
        cw, span = (2 * hw) / n, 2 * hw
        bright = 1.0 - 0.45 * abs(dy)
        cells = []
        for j in range(n):
            u = j / n
            nz = (math.sin(u * 12.2 + 1.1) * math.cos(dy * 4.3)
                  + 0.75 * math.sin(u * 25.0 + dy * 6.0)
                  + 0.45 * math.cos(u * 6.0 - dy * 9.0))
            if nz > 0.85:
                ch, fill, op = random.choice("#%@8"), ACCENT2, 0.85
            elif nz > 0.05:
                ch, fill, op = random.choice("+=*·"), ACCENT, 0.55
            else:
                if random.random() < 0.34:
                    continue
                ch, fill, op = random.choice(".:·"), DIM, 0.34
            cells.append((j, ch, fill, round(op * bright, 2)))
        A(f'<g><animateTransform attributeName="transform" type="translate" '
          f'values="0 0;{-span:.1f} 0" dur="{ROT}s" repeatCount="indefinite"/>')
        for copy in (0, 1):
            base = CX - hw + copy * span
            for (j, ch, fill, op) in cells:
                A(f'<text x="{base + j*cw + cw/2:.1f}" y="{y:.1f}" fill="{fill}" '
                  f'opacity="{op}">{ch}</text>')
        A('</g>')
    A('</g>')

    A(f'<g clip-path="url(#orbClip)" fill="none" stroke="{ACCENT}" opacity="0.3">')
    for lat in (-62, -31, 0, 31, 62):
        la = math.radians(lat)
        A(f'<ellipse cx="{CX}" cy="{CY + R*math.sin(la):.1f}" rx="{R*math.cos(la):.1f}" '
          f'ry="{R*math.cos(la)*0.2:.1f}"/>')
    for k in range(4):
        A(f'<ellipse cx="{CX}" cy="{CY}" rx="{R}" ry="{R}">'
          f'<animate attributeName="rx" values="{R};0;{R}" dur="{ROT}s" begin="-{k*ROT/4:.2f}s" '
          f'calcMode="spline" keySplines="{EASE};{EASE}" repeatCount="indefinite"/></ellipse>')
    A('</g>')
    A(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#terminator)" clip-path="url(#orbClip)"/>')
    A(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#vignette)" clip-path="url(#orbClip)"/>')

    A('<g clip-path="url(#orbClip)">')
    wedge = (f'M{CX} {CY} L{CX+R} {CY} A{R} {R} 0 0 0 '
             f'{CX + R*math.cos(math.radians(-72)):.1f} {CY + R*math.sin(math.radians(-72)):.1f} Z')
    A(f'<path d="{wedge}" fill="url(#sweep)">'
      f'<animateTransform attributeName="transform" type="rotate" from="0 {CX} {CY}" '
      f'to="360 {CX} {CY}" dur="4.6s" repeatCount="indefinite"/></path>')
    A(f'<line x1="{CX}" y1="{CY}" x2="{CX+R}" y2="{CY}" stroke="{ACCENT2}" stroke-width="1.8" '
      f'filter="url(#bloom)">'
      f'<animateTransform attributeName="transform" type="rotate" from="0 {CX} {CY}" '
      f'to="360 {CX} {CY}" dur="4.6s" repeatCount="indefinite"/></line>')
    A(f'<rect x="{CX-R}" y="{CY-R}" width="{2*R}" height="28" fill="url(#scanline)" opacity="0.55">'
      f'<animate attributeName="y" values="{CY-R};{CY+R-28};{CY-R}" dur="7s" calcMode="spline" '
      f'keySplines="{EASE};{EASE}" repeatCount="indefinite"/></rect>')
    A('</g>')
    A(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="{ACCENT}" stroke-width="1.6" opacity="0.9"/>')

    A(f'<g><animateTransform attributeName="transform" type="rotate" from="0 {CX} {CY}" '
      f'to="360 {CX} {CY}" dur="26s" repeatCount="indefinite"/>'
      f'<circle cx="{CX}" cy="{CY}" r="{R+9}" fill="none" stroke="{DIM}" stroke-width="1" '
      f'stroke-dasharray="1 8"/>')
    for k in range(24):
        a = math.radians(k * 15)
        lng = (k % 6 == 0)
        r1, r2 = R + 13, R + (24 if lng else 18)
        A(f'<line x1="{CX + r1*math.cos(a):.1f}" y1="{CY + r1*math.sin(a):.1f}" '
          f'x2="{CX + r2*math.cos(a):.1f}" y2="{CY + r2*math.sin(a):.1f}" stroke="{ACCENT}" '
          f'stroke-width="{1.6 if lng else 0.9}" opacity="{0.75 if lng else 0.4}"/>')
    A('</g>')
    A(f'<g><animateTransform attributeName="transform" type="rotate" from="360 {CX} {CY}" '
      f'to="0 {CX} {CY}" dur="18s" repeatCount="indefinite"/>'
      f'<circle cx="{CX}" cy="{CY}" r="{R+16}" fill="none" stroke="{ACCENT}" stroke-width="1.4" '
      f'stroke-dasharray="32 190" opacity="0.8" stroke-linecap="round"/></g>')
    A(f'<circle r="3.2" fill="{ACCENT2}" filter="url(#bloom)">'
      f'<animateMotion dur="9s" repeatCount="indefinite" '
      f'path="M{CX+R+16} {CY} A{R+16} {R+16} 0 1 1 {CX-R-16} {CY} '
      f'A{R+16} {R+16} 0 1 1 {CX+R+16} {CY}"/></circle>')

    for i, (bx, by) in enumerate([(-0.52, -0.40), (0.36, -0.60), (0.60, 0.26), (-0.30, 0.56)]):
        x, y = CX + bx * R * 0.92, CY + by * R * 0.92
        b = f"{i*0.92:.2f}s"
        A(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.8" fill="{ACCENT2}" opacity="0" filter="url(#bloom)">'
          f'<animate attributeName="opacity" values="0;1;0.35;0" dur="4.6s" begin="{b}" '
          f'calcMode="spline" keySplines="{OUT};{EASE};{EASE}" repeatCount="indefinite"/></circle>')
        A(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="none" stroke="{ACCENT2}" stroke-width="1.2">'
          f'<animate attributeName="r" values="3;20" dur="2.1s" begin="{b}" calcMode="spline" '
          f'keySplines="{OUT}" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0.85;0" dur="2.1s" begin="{b}" '
          f'calcMode="spline" keySplines="{EASE}" repeatCount="indefinite"/></circle>')
        if i == 1:
            for (sx, sy) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                A(f'<path d="M{x+sx*15:.1f} {y+sy*7:.1f} L{x+sx*15:.1f} {y+sy*15:.1f} '
                  f'L{x+sx*7:.1f} {y+sy*15:.1f}" fill="none" stroke="{ACCENT2}" stroke-width="1.4" '
                  f'opacity="0"><animate attributeName="opacity" values="0;1;1;0" '
                  f'keyTimes="0;0.08;0.8;1" dur="4.6s" begin="{b}" calcMode="spline" '
                  f'keySplines="{OUT};0 0 1 1;{EASE}" repeatCount="indefinite"/></path>')

    def wave(seed, amp):
        random.seed(seed)
        pts = [f"{34 + k*13.0:.1f} {432 - (random.uniform(-amp, amp) + amp*math.sin(k*0.9)*0.5):.1f}"
               for k in range(30)]
        return "M" + " L".join(pts)

    w1, w2, w3 = wave(3, 8), wave(9, 4), wave(21, 10)
    A(f'<path d="{w1}" fill="none" stroke="{ACCENT}" stroke-width="1.4" opacity="0.75" '
      f'stroke-linejoin="round"><animate attributeName="d" values="{w1};{w2};{w3};{w1}" '
      f'dur="4.4s" calcMode="spline" keySplines="{EASE};{EASE};{EASE}" repeatCount="indefinite"/></path>')
    A(f'<text x="34" y="414" font-family="{MONO}" font-size="10" fill="{DIM}">SIGNAL</text>')
    A(f'<text x="418" y="414" text-anchor="end" font-family="{MONO}" font-size="10" fill="{DIM}">'
      f'26.14N / 91.73E / UTC+05:30</text>')

    # ---------------------------------------------------------- data rain
    A(f'<g clip-path="url(#rainClip)" mask="url(#rainMask)" font-family="{MONO}" font-size="11" '
      f'fill="{ACCENT}" opacity="0.1">')
    random.seed(42)
    for c in range(8):
        x = 470 + c * 66
        glyphs = [random.choice("01#%$*+=/|:~^") for _ in range(16)]
        span = 16 * 16
        A(f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 {span}" '
          f'dur="{6 + c*1.2}s" repeatCount="indefinite"/>')
        for copy in (0, 1):
            for k, ch in enumerate(glyphs):
                A(f'<text x="{x}" y="{40 + copy*span + k*16}">{ch}</text>')
        A('</g>')
    A('</g>')

    # ---------------------------------------------------------- dossier
    rows = [
        ("HANDLE",    D["handle"],                      ACCENT2),
        ("NAME",      D["name"],                        TEXT),
        ("BIO",       D["bio"],                         TEXT),
        ("ROLE",      D["role"],                        TEXT),
        ("BASE",      D["base"],                        TEXT),
        ("STATUS",    D["status"],                      ACCENT2),
        ("LANGUAGES", D["languages"],                   TEXT),
        ("PLATFORMS", D["platforms"],                   TEXT),
        ("CLOUD",     D["cloud"],                       TEXT),
        ("FOCUS",     D["focus"],                       ACCENT2),
        ("UPTIME",    f'since {D["since"]}',            TEXT),
        ("FOLLOWERS", f'{D["followers"]} tracking',     TEXT),
        ("LINKS",     D["links"],                       TEXT),
        ("CONTACT",   D["email"],                       ACCENT2),
    ]
    Y0, RH, LX, VX = 104, 22.0, 470, 610
    A(f'<g font-family="{MONO}" font-size="12.5">')
    for i, (label, value, colour) in enumerate(rows):
        y = Y0 + i * RH
        t0 = (1.2 + i * 0.36) / CYCLE
        times = kt(0, t0, t0 + 0.30 / CYCLE, 0.945, 1)
        A(f'<line x1="{LX}" y1="{y+6}" x2="966" y2="{y+6}" stroke="{BORDER}" opacity="0.28"/>')
        A(f'<g opacity="1"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{times}" '
          f'calcMode="spline" keySplines="0 0 1 1;{OUT};0 0 1 1;{EASE}" dur="{CYCLE}s" '
          f'repeatCount="indefinite"/>'
          f'<animateTransform attributeName="transform" type="translate" '
          f'values="-14 0;-14 0;0 0;0 0;0 0" keyTimes="{times}" dur="{CYCLE}s" calcMode="spline" '
          f'keySplines="0 0 1 1;{OUT};0 0 1 1;0 0 1 1" repeatCount="indefinite"/>'
          f'<text x="{LX}" y="{y}" fill="{LABEL}">{label}</text></g>')
        typed(A, f"d{i}", VX, y, CYCLE, t0, 0.30 / CYCLE, len(value), 7.52, 12.5,
              [(value, colour)])
    A('</g>')

    BAR_Y = 424
    A(f'<text x="{LX}" y="{BAR_Y-8}" font-family="{MONO}" font-size="10.5" fill="{DIM}">DECODING PROFILE</text>')
    pct = ["0%", "14%", "29%", "43%", "58%", "72%", "86%", "SCAN COMPLETE"]
    for k, p in enumerate(pct):
        a = 0.06 + k * 0.082
        b = a + 0.082 if k < len(pct) - 1 else 0.95
        A(f'<text x="966" y="{BAR_Y-8}" text-anchor="end" font-family="{MONO}" font-size="10.5" '
          f'fill="{ACCENT if k == len(pct)-1 else LABEL}" opacity="0">'
          f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
          f'keyTimes="{kt(0, a, min(a+0.003,0.99), min(b,0.993), min(b+0.003,0.996), 1)}" '
          f'dur="{CYCLE}s" calcMode="discrete" repeatCount="indefinite"/>{p}</text>')
    A(f'<rect x="{LX}" y="{BAR_Y}" width="496" height="7" rx="3.5" fill="#0b2b21" '
      f'stroke="{BORDER}" stroke-width="0.8"/>')
    A(f'<rect x="{LX}" y="{BAR_Y}" width="496" height="7" rx="3.5" fill="url(#barfill)">'
      f'<animate attributeName="width" values="0;496;496;0" keyTimes="0;0.62;0.95;1" '
      f'calcMode="spline" keySplines="{EASE};0 0 1 1;{EASE}" dur="{CYCLE}s" '
      f'repeatCount="indefinite"/></rect>')
    A(f'<rect x="{LX}" y="{BAR_Y-2}" width="3" height="11" rx="1.5" fill="{ACCENT2}" '
      f'filter="url(#bloom)">'
      f'<animate attributeName="x" values="{LX};963;963;{LX}" keyTimes="0;0.62;0.95;1" '
      f'calcMode="spline" keySplines="{EASE};0 0 1 1;{EASE}" dur="{CYCLE}s" repeatCount="indefinite"/>'
      f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.62;0.66;1" '
      f'dur="{CYCLE}s" repeatCount="indefinite"/></rect>')

    # ---------------------------------------------------------- boot log
    log = [
        ("[ ok ] ", f'resolve github.com/{D["handle"]} ', "200"),
        ("[ ok ] ", "mount /dev/profile ", "ro"),
        ("[ ok ] ", "index repositories ", str(D["repos"])),
        ("[ ok ] ", "verify achievements ", f'{D["achievements"]}/5'),
        ("[ >> ] ", "streaming dossier ", "live"),
    ]
    for i, (tag, body, res) in enumerate(log):
        y = 510 + i * 14
        dots = "." * max(2, 34 - len(body))
        parts = [(tag, ACCENT if tag.strip("[ ]") == "ok" else AMBER),
                 (body, TEXT), (dots, DIM), (" " + res, ACCENT2)]
        n = len(tag) + len(body) + len(dots) + len(res) + 1
        typed(A, f"bl{i}", 34, y, CYCLE, (0.9 + i * 0.5) / CYCLE, 0.34 / CYCLE, n, 6.62, 11,
              parts, caret=(i == len(log) - 1))

    # ---------------------------------------------------------- counters
    tiles = [(D["contributions"], "CONTRIBUTIONS", ACCENT2),
             (D["streak"], "LONGEST STREAK", ACCENT2),
             (D["repos"], "REPOSITORIES", ACCENT2),
             (D["achievements"], "ACHIEVEMENTS", ACCENT2)]
    for i, (val, cap, col) in enumerate(tiles):
        x = 466 + i * 130
        A(f'<rect x="{x}" y="{494}" width="118" height="66" rx="8" fill="{INNER}" '
          f'stroke="{BORDER}" stroke-width="1"/>')
        A(f'<rect x="{x}" y="{494}" width="118" height="66" rx="8" fill="none" stroke="{ACCENT}" '
          f'stroke-width="1" opacity="0">'
          f'<animate attributeName="opacity" values="0;0.85;0;0" '
          f'keyTimes="{kt(0, 0.1 + i*0.03, 0.24 + i*0.03, 1)}" dur="{CYCLE}s" calcMode="spline" '
          f'keySplines="{OUT};{EASE};0 0 1 1" repeatCount="indefinite"/></rect>')
        countup(A, x + 59, 530, val, CYCLE, 0.10 + i * 0.03, 0.30, 25, col)
        A(f'<text x="{x+59}" y="550" text-anchor="middle" font-family="{MONO}" font-size="9" '
          f'letter-spacing="0.5" fill="{LABEL}">{cap}</text>')

    A(f'<text x="24" y="600" font-family="{MONO}" font-size="11.5" fill="{LABEL}">'
      f'$ curl -s github.com/{D["handle"]} | scan --deep</text>')
    A(f'<rect x="370" y="590" width="7" height="13" fill="{ACCENT2}">'
      f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" calcMode="discrete" '
      f'repeatCount="indefinite"/></rect>')
    A(f'<text x="976" y="600" text-anchor="end" font-family="{MONO}" font-size="10.5" fill="{DIM}">'
      f'exit 0 \u2022 connection held open</text>')
    # chromatic split on the footer prompt during glitch frames
    for col, dx, t in ((CYAN, -2.5, 0.331), (ROSE, 2.5, 0.331)):
        A(f'<text x="{24+dx}" y="600" font-family="{MONO}" font-size="11.5" fill="{col}" '
          f'opacity="0"><animate attributeName="opacity" values="0;0.75;0;0" '
          f'keyTimes="0;{t};{t+0.007:.3f};1" dur="{CYCLE}s" calcMode="discrete" '
          f'repeatCount="indefinite"/>$ curl -s github.com/{D["handle"]} | scan --deep</text>')
    crt(A, W, H, "shellClip", CYCLE)
    A('</svg>')
    svg = "\n".join(out)
    open(path, "w", encoding="utf-8").write(svg)
    return len(svg)


# =================================================================== stack.svg
def build_stack(path):
    W, H, CYCLE = 1000, 470, 16.0
    out = []
    A = out.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'role="img" aria-label="Editor panel: ankit.ts describing the stack of ankitorleaveit">')
    A('<title>ankit.ts</title>')
    A(f'<defs>{DEFS_COMMON}<clipPath id="shellClip"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>')
    shell(A, W, H)
    titlebar(A, W, [("ankit.ts", True), ("stack.json", False), ("README.md", False)], "UTF-8")

    panel(A, 16, 50, 968, 340, CYCLE, 0.1, None, None, ticks=True)
    A(f'<rect x="17" y="51" width="44" height="338" rx="9" fill="#061a13" opacity="0.75"/>')

    K, S, P, C, T, N, V = CYAN, ACCENT, LABEL, DIM, AMBER, ROSE, TEXT
    code = [
        [(f'// scanned from github.com/{D["handle"]}', C)],
        [("const ", K), ("ankit", V), (": ", P), ("Developer", T), (" = {", P)],
        [("  handle:    ", P), (f'"{D["handle"]}"', S), (",", P)],
        [("  name:      ", P), (f'"{D["name"]}"', S), (",", P)],
        [("  based:     ", P), ('"India"', S), (",", P), ("        // UTC+05:30", C)],
        [("  since:     ", P), (str(D["since_year"]), N), (",", P)],
        [("  stack:     [", P), ('"Java"', S), (", ", P), ('"CSS"', S), (", ", P), ('"OOP"', S), ("],", P)],
        [("  platforms: [", P), ('"Android"', S), (", ", P), ('"iOS"', S), (", ", P), ('"Windows"', S), ("],", P)],
        [("  cloud:     [", P), ('"Google Cloud"', S), (", ", P), ('"AWS"', S), ("],", P)],
        [("  focus:     ", P), ('"AI / ML"', S), (",", P)],
        [("  status:    ", P), ('"building"', S), (" as ", K), ("const", T), (",", P)],
        [("  reach:     ", P), (f'"{D["email"]}"', S), (",", P)],
        [("};", P)],
        [("", P)],
        [("export ", K), ("default ", K), ("ankit", V), (";", P), ("   // PRs welcome", C)],
    ]
    LH, Y0, CXX, FS, CHW = 21.0, 84, 76, 13.0, 7.82
    for i, parts in enumerate(code):
        y = Y0 + i * LH
        A(f'<text x="50" y="{y}" text-anchor="end" font-family="{MONO}" font-size="11" '
          f'fill="{DIM}" opacity="0.8">{i+1}</text>')
        n = sum(len(t) for t, _ in parts)
        if n == 0:
            continue
        t0 = (0.7 + i * 0.42) / CYCLE
        typed(A, f"s{i}", CXX, y, CYCLE, t0, max(0.12, n * 0.012) / CYCLE, n, CHW, FS, parts,
              caret=True)
    # active-line highlight sliding down the file
    A(f'<rect x="62" y="{Y0-15}" width="908" height="20" rx="4" fill="{ACCENT}" opacity="0.05">'
      f'<animate attributeName="y" values="{Y0-15};{Y0-15+14*LH};{Y0-15}" dur="{CYCLE}s" '
      f'calcMode="spline" keySplines="{EASE};{EASE}" repeatCount="indefinite"/></rect>')

    # console strip
    panel(A, 16, 400, 968, 54, CYCLE, 0.3, None, None, ticks=False)
    typed(A, "run1", 34, 424, CYCLE, 0.60, 0.12 / CYCLE, 16, 7.0, 12,
          [("$ ", ACCENT), ("node ankit.ts", TEXT)], caret=False)
    typed(A, "run2", 34, 442, CYCLE, 0.70, 0.16 / CYCLE, 42, 7.0, 12,
          [("\u2192 ", ACCENT2), (f'shipping since {D["since_year"]} \u2014 {D["bio"]}', LABEL)], caret=True)
    A(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.78;0.95;1" '
      f'calcMode="spline" keySplines="{OUT};0 0 1 1;{EASE}" dur="{CYCLE}s" repeatCount="indefinite"/>'
      f'<circle cx="905" cy="420" r="4" fill="{ACCENT2}" filter="url(#bloom)"/>'
      f'<text x="966" y="424" text-anchor="end" font-family="{MONO}" font-size="11" '
      f'fill="{ACCENT}">exit 0</text>'
      f'<text x="966" y="442" text-anchor="end" font-family="{MONO}" font-size="10" '
      f'fill="{DIM}">0 problems \u2022 main*</text></g>')
    crt(A, W, H, "shellClip", CYCLE)
    A('</svg>')
    svg = "\n".join(out)
    open(path, "w", encoding="utf-8").write(svg)
    return len(svg)


# ================================================================ activity.svg
def build_activity(path):
    W, H, CYCLE = 1000, 300, 14.0
    random.seed(19)
    out = []
    A = out.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'role="img" aria-label="Commit graph and signal matrix for ankitorleaveit">')
    A('<title>git log --graph</title>')
    A(f'<defs>{DEFS_COMMON}<clipPath id="shellClip"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>')
    shell(A, W, H)

    panel(A, 16, 16, 470, 268, CYCLE, 0.05, "COMMIT_GRAPH", "git log --graph")
    panel(A, 500, 16, 484, 268, CYCLE, 0.18, "SIGNAL_MATRIX", f'{D["contributions"]} contributions')

    # ------------------------------------------------ commit graph
    MAIN, FEAT, FIX = 190, 138, 242
    lanes = [
        (f"M60 {MAIN} L430 {MAIN}", ACCENT, 0.0),
        (f"M110 {MAIN} C140 {MAIN} 140 {FEAT} 170 {FEAT} L250 {FEAT} C285 {FEAT} 285 {MAIN} 315 {MAIN}", CYAN, 0.25),
        (f"M150 {MAIN} C180 {MAIN} 180 {FIX} 210 {FIX} L300 {FIX} C335 {FIX} 335 {MAIN} 365 {MAIN}", AMBER, 0.45),
    ]
    for i, (d, col, delay) in enumerate(lanes):
        A(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2" opacity="0.9" '
          f'stroke-linecap="round" stroke-dasharray="700">'
          f'<animate attributeName="stroke-dashoffset" values="700;0;0;700" '
          f'keyTimes="0;{0.1+delay*0.5:.3f};0.93;1" calcMode="spline" '
          f'keySplines="{OUT};0 0 1 1;{EASE}" dur="{CYCLE}s" repeatCount="indefinite"/></path>')
        # travelling packet along each lane
        A(f'<circle r="2.6" fill="{col}" filter="url(#bloom)" opacity="0.9">'
          f'<animateMotion dur="{5 + i}s" repeatCount="indefinite" path="{d}"/></circle>')

    nodes = [(60, MAIN, "init", ACCENT), (110, MAIN, "", ACCENT), (180, FEAT, "", CYAN),
             (225, FEAT, "feat: scan", CYAN), (215, FIX, "", AMBER), (275, FIX, "fix: camo", AMBER),
             (315, MAIN, "merge", ACCENT), (365, MAIN, "", ACCENT), (430, MAIN, "HEAD", ACCENT2)]
    for i, (x, y, lbl, col) in enumerate(nodes):
        b = 0.14 + i * 0.05
        A(f'<g transform="translate({x} {y})" opacity="1">'
          f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="{kt(0, b, 0.93, 1)}" '
          f'calcMode="spline" keySplines="{OUT};0 0 1 1;{EASE}" dur="{CYCLE}s" repeatCount="indefinite"/>'
          f'<animateTransform attributeName="transform" type="scale" values="0.2;1.25;1" '
          f'keyTimes="0;0.6;1" dur="0.7s" begin="{b*CYCLE:.2f}s" calcMode="spline" '
          f'keySplines="{OUT};{EASE}" repeatCount="indefinite"/>'
          f'<circle r="6" fill="{PANEL}" stroke="{col}" stroke-width="2.2"/>'
          f'<circle r="2.2" fill="{col}"/></g>')
        if lbl:
            A(f'<text x="{x}" y="{y - 16 if y != FIX else y + 24}" text-anchor="middle" '
              f'font-family="{MONO}" font-size="10" fill="{col}" opacity="1">'
              f'<animate attributeName="opacity" values="0;0.9;0.9;0" '
              f'keyTimes="{kt(0, b + 0.02, 0.93, 1)}" calcMode="spline" '
              f'keySplines="{OUT};0 0 1 1;{EASE}" dur="{CYCLE}s" repeatCount="indefinite"/>{lbl}</text>')
    A(f'<text x="34" y="272" font-family="{MONO}" font-size="10" fill="{DIM}">'
      f'main \u2022 {D["repos"]} repos \u2022 longest streak {D["streak"]} days</text>')

    # ------------------------------------------------ signal matrix
    COLS, ROWS, CELL, GAP = 26, 7, 14, 3
    X0, Y0 = 520, 80
    levels = [(DIM, 0.22), (ACCENT, 0.4), (ACCENT, 0.7), (ACCENT2, 0.95)]
    for c in range(COLS):
        for r in range(ROWS):
            if D["matrix"]:
                n_ = D["matrix"][r][c] if c < len(D["matrix"][r]) else 0
                lvl = 0 if n_ == 0 else 1 if n_ < 3 else 2 if n_ < 6 else 3
            else:
                v = random.random()
                lvl = 0 if v < 0.5 else 1 if v < 0.78 else 2 if v < 0.93 else 3
            col, op = levels[lvl]
            x = X0 + c * (CELL + GAP)
            y = Y0 + r * (CELL + GAP)
            delay = c * 0.05 + r * 0.02
            A(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{col}" '
              f'opacity="{op}">'
              f'<animate attributeName="opacity" values="0.06;{op};{op}" '
              f'keyTimes="0;{min(0.12+delay/CYCLE,0.5):.3f};1" calcMode="spline" '
              f'keySplines="{OUT};0 0 1 1" dur="{CYCLE}s" repeatCount="indefinite"/>'
              f'<animate attributeName="fill" values="{ACCENT2};{col};{col}" '
              f'keyTimes="0;{min(0.05 + (c*0.055) % 1.0, 0.9):.3f};1" dur="5.5s" '
              f'repeatCount="indefinite"/></rect>')
    A(f'<text x="520" y="{Y0 + ROWS*(CELL+GAP) + 26}" font-family="{MONO}" font-size="10" '
      f'fill="{DIM}">less</text>')
    for k, (col, op) in enumerate(levels):
        A(f'<rect x="{560 + k*18}" y="{Y0 + ROWS*(CELL+GAP) + 16}" width="12" height="12" rx="3" '
          f'fill="{col}" opacity="{op}"/>')
    A(f'<text x="{560 + 4*18 + 6}" y="{Y0 + ROWS*(CELL+GAP) + 26}" font-family="{MONO}" '
      f'font-size="10" fill="{DIM}">more</text>')
    A(f'<text x="966" y="{Y0 + ROWS*(CELL+GAP) + 26}" text-anchor="end" font-family="{MONO}" '
      f'font-size="10" fill="{DIM}">joined {D["since"]}</text>')
    crt(A, W, H, "shellClip", CYCLE)
    A('</svg>')
    svg = "\n".join(out)
    open(path, "w", encoding="utf-8").write(svg)
    return len(svg)


# ================================================================ telemetry.svg
def build_telemetry(path):
    W, H, CYCLE = 1000, 280, 12.0
    out = []
    A = out.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'role="img" aria-label="Hex dump of the profile buffer and scan gauges">')
    A('<title>xxd profile.bin</title>')
    A(f'<defs>{DEFS_COMMON}<clipPath id="shellClip"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>')
    shell(A, W, H)
    panel(A, 16, 16, 470, 248, CYCLE, 0.05, "HEX_DUMP", "xxd profile.bin")
    panel(A, 502, 16, 482, 248, CYCLE, 0.18, "SCAN_GAUGES", "realtime")

    data = f'{D["handle"]}|{D["name"]}|{D["focus"]}|{D["languages"]}'.encode("utf-8")
    data = data[:64].ljust(64, b"\x00")
    X0, Y0, BW, RH_ = 88, 72, 24, 22
    AX = 300
    xs, ys = [], []
    for i, byte in enumerate(data):
        row, col = i // 8, i % 8
        x, y = X0 + col * BW, Y0 + row * RH_
        xs.append(str(x - 3)); ys.append(str(y - 13))
        grp = (i // 4) % 2
        A(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="12.5" '
          f'fill="{TEXT if grp == 0 else LABEL}">{byte:02x}</text>')
        ch = chr(byte) if 32 <= byte < 127 else "."
        A(f'<text x="{AX + col*10}" y="{y}" font-family="{MONO}" font-size="12.5" '
          f'fill="{ACCENT2 if ch != "." else DIM}" opacity="{0.95 if ch != "." else 0.45}">'
          f'{esc(ch)}</text>')
    for row in range(8):
        A(f'<text x="34" y="{Y0 + row*RH_}" font-family="{MONO}" font-size="12.5" '
          f'fill="{DIM}">{row*8:04x}</text>')
    # read head stepping byte by byte
    A(f'<rect width="20" height="17" rx="3" fill="{ACCENT2}" opacity="0.28" x="{xs[0]}" y="{ys[0]}">'
      f'<animate attributeName="x" values="{";".join(xs)}" dur="8s" calcMode="discrete" '
      f'repeatCount="indefinite"/>'
      f'<animate attributeName="y" values="{";".join(ys)}" dur="8s" calcMode="discrete" '
      f'repeatCount="indefinite"/></rect>')
    A(f'<rect width="10" height="17" rx="3" fill="{ACCENT2}" opacity="0.2" '
      f'x="{AX-2}" y="{ys[0]}">'
      f'<animate attributeName="x" values="{";".join(str(AX - 2 + (i % 8) * 10) for i in range(64))}" '
      f'dur="8s" calcMode="discrete" repeatCount="indefinite"/>'
      f'<animate attributeName="y" values="{";".join(ys)}" dur="8s" calcMode="discrete" '
      f'repeatCount="indefinite"/></rect>')
    A(f'<text x="34" y="250" font-family="{MONO}" font-size="10" fill="{DIM}">'
      f'64 bytes \u2022 crc32 ok \u2022 utf-8</text>')
    A(f'<text x="468" y="250" text-anchor="end" font-family="{MONO}" font-size="10" fill="{ACCENT}" '
      f'opacity="0"><animate attributeName="opacity" values="0;0.95;0.95;0" '
      f'keyTimes="0;0.72;0.95;1" calcMode="spline" keySplines="{OUT};0 0 1 1;{EASE}" '
      f'dur="{CYCLE}s" repeatCount="indefinite"/>BUFFER DECODED</text>')

    gauges = [("INTEGRITY", 100, ACCENT2), ("UPLINK", 92, ACCENT), ("CACHE", 78, CYAN)]
    for i, (cap, pct, col) in enumerate(gauges):
        cx, cy, r = 582 + i * 161, 132, 50
        circ = 2 * math.pi * r
        A(f'<g transform="rotate(-90 {cx} {cy})">')
        A(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="8"/>')
        A(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="8" '
          f'stroke-linecap="round" stroke-dasharray="{circ:.1f}" '
          f'stroke-dashoffset="{circ*(1-pct/100):.1f}">'
          f'<animate attributeName="stroke-dashoffset" '
          f'values="{circ:.1f};{circ*(1-pct/100):.1f};{circ*(1-pct/100):.1f};{circ:.1f}" '
          f'keyTimes="0;0.35;0.94;1" calcMode="spline" keySplines="{OUT};0 0 1 1;{EASE}" '
          f'dur="{CYCLE}s" begin="{i*0.12:.2f}s" repeatCount="indefinite"/></circle>')
        A('</g>')
        for k in range(36):
            a = math.radians(k * 10 - 90)
            r1, r2 = r + 12, r + (18 if k % 3 == 0 else 15)
            A(f'<line x1="{cx + r1*math.cos(a):.1f}" y1="{cy + r1*math.sin(a):.1f}" '
              f'x2="{cx + r2*math.cos(a):.1f}" y2="{cy + r2*math.sin(a):.1f}" stroke="{col}" '
              f'stroke-width="{1.4 if k % 3 == 0 else 0.7}" opacity="{0.55 if k % 3 == 0 else 0.25}"/>')
        countup(A, cx - 6, cy + 8, pct, CYCLE, 0.05 + i * 0.04, 0.30, 24, col)
        A(f'<text x="{cx + 24}" y="{cy + 8}" font-family="{MONO}" font-size="13" fill="{col}" '
          f'opacity="0.8">%</text>')
        A(f'<text x="{cx}" y="{cy + 76}" text-anchor="middle" font-family="{MONO}" font-size="10" '
          f'letter-spacing="1.5" fill="{LABEL}">{cap}</text>')
        A(f'<circle cx="{cx}" cy="{cy}" r="{r+26}" fill="none" stroke="{col}" stroke-width="1" '
          f'opacity="0"><animate attributeName="r" values="{r};{r+30}" dur="2.6s" '
          f'begin="{i*0.7:.1f}s" calcMode="spline" keySplines="{OUT}" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values="0.55;0" dur="2.6s" begin="{i*0.7:.1f}s" '
          f'calcMode="spline" keySplines="{EASE}" repeatCount="indefinite"/></circle>')
    A(f'<text x="524" y="250" font-family="{MONO}" font-size="10" fill="{DIM}">'
      f'sampling 60hz \u2022 target ankitorleaveit</text>')
    crt(A, W, H, "shellClip", CYCLE)
    A('</svg>')
    svg = "\n".join(out)
    open(path, "w", encoding="utf-8").write(svg)
    return len(svg)


if __name__ == "__main__":
    fetch_live()
    p = lambda n: os.path.join(OUT_DIR, n)
    print("scan.svg     ", build_scan(p("scan.svg")))
    print("stack.svg    ", build_stack(p("stack.svg")))
    print("activity.svg ", build_activity(p("activity.svg")))
    print("telemetry.svg", build_telemetry(p("telemetry.svg")))
