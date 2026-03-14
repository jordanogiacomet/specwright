from initializer.ai.discovery_engine import AssistedDiscoveryResult
from initializer.ai.discovery_merge import merge_assisted_discovery


def test_merge_assisted_discovery_updates_allowed_answers_and_preserves_core_fields():
    original_spec = {
        "prompt": "Editorial CMS with admin panel and public website",
        "archetype": "editorial-cms",
        "archetype_data": {
            "id": "editorial-cms",
            "name": "editorial-cms",
            "features": ["authentication", "preview"],
            "capabilities": ["cms"],
            "stack": {
                "frontend": "nextjs",
                "backend": "payload",
                "database": "postgres",
            },
        },
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication", "preview"],
        "capabilities": ["cms"],
        "answers": {
            "project_name": "Editorial Project",
            "surface": "internal_admin_only",
        },
    }

    result = AssistedDiscoveryResult(
        answer_updates={
            "surface": "admin_plus_public_site",
            "tenant_model": "single_tenant",
            "archetype": "marketplace",  # should be ignored
            "unknown_field": "should_not_be_merged",  # should be ignored
        },
        capability_candidates=[],
        assumptions=["This likely needs a public-facing experience."],
        open_questions=["Does the project require editorial review before publishing?"],
        additional_questions=["Should scheduled publishing be enabled for MVP?"],
    )

    merged = merge_assisted_discovery(original_spec, result)

    assert merged["archetype"] == "editorial-cms"
    assert merged["archetype_data"]["id"] == "editorial-cms"
    assert merged["stack"]["frontend"] == "nextjs"
    assert merged["features"] == ["authentication", "preview"]

    assert merged["answers"]["project_name"] == "Editorial Project"
    assert merged["answers"]["surface"] == "internal_admin_only"
    assert merged["answers"]["tenant_model"] == "single_tenant"
    assert "unknown_field" not in merged["answers"]
    assert "archetype" not in merged["answers"]

    assert merged["discovery"]["assisted"] is True
    assert merged["discovery"]["assumptions"] == [
        "This likely needs a public-facing experience."
    ]
    assert merged["discovery"]["open_questions"] == [
        "Does the project require editorial review before publishing?"
    ]
    assert merged["discovery"]["additional_questions"] == [
        "Should scheduled publishing be enabled for MVP?"
    ]


def test_merge_assisted_discovery_adds_only_valid_capability_candidates():
    original_spec = {
        "archetype": "editorial-cms",
        "archetype_data": {"id": "editorial-cms"},
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication"],
        "capabilities": ["cms"],
        "answers": {},
    }

    result = AssistedDiscoveryResult(
        answer_updates={},
        capability_candidates=[
            "public-site",
            "scheduled-jobs",
            "not-a-real-capability",
            "cms",
            "public-site",
        ],
        assumptions=[],
        open_questions=[],
        additional_questions=[],
    )

    merged = merge_assisted_discovery(original_spec, result)

    assert merged["capabilities"] == ["cms", "public-site", "scheduled-jobs"]
    assert "not-a-real-capability" not in merged["capabilities"]


def test_merge_assisted_discovery_merges_discovery_metadata_without_duplication():
    original_spec = {
        "archetype": "editorial-cms",
        "archetype_data": {"id": "editorial-cms"},
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication"],
        "capabilities": ["cms"],
        "answers": {},
        "discovery": {
            "assisted": True,
            "assumptions": ["Existing assumption"],
            "open_questions": ["Existing question"],
            "additional_questions": ["Existing additional question"],
            "capability_candidates": ["public-site"],
        },
    }

    result = AssistedDiscoveryResult(
        answer_updates={},
        capability_candidates=["public-site", "i18n"],
        assumptions=["Existing assumption", "New assumption"],
        open_questions=["Existing question", "New question"],
        additional_questions=[
            "Existing additional question",
            "New additional question",
        ],
    )

    merged = merge_assisted_discovery(original_spec, result)

    assert merged["discovery"]["assisted"] is True
    assert merged["discovery"]["assumptions"] == [
        "Existing assumption",
        "New assumption",
    ]
    assert merged["discovery"]["open_questions"] == [
        "Existing question",
        "New question",
    ]
    assert merged["discovery"]["additional_questions"] == [
        "Existing additional question",
        "New additional question",
    ]
    assert merged["discovery"]["capability_candidates"] == [
        "public-site",
        "i18n",
    ]