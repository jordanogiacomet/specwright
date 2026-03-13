from __future__ import annotations

from datetime import datetime
from pathlib import Path


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def archive_prd(project_dir: Path, prd_content: str) -> None:
    history_dir = project_dir / "docs" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    archive_path = history_dir / f"PRD-{timestamp}.md"

    write_file(archive_path, prd_content)


def improve_prd(prd_content: str) -> str:
    """
    Placeholder refinement logic.

    Aqui você poderia integrar:
    - OpenClaw
    - LLM
    - heurísticas
    """

    if "## Version" in prd_content:
        return prd_content.replace("`0.1`", "`0.2`")

    return prd_content


def run_refine_project(path: str) -> int:

    project_dir = Path(path).resolve()

    prd_path = project_dir / "PRD.md"

    if not prd_path.exists():
        print("PRD.md not found.")
        return 1

    prd_content = read_file(prd_path)

    archive_prd(project_dir, prd_content)

    improved = improve_prd(prd_content)

    write_file(prd_path, improved)

    print()
    print("PRD refined successfully.")
    print(f"Project: {project_dir}")
    print("Previous version archived in docs/history/")
    print()

    return 0