"""Prepare Project Flow.

Final step before execution. Takes a generated (and optionally enriched)
project package and rewrites all execution artifacts with full context.

This is the "compiler" that produces the final execution-ready package:
- Consolidates .codex/AGENTS.md with PRD intelligence
- Rewrites PRD.md as the definitive version
- Detects stack and fills commands.json
- Validates package completeness
- Generates execution preview

Usage:
    initializer prepare output/my-project
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from initializer.engine.story_engine import generate_stories
from initializer.engine.validation_contract import detect_validation_bundle
from initializer.renderers.codex_bundle import write_codex_bundle
from initializer.renderers.openclaw_bundle import write_openclaw_bundle


def _load_spec(project_dir: Path) -> dict[str, Any]:
    spec_path = project_dir / "spec.json"
    if not spec_path.exists():
        raise ValueError(f"spec.json not found in {project_dir}")

    data = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"spec.json must contain a JSON object: {spec_path}")

    return data


def _get_decision_signals(spec: dict[str, Any]) -> dict[str, Any]:
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


# -------------------------------------------------------
# Consolidated AGENTS.md
# -------------------------------------------------------

def _build_consolidated_agents_md(spec: dict[str, Any]) -> str:
    """Build the definitive .codex/AGENTS.md with full context including
    PRD intelligence, scope boundaries, and execution rules."""
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    signals = _get_decision_signals(spec)
    intelligence = spec.get("prd_intelligence", {})
    stories = spec.get("stories", [])

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

    # Problem statement from intelligence
    problem = intelligence.get("problem_statement", "")

    # Personas
    personas = intelligence.get("personas", [])
    personas_text = ""
    if personas:
        for p in personas:
            personas_text += f"- **{p.get('name', '?')}**: {p.get('goal', '')}\n"

    # Success metrics
    metrics = intelligence.get("success_metrics", [])
    metrics_text = ""
    if metrics:
        for m in metrics:
            metrics_text += f"- {m}\n"

    # Scope
    scope = intelligence.get("scope", {})
    in_scope = scope.get("in_scope", [])
    out_of_scope = scope.get("out_of_scope", [])
    scope_text = ""
    if in_scope:
        scope_text += "### In scope\n"
        for item in in_scope:
            scope_text += f"- {item}\n"
        scope_text += "\n"
    if out_of_scope:
        scope_text += "### Out of scope\n"
        for item in out_of_scope:
            scope_text += f"- {item}\n"

    # Scope boundaries (do NOT rules)
    do_not_rules = []
    if "public-site" not in capabilities:
        do_not_rules.append("- Do NOT add a public-facing site, CDN, SSR/ISR, or SEO features")
    if "cms" not in capabilities:
        do_not_rules.append("- Do NOT add CMS, content management, or editorial features")
    if "i18n" not in capabilities:
        do_not_rules.append("- Do NOT add i18n, localization, or multi-language features")
    if "scheduled-jobs" not in capabilities:
        do_not_rules.append("- Do NOT add background workers, cron jobs, or scheduled tasks")
    do_not_section = "\n".join(do_not_rules) if do_not_rules else "- No specific restrictions"

    # Story count
    total_stories = len(stories)

    return f"""# AGENTS.md — {project_name}

## Mission

You are implementing **{project_name}** story-by-story.
The ralph.sh script feeds you one story at a time.
Your job is to implement each story with minimal, targeted changes.

## Product

{problem if problem else summary}

- **App shape**: {app_shape}
- **Audience**: {primary_audience}
- **Surface**: {surface}
- **Stack**: {stack.get("frontend", "?")} + {stack.get("backend", "?")} + {stack.get("database", "?")}
- **Capabilities**: {cap_text}
- **Features**: {feat_text}
- **Core work features**: {cwf_text}
- **Total stories**: {total_stories}

{f"## Personas{chr(10)}{chr(10)}{personas_text}" if personas_text else ""}
{f"## Success Metrics{chr(10)}{chr(10)}{metrics_text}" if metrics_text else ""}
{f"## Scope{chr(10)}{chr(10)}{scope_text}" if scope_text else ""}
## Execution Rules

