from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from initializer.flow.new_project import load_project_spec


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _resolve_plan_input_path(spec_path: str | None) -> str:
    if spec_path:
        return spec_path

    default_spec = Path("./spec.json")
    if default_spec.exists():
        return str(default_spec)

    raise ValueError(
        "Plan requires --spec <path> or a local ./spec.json file in the current directory."
    )


def render_prd(spec: dict[str, Any]) -> str:
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    architecture = spec.get("architecture", {})
    decisions = architecture.get("decisions", [])

    project_name = answers.get("project_name", "Unnamed Project")
    summary = answers.get("summary", "")
    prompt = spec.get("prompt", "")
    archetype = spec.get("archetype", "unknown")

    content = f"""# {project_name}

## Summary

{summary}

## Prompt

{prompt}

## Archetype

{archetype}

## Answers

- surface: {answers.get("surface", "unknown")}
- deploy_target: {answers.get("deploy_target", "unknown")}

## Stack

- frontend: {stack.get("frontend", "unknown")}
- backend: {stack.get("backend", "unknown")}
- database: {stack.get("database", "unknown")}

## Features
"""

    if features:
        for feature in features:
            content += f"- {feature}\n"
    else:
        content += "- none\n"

    content += "\n## Capabilities\n"
    if capabilities:
        for capability in capabilities:
            content += f"- {capability}\n"
    else:
        content += "- none\n"

    content += "\n## Architecture Decisions\n"
    if decisions:
        for decision in decisions:
            content += f"- {decision}\n"
    else:
        content += "- none\n"

    return content


def render_decisions(spec: dict[str, Any]) -> str:
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    archetype = spec.get("archetype", "unknown")
    architecture = spec.get("architecture", {})
    architecture_decisions = architecture.get("decisions", [])

    entries: list[dict[str, str]] = [
        {
            "id": "DEC-001",
            "decision": f"Use archetype `{archetype}` as the planning baseline.",
            "reason": "The plan was generated from the supplied spec input.",
            "consequences": "Future implementation planning should remain aligned with this archetype unless a later decision supersedes it.",
        },
        {
            "id": "DEC-002",
            "decision": (
                "Use stack "
                f"frontend=`{stack.get('frontend', 'unknown')}`, "
                f"backend=`{stack.get('backend', 'unknown')}`, "
                f"database=`{stack.get('database', 'unknown')}`."
            ),
            "reason": "The stack is part of the supplied spec contract.",
            "consequences": "Stories, architecture, and implementation work should assume this stack unless explicitly revised.",
        },
        {
            "id": "DEC-003",
            "decision": (
                f"Use surface `{answers.get('surface', 'unknown')}` "
                f"with deploy target `{answers.get('deploy_target', 'unknown')}`."
            ),
            "reason": "Surface and deploy target are explicit planning inputs.",
            "consequences": "Public-site behavior, operational decisions, and deployment assumptions should respect these values.",
        },
    ]

    next_index = 4
    for decision in architecture_decisions:
        entries.append(
            {
                "id": f"DEC-{next_index:03}",
                "decision": decision,
                "reason": "This decision was derived in the current spec architecture.",
                "consequences": "Implementation planning should account for this architectural constraint.",
            }
        )
        next_index += 1

    content = """# decisions.md

## Purpose

This file records stable repo-wide decisions that future work should treat as settled unless a newer decision explicitly replaces them.

---

## Status labels

Use one of these labels:

- `accepted`
- `superseded`
- `provisional`

---

## Decisions
"""

    for entry in entries:
        content += f"""

### {entry["id"]}
- **Date:** generated
- **Status:** accepted
- **Decision:** {entry["decision"]}
- **Reason:** {entry["reason"]}
- **Consequences:** {entry["consequences"]}
"""

    return content


def run_plan_project(spec_path: str | None = None) -> int:
    try:
        input_path = _resolve_plan_input_path(spec_path)
        spec = load_project_spec(input_path)
    except ValueError as exc:
        print(f"\nError: {exc}\n")
        return 1

    output_dir = Path(f"./plans/{spec['answers']['project_slug']}").resolve()

    if output_dir.exists():
        print("Plan directory already exists.")
        return 1

    output_dir.mkdir(parents=True)

    write_file(output_dir / "PRD.md", render_prd(spec))
    write_file(output_dir / "decisions.md", render_decisions(spec))
    write_file(
        output_dir / "prd.json",
        json.dumps(spec, indent=2, ensure_ascii=False),
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
