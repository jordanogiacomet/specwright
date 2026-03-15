"""OpenClaw Bundle Generator.

Generates a rich .openclaw/ bundle inside the output directory that
gives any execution agent (Codex, Claude Code, OpenClaw, Ralph loop)
everything it needs to start implementing story-by-story without
external context.

The bundle includes:
- AGENTS.md — project-specific instructions for the executor
- OPENCLAW.md — handoff document for OpenClaw-specific loops
- manifest.json — machine-readable project metadata
- repo-contract.json — contract rules for the generated package
- commands.json — validation commands (to be filled by the executor)
- execution-plan.json — ordered story list with phases and dependencies
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _get_decision_signals(spec: dict[str, Any]) -> dict[str, Any]:
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _build_execution_plan(spec: dict[str, Any]) -> dict[str, Any]:
    """Build an ordered execution plan from stories.

    Groups stories into phases:
    1. bootstrap — repository, database, backend, frontend setup
    2. features — authentication, roles, media-library, etc.
    3. product — product-shape stories (dashboard, portal, backoffice)
    4. domain — core work feature stories (deadlines, task-assignment, etc.)
    5. automation — scheduled jobs, background workers
    6. operations — monitoring, backups, operational stories
    """
    stories = spec.get("stories", [])

    phases = {
        "bootstrap": [],
        "features": [],
        "product": [],
        "domain": [],
        "automation": [],
        "operations": [],
    }

    for story in stories:
        if not isinstance(story, dict):
            continue

        story_id = story.get("id", "")
        story_key = story.get("story_key", "")
        title = story.get("title", "")

        entry = {
            "id": story_id,
            "title": title,
            "status": "pending",
        }
        if story_key:
            entry["story_key"] = story_key

        if story_key.startswith("bootstrap."):
            phases["bootstrap"].append(entry)
        elif story_key.startswith("feature."):
            phases["features"].append(entry)
        elif story_key.startswith("product."):
            if "automation" in story_key or "scheduled" in story_key:
                phases["automation"].append(entry)
            else:
                # Separate domain features from product shell
                if any(
                    kw in story_key
                    for kw in (
                        "deadlines", "progress", "task-assignment",
                        "reminders", "report", "approvals", "team-visibility",
                    )
                ):
                    phases["domain"].append(entry)
                else:
                    phases["product"].append(entry)
        elif story_id in ("ST-900", "ST-901") or "monitoring" in title.lower() or "backup" in title.lower():
            phases["operations"].append(entry)
        else:
            # Stories from capability handlers (i18n, cms, scheduled-jobs, public-site)
            # that don't have a story_key prefix
            lower_title = title.lower()
            if any(kw in lower_title for kw in ("locale", "i18n", "translation")):
                phases["features"].append(entry)
            elif any(kw in lower_title for kw in ("cms", "content model")):
                phases["features"].append(entry)
            elif any(kw in lower_title for kw in ("cdn", "public site")):
                phases["features"].append(entry)
            elif any(kw in lower_title for kw in ("worker", "scheduler", "automation", "scheduled")):
                phases["automation"].append(entry)
            else:
                phases["features"].append(entry)

    # Build ordered list
    ordered: list[dict[str, Any]] = []
    order = 1

    for phase_name in ("bootstrap", "features", "product", "domain", "automation", "operations"):
        phase_stories = phases[phase_name]
        for entry in phase_stories:
            entry["order"] = order
            entry["phase"] = phase_name
            ordered.append(entry)
            order += 1

    return {
        "total_stories": len(ordered),
        "phases": list(phases.keys()),
        "phase_order": [
            {"phase": "bootstrap", "description": "Project setup and infrastructure", "count": len(phases["bootstrap"])},
            {"phase": "features", "description": "Core feature implementation", "count": len(phases["features"])},
            {"phase": "product", "description": "Product shell and navigation", "count": len(phases["product"])},
            {"phase": "domain", "description": "Domain-specific work features", "count": len(phases["domain"])},
            {"phase": "automation", "description": "Background jobs and automation", "count": len(phases["automation"])},
            {"phase": "operations", "description": "Monitoring, backups, operational setup", "count": len(phases["operations"])},
        ],
        "stories": ordered,
    }


def _build_agents_md(spec: dict[str, Any]) -> str:
    """Build a project-specific AGENTS.md."""
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    signals = _get_decision_signals(spec)

    project_name = answers.get("project_name", "Generated Project")
    summary = answers.get("summary", "")
    surface = answers.get("surface", "unknown")
    app_shape = signals.get("app_shape", "unknown")
    primary_audience = signals.get("primary_audience", "unknown")
    core_work_features = signals.get("core_work_features", [])
    if not isinstance(core_work_features, list):
        core_work_features = []

    cap_text = ", ".join(capabilities) if capabilities else "none"
    feat_text = ", ".join(features) if features else "none"
    cwf_text = ", ".join(core_work_features) if core_work_features else "none specified"

    return f"""# AGENTS.md

You are an execution agent working on **{project_name}**.

## What this project is

{summary}

- **App shape**: {app_shape}
- **Primary audience**: {primary_audience}
- **Surface**: {surface}
- **Stack**: {stack.get("frontend", "?")} + {stack.get("backend", "?")} + {stack.get("database", "?")}
- **Capabilities**: {cap_text}
- **Features**: {feat_text}
- **Core work features**: {cwf_text}

## Read order

Before changing code, read these files in this order:

