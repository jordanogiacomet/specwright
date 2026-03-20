"""Tests for initializer.ai.refine_engine."""

from initializer.ai.refine_engine import (
    refine_prd,
    refine_stories,
    refine_spec,
    _split_complex_stories,
)


def _make_spec(**overrides):
    spec = {
        "answers": {"project_name": "test-app", "deploy_target": "docker"},
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "capabilities": [],
        "features": [],
        "architecture": {"decisions": []},
        "stories": [],
    }
    spec.update(overrides)
    return spec


# -------------------------------------------------------
# refine_prd
# -------------------------------------------------------


def test_refine_prd_adds_monitoring_decision():
    spec = _make_spec()
    result = refine_prd(spec)
    assert "Add monitoring and logging stack." in result["architecture"]["decisions"]


def test_refine_prd_adds_backup_decision():
    spec = _make_spec()
    result = refine_prd(spec)
    assert "Add automated database backups." in result["architecture"]["decisions"]


def test_refine_prd_adds_cdn_only_when_public_site():
    spec = _make_spec(capabilities=["public-site"])
    result = refine_prd(spec)
    assert "CDN recommended for public assets." in result["architecture"]["decisions"]


def test_refine_prd_no_cdn_without_public_site():
    spec = _make_spec(capabilities=[])
    result = refine_prd(spec)
    assert "CDN recommended for public assets." not in result["architecture"]["decisions"]


def test_refine_prd_idempotent():
    spec = _make_spec(capabilities=["public-site"])
    result1 = refine_prd(spec)
    decisions_count = len(result1["architecture"]["decisions"])
    result2 = refine_prd(result1)
    assert len(result2["architecture"]["decisions"]) == decisions_count


# -------------------------------------------------------
# refine_stories — ST-900 (monitoring)
# -------------------------------------------------------


def test_refine_stories_adds_st900():
    spec = _make_spec()
    result = refine_stories(spec)
    ids = [s["id"] for s in result["stories"]]
    assert "ST-900" in ids


def test_monitoring_story_has_story_key():
    spec = _make_spec()
    result = refine_stories(spec)
    st900 = next(s for s in result["stories"] if s["id"] == "ST-900")
    assert st900["story_key"] == "operations.monitoring"


def test_monitoring_story_has_health_check_criteria():
    spec = _make_spec()
    result = refine_stories(spec)
    st900 = next(s for s in result["stories"] if s["id"] == "ST-900")
    assert any("health check" in ac.lower() for ac in st900["acceptance_criteria"])


def test_monitoring_story_includes_db_health_for_postgres():
    spec = _make_spec()
    result = refine_stories(spec)
    st900 = next(s for s in result["stories"] if s["id"] == "ST-900")
    assert any("database connection" in ac.lower() for ac in st900["acceptance_criteria"])


def test_monitoring_story_includes_public_site_criteria():
    spec = _make_spec(capabilities=["public-site"])
    result = refine_stories(spec)
    st900 = next(s for s in result["stories"] if s["id"] == "ST-900")
    assert any("response time" in ac.lower() for ac in st900["acceptance_criteria"])


def test_monitoring_story_no_public_criteria_without_capability():
    spec = _make_spec(capabilities=[])
    result = refine_stories(spec)
    st900 = next(s for s in result["stories"] if s["id"] == "ST-900")
    assert not any("response time" in ac.lower() for ac in st900["acceptance_criteria"])


def test_monitoring_story_includes_job_logging_for_scheduled_jobs():
    spec = _make_spec(capabilities=["scheduled-jobs"])
    result = refine_stories(spec)
    st900 = next(s for s in result["stories"] if s["id"] == "ST-900")
    assert any("background job" in ac.lower() for ac in st900["acceptance_criteria"])


# -------------------------------------------------------
# refine_stories — ST-901 (backups)
# -------------------------------------------------------


def test_refine_stories_adds_st901():
    spec = _make_spec()
    result = refine_stories(spec)
    ids = [s["id"] for s in result["stories"]]
    assert "ST-901" in ids


def test_backups_story_has_story_key():
    spec = _make_spec()
    result = refine_stories(spec)
    st901 = next(s for s in result["stories"] if s["id"] == "ST-901")
    assert st901["story_key"] == "operations.backups"


def test_backups_story_postgres_specific():
    spec = _make_spec()
    result = refine_stories(spec)
    st901 = next(s for s in result["stories"] if s["id"] == "ST-901")
    assert any("pg_dump" in ac for ac in st901["acceptance_criteria"])


