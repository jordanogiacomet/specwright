"""Enrich Project Flow.

Post-generation step that enriches a generated project package with:
- PRD intelligence (problem statement, personas, success metrics, scope, assumptions)
- Architecture review suggestions
- Enriched PRD.md that incorporates intelligence

This is designed to run AFTER `initializer new` and BEFORE the
execution loop (OpenClaw/Ralph/Codex/Claude).

Usage:
    initializer enrich output/my-project
    initializer enrich output/my-project --review   # also run AI architecture review
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from initializer.engine.prd_intelligence_engine import generate_prd_intelligence
from initializer.ai.architecture_review import review_architecture


def _load_spec(project_dir: Path) -> dict[str, Any]:
    spec_path = project_dir / "spec.json"
    if not spec_path.exists():
        raise ValueError(f"spec.json not found in {project_dir}")

    data = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"spec.json must contain a JSON object: {spec_path}")

    return data


def _save_spec(project_dir: Path, spec: dict[str, Any]) -> None:
    spec_path = project_dir / "spec.json"
    spec_path.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_enriched_prd(project_dir: Path, spec: dict[str, Any]) -> None:
    """Write an enriched PRD.md that includes intelligence sections."""
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    architecture = spec.get("architecture", {})
    intelligence = spec.get("prd_intelligence", {})
    discovery = spec.get("discovery", {})

    project_name = answers.get("project_name", "Unnamed Project")
    summary = answers.get("summary", "")

    lines: list[str] = []

    lines.append(f"# {project_name}")
    lines.append("")

    # --- Problem Statement ---
    problem = intelligence.get("problem_statement", "")
    if problem:
        lines.append("## Problem Statement")
        lines.append("")
        lines.append(problem)
        lines.append("")

    # --- Summary ---
    lines.append("## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")

    # --- Personas ---
    personas = intelligence.get("personas", [])
    if personas:
        lines.append("## Personas")
        lines.append("")
        for persona in personas:
            name = persona.get("name", "Unknown")
            goal = persona.get("goal", "")
            lines.append(f"- **{name}**: {goal}")
        lines.append("")

    # --- Success Metrics ---
    metrics = intelligence.get("success_metrics", [])
    if metrics:
        lines.append("## Success Metrics")
        lines.append("")
        for metric in metrics:
            lines.append(f"- {metric}")
        lines.append("")

    # --- Scope ---
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

    # --- Assumptions ---
    assumptions = intelligence.get("assumptions", [])
    if assumptions:
        lines.append("## Assumptions")
        lines.append("")
        for assumption in assumptions:
            lines.append(f"- {assumption}")
        lines.append("")

    # --- Stack ---
    lines.append("## Stack")
    lines.append("")
    lines.append(f"- Frontend: {stack.get('frontend', 'unknown')}")
    lines.append(f"- Backend: {stack.get('backend', 'unknown')}")
    lines.append(f"- Database: {stack.get('database', 'unknown')}")
    lines.append("")

    # --- Features ---
    lines.append("## Features")
    lines.append("")
    for feature in features:
        lines.append(f"- {feature}")
    lines.append("")

    # --- Capabilities ---
    if capabilities:
        lines.append("## Capabilities")
        lines.append("")
        for capability in capabilities:
            lines.append(f"- {capability}")
        lines.append("")

    # --- Architecture Decisions ---
    decisions = architecture.get("decisions", [])
    if decisions:
        lines.append("## Architecture Decisions")
        lines.append("")
        for decision in decisions:
            lines.append(f"- {decision}")
        lines.append("")

    # --- Architecture Review ---
    review = spec.get("architecture_review", [])
    if review:
        lines.append("## Architecture Review Suggestions")
        lines.append("")
        for suggestion in review:
            lines.append(f"- {suggestion}")
        lines.append("")

    # --- Discovery Signals ---
    signals = discovery.get("decision_signals", {})
    if signals:
        lines.append("## Discovery Signals")
        lines.append("")
        for key, value in signals.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")

    conflicts = discovery.get("conflicts", [])
    if conflicts:
        lines.append("## Conflicts")
        lines.append("")
        for conflict in conflicts:
            lines.append(f"- {conflict}")
        lines.append("")

    prd_path = project_dir / "PRD.md"
    prd_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_intelligence_json(project_dir: Path, intelligence: dict[str, Any]) -> None:
    """Write prd_intelligence as a standalone JSON for agents to consume."""
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    path = docs_dir / "prd-intelligence.json"
    path.write_text(
        json.dumps(intelligence, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_review_json(project_dir: Path, suggestions: list[str]) -> None:
    """Write architecture review as a standalone JSON."""
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    path = docs_dir / "architecture-review.json"
    path.write_text(
        json.dumps({"suggestions": suggestions}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_enrich_project(path: str, *, review: bool = False) -> int:
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
    print()
    print(f"Enriching: {project_name}")
    print(f"Location:  {project_dir}")
    print()

    # --- PRD Intelligence ---
    print("Generating PRD intelligence...")
    intelligence = generate_prd_intelligence(spec)
    spec["prd_intelligence"] = intelligence
    _write_intelligence_json(project_dir, intelligence)
    print(f"  Problem statement: {intelligence.get('problem_statement', '')[:80]}...")
    print(f"  Personas: {len(intelligence.get('personas', []))}")
    print(f"  Success metrics: {len(intelligence.get('success_metrics', []))}")
    print()

    # --- Architecture Review ---
    suggestions: list[str] = []
    if review:
        print("Running architecture review...")
        suggestions = review_architecture(spec)
        spec["architecture_review"] = suggestions
        _write_review_json(project_dir, suggestions)
        print(f"  Suggestions: {len(suggestions)}")
        print()
    else:
        print("Skipping architecture review (use --review to enable)")
        print()

    # --- Save enriched spec ---
    _save_spec(project_dir, spec)
    print("Updated spec.json with intelligence data.")

    # --- Rewrite enriched PRD ---
    _write_enriched_prd(project_dir, spec)
    print("Rewrote PRD.md with enriched content.")

    print()
    print("Enrichment complete.")
    print()
    print("Artifacts updated:")
    print("  - spec.json (added prd_intelligence)")
    print("  - PRD.md (enriched with intelligence)")
    print("  - docs/prd-intelligence.json")
    if review:
        print("  - docs/architecture-review.json")
    print()

    return 0