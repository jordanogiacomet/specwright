"""
Public site capability handler.

Adds CDN component, public delivery decisions, and a CDN configuration story
with acceptance criteria, scope boundaries, and validation.
"""


def _add_unique_component(architecture, component):
    components = architecture.setdefault("components", [])
    name = component.get("name")

    if name:
        for existing in components:
            if existing.get("name") == name:
                return

    components.append(dict(component))


def _add_unique_decision(architecture, decision):
    decisions = architecture.setdefault("decisions", [])
    if decision not in decisions:
        decisions.append(decision)


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def apply_public_site(spec, architecture, stories):
    signals = _get_decision_signals(spec)

    needs_public_site = signals.get("needs_public_site")
    primary_audience = signals.get("primary_audience")

    if needs_public_site is False:
        return architecture, stories

    if primary_audience == "internal_teams" and needs_public_site is not True:
        return architecture, stories

    _add_unique_component(
        architecture,
        {
            "name": "cdn",
            "technology": "cdn",
            "role": "public asset delivery",
        },
    )

    _add_unique_decision(
        architecture,
        "Public assets should be delivered through a CDN.",
    )

    _add_unique_decision(
        architecture,
        "Use SSR or ISR for SEO-sensitive public pages when applicable.",
    )

    # Check if story already exists
    for story in stories:
        if story.get("title") == "Configure CDN":
            return architecture, stories

    stories.append(
        {
            "id": f"ST-{len(stories)+1:03}",
            "title": "Configure CDN",
            "description": "Configure CDN for public site asset delivery.",
            "acceptance_criteria": [
                "Public assets are served through a CDN or edge cache",
                "Cache headers are configured for static assets",
                "Public routes are accessible without authentication",
                "CDN configuration does not break authenticated admin routes",
            ],
            "scope_boundaries": [
                "Do NOT implement the full public site layout — only the delivery infrastructure",
                "Do NOT implement SEO optimizations in this story",
            ],
            "expected_files": [
                "next.config.ts (updated with caching/CDN headers if applicable)",
            ],
            "depends_on": ["bootstrap.frontend"],
            "validation": {
                "commands": ["npm run build"],
                "manual_check": "Public route loads and static assets have appropriate cache headers",
            },
        }
    )

    return architecture, stories