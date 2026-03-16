"""
i18n capability handler.

Adds locale-related decisions and locale support/routing stories
with acceptance criteria, scope boundaries, and validation.
"""


def _story_exists(stories, title):
    return any(story.get("title") == title for story in stories)


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _add_unique_decision(architecture, decision):
    decisions = architecture.setdefault("decisions", [])
    if decision not in decisions:
        decisions.append(decision)


def apply_i18n(spec, architecture, stories):
    signals = _get_decision_signals(spec)

    needs_i18n = signals.get("needs_i18n")
    needs_cms = signals.get("needs_cms")
    primary_audience = signals.get("primary_audience")

    if needs_i18n is False:
        return architecture, stories

    if needs_cms is True:
        _add_unique_decision(
            architecture,
            "Content models must support locale-aware fields and fallback rules.",
        )

        if not _story_exists(stories, "Add locale support"):
            stories.append({
                "id": f"ST-{len(stories)+1:03}",
                "title": "Add locale support",
                "description": "Add locale fields and fallback rules to content models.",
                "acceptance_criteria": [
                    "Content collections support locale-specific fields",
                    "Fallback rules are defined for missing translations",
                    "Admin interface allows editing content per locale",
                    "API responses include locale metadata",
                ],
                "scope_boundaries": [
                    "Do NOT implement locale routing in this story — that is separate",
                    "Do NOT implement machine translation",
                ],
                "expected_files": [
                    "src/lib/i18n.ts",
                ],
                "depends_on": ["bootstrap.backend"],
                "validation": {
                    "commands": ["npm run build"],
                    "manual_check": "Can create content in multiple locales via admin",
                },
            })

        if not _story_exists(stories, "Implement locale routing"):
            stories.append({
                "id": f"ST-{len(stories)+1:03}",
                "title": "Implement locale routing",
                "description": "Add locale-aware routing in the frontend experience.",
                "acceptance_criteria": [
                    "URLs include locale prefix (e.g., /en/..., /pt/...)",
                    "Correct locale content is rendered per route",
                    "Default locale is used when no prefix is provided",
                    "Locale can be switched without losing page context",
                ],
                "scope_boundaries": [
                    "Do NOT implement locale detection from browser headers",
                    "Do NOT implement per-user locale preferences",
                ],
                "expected_files": [
                    "src/app/[locale]/layout.tsx",
                    "src/lib/i18n.ts (updated with routing helpers)",
                ],
                "depends_on": ["bootstrap.frontend"],
                "validation": {
                    "commands": ["npm run build"],
                    "manual_check": "Can navigate /en/ and /pt/ and see different content",
                },
            })

        return architecture, stories

    # Non-CMS i18n
    _add_unique_decision(
        architecture,
        "Application UI and APIs must support locale-aware text, formatting, and translation resources.",
    )

    if primary_audience == "internal_teams":
        description = "Add translation resources and locale-aware formatting to the internal application UI."
    else:
        description = "Add translation resources and locale-aware formatting across the application experience."

    if not _story_exists(stories, "Add application locale support"):
        stories.append({
            "id": f"ST-{len(stories)+1:03}",
            "title": "Add application locale support",
            "description": description,
            "acceptance_criteria": [
                "Translation files exist for at least two locales",
                "UI text is loaded from translation resources, not hardcoded",
                "Date, number, and currency formatting respects active locale",
            ],
            "scope_boundaries": [
                "Do NOT implement locale routing — that is a separate story",
                "Do NOT implement machine translation or auto-detection",
            ],
            "expected_files": [
                "src/lib/i18n.ts",
                "src/locales/en.json",
                "src/locales/pt.json",
            ],
            "depends_on": ["bootstrap.frontend"],
            "validation": {
                "commands": ["npm run build"],
                "manual_check": "UI renders text from translation files",
            },
        })

    if not _story_exists(stories, "Implement locale selection"):
        stories.append({
            "id": f"ST-{len(stories)+1:03}",
            "title": "Implement locale selection",
            "description": "Allow users to choose locale and ensure locale-aware rendering and formatting.",
            "acceptance_criteria": [
                "Locale switcher is visible and accessible in the UI",
                "Changing locale updates all visible text and formatting",
                "Selected locale persists across page navigation",
            ],
            "scope_boundaries": [
                "Do NOT implement per-user locale persistence in the database",
            ],
            "expected_files": [
                "src/components/LocaleSwitcher.tsx",
            ],
            "depends_on": ["bootstrap.frontend"],
            "validation": {
                "commands": ["npm run build"],
                "manual_check": "Can switch locale and see UI update",
            },
        })

    return architecture, stories