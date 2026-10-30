#!/usr/bin/env python3
"""Animated profile banner: a crane lifts each floor into place, windows light up, data streams in.
Usage: python3 scripts/banner.py > assets/banner.svg
"""
import math
import random
import sys

W, H = 1200, 400
T = 13.0
C = math.cos(math.radians(30))
OX, OY, S = 268, 318, 24
X1, Y1 = 4.0, 3.0
NF, FH = 8, 0.78
FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif"
MONO = "ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace"
D = "'Arial Narrow','Roboto Condensed','Helvetica Neue',Arial,sans-serif"
rng = random.Random(11)


def P(x, y, z):
    return OX + (x - y) * C * S, OY + (x + y) * 0.5 * S - z * S


def pts(p):
    return " ".join(f"{a:.1f},{b:.1f}" for a, b in p)


def anim(attr, pp, mode="linear", tag="animate", extra=""):
    pp = sorted(pp)
    if pp[0][0] > 0:
        pp.insert(0, (0, pp[0][1]))
    if pp[-1][0] < T:
        pp.append((T, pp[-1][1]))
    kt, vs, last = [], [], -1.0
    for t, v in pp:
        k = max(0.0, min(1.0, t / T))
        k = k if k > last else last + 1e-4
        kt.append(f"{min(k, 1):.4f}")
        vs.append(str(v))
        last = k
    kt[-1] = "1"
    return (f'<{tag} attributeName="{attr}" dur="{T}s" repeatCount="indefinite" calcMode="{mode}" '
            f'keyTimes="{";".join(kt)}" values="{";".join(vs)}"{extra}/>')


land = [0.9 + k * 0.85 for k in range(NF)]          # floor k lands at this time
LIGHTS = land[-1] + 0.6
FADE = T - 0.9
o = []

# --- backdrop skyline (generic towers) with twinkling windows ---
sky = []
x = 18
while x < 560:
    w = rng.randint(26, 54)
    h = rng.randint(50, 150)
    sky.append(f'<rect x="{x}" y="{OY - 22 - h}" width="{w}" height="{h + 30}" fill="#141c25"/>')
    for wy in range(OY - 14 - h, OY - 4, 9):
        for wx in range(x + 5, x + w - 5, 8):
            if rng.random() < .18:
                sky.append(f'<rect class="tw" style="animation-delay:{rng.random() * 5:.2f}s" x="{wx}" y="{wy}" width="3" height="4" fill="#f2c94c"/>')
    x += w + rng.randint(4, 16)
o.append('<g opacity=".9">' + "".join(sky) + '</g>')
o.append(f'<rect x="0" y="{OY - 12}" width="560" height="120" fill="url(#ground)"/>')

