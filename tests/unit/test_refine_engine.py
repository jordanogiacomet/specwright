"""Tests for initializer.ai.refine_engine."""

from initializer.ai.refine_engine import (
    refine_prd,
    refine_stories,
    refine_spec,
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