1. `spec.json` — structured source of truth
2. `PRD.md` — enriched product requirements
3. `decisions.md` — stable architectural decisions
4. `progress.txt` — append-only execution log
5. `.openclaw/execution-plan.json` — ordered story list with phases
6. `docs/stories/` — individual story files
7. project source files

## Execution rules

- Work **one story at a time**, following the order in `execution-plan.json`
- Start with the **bootstrap phase** — these set up the project structure
- Do not skip ahead to domain stories before features are in place
- Do not silently change architecture or product scope
- Prefer minimal, targeted patches over large rewrites
- Validate after each story when possible
- Append progress to `progress.txt` after meaningful work

## What NOT to do

- Do not add a public-facing site unless `public-site` is in capabilities
- Do not add CMS features unless `cms` is in capabilities
- Do not add i18n unless `i18n` is in capabilities
- Do not redesign the architecture — it was derived from the spec
- Do not merge stories or skip validation steps

## Contract

- `spec.json` is the structured source of truth
- `decisions.md` contains stable decisions unless explicitly superseded
- `progress.txt` is append-only
- Stories under `docs/stories/` define execution slices
- Implementation must follow the generated architecture

## Validation

When relevant, validate in this order:

1. Targeted test for the current story
2. Full test suite
3. Lint
4. Build

If a command is unavailable, record that in `progress.txt`.

## Completion standard

A story is complete when:

- Code is changed and working
- Validation was attempted
- Results were recorded in `progress.txt`
- The story requirements are satisfied
"""


def _build_openclaw_md(spec: dict[str, Any]) -> str:
    """Build a project-specific OPENCLAW.md."""
    answers = spec.get("answers", {})
    project_name = answers.get("project_name", "Generated Project")

    return f"""# OPENCLAW.md

This is the execution package for **{project_name}**.

## Purpose

OpenClaw should treat this folder as a prepared execution package.
All planning is done — the agent's job is to implement.

## Source of truth

- `spec.json` — full project specification
- `PRD.md` — enriched product requirements with intelligence
- `decisions.md` — architectural decisions
- `progress.txt` — execution log
- `.openclaw/execution-plan.json` — ordered implementation plan
- `docs/stories/` — individual story definitions

## Execution model

1. Read `execution-plan.json` to find the next pending story
2. Read the story file in `docs/stories/`
3. Implement the story
4. Validate the work
5. Update `progress.txt`
6. Move to next story

## Constraints

- Do not replace the generated contract with a new architecture
- Do not rewrite unrelated parts of the project
- Do not skip validation when commands are available
- Do not mark work as complete without recording outcomes
- Follow the phase order: bootstrap → features → product → domain → automation → operations
"""


def write_openclaw_bundle(output_dir: Path, spec: dict[str, Any]) -> None:
    """Generate the .openclaw/ bundle with project-specific context."""
    openclaw_dir = output_dir / ".openclaw"
    openclaw_dir.mkdir(parents=True, exist_ok=True)

    project_slug = spec.get("answers", {}).get("project_slug", "generated-project")
    signals = _get_decision_signals(spec)

    # --- AGENTS.md ---
    agents_md = _build_agents_md(spec)
    (openclaw_dir / "AGENTS.md").write_text(agents_md, encoding="utf-8")

    # --- OPENCLAW.md ---
    openclaw_md = _build_openclaw_md(spec)
    (openclaw_dir / "OPENCLAW.md").write_text(openclaw_md, encoding="utf-8")

    # --- execution-plan.json ---
    execution_plan = _build_execution_plan(spec)
    (openclaw_dir / "execution-plan.json").write_text(
        json.dumps(execution_plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- manifest.json ---
    manifest = {
        "project_root_type": "generated-project-package",
        "project_slug": project_slug,
        "app_shape": signals.get("app_shape", "unknown"),
        "primary_audience": signals.get("primary_audience", "unknown"),
        "capabilities": spec.get("capabilities", []),
        "features": spec.get("features", []),
        "source_of_truth": [
            "spec.json",
            "PRD.md",
            "decisions.md",
            "progress.txt",
            "architecture.md",
            "docs/stories",
            ".openclaw/execution-plan.json",
            ".openclaw/AGENTS.md",
        ],
        "execution_mode": "story-by-story",
        "primary_input": "spec.json",
        "policies": {
            "one_story_at_a_time": True,
            "must_validate_before_done": True,
            "append_progress": True,
            "avoid_architecture_drift": True,
            "follow_phase_order": True,
        },
    }
    (openclaw_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- repo-contract.json ---
    repo_contract = {
        "contract": {
            "kind": "generated-project",
            "primary_spec": "spec.json",
            "primary_prd": "PRD.md",
            "primary_architecture": "architecture.md",
            "primary_decisions": "decisions.md",
            "primary_progress_log": "progress.txt",
            "stories_dir": "docs/stories",
            "execution_plan": ".openclaw/execution-plan.json",
        },
        "execution_expectations": {
            "story_driven": True,
            "validate_changes": True,
            "record_progress": True,
            "preserve_generated_scope": True,
            "follow_phase_order": True,
        },
    }
    (openclaw_dir / "repo-contract.json").write_text(
        json.dumps(repo_contract, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- commands.json ---
    commands = {
        "commands": {
            "test": "",
            "lint": "",
            "build": "",
            "dev": "",
        },
        "notes": [
            "Commands are empty until the executor sets up the project.",
            "After bootstrap phase, update this file with actual commands.",
            "The executor should run `test` after each story when available.",
        ],
    }
    (openclaw_dir / "commands.json").write_text(
        json.dumps(commands, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )