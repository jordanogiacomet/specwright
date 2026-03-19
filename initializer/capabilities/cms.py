"""
CMS capability handler.

Adds CMS-specific architecture decisions and a content model story
with acceptance criteria, scope boundaries, and validation.

When the spec includes a content_model (from guided_answers), the story
enumerates every collection and global so Codex knows exactly what to create.
"""


def _get_content_model(spec):
    """Extract content_model from guided_answers if present."""
    answers = spec.get("answers", {})
    ga = answers.get("guided_answers", {})
    return ga.get("content_model", {})


def _collection_criteria(collections, is_payload):
    """Build per-collection acceptance criteria from spec content_model."""
    criteria = []
    for col in collections:
        name = col.get("name", "")
        purpose = col.get("purpose", "")
        if is_payload:
            criteria.append(
                f"Payload collection `{name}` exists — {purpose}"
            )
        else:
            criteria.append(
                f"Collection `{name}` is defined with required fields — {purpose}"
            )
    return criteria


def _global_criteria(globals_list, is_payload):
    """Build per-global acceptance criteria from spec content_model."""
    criteria = []
    for g in globals_list:
        name = g.get("name", "")
        purpose = g.get("purpose", "")
        if is_payload:
            criteria.append(
                f"Payload global `{name}` exists — {purpose}"
            )
        else:
            criteria.append(
                f"Global config `{name}` is defined — {purpose}"
            )
    return criteria


def apply_cms(spec, architecture, stories):
    if "decisions" not in architecture:
        architecture["decisions"] = []

    if "components" not in architecture:
        architecture["components"] = []

    architecture["decisions"].append(
        "CMS content stored in structured collections."
    )

    architecture["decisions"].append(
        "Media assets served via CDN."
    )

    # Check if story already exists
    for story in stories:
        if story.get("title") == "Define CMS content model":
            return architecture, stories

    stack = spec.get("stack", {})
    backend = (stack.get("backend") or "").lower().strip()
    is_payload = backend in ("payload", "payload-cms")

    content_model = _get_content_model(spec)
    collections = content_model.get("collections", [])
    globals_list = content_model.get("globals", [])

    # --- Acceptance criteria ---
    acceptance_criteria = []

    if collections:
        acceptance_criteria.extend(_collection_criteria(collections, is_payload))
    else:
        acceptance_criteria.append(
            "Content collections are defined with required fields and validation"
        )

    if globals_list:
        acceptance_criteria.extend(_global_criteria(globals_list, is_payload))

    acceptance_criteria.append(
        "Content items can be created, read, updated, and deleted via the admin"
    )
    acceptance_criteria.append(
        "Media handling is configured for image and file uploads"
    )
    acceptance_criteria.append(
        "Database migration is generated and executed for all schema changes (run migrate:create then migrate)"
    )

    # --- Expected files ---
    expected_files = []

    if is_payload:
        acceptance_criteria.append("Payload collections are registered in payload.config.ts")
        expected_files.append("src/payload.config.ts (updated with collections)")
        for col in collections:
            name = col.get("name", "")
            cap_name = name.capitalize() if name else "Articles"
            expected_files.append(f"src/collections/{cap_name}.ts")
        if not collections:
            expected_files.append("src/collections/Articles.ts or equivalent")
    else:
        acceptance_criteria.append("Content API endpoints are created and respond correctly")
        expected_files.append("src/api/content.ts or equivalent")
        for col in collections:
            name = col.get("name", "")
            cap_name = name.capitalize() if name else "Article"
            expected_files.append(f"src/models/{cap_name}.ts")
        if not collections:
            expected_files.append("src/models/Article.ts or equivalent")

    # --- Description ---
    if collections or globals_list:
        col_names = [c.get("name", "") for c in collections]
        glob_names = [g.get("name", "") for g in globals_list]
        parts = []
        if col_names:
            parts.append(f"collections: {', '.join(col_names)}")
        if glob_names:
            parts.append(f"globals: {', '.join(glob_names)}")
        description = f"Define CMS content model — {'; '.join(parts)}."
    else:
        description = "Define CMS collections, media handling, and editorial workflows."

    stories.append(
        {
            "id": f"ST-{len(stories)+1:03}",
            "title": "Define CMS content model",
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "scope_boundaries": [
                "Do NOT implement draft/publish workflow — that is a separate story",
                "Do NOT implement media library UI — focus on the content model and API",
                "Do NOT implement public-facing content delivery",
            ],
            "expected_files": expected_files,
            "depends_on": ["bootstrap.backend"],
            "validation": {
                "commands": ["npm run build"],
                "manual_check": "Can create and retrieve a content item via admin or API",
            },
        }
    )

    return architecture, stories