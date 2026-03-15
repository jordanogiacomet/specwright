import json
from pathlib import Path

from initializer.renderers.codex_bundle import write_codex_bundle
from initializer.renderers.openclaw_bundle import write_openclaw_bundle


def _make_spec(**overrides):
    spec = {
        "prompt": "test project",
        "archetype": "generic-web-app",
        "archetype_data": {"id": "generic-web-app"},
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": ["authentication", "api"],
        "capabilities": ["scheduled-jobs"],
        "architecture": {
            "components": [
                {"name": "frontend", "technology": "nextjs", "role": "user interface"},
                {"name": "api", "technology": "node-api", "role": "application logic"},
                {"name": "database", "technology": "postgres", "role": "persistent storage"},
            ],
            "decisions": ["Implement structured logging."],
        },
        "stories": [
            {"id": "ST-001", "story_key": "bootstrap.repository", "title": "Initialize project repository", "description": "Create project structure."},
            {"id": "ST-002", "story_key": "bootstrap.database", "title": "Setup database", "description": "Configure database."},
            {"id": "ST-003", "story_key": "feature.authentication", "title": "Implement authentication", "description": "Add auth."},
            {"id": "ST-900", "title": "Setup monitoring and logging", "description": "Add monitoring."},
        ],
        "answers": {
            "project_name": "Test Project",
            "project_slug": "test-project",
            "summary": "A test project.",
            "surface": "internal_admin_only",
            "deploy_target": "docker",
        },
        "discovery": {
            "decision_signals": {
                "app_shape": "backoffice",
                "primary_audience": "internal_teams",
                "core_work_features": ["deadlines"],
                "needs_scheduled_jobs": True,
            },
        },
    }
    spec.update(overrides)
    return spec


# -------------------------------------------------------
# Codex bundle tests
# -------------------------------------------------------


def test_codex_bundle_creates_agents_md_in_codex_dir(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    agents_path = tmp_path / ".codex" / "AGENTS.md"
    assert agents_path.exists()

    content = agents_path.read_text()
    assert "Test Project" in content
    assert "backoffice" in content
    assert "internal_teams" in content
    assert "scheduled-jobs" in content


def test_codex_bundle_agents_md_has_scope_boundaries(tmp_path):
    spec = _make_spec(capabilities=["scheduled-jobs"])
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / ".codex" / "AGENTS.md").read_text()

    # Should NOT add public-site, CMS, i18n
    assert "Do NOT add a public-facing site" in content
    assert "Do NOT add CMS" in content
    assert "Do NOT add i18n" in content

    # Should NOT restrict scheduled-jobs since it's in capabilities
    assert "Do NOT add background workers" not in content


def test_codex_bundle_creates_executable_ralph_sh(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    ralph_path = tmp_path / "ralph.sh"
    assert ralph_path.exists()

    import os
    assert os.access(ralph_path, os.X_OK)


def test_codex_bundle_ralph_sh_contains_correct_model(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "gpt-5.4" in content
    assert 'model_reasoning_effort="xhigh"' in content
    assert "danger-full-access" in content


def test_codex_bundle_ralph_sh_has_auth_check(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "OPENAI_API_KEY" in content
    assert "Auth: OK" in content


# -------------------------------------------------------
# OpenClaw bundle tests
# -------------------------------------------------------


def test_openclaw_bundle_creates_all_files(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    openclaw_dir = tmp_path / ".openclaw"
    assert (openclaw_dir / "AGENTS.md").exists()
    assert (openclaw_dir / "OPENCLAW.md").exists()
    assert (openclaw_dir / "manifest.json").exists()
    assert (openclaw_dir / "repo-contract.json").exists()
    assert (openclaw_dir / "commands.json").exists()
    assert (openclaw_dir / "execution-plan.json").exists()


def test_openclaw_bundle_agents_md_is_project_specific(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    content = (tmp_path / ".openclaw" / "AGENTS.md").read_text()
    assert "Test Project" in content
    assert "backoffice" in content
    assert "internal_teams" in content


def test_openclaw_bundle_execution_plan_has_correct_phases(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    plan = json.loads((tmp_path / ".openclaw" / "execution-plan.json").read_text())

    assert plan["total_stories"] == 4
    assert "bootstrap" in plan["phases"]
    assert "features" in plan["phases"]
    assert "operations" in plan["phases"]

    # Check ordering
    stories = plan["stories"]
    phases_in_order = [s["phase"] for s in stories]

    # Bootstrap should come before features, features before operations
    bootstrap_indices = [i for i, p in enumerate(phases_in_order) if p == "bootstrap"]
    feature_indices = [i for i, p in enumerate(phases_in_order) if p == "features"]
    ops_indices = [i for i, p in enumerate(phases_in_order) if p == "operations"]

    if bootstrap_indices and feature_indices:
        assert max(bootstrap_indices) < min(feature_indices)
    if feature_indices and ops_indices:
        assert max(feature_indices) < min(ops_indices)


def test_openclaw_bundle_execution_plan_all_stories_pending(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    plan = json.loads((tmp_path / ".openclaw" / "execution-plan.json").read_text())

    for story in plan["stories"]:
        assert story["status"] == "pending"
        assert "order" in story
        assert "phase" in story


def test_openclaw_bundle_manifest_reflects_capabilities(tmp_path):
    spec = _make_spec(capabilities=["scheduled-jobs", "i18n"])
    write_openclaw_bundle(tmp_path, spec)

    manifest = json.loads((tmp_path / ".openclaw" / "manifest.json").read_text())

    assert manifest["capabilities"] == ["scheduled-jobs", "i18n"]
    assert manifest["app_shape"] == "backoffice"
    assert manifest["primary_audience"] == "internal_teams"
    assert manifest["policies"]["follow_phase_order"] is True