"""Story coverage validation.

Checks whether generated stories cover the active capabilities in the spec.
"""

from typing import Any


CAPABILITY_COVERAGE_RULES = {
    "cms": {
        "story_keys": {
            "feature.media-library",
            "feature.preview",
            "feature.scheduled-publishing",
        },
        "title_keywords": {
            "cms content model",
            "cms content management",
            "media library",
            "content preview",
            "scheduled publishing",
            "publish",
            "preview",
            "define cms",
        },
        "description_keywords": {
            "collections",
            "editorial",
            "media assets",
            "unpublished content",
            "content models",
            "content management",
            "cms collections",
        },
    },
    "public-site": {
        "story_keys": {
            "product.public-site",
        },
        "title_keywords": {
            "configure cdn",
            "public site",
            "landing page",
            "marketing site",
            "seo",
        },
        "description_keywords": {
            "public site",
            "public-facing",
            "cdn",
            "seo-sensitive",
        },
    },
    "scheduled-jobs": {
        "story_keys": {
            "product.automation-jobs",
            "feature.scheduled-publishing",
        },
        "title_keywords": {
            "setup job worker",
            "implement scheduled automation",
            "implement workflow automation jobs",
            "implement background automation jobs",
            "implement scheduled publishing",
            "scheduler",
            "background jobs",
        },
        "description_keywords": {
            "scheduled jobs",
            "automation jobs",
            "scheduled workflows",
            "background worker",
            "publish content at scheduled time",
            "background jobs",
            "automation workflows",
        },
    },
    "i18n": {
        "story_keys": {
            "product.i18n",
        },
        "title_keywords": {
            "add application locale support",
            "implement locale selection",
            "add locale support",
            "implement locale routing",
            "localization",
            "i18n",
        },
        "description_keywords": {
            "translation resources",
            "locale-aware",
            "multiple languages",
            "internationalization",
            "locale selection",
            "fallback rules",
        },
    },
}


def _normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _story_matches_rule(story: dict[str, Any], rule: dict[str, set[str]]) -> bool:
    story_key = _normalize_text(story.get("story_key"))
    title = _normalize_text(story.get("title"))
    description = _normalize_text(story.get("description"))

    if story_key and story_key in rule.get("story_keys", set()):
        return True

    for keyword in rule.get("title_keywords", set()):
        if keyword in title:
            return True

    for keyword in rule.get("description_keywords", set()):
        if keyword in description:
            return True

    return False


def check_story_coverage(spec: dict[str, Any]) -> list[str]:
    capabilities = spec.get("capabilities", [])
    stories = spec.get("stories", [])

    if not isinstance(capabilities, list) or not isinstance(stories, list):
        return []

    missing: list[str] = []

    for capability in capabilities:
        if not isinstance(capability, str):
            continue

        rule = CAPABILITY_COVERAGE_RULES.get(capability)
        if not rule:
            continue

        covered = any(
            isinstance(story, dict) and _story_matches_rule(story, rule)
            for story in stories
        )

        if not covered:
            missing.append(capability)

    return missing