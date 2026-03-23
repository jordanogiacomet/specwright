"""Tests for the story engine.

Updated to validate enriched story fields:
acceptance_criteria, scope_boundaries, expected_files, depends_on, validation.
"""

from initializer.engine.story_engine import derive_execution_metadata, generate_stories


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
            "draft-publish",
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


def test_stories_include_parallel_execution_metadata():
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
    by_key = {story.get("story_key"): story for story in stories}

    repository = by_key["bootstrap.repository"]["execution"]
    frontend = by_key["bootstrap.frontend"]["execution"]
    auth = by_key["feature.authentication"]["execution"]

    assert repository["tracks"] == ["shared"]
    assert frontend["tracks"] == ["frontend"]
    assert auth["tracks"] == ["frontend", "backend", "integration"]
    assert "auth" in auth["contract_domains"]
    assert frontend["modes"]["frontend"] == "real-ui"
    assert auth["modes"]["frontend"] == "mock-first"
    assert auth["modes"]["integration"] == "wire-real-data"


def test_rate_limiting_execution_tracks_include_backend_and_integration():
    execution = derive_execution_metadata(
        {
            "id": "ST-902",
            "story_key": "security.rate-limiting",
            "title": "Add rate limiting to auth endpoints",
            "description": "Protect authentication endpoints against brute-force attacks with configurable rate limiting.",
            "acceptance_criteria": [
                "Auth endpoints return 429 Too Many Requests after exceeding the request threshold",
                "Responses include rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, and Retry-After",
                "Rate limiting applies to Payload endpoints /api/users/login and /api/users/create",
                "Rate limiting is implemented as Next.js middleware or API route wrapper",
            ],
            "expected_files": ["src/lib/rate-limit.ts", "src/middleware.ts"],
        }
    )

    assert execution["tracks"] == ["backend", "integration"]
    assert execution["backend_files"] == ["src/lib/rate-limit.ts"]
    assert execution["integration_files"] == ["src/middleware.ts"]


def test_password_policy_execution_tracks_cover_client_and_server():
    execution = derive_execution_metadata(
        {
            "id": "ST-903",
            "story_key": "security.password-policy",
            "title": "Enforce password policy",
            "description": "Enforce minimum password length of 8 characters on both client and server.",
            "acceptance_criteria": [
                "Registration endpoint rejects passwords shorter than 8 characters with a 400 response and descriptive error message",
                "Login form validates minimum password length of 8 characters on the client before submission",
                "Password validation logic is centralized in a shared utility importable by both client and server",
            ],
            "expected_files": ["src/lib/validation.ts"],
        }
    )

    assert execution["tracks"] == ["frontend", "backend", "integration"]
    assert execution["contract_domains"] == ["auth"]
    assert execution["integration_files"] == ["src/lib/validation.ts"]


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
    assert "vitest" in criteria.lower()
    assert "npm test" in " ".join(repo["validation"]["commands"])


def test_bootstrap_repo_python_uses_stack_aware_runner_language():
    spec = {
        "stack": {"frontend": "", "backend": "django", "database": "postgres"},
        "features": [],
        "stories": [],
    }
    stories = generate_stories(spec)
    repo = next(s for s in stories if s.get("story_key") == "bootstrap.repository")
    criteria = " ".join(repo["acceptance_criteria"]).lower()

    assert "pytest" in criteria
    assert "package.json" not in criteria
    assert "pytest" in " ".join(repo["validation"]["commands"])


def test_bootstrap_repo_go_uses_stack_aware_runner_language():
    spec = {
        "stack": {"frontend": "", "backend": "gin", "database": "postgres"},
        "features": [],
        "stories": [],
    }
    stories = generate_stories(spec)
    repo = next(s for s in stories if s.get("story_key") == "bootstrap.repository")
    criteria = " ".join(repo["acceptance_criteria"]).lower()

    assert "go test" in criteria
    assert "package.json" not in criteria
    assert "go test ./..." in " ".join(repo["validation"]["commands"])


# -------------------------------------------------------
# FIX-1: Roles from spec appear in stories
# -------------------------------------------------------


def test_roles_story_uses_spec_role_names():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "roles"],
        "stories": [],
        "answers": {
            "guided_answers": {
                "roles_and_access": {
                    "admin_roles": [
                        {"name": "admin", "responsibility": "Manage everything"},
                        {"name": "editor", "responsibility": "Draft content"},
                        {"name": "reviewer", "responsibility": "Approve content"},
                    ]
                }
            }
        },
    }
    stories = generate_stories(spec)
    roles_story = next(s for s in stories if s.get("story_key") == "feature.roles")
    criteria = " ".join(roles_story["acceptance_criteria"])
    assert "admin" in criteria
    assert "editor" in criteria
    assert "reviewer" in criteria


