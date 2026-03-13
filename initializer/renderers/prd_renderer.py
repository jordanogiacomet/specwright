def render_prd(spec):

    stack = spec["stack"]
    architecture = spec["architecture"]

    text = f"""
# PRD

## Product

{spec["answers"]["project_name"]}

---

## Summary

{spec["prompt"]}

---

## Stack

Frontend: {stack["frontend"]}
Backend: {stack["backend"]}
Database: {stack["database"]}

---

## Architecture

Style: {architecture["style"]}

### Components
"""

    for comp in architecture["components"]:
        text += f"- {comp['name']} ({comp['technology']}) — {comp['role']}\n"

    text += "\n### Decisions\n"

    for d in architecture["decisions"]:
        text += f"- {d}\n"

    text += "\n---\n## Features\n"

    for f in spec["features"]:
        text += f"- {f}\n"

    text += "\n---\n## Stories\n"

    for s in spec["stories"]:
        text += f"- {s['id']} — {s['title']}\n"

    return text