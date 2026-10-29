#!/usr/bin/env python3
"""Render assets/site-stats.svg: GitHub stats as an animated construction-site progress board.

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
    today = dt.date(2026, 10, 29)
    days = []
    for k in range(365):
        d = today - dt.timedelta(days=364 - k)
        c = 0 if k < 180 else int(3 * (1 + math.sin(k / 9)) * (k % 3 == 0))
        days.append({"date": d.isoformat(), "contributionCount": c})
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, 365, 7)]
    return {"followers": {"totalCount": 0},
            "repositories": {"totalCount": 3, "nodes": [
                {"stargazerCount": 1, "languages": {"edges": [{"size": 90000, "node": {"name": "JavaScript"}}, {"size": 60000, "node": {"name": "TypeScript"}}]}},
                {"stargazerCount": 0, "languages": {"edges": [{"size": 40000, "node": {"name": "HTML"}}, {"size": 12000, "node": {"name": "Python"}}]}}]},
            "contributionsCollection": {"totalCommitContributions": 17, "totalPullRequestContributions": 0,
                                        "totalIssueContributions": 0,
                                        "contributionCalendar": {"totalContributions": 26, "weeks": weeks}}}


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
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    today = dt.date.fromisoformat(days[-1]["date"])
    # last 12 calendar months, oldest first
    months = []
    y, m = today.year, today.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()
    per = {k: 0 for k in months}
    for d in days:
        dd = dt.date.fromisoformat(d["date"])
        if (dd.year, dd.month) in per:
            per[(dd.year, dd.month)] += d["contributionCount"]
    counts = [per[k] for k in months]
    cur, best = streaks(days)
    stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
    langs = {}
    for n in u["repositories"]["nodes"]:
        for e in n["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    total_bytes = sum(v for _, v in top) or 1
    cc = u["contributionsCollection"]

    W, H = 1200, 420
    FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif"
    MONO = "ui-monospace,'SFMono-Regular',Menlo,Consolas,monospace"
    D = "'Arial Narrow','Roboto Condensed','Helvetica Neue',Arial,sans-serif"
    C = math.cos(math.radians(30))
    o = []

    # ---- skyline: one isometric tower per month ----
    s = 17                       # iso unit
    ox, oy = 70, 330             # origin of the plot
    STEP = 1.25
    mx = max(counts) or 1
    pad = []
    for i, (cnt, (yy, mm)) in enumerate(zip(counts, months)):
        a = i * STEP             # towers march left-to-right along the iso diagonal
        h = 0.35 + 11 * cnt / mx
        def P(x, yv, z):
            return ox + (x - yv) * C * s + 0 * z, oy + (x + yv) * 0.5 * s - z * s
        x0, x1, y0, y1 = a, a + 1.1, -a, -a + 1.1
        def poly(pts, fill, extra=""):
            return f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="{fill}"{extra}/>'
        left = [P(x0, y1, 0), P(x1, y1, 0), P(x1, y1, h), P(x0, y1, h)]
        right = [P(x1, y1, 0), P(x1, y0, 0), P(x1, y0, h), P(x1, y1, h)]
        topf = [P(x0, y0, h), P(x1, y0, h), P(x1, y1, h), P(x0, y1, h)]
        hot = cnt == mx and cnt > 0
        face_l, face_r, face_t = ("#ff8a1f", "#c4630f", "#ffb066") if hot else ("#1f4a6b", "#173a55", "#5ec8ff")
        if cnt == 0:
            face_l, face_r, face_t = "#232c36", "#1b232b", "#2f3a46"
        # window bands
        bands = []
        for k in range(1, int(h / 0.6) + 1):
            z = k * 0.6
            if z >= h - .1: break
            a, b = P(x0, y1, z), P(x1, y1, z)
            bands.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
        delay = i * 0.12
        o.append(f'<g class="tw" style="animation-delay:{delay:.2f}s;transform-origin:{P(x0,y1,0)[0]:.0f}px {P(x0,y1,0)[1]:.0f}px">'
                 f'{poly(left, face_l)}{poly(right, face_r)}{poly(topf, face_t)}'
                 f'<g stroke="#0f141a" stroke-width="1" opacity=".35">{"".join(bands)}</g></g>')
        lab = P(x0 + .55, y1 + .6, 0)
        o.append(f'<text x="{lab[0]:.1f}" y="{lab[1]+14:.1f}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#7d8a96">{dt.date(yy, mm, 1).strftime("%b").upper()}</text>')
        if cnt > 0:
            tp = P(x0 + .55, y0 + .55, h)
            o.append(f'<text class="num" style="animation-delay:{delay+.6:.2f}s" x="{tp[0]:.1f}" y="{tp[1]-8:.1f}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#e8eae4">{cnt}</text>')
        if hot:
            tp = P(x0 + .55, y0 + .55, h)
            o.append(f'<circle class="beacon" cx="{tp[0]:.1f}" cy="{tp[1]-24:.1f}" r="4" fill="#ff4a3a"/>')
        pad.append((P(x0 - .3, y0 - .3, 0), P(x1 + .3, y1 + .3, 0)))
    # ground slab under the skyline
    g0 = (ox + (-0.6 - -0.6) * C * s, 0)
    def P0(x, yv):
        return ox + (x - yv) * C * s, oy + (x + yv) * 0.5 * s
    L = 11 * STEP
    ground = [P0(-0.4, -0.4), P0(L + 1.5, -L - 0.4), P0(L + 1.5, -L + 1.9), P0(-0.4, 1.9)]
    o.insert(0, f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in ground)}" fill="#1a2129" stroke="#2b3541"/>')

    # ---- signboard counters ----
    bx = 640
    boards = [
        ("CONTRIBUTIONS", cal["totalContributions"], "past year"),
        ("COMMITS", cc["totalCommitContributions"], "past year"),
        ("PUBLIC REPOS", u["repositories"]["totalCount"], f"{stars} star{'s' if stars != 1 else ''}"),
        ("CURRENT STREAK", cur, f"best {best} day{'s' if best != 1 else ''}"),
    ]
    for k, (label, val, sub) in enumerate(boards):
        x = bx + (k % 2) * 270
        y = 92 + (k // 2) * 112
        o.append(f'<g class="board" style="animation-delay:{.3+k*.15:.2f}s">'
                 f'<rect x="{x}" y="{y}" width="250" height="96" fill="#151b22" stroke="#2b3541"/>'
                 f'<rect x="{x}" y="{y}" width="250" height="5" fill="url(#hazard)"/>'
                 f'<text x="{x+16}" y="{y+30}" font-family="{MONO}" font-size="11" fill="#7d8a96" letter-spacing="1.5">{label}</text>'
                 f'<text x="{x+16}" y="{y+76}" font-family="{D}" font-weight="800" font-size="46" fill="#e8eae4">{esc(val)}</text>'
                 f'<text x="{x+234}" y="{y+76}" text-anchor="end" font-family="{FONT}" font-size="13" fill="#aeb4ad">{esc(sub)}</text></g>')

    # ---- materials schedule (languages) ----
    my = 336
    o.append(f'<text x="{bx}" y="{my}" font-family="{MONO}" font-size="11" fill="#7d8a96" letter-spacing="1.5">MATERIALS SCHEDULE · LANGUAGES IN PUBLIC REPOS</text>')
    palette = ["#5ec8ff", "#ff8a1f", "#c58bff", "#7fd6a0", "#f2c94c"]
    xcur = bx
    total_w = 520
    for k, (name, size) in enumerate(top):
        w = max(6, total_w * size / total_bytes)
        o.append(f'<rect class="bar" style="animation-delay:{.8+k*.15:.2f}s;transform-origin:{xcur:.0f}px 0" x="{xcur:.1f}" y="{my+12}" width="{w-3:.1f}" height="16" fill="{palette[k]}"/>')
        xcur += w
    lx = bx
    for k, (name, size) in enumerate(top):
        pct = 100 * size / total_bytes
        t = f"{name} {pct:.0f}%"
        o.append(f'<rect x="{lx}" y="{my+42}" width="9" height="9" fill="{palette[k]}"/><text x="{lx+14}" y="{my+51}" font-family="{FONT}" font-size="13" fill="#aeb4ad">{esc(t)}</text>')
        lx += 30 + len(t) * 8.2
    if not top:
        o.append(f'<text x="{bx}" y="{my+30}" font-family="{FONT}" font-size="13" fill="#7d8a96">No public code yet</text>')

    stamp = today.strftime("%d %b %Y").upper()
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Site progress: {cal['totalContributions']} contributions and {cc['totalCommitContributions']} commits in the past year, {u['repositories']['totalCount']} public repositories, current streak {cur} days, best {best}.">
<style>
  .tw{{animation:up 1.1s cubic-bezier(.2,.8,.2,1) both}}
  @keyframes up{{from{{transform:scaleY(0);opacity:0}}to{{transform:scaleY(1);opacity:1}}}}
  .num,.board{{animation:fade .8s ease both}}
  @keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
  .bar{{animation:grow 1s cubic-bezier(.2,.8,.2,1) both}}
  @keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
  .beacon{{animation:blink 1.4s steps(2,start) infinite}}
  @keyframes blink{{to{{visibility:hidden}}}}
  .scan{{animation:scan 6s ease-in-out infinite}}
  @keyframes scan{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX(450px)}}}}
  @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
  <pattern id="g4" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#1d2731"/></pattern>
  <pattern id="hazard" width="14" height="5" patternUnits="userSpaceOnUse" patternTransform="skewX(-45)"><rect width="7" height="5" fill="#ff8a1f"/><rect x="7" width="7" height="5" fill="#0f141a"/></pattern>
</defs>
<rect width="{W}" height="{H}" rx="14" fill="#0f141a"/><rect width="{W}" height="{H}" rx="14" fill="url(#g4)"/>
<text x="40" y="50" font-family="{MONO}" font-size="13" fill="#7d8a96" letter-spacing="2">SITE PROGRESS · CONTRIBUTIONS PER MONTH</text>
<text x="{W-40}" y="50" text-anchor="end" font-family="{MONO}" font-size="11" fill="#3b4652" letter-spacing="1">SURVEYED {stamp} · PUBLIC ACTIVITY</text>
{"".join(o)}
<line class="scan" x1="70" y1="110" x2="70" y2="400" stroke="#5ec8ff" stroke-width="1.5" stroke-dasharray="4 4" opacity=".5"/>
</svg>'''


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        print(render(sample()))
    else:
        login = sys.argv[1] if len(sys.argv) > 1 else os.environ["GITHUB_REPOSITORY_OWNER"]
        print(render(fetch(login, os.environ["GITHUB_TOKEN"])))