def test_roles_story_falls_back_to_defaults():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "roles"],
        "stories": [],
    }
    stories = generate_stories(spec)
    roles_story = next(s for s in stories if s.get("story_key") == "feature.roles")
    criteria = " ".join(roles_story["acceptance_criteria"])
    assert "admin" in criteria
    assert "user" in criteria


# -------------------------------------------------------
# FIX-2: Draft-publish uses spec roles
# -------------------------------------------------------


def test_draft_publish_uses_spec_roles():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "roles", "draft-publish"],
        "stories": [],
        "answers": {
            "guided_answers": {
                "roles_and_access": {
                    "admin_roles": [
                        {"name": "admin"},
                        {"name": "editor"},
                        {"name": "reviewer"},
                    ]
                }
            }
        },
    }
    stories = generate_stories(spec)
    dp = next(s for s in stories if s.get("story_key") == "feature.draft-publish")
    criteria = " ".join(dp["acceptance_criteria"])
    assert "editor" in criteria or "reviewer" in criteria


# -------------------------------------------------------
# FIX-3: Media library uses storage backend from spec
# -------------------------------------------------------


def test_media_library_local_storage():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "media-library"],
        "stories": [],
        "answers": {
            "guided_answers": {
                "storage_requirements": {
                    "upload_backend": "local_filesystem",
                }
            }
        },
    }
    stories = generate_stories(spec)
    media = next(s for s in stories if s.get("story_key") == "feature.media-library")
    criteria = " ".join(media["acceptance_criteria"])
    boundaries = " ".join(media["scope_boundaries"])
    assert "local" in criteria.lower()
    assert "S3" in boundaries


def test_media_library_s3_storage():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "media-library"],
        "stories": [],
        "answers": {
            "guided_answers": {
                "storage_requirements": {
                    "upload_backend": "s3",
                }
            }
        },
    }
    stories = generate_stories(spec)
    media = next(s for s in stories if s.get("story_key") == "feature.media-library")
    criteria = " ".join(media["acceptance_criteria"])
    assert "S3" in criteria


# -------------------------------------------------------
# FIX-4: Scheduled publishing mentions node-cron
# -------------------------------------------------------


def test_scheduled_publishing_mentions_node_cron():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish", "scheduled-publishing"],
        "stories": [],
    }
    stories = generate_stories(spec)
    sched = next(s for s in stories if s.get("story_key") == "feature.scheduled-publishing")
    criteria = " ".join(sched["acceptance_criteria"])
    assert "node-cron" in criteria
    assert "idempotent" in criteria


def test_scheduled_publishing_includes_content_status_in_expected_files():
    """BE-ST-012: scheduled-publishing must own content-status.ts so Codex
    can add the 'scheduled' status without being reverted by enforce_owned_files."""
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish", "scheduled-publishing"],
        "stories": [],
    }
    stories = generate_stories(spec)
    sched = next(s for s in stories if s.get("story_key") == "feature.scheduled-publishing")
    expected = sched.get("expected_files", [])
    assert any("content-status" in f for f in expected), (
        f"content-status.ts missing from scheduled-publishing expected_files: {expected}"
    )


# -------------------------------------------------------
# FIX-5: Public site rendering story
# -------------------------------------------------------


def test_public_site_rendering_story_generated():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish"],
        "capabilities": ["cms", "public-site"],
        "stories": [],
        "answers": {
            "guided_answers": {
                "content_model": {
                    "collections": [
                        {"name": "pages", "purpose": "Landing pages"},
                        {"name": "posts", "purpose": "News articles"},
                        {"name": "media", "purpose": "Uploaded files"},
                    ]
                }
            }
        },
    }
    stories = generate_stories(spec)
    public = next(s for s in stories if s.get("story_key") == "product.public-site-rendering")
    assert public is not None
    criteria = " ".join(public["acceptance_criteria"])
    # media should be excluded from public routes
    assert "/pages/" in criteria
    assert "/posts/" in criteria
    assert "/media/" not in criteria
    assert "SSR" in criteria or "ISR" in criteria
    assert "draft" in criteria.lower()


def test_public_site_rendering_defaults_without_content_model():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish"],
        "capabilities": ["cms", "public-site"],
        "stories": [],
    }
    stories = generate_stories(spec)
    public = next(s for s in stories if s.get("story_key") == "product.public-site-rendering")
    criteria = " ".join(public["acceptance_criteria"])
    # defaults to posts and pages
    assert "/posts/" in criteria
    assert "/pages/" in criteria


