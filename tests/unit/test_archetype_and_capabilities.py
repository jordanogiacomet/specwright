from initializer.engine.archetype_engine import detect_archetype
from initializer.engine.capability_derivation import derive_capabilities


def test_editorial_prompt_maps_to_editorial_cms():
    result = detect_archetype(
        "Editorial CMS with admin panel, public website, media library, preview, and scheduled publishing for articles"
    )

    assert result["id"] == "editorial-cms"
    assert result["name"] == "editorial-cms"
    assert result["stack"]["frontend"] == "nextjs"
    assert result["stack"]["backend"] == "payload"
    assert result["stack"]["database"] == "postgres"
    assert "cms" in result["capabilities"]
    assert "authentication" in result["features"]
    assert "roles" in result["features"]
    assert "media-library" in result["features"]
    assert "preview" in result["features"]
    assert "scheduled-publishing" in result["features"]


def test_public_surface_derives_public_site_capability():
    capabilities = derive_capabilities(
        archetype="editorial-cms",
        archetype_data={"id": "editorial-cms", "capabilities": ["cms"]},
        answers={"surface": "admin_plus_public_site"},
        existing_capabilities=[],
    )

    assert capabilities == ["cms", "public-site"]


def test_internal_admin_only_does_not_add_public_site():
    capabilities = derive_capabilities(
        archetype="editorial-cms",
        archetype_data={"id": "editorial-cms", "capabilities": ["cms"]},
        answers={"surface": "internal_admin_only"},
        existing_capabilities=[],
    )

    assert capabilities == ["cms"]