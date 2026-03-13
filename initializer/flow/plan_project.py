from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from initializer.flow.new_project import (
    BootstrapInput,
    collect_input,
    load_semantic_spec,
    render_prd,
    render_decisions,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def run_plan_project(spec_path: str | None = None) -> int:

    if spec_path:
        print("Loading semantic spec...")
        data = load_semantic_spec(spec_path)
    else:
        data = collect_input()

    output_dir = Path(f"./plans/{data.project_slug}").resolve()

    if output_dir.exists():
        print("Plan directory already exists.")
        return 1

    output_dir.mkdir(parents=True)

    write_file(output_dir / "PRD.md", render_prd(data))

    write_file(output_dir / "decisions.md", render_decisions(data))

    write_file(
        output_dir / "prd.json",
        json.dumps(asdict(data), indent=2, ensure_ascii=False),
    )

    print()
    print("Plan generated successfully.")
    print(f"Location: {output_dir}")
    print()
    print("Artifacts:")
    print("  - PRD.md")
    print("  - decisions.md")
    print("  - prd.json")
    print()
    print("Review this plan before generating a full project bootstrap.")

    return 0