def test_public_site_rendering_owns_app_page_to_avoid_duplicate_route():
    """BUG-038: (app)/page.tsx and (public)/page.tsx both resolve to '/'.
    public-site-rendering must own (app)/page.tsx so Codex can relocate it."""
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish"],
        "capabilities": ["cms", "public-site"],
        "stories": [],
        "answers": {
            "guided_answers": {
                "content_model": {
                    "collections": [
                        {"name": "pages", "purpose": "Landing pages"},
                        {"name": "posts", "purpose": "News articles"},
                    ]
                }
            }
        },
    }
    stories = generate_stories(spec)
    public = next(s for s in stories if s.get("story_key") == "product.public-site-rendering")
    expected_files = public["expected_files"]
    assert "src/app/(public)/page.tsx" in expected_files
    assert "src/app/(app)/page.tsx" in expected_files


def test_no_public_site_rendering_without_capability():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish"],
        "capabilities": ["cms"],
        "stories": [],
    }
    stories = generate_stories(spec)
    keys = [s.get("story_key") for s in stories]
    assert "product.public-site-rendering" not in keys


def test_editorial_roles_fall_back_to_canonical_roles_when_cms_enabled():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "roles"],
        "capabilities": ["cms"],
        "stories": [],
    }
    stories = generate_stories(spec)
    roles_story = next(s for s in stories if s.get("story_key") == "feature.roles")
    criteria = " ".join(roles_story["acceptance_criteria"])
    assert "editor" in criteria
    assert "reviewer" in criteria
    assert "manage users" in criteria


def test_editorial_media_library_depends_on_cms_content_model():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "media-library"],
        "capabilities": ["cms"],
        "stories": [
            {
                "id": "ST-001",
                "story_key": "product.cms-content-model",
                "title": "Define CMS content model",
                "description": "Existing CMS model story.",
            }
        ],
    }
    stories = generate_stories(spec)
    media = next(s for s in stories if s.get("story_key") == "feature.media-library")
    assert "product.cms-content-model" in media["depends_on"]


def test_editorial_draft_publish_depends_on_cms_content_model():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "roles", "draft-publish"],
        "capabilities": ["cms"],
        "stories": [
            {
                "id": "ST-001",
                "story_key": "product.cms-content-model",
                "title": "Define CMS content model",
                "description": "Existing CMS model story.",
            }
        ],
    }
    stories = generate_stories(spec)
    draft = next(s for s in stories if s.get("story_key") == "feature.draft-publish")
    criteria = " ".join(draft["acceptance_criteria"])
    assert "in_review" in criteria
    assert "Publishing requires admin or reviewer role" in criteria
    assert "product.cms-content-model" in draft["depends_on"]
    assert any("src/lib/migrations" in item for item in draft["scope_boundaries"])


def test_editorial_preview_uses_preview_handlers_and_depends_on_public_rendering():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish", "preview"],
        "capabilities": ["cms", "public-site"],
        "stories": [
            {
                "id": "ST-001",
                "story_key": "product.cms-content-model",
                "title": "Define CMS content model",
                "description": "Existing CMS model story.",
            }
        ],
        "answers": {
            "guided_answers": {
                "content_model": {
                    "collections": [
                        {"name": "pages", "purpose": "Pages"},
                        {"name": "posts", "purpose": "Posts"},
                    ]
                }
            }
        },
    }
    stories = generate_stories(spec)
    preview = next(s for s in stories if s.get("story_key") == "feature.preview")
    files = " ".join(preview["expected_files"])
    assert "api/preview/route.ts" in files
    assert "product.public-site-rendering" in preview["depends_on"]


def test_editorial_scheduled_publishing_depends_on_public_rendering():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish", "scheduled-publishing"],
        "capabilities": ["cms", "public-site"],
        "stories": [
            {
                "id": "ST-001",
                "story_key": "product.cms-content-model",
                "title": "Define CMS content model",
                "description": "Existing CMS model story.",
            }
        ],
        "answers": {
            "guided_answers": {
                "content_model": {
                    "collections": [
                        {"name": "pages", "purpose": "Pages"},
                        {"name": "posts", "purpose": "Posts"},
                    ]
                }
            }
        },
    }
    stories = generate_stories(spec)
    scheduled = next(s for s in stories if s.get("story_key") == "feature.scheduled-publishing")
    criteria = " ".join(scheduled["acceptance_criteria"])
    assert "revalidation" in criteria or "public-rendering refresh" in criteria
    assert "product.cms-content-model" in scheduled["depends_on"]
    assert "product.public-site-rendering" in scheduled["depends_on"]


