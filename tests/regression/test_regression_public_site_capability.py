from initializer.flow.new_project import (
    build_initial_spec,
    derive_capabilities_from_answers,
)


def test_regression_public_surface_adds_public_site_capability():
    spec = build_initial_spec(
        "Editorial CMS with admin panel and public website"
    )

    spec["answers"] = {
        "project_name": "Editorial Regression",
        "project_slug": "editorial-regression",
        "summary": "Regression test",
        "surface": "admin_plus_public_site",
        "deploy_target": "docker",
    }

    updated = derive_capabilities_from_answers(spec)

    assert updated["archetype"] == "editorial-cms"
    assert updated["capabilities"] == ["cms", "public-site"]


def test_regression_internal_surface_does_not_add_public_site():
    spec = build_initial_spec(
        "Editorial CMS with admin panel only"
    )

    spec["answers"] = {
        "project_name": "Editorial Internal",
        "project_slug": "editorial-internal",
        "summary": "Regression test",
        "surface": "internal_admin_only",
        "deploy_target": "docker",
    }

    updated = derive_capabilities_from_answers(spec)

    assert updated["archetype"] == "editorial-cms"
    assert updated["capabilities"] == ["cms"]