"""
AI Refine Engine

Improves generated spec using heuristics now
and AI later.

Key change: CDN recommendation is only added when
public-site is in the reconciled capabilities list.
"""


def _has_public_site(spec):
    """Check if public-site is in the reconciled capabilities list."""
    capabilities = spec.get("capabilities", [])
    return "public-site" in capabilities


def refine_prd(spec):

    architecture = spec.get("architecture", {})
    decisions = architecture.get("decisions", [])

    improvements = []

    # CDN is only relevant for public-facing sites
    if _has_public_site(spec):
        if "CDN recommended for public assets." not in decisions:
            improvements.append("CDN recommended for public assets.")

    if "Add monitoring and logging stack." not in decisions:
        improvements.append("Add monitoring and logging stack.")

    if "Add automated database backups." not in decisions:
        improvements.append("Add automated database backups.")

    decisions.extend(improvements)

    spec["architecture"]["decisions"] = decisions

    return spec


def refine_stories(spec):

    stories = spec.get("stories", [])

    ids = [s["id"] for s in stories]

    if "ST-900" not in ids:
        stories.append(
            {
                "id": "ST-900",
                "title": "Setup monitoring and logging",
                "description": "Integrate monitoring, logging and error tracking."
            }
        )

    if "ST-901" not in ids:
        stories.append(
            {
                "id": "ST-901",
                "title": "Implement backups",
                "description": "Automate database backups and retention policies."
            }
        )

    spec["stories"] = stories

    return spec


def refine_spec(spec):

    spec = refine_prd(spec)
    spec = refine_stories(spec)

    return spec