# --- site plate ---
plate = [P(-1.4, -1.4, 0), P(X1 + 1.4, -1.4, 0), P(X1 + 1.4, Y1 + 1.4, 0), P(-1.4, Y1 + 1.4, 0)]
o.append(f'<polygon points="{pts(plate)}" fill="#1a2129" stroke="#2b3541"/>')
o.append(f'<polygon points="{pts([P(-.15, -.15, 0), P(X1 + .15, -.15, 0), P(X1 + .15, Y1 + .15, 0), P(-.15, Y1 + .15, 0)])}" fill="none" stroke="#5ec8ff" stroke-dasharray="4 4" opacity=".55"/>')
# ghost massing
ZT = NF * FH
gb = [P(0, 0, 0), P(X1, 0, 0), P(X1, Y1, 0), P(0, Y1, 0)]
gt = [P(0, 0, ZT), P(X1, 0, ZT), P(X1, Y1, ZT), P(0, Y1, ZT)]
o.append('<g fill="none" stroke="#5ec8ff" stroke-width="1" stroke-dasharray="4 4" opacity=".35">'
         + f'<polygon points="{pts(gt)}"/>' + "".join(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>' for a, b in zip(gb, gt)) + '</g>')

# --- crane (behind the building) ---
mb = P(-1.0, -0.6, 0)
mt = (mb[0], P(0, 0, ZT + 2.3)[1])
hook_x = P(X1 / 2, Y1 / 2, 0)[0]
o.append(f'<line x1="{mb[0]:.1f}" y1="{mb[1]:.1f}" x2="{mt[0]:.1f}" y2="{mt[1]:.1f}" stroke="#ff8a1f" stroke-width="5"/>')
o.append('<g stroke="#ff8a1f" stroke-width="1" opacity=".55">' + "".join(
    f'<line x1="{mb[0] - 3:.1f}" y1="{mb[1] - i * 12:.1f}" x2="{mb[0] + 3:.1f}" y2="{mb[1] - i * 12 - 9:.1f}"/>' for i in range(int((mb[1] - mt[1]) // 12))) + '</g>')
o.append(f'<line x1="{mt[0] - 62:.1f}" y1="{mt[1]:.1f}" x2="{hook_x + 150:.1f}" y2="{mt[1]:.1f}" stroke="#ff8a1f" stroke-width="4"/>')
o.append(f'<rect x="{mt[0] - 74:.1f}" y="{mt[1] - 5:.1f}" width="28" height="15" fill="#c9ccc4"/>')
o.append(f'<rect x="{mt[0] - 9:.1f}" y="{mt[1] + 2:.1f}" width="18" height="13" fill="#2a5f86" stroke="#5ec8ff" stroke-width=".8"/>')
o.append(f'<circle class="beacon" cx="{mt[0]:.1f}" cy="{mt[1] - 9:.1f}" r="4" fill="#ff4a3a"/>')
o.append(f'<rect x="{hook_x - 9:.1f}" y="{mt[1] + 1:.1f}" width="18" height="6" fill="#c9ccc4"/>')

# hook + slab: for each floor, rise from the ground to the landing level, release, drop back
ground_y = OY + 20
hook_pts, slab_op = [(0, ground_y)], [(0, 0)]
for k, t in enumerate(land):
    top_y = P(X1 / 2, Y1 / 2, (k + 1) * FH)[1] - 22
    hook_pts += [(t - 0.8, ground_y), (t - 0.08, top_y), (t + 0.05, top_y), (t + 0.5, ground_y)]
    slab_op += [(t - 0.8, 0), (t - 0.78, 1), (t - 0.02, 1), (t, 0)]
hook_pts += [(T, ground_y)]
cable_len = [(t, f"{v - mt[1] - 7:.1f}") for t, v in hook_pts]
o.append(f'<line x1="{hook_x:.1f}" y1="{mt[1] + 7:.1f}" x2="{hook_x:.1f}" y2="{ground_y:.1f}" stroke="#7d8a96" stroke-width="1.3">'
         + anim("y2", [(t, f"{v:.1f}") for t, v in hook_pts]) + '</line>')
slab = [P(.6, .5, 0), P(X1 - .6, .5, 0), P(X1 - .6, Y1 - .5, 0), P(.6, Y1 - .5, 0)]
sx0, sy0 = P(X1 / 2, Y1 / 2, 0)
slab_rel = [(a - sx0, b - sy0 + 14) for a, b in slab]
o.append(f'<g opacity="0">{anim("opacity", slab_op)}'
         f'<g>{anim("transform", [(t, f"{hook_x:.1f} {v:.1f}") for t, v in hook_pts], tag="animateTransform", extra=" type=\"translate\"")}'
         f'<line x1="0" y1="0" x2="{slab_rel[0][0]:.1f}" y2="{slab_rel[0][1]:.1f}" stroke="#7d8a96" stroke-width=".8"/>'
         f'<line x1="0" y1="0" x2="{slab_rel[2][0]:.1f}" y2="{slab_rel[2][1]:.1f}" stroke="#7d8a96" stroke-width=".8"/>'
         f'<polygon points="{pts(slab_rel)}" fill="#c9ccc4" stroke="#8e948d"/></g></g>')

# --- floors ---
for k in range(NF):
    z0, z1 = k * FH, (k + 1) * FH
    zs = z1 - 0.13
    left = [P(0, Y1, z0), P(X1, Y1, z0), P(X1, Y1, zs), P(0, Y1, zs)]
    right = [P(X1, Y1, z0), P(X1, 0, z0), P(X1, 0, zs), P(X1, Y1, zs)]
    sl = [P(0, Y1, zs), P(X1, Y1, zs), P(X1, Y1, z1), P(0, Y1, z1)]
    sr = [P(X1, Y1, zs), P(X1, 0, zs), P(X1, 0, z1), P(X1, Y1, z1)]
    tp = [P(0, 0, z1), P(X1, 0, z1), P(X1, Y1, z1), P(0, Y1, z1)]
    mull = []
    wins = []
    for i in range(1, 8):
        xx = X1 * i / 8
        a, b = P(xx, Y1, z0), P(xx, Y1, zs)
        mull.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
    for i in range(1, 6):
        yy = Y1 * i / 6
        a, b = P(X1, yy, z0), P(X1, yy, zs)
        mull.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
    for i in range(8):
        if rng.random() < .55:
            xa, xb = X1 * i / 8 + .06, X1 * (i + 1) / 8 - .06
            pw = [P(xa, Y1, z0 + .08), P(xb, Y1, z0 + .08), P(xb, Y1, zs - .08), P(xa, Y1, zs - .08)]
            on = LIGHTS + k * .12 + rng.random() * .4
            wins.append(f'<polygon points="{pts(pw)}" fill="#ffd27a" opacity="0">'
                        + anim("opacity", [(on, 0), (on + .05, .95), (on + .12, .4), (on + .2, .85), (FADE, .85), (FADE + .3, 0)]) + '</polygon>')
    t = land[k]
    o.append(f'<g opacity="0">{anim("opacity", [(t - .01, 0), (t, 1), (FADE, 1), (FADE + .6, 0)])}'
             f'<polygon points="{pts(left)}" fill="#1f4a6b"/><polygon points="{pts(right)}" fill="#173a55"/>'
             + "".join(wins) +
             f'<g stroke="#c9ccc4" stroke-width="1.1" opacity=".5">{"".join(mull)}</g>'
             f'<polygon points="{pts(sl)}" fill="#c9ccc4"/><polygon points="{pts(sr)}" fill="#9aa09a"/>'
             f'<polygon points="{pts(tp)}" fill="#e3e5df">{anim("opacity", [(land[k + 1] if k + 1 < NF else T, 1), ((land[k + 1] + .01) if k + 1 < NF else T, 0)] if k + 1 < NF else [(0, 1)])}</polygon>'
             '</g>')
    # landing dust
    a = P(X1 / 2, Y1 / 2, z1)
    o.append(f'<ellipse cx="{a[0]:.1f}" cy="{a[1] + 8:.1f}" rx="70" ry="16" fill="#c9ccc4" opacity="0">'
             + anim("opacity", [(t - .01, 0), (t + .02, .22), (t + .5, 0)]) + anim("rx", [(t, 50), (t + .5, 110)]) + '</ellipse>')

# roof beacon + scan plane after completion
rb = P(X1 / 2, Y1 / 2, ZT)
o.append(f'<circle cx="{rb[0]:.1f}" cy="{rb[1] - 6:.1f}" r="3.5" fill="#ff4a3a" opacity="0">' + anim("opacity", [(LIGHTS, 0), (LIGHTS + .1, 1), (FADE, 1), (FADE + .3, 0)]) + '</circle>')
scan = [P(-.2, -.2, 0), P(X1 + .2, -.2, 0), P(X1 + .2, Y1 + .2, 0), P(-.2, Y1 + .2, 0)]
o.append(f'<polygon points="{pts(scan)}" fill="#5ec8ff" fill-opacity=".14" stroke="#5ec8ff" stroke-width="1.5" opacity="0">'
         + anim("opacity", [(LIGHTS + .8, 0), (LIGHTS + 1, .9), (LIGHTS + 2.6, .9), (LIGHTS + 2.8, 0)])
         + anim("transform", [(LIGHTS + .8, "0 0"), (LIGHTS + 2.8, f"0 {-ZT * S:.0f}")], tag="animateTransform", extra=' type="translate"') + '</polygon>')

# data streams flying into the building
streams = []
targets = [P(X1, Y1 * .5, ZT * f) for f in (.25, .5, .75, .9)]
srcs = [(-20, 80), (-20, 210), (590, 40), (590, 300), (120, -20), (420, -20)]
for i, (sx, sy) in enumerate(srcs):
    tx, ty = targets[i % len(targets)]
    cx, cy = (sx + tx) / 2 + rng.uniform(-60, 60), min(sy, ty) - 60
    pid = f"s{i}"
    streams.append(f'<path id="{pid}" d="M{sx} {sy} Q{cx:.0f} {cy:.0f} {tx:.0f} {ty:.0f}" fill="none" stroke="#5ec8ff" stroke-width="1" stroke-dasharray="2 6" opacity=".18"/>')
    for j in range(2):
        b = rng.uniform(0, 4) + j * 2.1
        col = ("#5ec8ff", "#7fd6a0", "#c58bff", "#ff8a1f")[(i + j) % 4]
        streams.append(f'<g><circle r="7" fill="{col}" opacity=".35" filter="url(#glow)"/><circle r="2.6" fill="#ffffff"/>'
                       f'<animateMotion dur="4.2s" begin="{b:.2f}s" repeatCount="indefinite"><mpath href="#{pid}"/></animateMotion></g>')
o.append("".join(streams))

# --- title block ---
roles = ["BIM MANAGER", "ARCHITECT", "AUTOMATION DEVELOPER", "SOLUTIONS BUILDER"]
rt = []
for i, r in enumerate(roles):
    a, b = i * T / len(roles), (i + 1) * T / len(roles)
    rt.append(f'<text x="560" y="182" font-family="{D}" font-weight="700" font-size="28" fill="#ff8a1f" letter-spacing="3" opacity="0">{r}'
              + anim("opacity", [(a, 0), (a + .35, 1), (b - .35, 1), (b, 0)])
              + anim("transform", [(a, "0 10"), (a + .35, "0 0"), (b - .35, "0 0"), (b, "0 -10")], tag="animateTransform", extra=' type="translate"') + '</text>')

title = f'''
<text x="560" y="74" font-family="{MONO}" font-size="13" fill="#7d8a96" letter-spacing="3">OBMI · DUBAI · BIM AUTOMATION</text>
<g clip-path="url(#reveal)"><text x="556" y="140" font-family="{D}" font-weight="800" font-size="60" fill="#e8eae4" textLength="590" lengthAdjust="spacingAndGlyphs">J K ROSHAN KERKETTA</text></g>
{"".join(rt)}
<rect x="560" y="194" width="0" height="2" fill="#ff8a1f">{anim("width", [(0, 0), (1.2, 120), (T - .6, 120), (T, 0)])}</rect>
<text x="560" y="226" font-family="{FONT}" font-size="17" fill="#aeb4ad">Revit &amp; Navisworks add-ins, Autodesk Platform Services apps and</text>
<text x="560" y="249" font-family="{FONT}" font-size="17" fill="#aeb4ad">Power Platform pipelines for airports, stadiums and giga-projects.</text>
<g class="play">
  <polygon points="560,280 960,280 984,306 960,332 560,332" fill="#ff8a1f"/>
  <g clip-path="url(#btn)"><rect x="480" y="270" width="60" height="80" fill="url(#shine)" transform="skewX(-20)">
    <animate attributeName="x" values="480;1060;1060" keyTimes="0;.35;1" dur="3.2s" repeatCount="indefinite"/></rect></g>
  <g class="arrow"><polygon points="584,294 584,318 604,306" fill="#0f141a"/></g>
  <text x="620" y="316" font-family="{D}" font-weight="800" font-size="27" fill="#0f141a" textLength="320" lengthAdjust="spacingAndGlyphs">PLAY MY 3D BUILD SITE</text>
</g>
<text x="560" y="360" font-family="{MONO}" font-size="12" fill="#5e6a75" letter-spacing="1">roshanjohnobmi.github.io · drive · build · explore 11 apps</text>
<text x="{W - 20}" y="380" text-anchor="end" font-family="{MONO}" font-size="11" fill="#3b4652">DWG JKR-000 · REV P02</text>'''

stars = "".join(f'<circle class="tw" style="animation-delay:{rng.random() * 4:.2f}s" cx="{rng.uniform(10, 1190):.0f}" cy="{rng.uniform(10, 150):.0f}" r="{rng.choice((.8, 1, 1.3))}" fill="#e8eae4"/>' for _ in range(40))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="J K Roshan Kerketta. BIM Manager, architect and automation developer at OBMI Dubai. A crane builds a tower floor by floor. Play the 3D build site.">
<style>
  .tw{{animation:tw 4s ease-in-out infinite}}
  @keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.9}}}}
  .beacon{{animation:blink 1.4s steps(2,start) infinite}}
  @keyframes blink{{to{{visibility:hidden}}}}
  .play{{animation:pulse 2.4s ease-in-out infinite;transform-origin:772px 306px}}
  @keyframes pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.035)}}}}
  .arrow{{animation:nudge 1.2s ease-in-out infinite}}
  @keyframes nudge{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX(5px)}}}}
  @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#1a222b" stroke-width="1"/></pattern>
  <linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#0f141a" stop-opacity="0"/><stop offset=".5" stop-color="#0f141a" stop-opacity=".92"/></linearGradient>
  <linearGradient id="ground" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f141a" stop-opacity="0"/><stop offset=".3" stop-color="#0f141a"/></linearGradient>
  <radialGradient id="glowsky" cx="23%" cy="78%" r="45%"><stop offset="0" stop-color="#ff8a1f" stop-opacity=".16"/><stop offset=".5" stop-color="#1b3550" stop-opacity=".35"/><stop offset="1" stop-color="#0f141a" stop-opacity="0"/></radialGradient>
  <linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="btn"><polygon points="560,280 960,280 984,306 960,332 560,332"/></clipPath>
  <clipPath id="reveal"><rect x="550" y="80" width="0" height="80">{anim("width", [(0, 0), (1.1, 620), (T - .5, 620), (T, 0)])}</rect></clipPath>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="#0f141a"/>
<rect width="{W}" height="{H}" rx="14" fill="url(#grid)"/>
<rect width="{W}" height="{H}" rx="14" fill="url(#glowsky)"/>
{stars}
{"".join(o)}
<rect x="520" width="{W - 520}" height="{H}" fill="url(#fade)"/>
{title}
</svg>'''
sys.stdout.write(svg)
