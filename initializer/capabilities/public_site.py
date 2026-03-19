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
        title = story.get("title", "")
        if title in ("Configure CDN", "Configure static asset delivery"):
            return architecture, stories

    stories.append(
        {
            "id": f"ST-{len(stories)+1:03}",
            "title": "Configure static asset delivery",
            "story_key": "infra.static-delivery",
            "description": "Configure Next.js static asset optimization, cache headers, and Image component for public site delivery.",
            "acceptance_criteria": [
                "next.config.ts configures image domains/remotePatterns for external images if applicable",
                "Static assets (JS, CSS, fonts) have appropriate Cache-Control headers via Next.js output config",
                "Next.js Image component is used for optimized image delivery in at least one component",
                "Public routes are accessible without authentication",
                "Admin routes remain unaffected by caching configuration",
            ],
            "scope_boundaries": [
                "Do NOT implement an external CDN provider (Cloudflare, CloudFront, etc.) — use Next.js built-in optimization only",
                "Do NOT implement the full public site layout — only the delivery infrastructure",
                "Do NOT implement SEO meta tags in this story",
            ],
            "expected_files": [
                "next.config.ts (updated with images and headers config)",
            ],
            "depends_on": ["bootstrap.frontend"],
            "validation": {
                "commands": ["npm run build"],
                "manual_check": "Static assets have cache headers; Next.js Image component renders optimized images",
            },
        }
    )

    return architecture, stories