"""Tests for the story engine.

Updated to validate enriched story fields:
acceptance_criteria, scope_boundaries, expected_files, depends_on, validation.
"""

from initializer.engine.story_engine import generate_stories


def test_generate_stories_creates_canonical_editorial_stories():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": [
            "authentication",
            "roles",
            "media-library",
            "preview",
            "scheduled-publishing",
        ],
        "stories": [],
    }

    stories = generate_stories(spec)

    titles = [story["title"] for story in stories]
    ids = [story["id"] for story in stories]

    assert "Initialize project repository" in titles
    assert "Setup database" in titles
    assert "Setup backend service" in titles
    assert "Create frontend application" in titles
    assert "Implement authentication" in titles
    assert "Implement role-based access control" in titles
    assert "Implement media library" in titles
    assert "Implement content preview" in titles
    assert "Implement scheduled publishing" in titles

    assert len(ids) == len(set(ids))
    assert len(titles) == len(set(titles))


def test_generate_stories_upserts_existing_story_instead_of_duplicating():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication"],
        "stories": [
            {
                "id": "ST-001",
                "story_key": "feature.authentication",
                "title": "Custom auth story title",
                "description": "Custom auth description kept from previous enrichment.",
            }
        ],
    }

    stories = generate_stories(spec)

    auth_stories = [
        story for story in stories if story.get("story_key") == "feature.authentication"
    ]
    assert len(auth_stories) == 1

    auth_story = auth_stories[0]
    assert auth_story["id"] == "ST-001"
    assert auth_story["title"] == "Custom auth story title"
    assert auth_story["description"] == (
        "Custom auth description kept from previous enrichment."
    )

    assert "Implement authentication" in auth_story["title_alternatives"]
    # Description alternative uses new enriched text
    assert any(
        "login" in alt.lower() or "registration" in alt.lower()
        for alt in auth_story.get("description_alternatives", [])
    )


def test_generate_stories_is_stable_on_rerun_for_canonical_output():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication", "roles", "media-library"],
        "stories": [],
    }

    first = generate_stories(spec)
    second = generate_stories({**spec, "stories": first})

    first_titles = [story["title"] for story in first]
    second_titles = [story["title"] for story in second]

    assert len(first) == len(second)
    assert first_titles == second_titles
    assert len(second_titles) == len(set(second_titles))


# -------------------------------------------------------------------
# New enrichment fields
# -------------------------------------------------------------------

def test_every_story_has_acceptance_criteria():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication", "roles", "media-library"],
        "stories": [],
    }

    stories = generate_stories(spec)

    for story in stories:
        ac = story.get("acceptance_criteria", [])
        assert isinstance(ac, list), f"{story['id']} missing acceptance_criteria"
        assert len(ac) > 0, f"{story['id']} has empty acceptance_criteria"


def test_every_story_has_scope_boundaries():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication", "roles"],
        "stories": [],
    }

    stories = generate_stories(spec)

    for story in stories:
        sb = story.get("scope_boundaries", [])
        assert isinstance(sb, list), f"{story['id']} missing scope_boundaries"
        assert len(sb) > 0, f"{story['id']} has empty scope_boundaries"


def test_every_story_has_validation():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication"],
        "stories": [],
    }

    stories = generate_stories(spec)

    for story in stories:
        val = story.get("validation", {})
        assert isinstance(val, dict), f"{story['id']} missing validation"
        assert "commands" in val, f"{story['id']} validation missing commands"


def test_bootstrap_stories_have_correct_dependency_chain():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": [],
        "stories": [],
    }

    stories = generate_stories(spec)
    by_key = {s.get("story_key"): s for s in stories}

    repo = by_key.get("bootstrap.repository")
    db = by_key.get("bootstrap.database")
    backend = by_key.get("bootstrap.backend")
    frontend = by_key.get("bootstrap.frontend")

    assert repo is not None
    assert db is not None
    assert backend is not None
    assert frontend is not None

    assert repo["depends_on"] == []
    assert "bootstrap.repository" in db["depends_on"]
    assert "bootstrap.database" in backend["depends_on"]
    assert "bootstrap.backend" in frontend["depends_on"]


def test_feature_stories_depend_on_bootstrap():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication", "roles"],
        "stories": [],
    }

    stories = generate_stories(spec)
    by_key = {s.get("story_key"): s for s in stories}

    auth = by_key.get("feature.authentication")
    roles = by_key.get("feature.roles")

    assert auth is not None
    assert "bootstrap.backend" in auth["depends_on"]
    assert "bootstrap.frontend" in auth["depends_on"]

    assert roles is not None
    assert "feature.authentication" in roles["depends_on"]


