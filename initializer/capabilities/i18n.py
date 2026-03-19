"""
i18n capability handler.

Adds locale-related decisions and locale support/routing stories
with acceptance criteria, scope boundaries, and validation.
"""

from initializer.engine.validation_contract import migration_commands


def _story_exists(stories, story_key=None, title=None):
    for story in stories:
        if story_key and story.get("story_key") == story_key:
            return True
        if title and story.get("title") == title:
            return True
    return False


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


def _guided_answers(spec):
    answers = spec.get("answers", {})
    ga = answers.get("guided_answers", {})
    return ga if isinstance(ga, dict) else {}


def _get_content_model(spec):
    return _guided_answers(spec).get("content_model", {})


def _public_collection_names(spec):
    content_model = _get_content_model(spec)
    collections = content_model.get("collections", [])
    if not isinstance(collections, list):
        collections = []

    names = [
        item.get("name", "").strip().lower()
        for item in collections
        if isinstance(item, dict) and item.get("name")
    ]
    names = [name for name in names if name not in {"media", "authors", "users"}]
    return names or ["pages", "posts"]


def _global_names(spec):
    content_model = _get_content_model(spec)
    globals_list = content_model.get("globals", [])
    if not isinstance(globals_list, list):
        globals_list = []
    return [
        item.get("name", "").strip().lower()
        for item in globals_list
        if isinstance(item, dict) and item.get("name")
    ]


def _pascal_case(value):
    return "".join(part.capitalize() for part in value.replace("_", "-").split("-") if part)


def apply_i18n(spec, architecture, stories):
    signals = _get_decision_signals(spec)
    migration_cmds = migration_commands(spec)

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

        public_collections = _public_collection_names(spec)
        globals_list = _global_names(spec)

        localized_files = ["src/lib/i18n.ts"]
        for name in public_collections:
            localized_files.append(f"src/collections/{_pascal_case(name)}.ts")
        for name in globals_list:
            localized_files.append(f"src/globals/{_pascal_case(name)}.ts")

        if not _story_exists(
            stories,
            story_key="feature.cms-localization",
            title="Enable localized CMS content",
        ):
            stories.append({
                "id": f"ST-{len(stories)+1:03}",
                "story_key": "feature.cms-localization",
                "title": "Enable localized CMS content",
                "description": "Add locale-aware fields and fallback behavior to CMS collections and globals used by editorial and public surfaces.",
                "acceptance_criteria": [
                    f"Public-facing collections ({', '.join(public_collections)}) support locale-specific content for at least two locales",
                    (
                        f"Shared globals ({', '.join(globals_list)}) expose locale-aware values"
                        if globals_list
                        else "Shared CMS globals used by the public surface expose locale-aware values"
                    ),
                    "Fallback rules are defined when a requested locale is missing",
                    "Admin editing UI allows switching locale while editing the same entry",
                    "Content loaders/API responses accept locale and include locale metadata",
                    "Database migration is generated and executed for locale field changes "
                    f"(run `{migration_cmds['create']}` then `{migration_cmds['run']}`)",
                ],
                "scope_boundaries": [
                    "Do NOT implement locale-prefixed routing in this story — that is separate",
                    "Do NOT implement machine translation",
                    "Do NOT add new collections/globals just to support localization",
                ],
                "expected_files": localized_files,
                "depends_on": ["product.cms-content-model"],
                "validation": {
                    "commands": ["npm run build"],
                    "manual_check": "Admin can edit the same page/post in two locales and retrieve locale-specific content with fallback behavior.",
                },
            })

        route_files = [
            "src/middleware.ts",
            "src/app/[locale]/layout.tsx",
            "src/components/LocaleSwitcher.tsx",
            "src/lib/i18n.ts (updated with routing helpers)",
        ]
        for name in public_collections:
            route_files.append(f"src/app/[locale]/(public)/{name}/[slug]/page.tsx")

        route_depends = ["feature.cms-localization"]
        if "public-site" in spec.get("capabilities", []):
            route_depends.append("product.public-site-rendering")
        else:
            route_depends.append("bootstrap.frontend")

        if not _story_exists(
            stories,
            story_key="feature.locale-routing",
            title="Implement locale-aware routing",
        ):
            stories.append({
                "id": f"ST-{len(stories)+1:03}",
                "story_key": "feature.locale-routing",
                "title": "Implement locale-aware routing",
                "description": "Add locale-prefixed public routing that resolves localized CMS content without duplicating route ownership.",
                "acceptance_criteria": [
                    "URLs include locale prefix (e.g., /en/..., /pt/...)",
                    f"Localized routes exist for {', '.join(public_collections)} and resolve the matching localized content by slug",
                    "Default locale redirect exists when no prefix is provided",
                    "Locale can be switched without losing page context or slug",
                    "Fallback-to-default-locale or 404 behavior is explicit when a translation is missing",
                ],
                "scope_boundaries": [
                    "Do NOT implement locale detection from browser headers",
                    "Do NOT implement per-user locale preferences",
                    "Do NOT leave duplicate non-localized public routes alongside the localized route tree",
                ],
                "expected_files": route_files,
                "depends_on": route_depends,
                "validation": {
                    "commands": ["npm run build"],
                    "manual_check": "Can navigate localized public routes, switch locale, and verify the same slug resolves localized content or fallback behavior.",
                },
            })

        return architecture, stories

    _add_unique_decision(
        architecture,
        "Application UI and APIs must support locale-aware text, formatting, and translation resources.",
    )

    if primary_audience == "internal_teams":
        description = "Add translation resources and locale-aware formatting to the internal application UI."
    else:
        description = "Add translation resources and locale-aware formatting across the application experience."

    if not _story_exists(
        stories,
        story_key="feature.localized-ui",
        title="Add application locale support",
    ):
        stories.append({
            "id": f"ST-{len(stories)+1:03}",
            "story_key": "feature.localized-ui",
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

    if not _story_exists(
        stories,
        story_key="feature.locale-selection",
        title="Implement locale selection",
    ):
        stories.append({
            "id": f"ST-{len(stories)+1:03}",
            "story_key": "feature.locale-selection",
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