def test_backups_story_mongodb_specific():
    spec = _make_spec(stack={"frontend": "nextjs", "backend": "node-api", "database": "mongodb"})
    result = refine_stories(spec)
    st901 = next(s for s in result["stories"] if s["id"] == "ST-901")
    assert any("mongodump" in ac for ac in st901["acceptance_criteria"])


def test_backups_story_docker_criteria():
    spec = _make_spec()
    result = refine_stories(spec)
    st901 = next(s for s in result["stories"] if s["id"] == "ST-901")
    assert any("docker" in ac.lower() for ac in st901["acceptance_criteria"])


def test_backups_story_expected_files():
    spec = _make_spec()
    result = refine_stories(spec)
    st901 = next(s for s in result["stories"] if s["id"] == "ST-901")
    assert "scripts/backup.sh" in st901["expected_files"]
    assert "scripts/restore.sh" in st901["expected_files"]


# -------------------------------------------------------
# refine_stories — ST-902 (rate limiting)
# -------------------------------------------------------


def test_refine_stories_adds_st902_when_auth_present():
    spec = _make_spec(features=["authentication"])
    result = refine_stories(spec)
    ids = [s["id"] for s in result["stories"]]
    assert "ST-902" in ids


def test_refine_stories_no_st902_without_auth():
    spec = _make_spec(features=[])
    result = refine_stories(spec)
    ids = [s["id"] for s in result["stories"]]
    assert "ST-902" not in ids


def test_rate_limiting_story_has_story_key():
    spec = _make_spec(features=["authentication"])
    result = refine_stories(spec)
    st902 = next(s for s in result["stories"] if s["id"] == "ST-902")
    assert st902["story_key"] == "security.rate-limiting"


def test_rate_limiting_story_depends_on_auth():
    spec = _make_spec(features=["authentication"])
    result = refine_stories(spec)
    st902 = next(s for s in result["stories"] if s["id"] == "ST-902")
    assert "feature.authentication" in st902["depends_on"]


def test_rate_limiting_story_payload_specific():
    spec = _make_spec(
        features=["authentication"],
        stack={"frontend": "nextjs", "backend": "payload", "database": "postgres"},
    )
    result = refine_stories(spec)
    st902 = next(s for s in result["stories"] if s["id"] == "ST-902")
    assert any("/api/users/login" in ac for ac in st902["acceptance_criteria"])


def test_rate_limiting_story_nextjs_specific():
    spec = _make_spec(features=["authentication"])
    result = refine_stories(spec)
    st902 = next(s for s in result["stories"] if s["id"] == "ST-902")
    assert any("next.js middleware" in ac.lower() for ac in st902["acceptance_criteria"])


def test_rate_limiting_deduplication():
    spec = _make_spec(
        features=["authentication"],
        stories=[{"id": "ST-902", "title": "existing rate limiting"}],
    )
    result = refine_stories(spec)
    assert len([s for s in result["stories"] if s["id"] == "ST-902"]) == 1


# -------------------------------------------------------
# refine_stories — ST-903 (password policy)
# -------------------------------------------------------


def test_refine_stories_adds_st903_when_auth_present():
    spec = _make_spec(features=["authentication"])
    result = refine_stories(spec)
    ids = [s["id"] for s in result["stories"]]
    assert "ST-903" in ids


def test_refine_stories_no_st903_without_auth():
    spec = _make_spec(features=[])
    result = refine_stories(spec)
    ids = [s["id"] for s in result["stories"]]
    assert "ST-903" not in ids


def test_password_policy_story_has_story_key():
    spec = _make_spec(features=["authentication"])
    result = refine_stories(spec)
    st903 = next(s for s in result["stories"] if s["id"] == "ST-903")
    assert st903["story_key"] == "security.password-policy"


def test_password_policy_story_depends_on_auth():
    spec = _make_spec(features=["authentication"])
    result = refine_stories(spec)
    st903 = next(s for s in result["stories"] if s["id"] == "ST-903")
    assert "feature.authentication" in st903["depends_on"]


def test_password_policy_story_has_minlength_criteria():
    spec = _make_spec(features=["authentication"])
    result = refine_stories(spec)
    st903 = next(s for s in result["stories"] if s["id"] == "ST-903")
    assert any("8 characters" in ac for ac in st903["acceptance_criteria"])


def test_password_policy_deduplication():
    spec = _make_spec(
        features=["authentication"],
        stories=[{"id": "ST-903", "title": "existing password policy"}],
    )
    result = refine_stories(spec)
    assert len([s for s in result["stories"] if s["id"] == "ST-903"]) == 1


