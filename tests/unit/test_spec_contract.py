from initializer.flow.new_project import (
    build_initial_spec,
    derive_capabilities_from_answers,
)


def test_build_initial_spec_has_canonical_contract():
    prompt = (
        "Editorial CMS with admin panel, public website, media library, "
        "preview, and scheduled publishing for articles"
    )

    spec = build_initial_spec(prompt)

    assert spec["prompt"] == prompt
    assert spec["archetype"] == "editorial-cms"
    assert spec["archetype_data"]["id"] == spec["archetype"]

    assert isinstance(spec["stack"], dict)
    assert spec["stack"]["frontend"] == "nextjs"
    assert spec["stack"]["backend"] == "payload"
    assert spec["stack"]["database"] == "postgres"

    assert isinstance(spec["features"], list)
    assert "authentication" in spec["features"]
    assert "roles" in spec["features"]
    assert "media-library" in spec["features"]
    assert "preview" in spec["features"]
    assert "scheduled-publishing" in spec["features"]

    assert spec["capabilities"] == ["cms"]
    assert spec["architecture"] == {}
    assert spec["stories"] == []
    assert spec["answers"] == {}


def test_derive_capabilities_from_answers_updates_spec_capabilities():
    spec = build_initial_spec(
        "Editorial CMS with admin panel and public website"
    )

    spec["answers"] = {
        "surface": "admin_plus_public_site",
    }

    updated = derive_capabilities_from_answers(spec)

    assert updated["archetype"] == "editorial-cms"
    assert updated["archetype_data"]["id"] == "editorial-cms"
    assert updated["capabilities"] == ["cms", "public-site"]