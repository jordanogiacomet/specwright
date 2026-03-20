"""Stories Renderer.

Writes individual story markdown files to docs/stories/.

Each story file now includes:
- Acceptance criteria
- Scope boundaries (what NOT to do)
- Expected files to create/modify
- Dependencies on other stories
- Validation commands and manual checks
"""

from pathlib import Path


def _render_story(story):
    """Render a single story dict to a markdown string."""
    story_id = story.get("id", "???")
    title = story.get("title", "Untitled")
    description = story.get("description", "")
    acceptance_criteria = story.get("acceptance_criteria", [])
    scope_boundaries = story.get("scope_boundaries", [])
    expected_files = story.get("expected_files", [])
    depends_on = story.get("depends_on", [])
    validation = story.get("validation", {})
    story_key = story.get("story_key", "")
    execution = story.get("execution", {})

    lines = []

    # --- Header ---
    lines.append(f"# {story_id} — {title}")
    lines.append("")

    if story_key:
        lines.append(f"**Story key:** `{story_key}`")
        lines.append("")

    if execution:
        tracks = execution.get("tracks", [])
        contract_domains = execution.get("contract_domains", [])

        if tracks:
            lines.append("**Execution tracks:** " + ", ".join(f"`{track}`" for track in tracks))
            lines.append("")

        if contract_domains:
            lines.append("**Contract domains:** " + ", ".join(f"`{domain}`" for domain in contract_domains))
            lines.append("")

    # --- Description ---
    lines.append("## Description")
    lines.append("")
    lines.append(description)
    lines.append("")

    # --- Acceptance Criteria ---
    if acceptance_criteria:
        lines.append("## Acceptance Criteria")
        lines.append("")
        for criterion in acceptance_criteria:
            lines.append(f"- [ ] {criterion}")
        lines.append("")

    # --- Scope Boundaries ---
    if scope_boundaries:
        lines.append("## Scope Boundaries")
        lines.append("")
        for boundary in scope_boundaries:
            lines.append(f"- {boundary}")
        lines.append("")

    # --- Expected Files ---
    if expected_files:
        lines.append("## Expected Files")
        lines.append("")
        for filepath in expected_files:
            lines.append(f"- `{filepath}`")
        lines.append("")

    # --- Dependencies ---
    if depends_on:
        lines.append("## Dependencies")
        lines.append("")
        for dep in depends_on:
            lines.append(f"- `{dep}`")
        lines.append("")

    # --- Validation ---
    if validation:
        commands = validation.get("commands", [])
        manual_check = validation.get("manual_check")

        if commands or manual_check:
            lines.append("## Validation")
            lines.append("")

            if commands:
                for cmd in commands:
                    lines.append(f"- Run: `{cmd}`")

            if manual_check:
                lines.append(f"- Manual: {manual_check}")

            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_stories(project_dir, stories):
    """Write individual story files to docs/stories/.

    Args:
        project_dir: Root output directory for the generated project.
        stories: List of story dicts from spec["stories"].
    """
    stories_dir = Path(project_dir) / "docs/stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    for story in stories:
        if not isinstance(story, dict):
            continue

        story_id = story.get("id")
        if not story_id:
            continue

        content = _render_story(story)
        path = stories_dir / f"{story_id}.md"
        path.write_text(content, encoding="utf-8")
