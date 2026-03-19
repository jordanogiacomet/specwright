"""Tests for CMS capability handler enrichment."""

from initializer.capabilities.cms import apply_cms


def _make_spec(
    backend="payload",
    collections=None,
    globals_list=None,
    features=None,
    capabilities=None,
):
    content_model = {}
    if collections is not None:
        content_model["collections"] = collections
    if globals_list is not None:
        content_model["globals"] = globals_list
    return {
        "stack": {"frontend": "nextjs", "backend": backend, "database": "postgres"},
        "features": features or [],
        "capabilities": capabilities or ["cms"],
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
    assert "slug" in criteria


def test_cms_story_has_story_key():
    spec = _make_spec(
        collections=[{"name": "posts", "purpose": "News articles"}],
    )
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    cms_story = stories[0]
    assert cms_story["story_key"] == "product.cms-content-model"
    assert cms_story["depends_on"] == ["bootstrap.backend"]


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
    assert "default_seo" in criteria
    assert "featured_posts" in criteria


def test_cms_expected_files_per_collection_and_global():
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

    cms_story = stories[0]
    files = cms_story["expected_files"]
    assert any("src/collections/Pages.ts" in f for f in files)
    assert any("src/collections/Posts.ts" in f for f in files)
    assert any("src/globals/SiteSettings.ts" in f for f in files)


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
        "features": [],
        "capabilities": ["cms"],
    }
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    cms_story = stories[0]
    criteria = " ".join(cms_story["acceptance_criteria"])
    assert "primary content collection" in criteria
    assert any("Posts" in f for f in cms_story["expected_files"])
    assert any("SiteSettings" in f for f in cms_story["expected_files"])


def test_cms_public_collections_reference_public_routes():
    spec = _make_spec(
        collections=[
            {"name": "pages", "purpose": "Pages"},
            {"name": "posts", "purpose": "Posts"},
            {"name": "authors", "purpose": "Authors"},
        ],
        features=["draft-publish"],
        capabilities=["cms", "public-site"],
    )
    arch = {"decisions": [], "components": []}
    _, stories = apply_cms(spec, arch, [])

    cms_story = stories[0]
    criteria = " ".join(cms_story["acceptance_criteria"])
    assert "/pages/[slug]" in criteria
    assert "/posts/[slug]" in criteria
    assert "/authors/[slug]" not in criteria


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
