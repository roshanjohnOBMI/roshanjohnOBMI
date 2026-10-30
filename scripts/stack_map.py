#!/usr/bin/env python3
"""Single source of truth: which tools each app routes through.

`python3 scripts/stack_map.py --validate` checks the map (and the README Work table) and exits 1
on any disconnection. `--json` prints the validated map for the interactive explorer.
"""
import json
import os
import re
import sys

STAGES = ["Authoring", "Code", "Cloud", "Data", "Platform", "Output"]

CATEGORY_COLOURS = {
    "AEC": "#ff8a1f", "Code": "#f2c94c", "Cloud": "#5ec8ff",
    "Data": "#7fd6a0", "Power Platform": "#c58bff", "Output": "#e8eae4",
}

# name: (short chip label, category, stage)
TOOLS = {
    "Revit API":                  ("Revit API", "AEC", "Authoring"),
    "Navisworks API":             ("Navisworks", "AEC", "Authoring"),
    "C# / .NET":                  ("C# / .NET", "Code", "Code"),
    "JavaScript / Node.js":       ("Node.js", "Code", "Code"),
    "TypeScript":                 ("TypeScript", "Code", "Code"),
    "Autodesk Platform Services": ("APS", "Cloud", "Cloud"),
    "ACC":                        ("ACC", "Cloud", "Cloud"),
    "Azure":                      ("Azure", "Cloud", "Cloud"),
    "GraphQL / REST":             ("GraphQL", "Data", "Data"),
    "ClosedXML":                  ("ClosedXML", "Data", "Data"),
    "Power Query":                ("Power Query", "Data", "Data"),
    "SharePoint":                 ("SharePoint", "Data", "Data"),
    "Power Automate":             ("Automate", "Power Platform", "Platform"),
    "Power Apps":                 ("Power Apps", "Power Platform", "Platform"),
    "Power BI":                   ("Power BI", "Power Platform", "Platform"),
}
OUTPUTS = ["Dashboards", "Reports", "Model updates", "Web apps"]

# Tools in the stack that aren't part of a published app route (shown, not hidden).
STANDALONE = {}

# name must match the README Work table exactly
APPS = [
    {"name": "OBMI Meridian", "status": "wip", "output": "Dashboards",
     "tools": ["Revit API", "Navisworks API", "C# / .NET", "JavaScript / Node.js", "Autodesk Platform Services", "Azure"],
     "what": "Deploys and tracks BIM add-ins office-wide"},
    {"name": "ACC Model Health Check", "status": "live", "output": "Dashboards",
     "tools": ["JavaScript / Node.js", "Autodesk Platform Services", "ACC"],
     "what": "Health reports for Revit models on ACC"},
    {"name": "TIDP / MIDP Checker", "status": "live", "output": "Reports",
     "tools": ["JavaScript / Node.js", "Autodesk Platform Services", "ACC"],
     "what": "Checks delivery plans against ACC deliverables"},
    {"name": "Workset Manager", "status": "live", "output": "Model updates",
     "tools": ["Revit API", "C# / .NET"],
     "what": "Bulk workset assignment from Excel rules"},
    {"name": "ClashCommentSync", "status": "live", "output": "Reports",
     "tools": ["Navisworks API", "C# / .NET", "ClosedXML"],
     "what": "Round-trips clash comments through Excel"},
    {"name": "Clash Tolerance Updater", "status": "live", "output": "Model updates",
     "tools": ["Navisworks API", "C# / .NET"],
     "what": "Bulk tolerance edits through the Clash API"},
    {"name": "ACC → Power BI Live Data", "status": "live", "output": "Dashboards",
     "tools": ["ACC", "Autodesk Platform Services", "GraphQL / REST", "Power Query", "Power BI"],
     "what": "Live Revit data in Power BI Online"},
    {"name": "ACC File Activity Tracker", "status": "live", "output": "Dashboards",
     "tools": ["ACC", "SharePoint", "Power Automate", "Power Apps"],
     "what": "Logs ACC file activity to SharePoint"},
    {"name": "OBMI Move30", "status": "wip", "output": "Web apps",
     "tools": ["JavaScript / Node.js", "Azure"],
     "what": "30x30 Wellness Challenge web app"},
    {"name": "obmiAppCosting", "status": "live", "output": "Web apps",
     "tools": ["TypeScript"],
     "what": "Costing app for OBMI applications"},
    {"name": "Roshan's Build Site", "status": "live", "output": "Web apps",
     "tools": ["JavaScript / Node.js"],
     "what": "This profile as a playable 3D site"},
]


def stage_of(tool):
    return TOOLS[tool][2]


def route(app):
    """Tools sorted by stage, then the output."""
    order = {s: i for i, s in enumerate(STAGES)}
    return sorted(app["tools"], key=lambda t: order[stage_of(t)]) + [app["output"]]


def readme_apps(path):
    if not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8").read()
    m = re.search(r"\| Name \| Description \|.*?\n\|[-| ]+\|\n((?:\|.*\|\n?)+)", text)
    if not m:
        return []
    return [row.split("|")[1].strip() for row in m.group(1).strip().splitlines()]


def validate(readme="README.md"):
    errors, notes = [], []
    used = set()
    for app in APPS:
        if not app["tools"]:
            errors.append(f"{app['name']}: no tools routed")
        for t in app["tools"]:
            if t not in TOOLS:
                errors.append(f"{app['name']}: unknown tool '{t}'")
            used.add(t)
        if app["output"] not in OUTPUTS:
            errors.append(f"{app['name']}: unknown output '{app['output']}'")
    for t in TOOLS:
        if t not in used and t not in STANDALONE:
            errors.append(f"orphan tool: '{t}' is in the stack but no app routes through it")
        if t in used and t in STANDALONE:
            errors.append(f"'{t}' is marked standalone but an app routes through it")
    for o in OUTPUTS:
        if not any(a["output"] == o for a in APPS):
            errors.append(f"unused output '{o}'")
    names = [a["name"] for a in APPS]
    if len(set(names)) != len(names):
        errors.append("duplicate app names")
    table = readme_apps(readme)
    if table is not None:
        for n in names:
            if n not in table:
                errors.append(f"'{n}' is mapped but missing from the README Work table")
        for n in table:
            if n not in names:
                errors.append(f"'{n}' is in the README Work table but has no route in the map")
    else:
        notes.append("README not found; Work table not checked")
    return errors, notes


def as_json():
    return {
        "stages": STAGES,
        "colours": CATEGORY_COLOURS,
        "tools": [{"name": n, "short": s, "category": c, "stage": st, "standalone": STANDALONE.get(n)}
                  for n, (s, c, st) in TOOLS.items()],
        "outputs": OUTPUTS,
        "apps": [{**a, "route": route(a)} for a in APPS],
    }


if __name__ == "__main__":
    readme = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")
    errors, notes = validate(readme)
    if "--json" in sys.argv:
        if errors:
            sys.exit("map invalid:\n  " + "\n  ".join(errors))
        print(json.dumps(as_json(), indent=1, ensure_ascii=False))
    else:
        for n in notes:
            print("note:", n)
        if errors:
            print("FAILED")
            for e in errors:
                print("  ✗", e)
            sys.exit(1)
        print(f"OK · {len(APPS)} apps routed · {len(TOOLS)} tools · {len(STANDALONE)} standalone · 0 orphans")