# -------------------------------------------------------
# refine_stories — deduplication
# -------------------------------------------------------


def test_refine_stories_does_not_duplicate():
    spec = _make_spec(stories=[
        {"id": "ST-900", "title": "existing monitoring"},
        {"id": "ST-901", "title": "existing backups"},
    ])
    result = refine_stories(spec)
    assert len([s for s in result["stories"] if s["id"] == "ST-900"]) == 1
    assert len([s for s in result["stories"] if s["id"] == "ST-901"]) == 1


# -------------------------------------------------------
# _split_complex_stories
# -------------------------------------------------------


def _make_story(ac_count=3, file_count=2, **overrides):
    story = {
        "id": "ST-099",
        "title": "Test story",
        "story_key": "test.story",
        "description": "A test story.",
        "acceptance_criteria": [f"AC-{i}" for i in range(ac_count)],
        "scope_boundaries": ["Do NOT touch unrelated code"],
        "expected_files": [f"src/file-{i}.ts" for i in range(file_count)],
        "depends_on": ["bootstrap.backend"],
        "validation": {"commands": ["npm run build"], "manual_check": "It works"},
    }
    story.update(overrides)
    return story


def test_split_does_not_touch_small_stories():
    story = _make_story(ac_count=5, file_count=3)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    assert len(result["stories"]) == 1
    assert result["stories"][0]["id"] == "ST-099"


def test_split_skips_stories_just_at_threshold():
    """8 ACs is at the boundary but not over MAX_AC_COUNT=9, so no split."""
    story = _make_story(ac_count=8, file_count=2)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    assert len(result["stories"]) == 1


def test_split_triggers_on_high_ac_count():
    story = _make_story(ac_count=10, file_count=2)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    assert len(result["stories"]) == 2


def test_split_triggers_on_high_file_count():
    """High files trigger split only if ACs are also worth splitting (>=8)."""
    story = _make_story(ac_count=10, file_count=10)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    assert len(result["stories"]) == 2


def test_split_skips_high_files_with_few_acs():
    """Many files but too few ACs to produce meaningful parts — skip split."""
    story = _make_story(ac_count=3, file_count=10)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    assert len(result["stories"]) == 1


def test_split_part1_keeps_original_key():
    story = _make_story(ac_count=10)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    assert result["stories"][0]["story_key"] == "test.story"
    assert result["stories"][0]["id"] == "ST-099"


def test_split_parts_chain_dependencies():
    story = _make_story(ac_count=10)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    parts = result["stories"]
    # Part 1 keeps original depends_on
    assert "bootstrap.backend" in parts[0]["depends_on"]
    # Part 2 depends on part 1's story_key
    assert "test.story" in parts[1]["depends_on"]


def test_split_preserves_scope_boundaries():
    story = _make_story(ac_count=10)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    for part in result["stories"]:
        assert "Do NOT touch unrelated code" in part["scope_boundaries"]


def test_split_titles_include_part_numbers():
    story = _make_story(ac_count=10)
    spec = _make_spec(stories=[story])
    result = _split_complex_stories(spec)
    assert "(part 1 of 2)" in result["stories"][0]["title"]
    assert "(part 2 of 2)" in result["stories"][1]["title"]


# -------------------------------------------------------
# refine_spec (full pipeline)
# -------------------------------------------------------


def test_refine_spec_full_pipeline():
    spec = _make_spec(capabilities=["public-site"])
    result = refine_spec(spec)

    # PRD decisions
    assert "CDN recommended for public assets." in result["architecture"]["decisions"]
    assert "Add monitoring and logging stack." in result["architecture"]["decisions"]

    # Stories
    ids = [s["id"] for s in result["stories"]]
    assert "ST-900" in ids
    assert "ST-901" in ids


def test_refine_spec_includes_security_stories():
    spec = _make_spec(features=["authentication"])
    result = refine_spec(spec)
    ids = [s["id"] for s in result["stories"]]
    assert "ST-902" in ids
    assert "ST-903" in ids


def test_refine_spec_includes_splitting():
    story = _make_story(ac_count=10)
    spec = _make_spec(stories=[story])
    result = refine_spec(spec)
    # Original story split + ST-900 + ST-901 (no auth so no ST-902/903)
    titles = [s["title"] for s in result["stories"]]
    assert any("part 1 of 2" in t for t in titles)
    assert any("part 2 of 2" in t for t in titles)
