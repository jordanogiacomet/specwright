"""Tests for i18n capability handler."""

from initializer.capabilities.i18n import apply_i18n


def _make_spec(needs_cms=False, capabilities=None):
    return {
        "stack": {"frontend": "nextjs", "backend": "payload" if needs_cms else "node-api", "database": "postgres"},
        "capabilities": capabilities or [],
        "discovery": {
            "decision_signals": {
                "needs_i18n": True,
                "needs_cms": needs_cms,
            }
        },
        "answers": {
            "guided_answers": {
                "content_model": {
                    "collections": [
                        {"name": "pages", "purpose": "Pages"},
                        {"name": "posts", "purpose": "Posts"},
                    ],
                    "globals": [
                        {"name": "site-settings", "purpose": "Settings"},
                    ],
                }
            }
        },
    }


def test_cms_i18n_stories_have_story_keys():
    spec = _make_spec(needs_cms=True, capabilities=["cms", "public-site"])
    arch = {"decisions": [], "components": []}
    _, stories = apply_i18n(spec, arch, [])

    keys = [story.get("story_key") for story in stories]
    assert "feature.cms-localization" in keys
    assert "feature.locale-routing" in keys


def test_cms_locale_routing_depends_on_public_rendering():
    spec = _make_spec(needs_cms=True, capabilities=["cms", "public-site"])
    arch = {"decisions": [], "components": []}
    _, stories = apply_i18n(spec, arch, [])

    routing = next(story for story in stories if story.get("story_key") == "feature.locale-routing")
    assert "product.public-site-rendering" in routing["depends_on"]
    assert any("[locale]" in path for path in routing["expected_files"])


def test_non_cms_i18n_stories_have_story_keys():
    spec = _make_spec(needs_cms=False, capabilities=["i18n"])
    arch = {"decisions": [], "components": []}
    _, stories = apply_i18n(spec, arch, [])

    keys = [story.get("story_key") for story in stories]
    assert "feature.localized-ui" in keys
    assert "feature.locale-selection" in keys
