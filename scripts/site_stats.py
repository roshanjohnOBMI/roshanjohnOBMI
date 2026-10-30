#!/usr/bin/env python3
"""Render assets/site-stats.svg: a tower with one floor per contribution, plus site counters.

Runs in GitHub Actions with GITHUB_TOKEN (public data only). Standard library only.
Usage: GITHUB_TOKEN=... python3 scripts/site_stats.py <login> > assets/site-stats.svg
       python3 scripts/site_stats.py --sample > preview.svg
"""
import datetime as dt
import json
import math
import os
import sys
import urllib.request

QUERY = """
query($login:String!){
  user(login:$login){
    followers{totalCount}
    repositories(ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, first:100){
      totalCount
      nodes{ stargazerCount languages(first:10, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name } } } }
    }
    contributionsCollection{
      totalCommitContributions totalPullRequestContributions totalIssueContributions
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
    }
  }
}"""


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body,
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                                          "User-Agent": "site-stats"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]


def sample():
    today = dt.date(2026, 10, 30)
    hot = {dt.date(2026, 4, 14): 4, dt.date(2026, 4, 20): 2, dt.date(2026, 5, 6): 1}
    for i, c in enumerate([3, 4, 2, 5, 6, 3, 2, 4, 3]):
        hot[dt.date(2026, 10, 21) + dt.timedelta(days=i)] = c
    days = [{"date": (today - dt.timedelta(days=364 - k)).isoformat(),
             "contributionCount": hot.get(today - dt.timedelta(days=364 - k), 0)} for k in range(365)]
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, 365, 7)]
    return {"followers": {"totalCount": 0},
            "repositories": {"totalCount": 4, "nodes": [
                {"stargazerCount": 1, "languages": {"edges": [{"size": 90000, "node": {"name": "JavaScript"}}, {"size": 50000, "node": {"name": "TypeScript"}}]}},
                {"stargazerCount": 0, "languages": {"edges": [{"size": 76000, "node": {"name": "HTML"}}, {"size": 48000, "node": {"name": "CSS"}}, {"size": 22000, "node": {"name": "Python"}}]}}]},
            "contributionsCollection": {"totalCommitContributions": 28, "totalPullRequestContributions": 0,
                                        "totalIssueContributions": 0,
                                        "contributionCalendar": {"totalContributions": 39, "weeks": weeks}}}


