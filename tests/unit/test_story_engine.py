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
    assert (
        "Add login, logout and session management."
        in auth_story["description_alternatives"]
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