1. Read the story file passed to you
2. Read `spec.json` for full project context
3. Read `architecture.md` for component structure
4. Implement with minimal, targeted changes
5. Run validation if commands are available (see `.openclaw/commands.json`)
6. Do NOT change architecture or scope beyond what the story requires
7. Do NOT skip stories or combine multiple stories

## Scope Boundaries

{do_not_section}
- Do NOT redesign the architecture
- Do NOT add features not listed in the spec
- Do NOT skip to later stories — implement only what is asked

## File Reference

| File | Purpose |
|------|---------|
| `spec.json` | Structured source of truth |
| `PRD.md` | Product requirements with intelligence |
| `architecture.md` | Components, tech choices, decisions |
| `decisions.md` | Stable architectural decisions |
| `progress.txt` | Append-only execution log |
| `.openclaw/execution-plan.json` | Ordered story list with phases |
| `.openclaw/commands.json` | Validation commands |
| `docs/stories/` | Individual story definitions |

## Validation

After each story, run in this order (if available):

1. Test command (see commands.json)
2. Lint command
3. Build command

If a command doesn't exist yet, note that. After bootstrap stories,
update `.openclaw/commands.json` with the actual commands.

## Stack

- **Frontend**: {stack.get("frontend", "unknown")}
- **Backend**: {stack.get("backend", "unknown")}
- **Database**: {stack.get("database", "unknown")}
- **Deploy target**: {answers.get("deploy_target", "unknown")}
"""


# -------------------------------------------------------
# Consolidated PRD.md
# -------------------------------------------------------

def _build_consolidated_prd(spec: dict[str, Any]) -> str:
    """Build the definitive PRD.md with all available context."""
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    architecture = spec.get("architecture", {})
    intelligence = spec.get("prd_intelligence", {})
    discovery = spec.get("discovery", {})
    signals = _get_decision_signals(spec)
    stories = spec.get("stories", [])

    project_name = answers.get("project_name", "Unnamed Project")
    summary = answers.get("summary", "")

    lines: list[str] = []
    lines.append(f"# {project_name}")
    lines.append("")

    # Problem Statement
    problem = intelligence.get("problem_statement", "")
    if problem:
        lines.append("## Problem Statement")
        lines.append("")
        lines.append(problem)
        lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")

    # Personas
    personas = intelligence.get("personas", [])
    if personas:
        lines.append("## Personas")
        lines.append("")
        for persona in personas:
            lines.append(f"- **{persona.get('name', '?')}**: {persona.get('goal', '')}")
        lines.append("")

    # Success Metrics
    metrics = intelligence.get("success_metrics", [])
    if metrics:
        lines.append("## Success Metrics")
        lines.append("")
        for metric in metrics:
            lines.append(f"- {metric}")
        lines.append("")

    # Scope
    scope = intelligence.get("scope", {})
    in_scope = scope.get("in_scope", [])
    out_of_scope = scope.get("out_of_scope", [])
    if in_scope or out_of_scope:
        lines.append("## Scope")
        lines.append("")
        if in_scope:
            lines.append("### In Scope")
            lines.append("")
            for item in in_scope:
                lines.append(f"- {item}")
            lines.append("")
        if out_of_scope:
            lines.append("### Out of Scope")
            lines.append("")
            for item in out_of_scope:
                lines.append(f"- {item}")
            lines.append("")

    # Assumptions
    assumptions = intelligence.get("assumptions", [])
    if assumptions:
        lines.append("## Assumptions")
        lines.append("")
        for assumption in assumptions:
            lines.append(f"- {assumption}")
        lines.append("")

    # Stack
    lines.append("## Stack")
    lines.append("")
    lines.append(f"- Frontend: {stack.get('frontend', 'unknown')}")
    lines.append(f"- Backend: {stack.get('backend', 'unknown')}")
    lines.append(f"- Database: {stack.get('database', 'unknown')}")
    lines.append("")

    # Features
    lines.append("## Features")
    lines.append("")
    for feature in features:
        lines.append(f"- {feature}")
    lines.append("")

    # Capabilities
    if capabilities:
        lines.append("## Capabilities")
        lines.append("")
        for capability in capabilities:
            lines.append(f"- {capability}")
        lines.append("")

    # Architecture Decisions
    decisions = architecture.get("decisions", [])
    if decisions:
        lines.append("## Architecture Decisions")
        lines.append("")
        for decision in decisions:
            lines.append(f"- {decision}")
        lines.append("")

    # Stories overview
    if stories:
        lines.append("## Stories")
        lines.append("")
        for story in stories:
            sid = story.get("id", "?")
            title = story.get("title", "?")
            phase = ""
            story_key = story.get("story_key", "")
            if story_key.startswith("bootstrap."):
                phase = "bootstrap"
            elif story_key.startswith("feature."):
                phase = "feature"
            elif story_key.startswith("product."):
                phase = "product"
            lines.append(f"- **{sid}**: {title}" + (f" ({phase})" if phase else ""))
        lines.append("")

    # Discovery Signals
    if signals:
        lines.append("## Discovery Signals")
        lines.append("")
        for key, value in signals.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")

    # Conflicts
    conflicts = discovery.get("conflicts", []) if isinstance(discovery, dict) else []
    if conflicts:
        lines.append("## Conflicts")
        lines.append("")
        for conflict in conflicts:
            lines.append(f"- {conflict}")
        lines.append("")

    return "\n".join(lines) + "\n"


# -------------------------------------------------------
# Commands detection
# -------------------------------------------------------

def _detect_commands(project_dir: Path, spec: dict[str, Any]) -> dict[str, Any]:
    """Detect available validation commands + contract based on project files."""
    return detect_validation_bundle(project_dir, spec)


# -------------------------------------------------------
# Package validation
# -------------------------------------------------------

def _validate_package(project_dir: Path, spec: dict[str, Any]) -> list[str]:
    """Validate that the execution package is complete."""
    issues: list[str] = []

    required_files = [
        "spec.json",
        "PRD.md",
        "architecture.md",
        "decisions.md",
        "progress.txt",
    ]
    for filename in required_files:
        if not (project_dir / filename).exists():
            issues.append(f"Missing: {filename}")

    if not (project_dir / "docs" / "stories").exists():
        issues.append("Missing: docs/stories/")

    stories = spec.get("stories", [])
    if not stories:
        issues.append("No stories in spec.json")

    stories_dir = project_dir / "docs" / "stories"
    if stories_dir.exists():
        for story in stories:
            sid = story.get("id", "")
            if sid and not (stories_dir / f"{sid}.md").exists():
                issues.append(f"Missing story file: docs/stories/{sid}.md")

    if not spec.get("architecture", {}).get("components"):
        issues.append("No architecture components in spec.json")

    if not spec.get("architecture", {}).get("decisions"):
        issues.append("No architecture decisions in spec.json")

    return issues


# -------------------------------------------------------
# Execution preview
# -------------------------------------------------------

def _print_execution_preview(spec: dict[str, Any], project_dir: Path) -> None:
    """Print a human-readable preview of what the ralph loop will do."""
    stories = spec.get("stories", [])
    signals = _get_decision_signals(spec)
    capabilities = spec.get("capabilities", [])

    # Read execution plan if available
    plan_path = project_dir / ".openclaw" / "execution-plan.json"
    plan = None
    if plan_path.exists():
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    print("Execution Preview")
    print("=" * 50)
    print("")

    if plan:
        phase_order = plan.get("phase_order", [])
        for phase_info in phase_order:
            phase = phase_info.get("phase", "?")
            desc = phase_info.get("description", "")
            count = phase_info.get("count", 0)
            if count > 0:
                print(f"  {phase} ({count} stories) — {desc}")

        print("")
        print("Story order:")
        print("")
        for story in plan.get("stories", []):
            order = story.get("order", "?")
            sid = story.get("id", "?")
            title = story.get("title", "?")
            phase = story.get("phase", "?")
            print(f"  {order:>2}. [{phase}] {sid} — {title}")

        parallel = plan.get("parallel_execution", {})
        if parallel:
            print("")
            print("Parallel loops:")
            print(f"  Strategy: {parallel.get('strategy', 'n/a')}")
            for track_info in parallel.get("tracks", []):
                label = track_info.get("label", track_info.get("track", "?"))
                count = track_info.get("count", 0)
                plan_file = track_info.get("plan_file", "")
                print(f"  - {label}: {count} slices ({plan_file})")
    else:
        print("  (no execution plan found)")

    print("")
    print(f"Capabilities: {', '.join(capabilities) if capabilities else 'none'}")
    print(f"App shape: {signals.get('app_shape', 'unknown')}")
    print(f"Audience: {signals.get('primary_audience', 'unknown')}")
    print("")


# -------------------------------------------------------
# Main flow
# -------------------------------------------------------

def run_prepare_project(path: str) -> int:
    project_dir = Path(path).resolve()

    if not project_dir.exists():
        print(f"\nError: Directory not found: {project_dir}\n")
        return 1

    try:
        spec = _load_spec(project_dir)
    except ValueError as exc:
        print(f"\nError: {exc}\n")
        return 1

    project_name = spec.get("answers", {}).get("project_name", "unknown")
    print("")
    print(f"Preparing: {project_name}")
    print(f"Location:  {project_dir}")
    print("")

    # --- Validate package ---
    print("Validating package...")
    issues = _validate_package(project_dir, spec)
    if issues:
        print("  Issues found:")
        for issue in issues:
            print(f"    - {issue}")
        print("")
    else:
        print("  Package is complete.")
        print("")

    # --- Rewrite .codex/AGENTS.md ---
    print("Writing consolidated .codex/AGENTS.md...")
    codex_dir = project_dir / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    agents_content = _build_consolidated_agents_md(spec)
    (codex_dir / "AGENTS.md").write_text(agents_content, encoding="utf-8")

    # --- Rewrite PRD.md ---
    print("Writing consolidated PRD.md...")
    prd_content = _build_consolidated_prd(spec)
    (project_dir / "PRD.md").write_text(prd_content, encoding="utf-8")

    # --- BUG-040: re-generate stories so latest story_engine fixes
    # (expected_files + execution metadata) apply even to old specs.
    # Clear stale expected_files and execution so _merge_story() accepts
    # the freshly generated values from the current story_engine. ---
    for story in spec.get("stories", []):
        if isinstance(story, dict):
            story.pop("expected_files", None)
            story.pop("execution", None)
    spec["stories"] = generate_stories(spec)

    # --- Regenerate openclaw bundle (with latest spec) ---
    print("Regenerating .openclaw/ bundle...")
    write_openclaw_bundle(project_dir, spec)

    # --- Detect commands from actual project files ---
    print("Detecting validation commands...")
    commands_data = _detect_commands(project_dir, spec)
    openclaw_dir = project_dir / ".openclaw"
    openclaw_dir.mkdir(parents=True, exist_ok=True)
    (openclaw_dir / "commands.json").write_text(
        json.dumps(commands_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    for cmd_name, cmd_value in commands_data.get("commands", {}).items():
        if cmd_value:
            print(f"  {cmd_name}: {cmd_value}")
        else:
            print(f"  {cmd_name}: (not detected)")

    print("")

    # --- Regenerate codex ralph.sh ---
    print("Regenerating ralph.sh...")
    write_codex_bundle(project_dir, spec)

    print("")

    # --- Execution preview ---
    _print_execution_preview(spec, project_dir)

    print("Preparation complete.")
    print("")
    print("Next steps:")
    print(f"  cd {project_dir}")
    print("  ./ralph.sh --dry-run    # preview")
    print("  ./ralph.sh              # execute")
    print("")

    return 0
