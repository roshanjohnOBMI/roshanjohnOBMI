#!/usr/bin/env python3
"""Animated 3D double-helix of the tech stack (SMIL, no JS, works in GitHub READMEs)."""
import math

W, H = 1200, 700
CX, R = 600, 235
TOP, DY = 132, 58
FRAMES, DUR = 48, 14          # keyframes per turn, seconds per turn
TWIST = 0.72                  # phase step per rung

CATS = {
    "AEC":            "#ff8a1f",
    "Code":           "#f2c94c",
    "Cloud":          "#5ec8ff",
    "Power Platform": "#c58bff",
    "Data":           "#7fd6a0",
}
RUNGS = [
    ("AEC", "Revit API", "Navisworks API"),
    ("Code", "C# / .NET", "Python"),
    ("Cloud", "Autodesk Platform Services", "ACC"),
    ("Power Platform", "Power BI", "Power Automate"),
    ("Data", "ClosedXML", "SharePoint"),
    ("AEC", "pyRevit", "Dynamo"),
    ("Code", "JavaScript / Node.js", "TypeScript"),
    ("Cloud", "GraphQL / REST", "Azure"),
    ("Power Platform", "Power Apps", "Power Query"),
]
N = len(RUNGS)
ts = [2 * math.pi * f / FRAMES for f in range(FRAMES + 1)]   # +1 closes the loop exactly

def end(i, t, strand):
    """x, depth (−1 back … +1 front) of a rung end."""
    a = i * TWIST + t + (math.pi if strand else 0)
    return CX + R * math.sin(a), math.cos(a)

def vals(seq):
    return ";".join(seq)

def anim(attr, values):
    return f'<animate attributeName="{attr}" dur="{DUR}s" repeatCount="indefinite" calcMode="linear" values="{vals(values)}"/>'

FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif"
MONO = "ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace"
out = []

# backbones: sampled finely so the curve stays smooth
def backbone(strand):
    ds = []
    steps = (N - 1) * 6
    for t in ts:
        pts = []
        for k in range(steps + 1):
            u = k / 6
            x, _ = end(u, t, strand)
            pts.append(f"{x:.1f} {TOP + u*DY:.1f}")
        ds.append("M" + " L".join(pts))
    return ds

for s, col in ((0, "#5e6a75"), (1, "#3b4652")):
    d = backbone(s)
    out.append(f'<path d="{d[0]}" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="round">{anim("d", d)}</path>')

for i, (cat, a, b) in enumerate(RUNGS):
    y = TOP + i * DY
    col = CATS[cat]
    xa = [end(i, t, 0) for t in ts]
    xb = [end(i, t, 1) for t in ts]
    # rung (base pair) — gradient-free: two half-lines so each half fades with its own end
    mid = CX
    for side in (xa, xb):
        out.append(f'<line y1="{y}" y2="{y}" stroke="{col}" stroke-width="3" stroke-linecap="round" x2="{mid}" x1="{side[0][0]:.1f}" opacity="{0.35+0.45*(side[0][1]+1)/2:.2f}">'
                   f'{anim("x1", [f"{p[0]:.1f}" for p in side])}{anim("opacity", [f"{0.2+0.55*(p[1]+1)/2:.2f}" for p in side])}</line>')
    for label, pts in ((a, xa), (b, xb)):
        rs = [f"{5 + 4*(p[1]+1)/2:.1f}" for p in pts]
        ops = [f"{0.22 + 0.78*((p[1]+1)/2)**1.4:.2f}" for p in pts]
        xs = [f"{p[0]:.1f}" for p in pts]
        out.append(f'<circle cy="{y}" cx="{xs[0]}" r="{rs[0]}" fill="{col}" opacity="{ops[0]}">{anim("cx", xs)}{anim("r", rs)}{anim("opacity", ops)}</circle>')
        out.append(f'<text y="{y-14}" x="{xs[0]}" text-anchor="middle" font-family="{FONT}" font-size="15" font-weight="600" fill="#e8eae4" opacity="{ops[0]}">{label}'
                   f'{anim("x", xs)}{anim("opacity", ops)}</text>')

# legend
lx = 168
legend = []
for name, col in CATS.items():
    legend.append(f'<circle cx="{lx}" cy="{H-44}" r="6" fill="{col}"/><text x="{lx+14}" y="{H-39}" font-family="{MONO}" font-size="13" fill="#aeb4ad" letter-spacing="1">{name.upper()}</text>')
    lx += 34 + len(name) * 9.4 + 40

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Tech stack as a rotating double helix. AEC: Revit API, Navisworks API, pyRevit, Dynamo. Code: C# and .NET, Python, JavaScript and Node.js, TypeScript. Cloud: Autodesk Platform Services, ACC, GraphQL and REST, Azure. Power Platform: Power BI, Power Automate, Power Apps, Power Query. Data: ClosedXML, SharePoint.">
<defs><pattern id="g3" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#1d2731"/></pattern>
<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#5ec8ff" stop-opacity=".10"/><stop offset="1" stop-color="#5ec8ff" stop-opacity="0"/></radialGradient></defs>
<rect width="{W}" height="{H}" rx="14" fill="#0f141a"/><rect width="{W}" height="{H}" rx="14" fill="url(#g3)"/>
<ellipse cx="{CX}" cy="{TOP + (N-1)*DY/2}" rx="420" ry="300" fill="url(#glow)"/>
<text x="40" y="50" font-family="{MONO}" font-size="13" fill="#7d8a96" letter-spacing="2">TECH STACK · DOUBLE HELIX</text>
<text x="{W-40}" y="50" text-anchor="end" font-family="{MONO}" font-size="11" fill="#3b4652" letter-spacing="1">DWG JKR-300 · EACH RUNG PAIRS TWO TOOLS</text>
{''.join(out)}
{''.join(legend)}
</svg>'''
import sys
sys.stdout.write(svg)
