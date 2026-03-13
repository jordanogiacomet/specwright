from pathlib import Path


def write_architecture(project_dir, architecture):

    arch_dir = Path(project_dir) / "docs/architecture"

    arch_dir.mkdir(parents=True, exist_ok=True)

    text = f"""
# Architecture

Style: {architecture["style"]}

## Components
"""

    for c in architecture["components"]:
        text += f"- {c['name']} ({c['technology']}) — {c['role']}\n"

    text += "\n## Decisions\n"

    for d in architecture["decisions"]:
        text += f"- {d}\n"

    path = arch_dir / "architecture.md"

    path.write_text(text.strip())