def test_public_site_rendering_depends_on_cms_content_model():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish"],
        "capabilities": ["cms", "public-site"],
        "stories": [
            {
                "id": "ST-001",
                "story_key": "product.cms-content-model",
                "title": "Define CMS content model",
                "description": "Existing CMS model story.",
            }
        ],
    }
    stories = generate_stories(spec)
    public = next(s for s in stories if s.get("story_key") == "product.public-site-rendering")
    criteria = " ".join(public["acceptance_criteria"])
    assert "slug" in criteria
    assert "product.cms-content-model" in public["depends_on"]


def test_cms_i18n_uses_capability_specific_stories_not_generic_i18n_setup():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": [],
        "capabilities": ["cms", "i18n"],
        "stories": [],
    }
    stories = generate_stories(spec)
    keys = [s.get("story_key") for s in stories]
    assert "feature.i18n-setup" not in keys


def test_story_engine_respects_disabled_editorial_workflow_answers():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish", "preview", "scheduled-publishing"],
        "capabilities": ["cms", "public-site"],
        "stories": [],
        "answers": {
            "critical_confirmations": {
                "preview_workflow": False,
                "draft_publish_workflow": False,
                "background_jobs": False,
            },
            "guided_answers": {
                "editorial_workflows": {
                    "draft_publish": False,
                    "preview": False,
                    "scheduled_publishing": False,
                }
            },
        },
    }
    stories = generate_stories(spec)
    keys = [s.get("story_key") for s in stories]
    assert "feature.draft-publish" not in keys
    assert "feature.preview" not in keys
    assert "feature.scheduled-publishing" not in keys


def test_preview_and_scheduled_are_not_generated_without_draft_publish():
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "preview", "scheduled-publishing"],
        "stories": [],
    }
    stories = generate_stories(spec)
    keys = [s.get("story_key") for s in stories]
    assert "feature.preview" not in keys
    assert "feature.scheduled-publishing" not in keys


def test_public_site_rendering_has_force_dynamic_scope_boundary():
    """IN-ST-013: public pages must use force-dynamic to avoid SSG DB connection at build time."""
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "draft-publish"],
        "capabilities": ["cms", "public-site"],
        "stories": [],
        "answers": {
            "guided_answers": {
                "content_model": {
                    "collections": [
                        {"name": "pages", "purpose": "Landing pages"},
                    ]
                }
            }
        },
    }
    stories = generate_stories(spec)
    public = next(s for s in stories if s.get("story_key") == "product.public-site-rendering")
    boundaries = public.get("scope_boundaries", [])
    assert any("force-dynamic" in b for b in boundaries), (
        "public-site-rendering must instruct Codex to use force-dynamic to avoid SSG DB issues"
    )


def test_payload_stories_have_type_boundary():
    """Payload Access/hook type hints reduce Codex retry loops (Run 14: BE-ST-008, BE-ST-010, IN-ST-011)."""
    spec = {
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication", "roles", "draft-publish", "preview"],
        "capabilities": ["cms", "public-site"],
        "stories": [],
        "answers": {
            "guided_answers": {
                "content_model": {
                    "collections": [
                        {"name": "pages", "purpose": "Landing pages"},
                    ]
                }
            }
        },
    }
    stories = generate_stories(spec)
    stories_by_key = {s["story_key"]: s for s in stories}

    for key in ["feature.authentication", "feature.roles", "feature.draft-publish", "feature.preview"]:
        story = stories_by_key.get(key)
        assert story is not None, f"{key} not generated"
        boundaries = story.get("scope_boundaries", [])
        assert any("req.user" in b and "Access" in b for b in boundaries), (
            f"{key} must include Payload v3 type boundary (Access signature + req.user null-check)"
        )


def test_non_payload_stories_omit_payload_type_boundary():
    """Non-Payload backends should NOT get Payload-specific type boundaries."""
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": ["authentication", "roles"],
        "capabilities": [],
        "stories": [],
        "answers": {"guided_answers": {}},
    }
    stories = generate_stories(spec)
    stories_by_key = {s["story_key"]: s for s in stories}

    for key in ["feature.authentication", "feature.roles"]:
        story = stories_by_key.get(key)
        assert story is not None, f"{key} not generated"
        boundaries = story.get("scope_boundaries", [])
        assert not any("Payload v3" in b for b in boundaries), (
            f"{key} should not have Payload type boundary for node-api backend"
        )