def streaks(days):
    cur = best = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        best = max(best, run)
    # current streak counts back from today (today may still be empty)
    for i, d in enumerate(reversed(days)):
        if d["contributionCount"] > 0:
            cur += 1
        elif i == 0:
            continue
        else:
            break
    return cur, best


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(u):
    cal = u["contributionsCollection"]["contributionCalendar"]
    cc = u["contributionsCollection"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    today = dt.date.fromisoformat(days[-1]["date"])
    total = cal["totalContributions"]
    cur, best = streaks(days)
    stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
    langs = {}
    for n in u["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    total_bytes = sum(v for _, v in top) or 1

    # ---- one floor per contribution (or per N if the year is busy), stacked in date order ----
    MAXF = 46
    unit = max(1, math.ceil(sum(d["contributionCount"] for d in days) / MAXF))
    floors, acc = [], 0
    for d in days:
        acc += d["contributionCount"]
        while acc >= unit:
            acc -= unit
            floors.append(dt.date.fromisoformat(d["date"]))
    if not floors:
        floors = [today]
    month_keys = sorted({(f.year, f.month) for f in floors})
    PAL = ["#5ec8ff", "#7fd6a0", "#c58bff", "#f2c94c", "#ff8a1f", "#ff6b8a"]
    mcol = {k: PAL[i % len(PAL)] for i, k in enumerate(month_keys)}

    W, H = 1200, 460
    FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif"
    MONO = "ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace"
    D = "'Arial Narrow','Roboto Condensed','Helvetica Neue',Arial,sans-serif"
    C = math.cos(math.radians(30))
    s = 28
    ox, oy = 250, 392
    fh = min(9.0, 200 / len(floors))
    TW, TD = 3.0, 2.4
    o, css = [], []

    def P(x, y, zpx):
        return ox + (x - y) * C * s, oy + (x + y) * 0.5 * s - zpx

    def poly(pts, fill, extra=""):
        return f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="{fill}"{extra}/>'

    # ground plate + setting-out
    o.append(poly([P(-1.3, -1.3, 0), P(TW + 1.3, -1.3, 0), P(TW + 1.3, TD + 1.3, 0), P(-1.3, TD + 1.3, 0)], "#1a2129", ' stroke="#2b3541"'))
    o.append(poly([P(-.15, -.15, 0), P(TW + .15, -.15, 0), P(TW + .15, TD + .15, 0), P(-.15, TD + .15, 0)], "none", ' stroke="#5ec8ff" stroke-dasharray="4 4" opacity=".5"'))
    # ghost of the full tower (blueprint)
    Ht = fh * len(floors)
    gb = [P(0, 0, 0), P(TW, 0, 0), P(TW, TD, 0), P(0, TD, 0)]
    gt = [P(0, 0, Ht), P(TW, 0, Ht), P(TW, TD, Ht), P(0, TD, Ht)]
    o.append('<g fill="none" stroke="#5ec8ff" stroke-width="1" stroke-dasharray="3 4" opacity=".3">' + poly(gt, "none")
             + "".join(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>' for a, b in zip(gb, gt)) + '</g>')

    BUILD = 4.6
    step = BUILD / len(floors)
    for k, f in enumerate(floors):
        z0, z1 = k * fh, (k + 1) * fh
        col = mcol[(f.year, f.month)]
        left = [P(0, TD, z0), P(TW, TD, z0), P(TW, TD, z1 - .8), P(0, TD, z1 - .8)]
        right = [P(TW, TD, z0), P(TW, 0, z0), P(TW, 0, z1 - .8), P(TW, TD, z1 - .8)]
        slab_l = [P(0, TD, z1 - .8), P(TW, TD, z1 - .8), P(TW, TD, z1), P(0, TD, z1)]
        slab_r = [P(TW, TD, z1 - .8), P(TW, 0, z1 - .8), P(TW, 0, z1), P(TW, TD, z1)]
        wins = []
        if False:
            for w in range(6):
                a = P(.25 + w * .5, TD, z0 + fh * .2)
                wins.append(f'<rect class="win" style="animation-delay:{(k * 7 + w * 3) % 23 * .37:.2f}s" x="{a[0]:.1f}" y="{a[1] - fh * .55 - (.25 + w * .5) * .5 * s * 0:.1f}" width="{.36 * C * s:.1f}" height="{fh * .45:.1f}" fill="#fff6d6" transform="skewY(30) translate(0 {-(a[0] - ox) * math.tan(math.radians(30)):.1f})"/>')
        o.append(f'<g class="fl" style="animation-delay:{k * step:.2f}s">'
                 + poly(left, col, ' opacity=".82"') + poly(right, col, ' opacity=".55"')
                 + poly(slab_l, "#c9ccc4") + poly(slab_r, "#8e948d")
                 + (f'<line x1="{left[3][0]:.1f}" y1="{left[3][1]:.1f}" x2="{left[2][0]:.1f}" y2="{left[2][1]:.1f}" stroke="#0f141a" stroke-width=".6" opacity=".5"/>') + '</g>')
    topz = len(floors) * fh
    o.append(f'<g class="fl" style="animation-delay:{len(floors) * step:.2f}s">'
             + poly([P(0, 0, topz), P(TW, 0, topz), P(TW, TD, topz), P(0, TD, topz)], "#e3e5df") + '</g>')

    # month call-outs (pushed apart so they never overlap)
    starts = {}
    for k, f in enumerate(floors):
        starts.setdefault((f.year, f.month), k)
    counts = {}
    for d in days:
        dd = dt.date.fromisoformat(d["date"])
        counts[(dd.year, dd.month)] = counts.get((dd.year, dd.month), 0) + d["contributionCount"]
    last_y = 1e9
    for key in sorted(starts, key=lambda k: starts[k]):
        k = starts[key]
        n = sum(1 for f in floors if (f.year, f.month) == key)
        mid = (k + n / 2) * fh
        a = P(TW, 0, mid)
        ly = min(a[1], last_y - 18)
        last_y = ly
        lx = a[0] + 46
        name = dt.date(key[0], key[1], 1).strftime("%b %Y").upper()
        o.append(f'<g class="lab" style="animation-delay:{k * step + .3:.2f}s"><polyline points="{a[0] + 4:.1f},{a[1]:.1f} {a[0] + 24:.1f},{ly:.1f} {lx - 4:.1f},{ly:.1f}" fill="none" stroke="{mcol[key]}" stroke-width="1.2"/>'
                 f'<circle cx="{a[0] + 4:.1f}" cy="{a[1]:.1f}" r="2.5" fill="{mcol[key]}"/>'
                 f'<text x="{lx:.1f}" y="{ly + 4:.1f}" font-family="{MONO}" font-size="11.5" fill="#e8eae4" letter-spacing="1">{name}'
                 f'<tspan fill="{mcol[key]}" dx="8">+{counts.get(key, 0)}</tspan></text></g>')

    # tower crane: mast beside the tower, jib slewing, hook delivering the next floor
    mb = P(-0.9, TD + 0.6, 0)
    mt = (mb[0], max(108, P(0, 0, topz + 34)[1]))
    o.append(f'<line x1="{mb[0]:.1f}" y1="{mb[1]:.1f}" x2="{mt[0]:.1f}" y2="{mt[1]:.1f}" stroke="#ff8a1f" stroke-width="5"/>')
    o.append('<g stroke="#ff8a1f" stroke-width="1" opacity=".55">' + "".join(
        f'<line x1="{mb[0] - 3:.1f}" y1="{mb[1] - i * 12:.1f}" x2="{mb[0] + 3:.1f}" y2="{mb[1] - i * 12 - 9:.1f}"/>' for i in range(int((mb[1] - mt[1]) // 12))) + '</g>')
    jx = mt[0]
    hook_x = P(TW / 2, TD / 2, 0)[0]
    o.append(f'<g class="jib" style="transform-origin:{jx:.1f}px {mt[1]:.1f}px">'
             f'<line x1="{jx - 60:.1f}" y1="{mt[1]:.1f}" x2="{jx + 300:.1f}" y2="{mt[1]:.1f}" stroke="#ff8a1f" stroke-width="4"/>'
             f'<rect x="{jx - 70:.1f}" y="{mt[1] - 4:.1f}" width="26" height="14" fill="#c9ccc4"/>'
             f'<rect x="{jx - 8:.1f}" y="{mt[1] + 2:.1f}" width="16" height="12" fill="#2a5f86" stroke="#5ec8ff" stroke-width=".8"/></g>')
    o.append(f'<g class="hook"><line x1="{hook_x:.1f}" y1="{mt[1] + 2:.1f}" x2="{hook_x:.1f}" y2="{P(0,0,topz + 26)[1]:.1f}" stroke="#7d8a96" stroke-width="1.2"/>'
             f'<rect x="{hook_x - 22:.1f}" y="{P(0,0,topz + 26)[1]:.1f}" width="44" height="6" fill="#c9ccc4"/></g>')
    o.append(f'<circle class="beacon" cx="{jx:.1f}" cy="{mt[1] - 9:.1f}" r="4" fill="#ff4a3a"/>')
    # survey laser sweeping up the tower
    o.append(f'<line class="laser" x1="{P(-1.3, TD + 1.3, 0)[0]:.1f}" x2="{P(TW + 1.3, -1.3, 0)[0]:.1f}" y1="{oy - 4}" y2="{oy - 4}" stroke="#5ec8ff" stroke-width="1.5" opacity=".7" style="--h:{topz + 40:.0f}px"/>')
    # stars
    rnd = __import__("random").Random(3)
    stars_svg = "".join(f'<circle class="tw" style="animation-delay:{rnd.random() * 4:.2f}s" cx="{rnd.uniform(30, 560):.0f}" cy="{rnd.uniform(70, 230):.0f}" r="{rnd.choice((1, 1, 1.4)):.1f}" fill="#e8eae4"/>' for _ in range(26))

    # ---- counters with a count-up ----
    T = 14

    def counter(x, y, label, val, sub, delay):
        steps = sorted(set([round(val * f) for f in (0, .15, .35, .6, .8, .93, 1)]))
        parts = []
        times = [delay + i * .14 for i in range(len(steps))]
        for i, v in enumerate(steps):
            on = times[i] / T
            off = times[i + 1] / T if i + 1 < len(steps) else (T - .3) / T
            if i == len(steps) - 1:
                kts, vals = f"0;{on:.4f};{off:.4f}", "0;1;0"
            else:
                kts, vals = f"0;{on:.4f};{off:.4f}", "0;1;0"
            parts.append(f'<text x="{x + 18}" y="{y + 78}" font-family="{D}" font-weight="800" font-size="50" fill="#e8eae4" opacity="0">{v}'
                         f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kts}" values="{vals}"/></text>')
        return (f'<g><rect x="{x}" y="{y}" width="262" height="100" rx="6" fill="#151b22" stroke="#2b3541"/>'
                f'<rect x="{x}" y="{y}" width="262" height="5" fill="url(#hazard)"/>'
                f'<text x="{x + 18}" y="{y + 30}" font-family="{MONO}" font-size="11" fill="#7d8a96" letter-spacing="1.5">{label}</text>'
                + "".join(parts) +
                f'<text x="{x + 244}" y="{y + 78}" text-anchor="end" font-family="{FONT}" font-size="13" fill="#aeb4ad">{esc(sub)}</text></g>')

    bx = 640
    o.append(counter(bx, 96, "FLOORS POURED", total, "contributions · past year", .2))
    o.append(counter(bx + 282, 96, "COMMITS", cc["totalCommitContributions"], "past year", .35))
    o.append(counter(bx, 214, "PUBLIC REPOS", u["repositories"]["totalCount"], f"{stars} star{'s' if stars != 1 else ''}", .5))
    o.append(counter(bx + 282, 214, "CURRENT STREAK", cur, f"best {best} day{'s' if best != 1 else ''}", .65))

    my = 352
    o.append(f'<text x="{bx}" y="{my}" font-family="{MONO}" font-size="11" fill="#7d8a96" letter-spacing="1.5">MATERIALS SCHEDULE · LANGUAGES IN PUBLIC REPOS</text>')
    langpal = ["#5ec8ff", "#ff8a1f", "#c58bff", "#7fd6a0", "#f2c94c"]
    xcur, total_w = bx, 544
    for k, (name, size) in enumerate(top):
        w = max(6, total_w * size / total_bytes)
        o.append(f'<rect class="bar" style="animation-delay:{.9 + k * .15:.2f}s;transform-origin:{xcur:.0f}px 0" x="{xcur:.1f}" y="{my + 12}" width="{w - 3:.1f}" height="14" rx="2" fill="{langpal[k]}"/>')
        xcur += w
    lx = bx
    for k, (name, size) in enumerate(top):
        t = f"{name} {100 * size / total_bytes:.0f}%"
        o.append(f'<rect x="{lx}" y="{my + 40}" width="9" height="9" rx="2" fill="{langpal[k]}"/><text x="{lx + 14}" y="{my + 49}" font-family="{FONT}" font-size="13" fill="#aeb4ad">{esc(t)}</text>')
        lx += 34 + len(t) * 7.6
    unit_note = f"1 floor = {unit} contribution{'s' if unit != 1 else ''}"
    stamp = today.strftime("%d %b %Y").upper()
    pct = lambda t: f"{100 * t / T:.2f}%"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Site progress: a tower with one floor per contribution, {total} contributions and {cc['totalCommitContributions']} commits in the past year, {u['repositories']['totalCount']} public repositories, current streak {cur} days, best {best}.">
<style>
  .fl{{animation:pour {T}s cubic-bezier(.2,.8,.2,1) infinite both}}
  @keyframes pour{{0%{{opacity:0;transform:translateY(-34px)}}3%{{opacity:1;transform:none}}94%{{opacity:1;transform:none}}100%{{opacity:0;transform:none}}}}
  .lab{{animation:lab {T}s ease infinite both}}
  @keyframes lab{{0%{{opacity:0}}4%{{opacity:1}}94%{{opacity:1}}100%{{opacity:0}}}}
  .win{{animation:win 4.6s steps(1) infinite}}
  @keyframes win{{0%{{opacity:.9}}40%{{opacity:.15}}70%{{opacity:.75}}}}
  .jib{{animation:slew 9s ease-in-out infinite}}
  @keyframes slew{{0%,100%{{transform:scaleX(1)}}50%{{transform:scaleX(.82)}}}}
  .hook{{animation:hook 3.2s ease-in-out infinite}}
  @keyframes hook{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(16px)}}}}
  .beacon{{animation:blink 1.4s steps(2,start) infinite}}
  @keyframes blink{{to{{visibility:hidden}}}}
  .laser{{animation:laser 5s ease-in-out infinite}}
  @keyframes laser{{0%,100%{{transform:translateY(0);opacity:0}}10%{{opacity:.7}}50%{{transform:translateY(calc(var(--h) * -1));opacity:.7}}60%{{opacity:0}}}}
  .tw{{animation:tw 4s ease-in-out infinite}}
  @keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:.8}}}}
  .bar{{animation:grow {T}s cubic-bezier(.2,.8,.2,1) infinite both}}
  @keyframes grow{{0%{{transform:scaleX(0)}}8%{{transform:scaleX(1)}}100%{{transform:scaleX(1)}}}}
  @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
  <pattern id="g4" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#1d2731"/></pattern>
  <pattern id="hazard" width="14" height="5" patternUnits="userSpaceOnUse" patternTransform="skewX(-45)"><rect width="7" height="5" fill="#ff8a1f"/><rect x="7" width="7" height="5" fill="#0f141a"/></pattern>
  <radialGradient id="skyg" cx="25%" cy="70%" r="55%"><stop offset="0" stop-color="#1b3550" stop-opacity=".7"/><stop offset="1" stop-color="#0f141a" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="#0f141a"/><rect width="{W}" height="{H}" rx="14" fill="url(#g4)"/>
<rect width="{W}" height="{H}" rx="14" fill="url(#skyg)"/>
{stars_svg}
<text x="40" y="50" font-family="{MONO}" font-size="13" fill="#7d8a96" letter-spacing="2">SITE PROGRESS · ONE FLOOR PER CONTRIBUTION</text>
<text x="40" y="70" font-family="{MONO}" font-size="11" fill="#3b4652" letter-spacing="1">{unit_note.upper()} · COLOURED BY MONTH</text>
<text x="{W - 40}" y="50" text-anchor="end" font-family="{MONO}" font-size="11" fill="#3b4652" letter-spacing="1">SURVEYED {stamp} · PUBLIC ACTIVITY</text>
{"".join(o)}
</svg>'''


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        print(render(sample()))
    else:
        login = sys.argv[1] if len(sys.argv) > 1 else os.environ["GITHUB_REPOSITORY_OWNER"]
        print(render(fetch(login, os.environ["GITHUB_TOKEN"])))
