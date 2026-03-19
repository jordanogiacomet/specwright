"""Tests for CMS capability handler enrichment.

Validates that when guided_answers includes content_model,
the CMS story enumerates collections and globals explicitly.
"""

from initializer.capabilities.cms import apply_cms


def _make_spec(backend="payload", collections=None, globals_list=None):
    content_model = {}
    if collections is not None:
        content_model["collections"] = collections
    if globals_list is not None:
        content_model["globals"] = globals_list
    return {
        "stack": {"frontend": "nextjs", "backend": backend, "database": "postgres"},
        "answers": {
            "guided_answers": {
                "content_model": content_model,
            }
        },
    }


def test_cms_enumerates_collections_from_spec():
    spec = _make_spec(
        collections=[
            {"name": "pages", "purpose": "Landing pages"},
            {"name": "posts", "purpose": "News articles"},
            {"name": "authors", "purpose": "Author profiles"},
        ],
    )
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    cms_story = stories[0]
    criteria = " ".join(cms_story["acceptance_criteria"])
    assert "pages" in criteria
    assert "posts" in criteria
    assert "authors" in criteria
    assert "Landing pages" in criteria


def test_cms_enumerates_globals_from_spec():
    spec = _make_spec(
        collections=[{"name": "posts", "purpose": "Articles"}],
        globals_list=[
            {"name": "site-settings", "purpose": "Navigation and SEO defaults"},
            {"name": "homepage", "purpose": "Featured editorial slots"},
        ],
    )
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    cms_story = stories[0]
    criteria = " ".join(cms_story["acceptance_criteria"])
    assert "site-settings" in criteria
    assert "homepage" in criteria


def test_cms_expected_files_per_collection():
    spec = _make_spec(
        collections=[
            {"name": "pages", "purpose": "Pages"},
            {"name": "posts", "purpose": "Posts"},
        ],
    )
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    cms_story = stories[0]
    files = cms_story["expected_files"]
    assert any("Pages" in f for f in files)
    assert any("Posts" in f for f in files)


def test_cms_description_includes_collection_names():
    spec = _make_spec(
        collections=[
            {"name": "pages", "purpose": "Pages"},
            {"name": "posts", "purpose": "Posts"},
        ],
        globals_list=[
            {"name": "site-settings", "purpose": "Settings"},
        ],
    )
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    desc = stories[0]["description"]
    assert "pages" in desc
    assert "posts" in desc
    assert "site-settings" in desc


def test_cms_fallback_without_content_model():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
    }
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    cms_story = stories[0]
    criteria = " ".join(cms_story["acceptance_criteria"])
    assert "Content collections are defined" in criteria
    assert any("Articles" in f for f in cms_story["expected_files"])


def test_cms_node_api_backend_paths():
    spec = _make_spec(
        backend="node-api",
        collections=[
            {"name": "posts", "purpose": "Articles"},
        ],
    )
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    cms_story = stories[0]
    files = cms_story["expected_files"]
    assert any("src/models/" in f for f in files)
    assert not any("src/collections/" in f for f in files)
