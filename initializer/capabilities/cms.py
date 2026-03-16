"""
CMS capability handler.

Adds CMS-specific architecture decisions and a content model story
with acceptance criteria, scope boundaries, and validation.
"""


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

    acceptance_criteria = [
        "Content collections are defined with required fields and validation",
        "Content items can be created, read, updated, and deleted via the admin",
        "Media handling is configured for image and file uploads",
        "Database migration is generated and executed for all schema changes (run migrate:create then migrate)",
    ]

    expected_files = []

    if is_payload:
        acceptance_criteria.append("Payload collections are registered in payload.config.ts")
        expected_files.append("src/payload.config.ts (updated with collections)")
        expected_files.append("src/collections/Articles.ts or equivalent")
    else:
        acceptance_criteria.append("Content API endpoints are created and respond correctly")
        expected_files.append("src/api/content.ts or equivalent")
        expected_files.append("src/models/Article.ts or equivalent")

    stories.append(
        {
            "id": f"ST-{len(stories)+1:03}",
            "title": "Define CMS content model",
            "description": "Define CMS collections, media handling, and editorial workflows.",
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