def test_expected_files_use_payload_paths_for_payload_backend():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication"],
        "stories": [],
    }

    stories = generate_stories(spec)
    by_key = {s.get("story_key"): s for s in stories}

    auth = by_key.get("feature.authentication")
    assert auth is not None

    files = auth.get("expected_files", [])
    assert any("collections/Users" in f for f in files), f"Expected Payload collection path, got {files}"


def test_expected_files_use_api_paths_for_node_api_backend():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": ["authentication"],
        "stories": [],
    }

    stories = generate_stories(spec)
    by_key = {s.get("story_key"): s for s in stories}

    auth = by_key.get("feature.authentication")
    assert auth is not None

    files = auth.get("expected_files", [])
    assert any("api/auth" in f for f in files), f"Expected API path, got {files}"


def test_merge_preserves_enrichment_fields():
    """When upserting into an existing story that already has acceptance_criteria,
    the existing criteria should be preserved."""
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication"],
        "stories": [
            {
                "id": "ST-001",
                "story_key": "feature.authentication",
                "title": "Custom auth",
                "description": "Custom desc.",
                "acceptance_criteria": ["Custom criterion"],
                "depends_on": ["custom.dep"],
            }
        ],
    }

    stories = generate_stories(spec)
    auth = next(s for s in stories if s.get("story_key") == "feature.authentication")

    # Existing enrichment fields should be preserved
    assert auth["acceptance_criteria"] == ["Custom criterion"]
    assert auth["depends_on"] == ["custom.dep"]


# -------------------------------------------------------
# STORY-001: Migration directory scope boundary
# -------------------------------------------------------


def test_database_story_has_migration_dir_boundary():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": [],
        "stories": [],
    }
    stories = generate_stories(spec)
    db_story = next(s for s in stories if s.get("story_key") == "bootstrap.database")
    assert any("src/lib/migrations" in b for b in db_story["scope_boundaries"])


def test_auth_story_has_migration_dir_boundary():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": ["authentication"],
        "stories": [],
    }
    stories = generate_stories(spec)
    auth = next(s for s in stories if s.get("story_key") == "feature.authentication")
    assert any("src/lib/migrations" in b for b in auth["scope_boundaries"])


def test_todo_model_has_migration_dir_boundary():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": ["authentication"],
        "stories": [],
        "archetype": "todo-app",
    }
    stories = generate_stories(spec)
    todo = next(s for s in stories if s.get("story_key") == "product.todo-model")
    assert any("src/lib/migrations" in b for b in todo["scope_boundaries"])


# -------------------------------------------------------
# STORY-002: i18n story generation
# -------------------------------------------------------


def test_i18n_capability_generates_story():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": [],
        "capabilities": ["i18n"],
        "stories": [],
    }
    stories = generate_stories(spec)
    i18n = next((s for s in stories if s.get("story_key") == "feature.i18n-setup"), None)
    assert i18n is not None
    assert "middleware" in i18n["description"].lower() or "middleware" in " ".join(i18n.get("acceptance_criteria", [])).lower()


def test_i18n_story_warns_about_orphan_routes():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": [],
        "capabilities": ["i18n"],
        "stories": [],
    }
    stories = generate_stories(spec)
    i18n = next(s for s in stories if s.get("story_key") == "feature.i18n-setup")
    boundaries = " ".join(i18n["scope_boundaries"])
    assert "orphan" in boundaries.lower() or "outside" in boundaries.lower()


def test_i18n_story_requires_moving_all_pages():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": [],
        "capabilities": ["i18n"],
        "stories": [],
    }
    stories = generate_stories(spec)
    i18n = next(s for s in stories if s.get("story_key") == "feature.i18n-setup")
    criteria = " ".join(i18n["acceptance_criteria"])
    assert "MOVED" in criteria or "move" in criteria.lower()


# -------------------------------------------------------
# STORY-003: API response contracts in auth
# -------------------------------------------------------


def test_auth_story_has_status_codes():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": ["authentication"],
        "stories": [],
    }
    stories = generate_stories(spec)
    auth = next(s for s in stories if s.get("story_key") == "feature.authentication")
    criteria = " ".join(auth["acceptance_criteria"])
    assert "201" in criteria
    assert "401" in criteria
    assert "200" in criteria


# -------------------------------------------------------
# STORY-004: Test framework in bootstrap
# -------------------------------------------------------


def test_bootstrap_repo_requires_test_framework():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": [],
        "stories": [],
    }
    stories = generate_stories(spec)
    repo = next(s for s in stories if s.get("story_key") == "bootstrap.repository")
    criteria = " ".join(repo["acceptance_criteria"])
    assert "vitest" in criteria.lower() or "jest" in criteria.lower()
    assert "npm test" in " ".join(repo["validation"]["commands"])