#!/usr/bin/env python3
"""Animated 'Integration routes' board from the validated stack map.

One lane per app. A packet runs through the app's tools stage by stage; each chip lights as the
packet reaches it, and the lane stamps VALIDATED when the route completes.
Usage: python3 scripts/routes_board.py > assets/routes.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stack_map as M  # noqa: E402

errors, _ = M.validate(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md"))
if errors:
    sys.exit("map invalid:\n  " + "\n  ".join(errors))

W = 1400
PADX = 36
NAME_W = 262
CHECK_W = 132
COLS = len(M.STAGES)
COL_W = (W - 2 * PADX - NAME_W - CHECK_W) / COLS
TOP = 148
LANE = 50
H = TOP + LANE * len(M.APPS) + 96
X0 = PADX + NAME_W
T = 16.0                  # cycle seconds
TRAVEL = 2.6              # seconds for a packet to cross a lane
STAGGER = 0.85            # delay between lanes

FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif"
MONO = "ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace"
D = "'Arial Narrow','Roboto Condensed','Helvetica Neue',Arial,sans-serif"
C = M.CATEGORY_COLOURS


def chip_w(label):
    return len(label) * 6.9 + 18


def col_x(stage):
    i = M.STAGES.index(stage)
    return X0 + COL_W * i + COL_W / 2


def anim(attr, pts, mode="linear"):
    pts = sorted(pts)
    if pts[0][0] > 0:
        pts.insert(0, (0, pts[0][1]))
    if pts[-1][0] < T:
        pts.append((T, pts[-1][1]))
    kt, vs, last = [], [], -1.0
    for t, v in pts:
        k = max(0.0, min(1.0, t / T))
        k = k if k > last else last + 1e-4
        kt.append(f"{min(k, 1):.4f}")
        vs.append(str(v))
        last = k
    kt[-1] = "1"
    return (f'<animate attributeName="{attr}" dur="{T}s" repeatCount="indefinite" calcMode="{mode}" '
            f'keyTimes="{";".join(kt)}" values="{";".join(vs)}"/>')


o = []
# stage columns
for i, s in enumerate(M.STAGES):
    x = X0 + COL_W * i
    o.append(f'<rect x="{x:.1f}" y="{TOP - 34}" width="{COL_W:.1f}" height="{LANE * len(M.APPS) + 26}" fill="{"#131a22" if i % 2 == 0 else "#0f141a"}" opacity=".9"/>')
    o.append(f'<text x="{x + COL_W / 2:.1f}" y="{TOP - 46}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#7d8a96" letter-spacing="2">{i + 1:02d} · {s.upper()}</text>')

for r, app in enumerate(M.APPS):
    y = TOP + r * LANE + LANE / 2 - 12
    start = 0.4 + r * STAGGER
    route = M.route(app)
    # group chips by stage
    by_stage = {}
    for t in route:
        st = "Output" if t in M.OUTPUTS else M.stage_of(t)
        by_stage.setdefault(st, []).append(t)
    first_x = min(col_x(s) for s in by_stage) - 60
    last_x = col_x("Output")
    total = last_x - X0 + 10

    def t_at(x):
        return start + TRAVEL * max(0, (x - X0)) / total

    # lane rule
    o.append(f'<line x1="{PADX}" y1="{y + 24:.1f}" x2="{W - PADX}" y2="{y + 24:.1f}" stroke="#1d2731"/>')
    # app name + status
    badge = "#ff8a1f" if app["status"] == "wip" else "#7fd6a0"
    o.append(f'<text x="{PADX + 14}" y="{y + 4:.1f}" font-family="{FONT}" font-size="15" font-weight="600" fill="#e8eae4">{app["name"].replace("&", "&amp;")}</text>')
    o.append(f'<circle cx="{PADX + 4}" cy="{y - 1:.1f}" r="4" fill="{badge}"/>')
    o.append(f'<text x="{PADX + 14}" y="{y + 20:.1f}" font-family="{FONT}" font-size="11.5" fill="#7d8a96">{app["what"]}</text>')
    # track: dim base + bright section that the packet "energises"
    o.append(f'<line x1="{first_x:.1f}" y1="{y:.1f}" x2="{last_x:.1f}" y2="{y:.1f}" stroke="#2b3541" stroke-width="2" stroke-dasharray="2 5"/>')
    seg = last_x - first_x
    o.append(f'<line x1="{first_x:.1f}" y1="{y:.1f}" x2="{last_x:.1f}" y2="{y:.1f}" stroke="#5ec8ff" stroke-width="2" stroke-dasharray="{seg:.0f}" stroke-dashoffset="{seg:.0f}" opacity=".55">'
             + anim("stroke-dashoffset", [(t_at(first_x), f"{seg:.0f}"), (t_at(last_x), 0), (T - .6, 0), (T - .2, f"{seg:.0f}")]) + '</line>')
    # chips
    for st, items in by_stage.items():
        widths = [chip_w(M.TOOLS[t][0] if t in M.TOOLS else t) for t in items]
        gap = 6
        stacked = sum(widths) + gap * (len(items) - 1) > COL_W - 10
        x = col_x(st) - (sum(widths) + gap * (len(items) - 1)) / 2
        for idx, (t, w) in enumerate(zip(items, widths)):
            cy = y + (idx - (len(items) - 1) / 2) * 23 if stacked else y
            if stacked:
                x = col_x(st) - w / 2
            label = M.TOOLS[t][0] if t in M.TOOLS else t
            col = C["Output"] if t in M.OUTPUTS else C[M.TOOLS[t][1]]
            hit = t_at(x + w / 2)
            fill_on = "#0f141a" if t in M.OUTPUTS else col
            o.append(f'<g><rect x="{x:.1f}" y="{cy - 10:.1f}" width="{w:.1f}" height="20" rx="10" fill="#151b22" stroke="{col}" stroke-width="1.2"/>'
                     f'<rect x="{x:.1f}" y="{cy - 10:.1f}" width="{w:.1f}" height="20" rx="10" fill="{col}" opacity="0">'
                     + anim("opacity", [(hit - .02, 0), (hit + .04, .95), (hit + .5, .22), (T - .6, .22), (T - .2, 0)]) + '</rect>'
                     f'<text x="{x + w / 2:.1f}" y="{cy + 4:.1f}" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="600" fill="#e8eae4">{label}</text></g>')
            if not stacked:
                x += w + gap
    # packet with trail
    path = f"M{first_x:.1f} {y:.1f} H{last_x + 40:.1f}"
    o.append(f'<path id="lane{r}" d="{path}" fill="none"/>')
    o.append(f'<g opacity="0">' + anim("opacity", [(t_at(first_x) - .01, 0), (t_at(first_x), 1), (t_at(last_x) + .1, 1), (t_at(last_x) + .25, 0)])
             + f'<circle r="11" fill="#5ec8ff" opacity=".35" filter="url(#glow)"/><circle r="4.5" fill="#ffffff"/>'
             + f'<animateMotion dur="{T}s" repeatCount="indefinite" calcMode="linear" keyPoints="0;0;1;1" '
             + f'keyTimes="0;{t_at(first_x) / T:.4f};{t_at(last_x + 40) / T:.4f};1"><mpath href="#lane{r}"/></animateMotion></g>')
    # validated stamp
    sx = W - PADX - CHECK_W + 22
    done = t_at(last_x) + .2
    o.append(f'<g opacity="0">' + anim("opacity", [(done, 0), (done + .15, 1), (T - .6, 1), (T - .2, 0)])
             + f'<rect x="{sx}" y="{y - 12:.1f}" width="{CHECK_W - 26}" height="24" rx="4" fill="none" stroke="#7fd6a0" stroke-width="1.5"/>'
             + f'<text x="{sx + (CHECK_W - 26) / 2:.1f}" y="{y + 4.5:.1f}" text-anchor="middle" font-family="{MONO}" font-size="11.5" fill="#7fd6a0" letter-spacing="1.5">✓ VALIDATED</text></g>')

# counter
N = len(M.APPS)
dones = [0.4 + r * STAGGER + TRAVEL + .2 for r in range(N)]
for k in range(N + 1):
    if k == 0:
        vals, kts = "1;0;1", f"0;{dones[0]/T:.4f};{(T-.2)/T:.4f}"
    elif k == N:
        vals, kts = "0;1;0", f"0;{dones[-1]/T:.4f};{(T-.2)/T:.4f}"
    else:
        vals, kts = "0;1;0", f"0;{dones[k-1]/T:.4f};{dones[k]/T:.4f}"
    o.append(f'<text x="{W - PADX}" y="44" text-anchor="end" font-family="{D}" font-weight="800" font-size="26" fill="#7fd6a0" opacity="{1 if k == 0 else 0}">'
             f'{k:02d}/{N:02d} ROUTES VALIDATED<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{vals}"/></text>')

# legend + standalone note
lx, ly = PADX, H - 34
leg = []
for name, col in C.items():
    leg.append(f'<rect x="{lx}" y="{ly - 10}" width="12" height="12" rx="6" fill="#151b22" stroke="{col}" stroke-width="1.5"/>'
               f'<text x="{lx + 18}" y="{ly}" font-family="{MONO}" font-size="11.5" fill="#aeb4ad" letter-spacing="1">{name.upper()}</text>')
    lx += 30 + len(name) * 8.6 + 26
stand = " · ".join(f"{k} ({v[0].lower() + v[1:]})" for k, v in M.STANDALONE.items())
if stand:
    leg.append(f'<text x="{W - PADX}" y="{ly}" text-anchor="end" font-family="{FONT}" font-size="12" fill="#7d8a96">Also in the toolkit: {stand}</text>')

tools_n = len(M.TOOLS)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Integration routes: {N} apps, each routed through its tools from authoring to output. {'; '.join(a['name'] + ': ' + ', '.join(M.route(a)) for a in M.APPS)}.">
<defs>
  <pattern id="gr" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#1a222b"/></pattern>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4"/></filter>
</defs>
<style>@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<rect width="{W}" height="{H}" rx="14" fill="#0f141a"/><rect width="{W}" height="{H}" rx="14" fill="url(#gr)"/>
<text x="{PADX}" y="48" font-family="{D}" font-weight="800" font-size="30" fill="#e8eae4" letter-spacing=".5">INTEGRATION ROUTES</text>
<text x="{PADX}" y="72" font-family="{MONO}" font-size="12" fill="#7d8a96" letter-spacing="1.5">{N} APPS · {tools_n} TOOLS · 0 ORPHANS · CHECKED NIGHTLY AGAINST THE STACK MAP</text>
<circle cx="{W - PADX - 196}" cy="68" r="4" fill="#7fd6a0"/><text x="{W - PADX - 186}" y="72" font-family="{MONO}" font-size="11" fill="#7d8a96" letter-spacing="1">LIVE</text>
<circle cx="{W - PADX - 108}" cy="68" r="4" fill="#ff8a1f"/><text x="{W - PADX}" y="72" text-anchor="end" font-family="{MONO}" font-size="11" fill="#7d8a96" letter-spacing="1">IN PROGRESS</text>
{"".join(o)}
{"".join(leg)}
</svg>'''
sys.stdout.write(svg)
