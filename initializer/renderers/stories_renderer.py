from pathlib import Path


def write_stories(project_dir, stories):

    stories_dir = Path(project_dir) / "docs/stories"

    stories_dir.mkdir(parents=True, exist_ok=True)

    for s in stories:

        content = f"""
# {s["id"]}

## Title

{s["title"]}

## Description

{s["description"]}
"""

        path = stories_dir / f"{s['id']}.md"

        path.write_text(content.strip())