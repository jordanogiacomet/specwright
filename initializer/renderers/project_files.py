from pathlib import Path


def write_basic_files(project_dir):

    Path(project_dir).mkdir(parents=True, exist_ok=True)

    (Path(project_dir) / "docs").mkdir(exist_ok=True)

    (Path(project_dir) / "docs/stories").mkdir(parents=True, exist_ok=True)

    (Path(project_dir) / "docs/architecture").mkdir(parents=True, exist_ok=True)

    (Path(project_dir) / "src").mkdir(exist_ok=True)

    (Path(project_dir) / "public").mkdir(exist_ok=True)


def write_agents(project_dir):

    text = """
# AGENTS.md

You are an execution agent working inside this repository.

Read order:
1. PRD.md
2. decisions.md
3. progress.txt
4. docs/stories/

Rules:
- Work one story at a time
- Do not deploy automatically
- Update progress.txt after work
"""

    (Path(project_dir) / "AGENTS.md").write_text(text.strip())


def write_progress(project_dir):

    text = """
# progress.txt

[BOOTSTRAP] Project initialized
"""

    (Path(project_dir) / "progress.txt").write_text(text.strip())


def write_decisions(project_dir):

    text = """
# decisions.md

## Architecture decisions

Initial architecture generated from archetype playbook.
"""

    (Path(project_dir) / "decisions.md").write_text(text.strip())