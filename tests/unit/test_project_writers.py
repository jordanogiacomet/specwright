"""Tests for PRD, architecture, and decisions generators.

Validates that write_prd, write_architecture, and write_decisions produce
useful, non-generic content for AI agents.
"""

from pathlib import Path

from initializer.flow.new_project import (
    write_prd,
    write_architecture,
    write_decisions,
)


def _make_spec(**overrides):
    spec = {
        "answers": {
            "project_name": "Test Project",
            "project_slug": "test-project",
            "summary": "A task management app for teams.",
            "surface": "internal_admin_only",
            "deploy_target": "docker",
        },
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": ["authentication", "api", "notifications"],
        "capabilities": ["scheduled-jobs", "i18n"],
        "architecture": {
            "style": "service-oriented",
            "components": [
                {"name": "frontend", "technology": "nextjs", "role": "user interface"},
                {"name": "api", "technology": "node-api", "role": "application logic"},
                {"name": "database", "technology": "postgres", "role": "persistent storage"},
                {"name": "worker", "technology": "node-api", "role": "process scheduled jobs"},
            ],
            "communication": [
                {
                    "from": "frontend",
                    "to": "api",
                    "protocol": "http",
                    "pattern": "REST API",
                    "auth": "JWT bearer token",
                },
                {
                    "from": "api",
                    "to": "database",
                    "protocol": "tcp",
                    "pattern": "ORM over postgres",
                },
            ],
            "boundaries": {
                "frontend": ["Rendering pages", "Client-side routing"],
                "backend": ["Business logic", "Auth and authorization"],
                "shared": ["Shared types"],
            },
            "decisions": [
                "Use SSR or ISR for SEO-sensitive pages.",
                "Implement structured logging.",
                "Add health check endpoints.",
                "Add automated database backups.",
                "Authentication handled via JWT.",
                "[todo-data-model] Standard: title, completed, dueDate, priority.",
                "Use SSR or ISR for SEO-sensitive public pages when applicable.",
                "CDN recommended for public assets.",
                "Serve static assets through CDN.",
            ],
        },
        "stories": [
            {"id": "ST-001", "story_key": "bootstrap.repository", "title": "Initialize project"},
            {"id": "ST-002", "story_key": "bootstrap.database", "title": "Setup database"},
            {"id": "ST-003", "story_key": "feature.authentication", "title": "Implement auth"},
        ],
        "discovery": {
            "decision_signals": {
                "app_shape": "internal-work-organizer",
                "primary_audience": "internal_teams",
                "core_work_features": ["deadlines", "task-assignment"],
            },
        },
        "domain_model": {
            "entities": [
                {"name": "Task", "description": "A work item"},
            ],
            "roles": [
                {"name": "user", "can": ["create_task", "read_own_tasks"]},
                {"name": "admin", "can": ["manage_users", "read_all_tasks"]},
            ],
        },
    }
    spec.update(overrides)
    return spec


# -------------------------------------------------------
# PRD tests
# -------------------------------------------------------


def test_prd_has_project_name(tmp_path):
    path = tmp_path / "PRD.md"
    write_prd(path, _make_spec())
    content = path.read_text()
    assert "# Test Project" in content


def test_prd_has_concrete_problem_statement(tmp_path):
    path = tmp_path / "PRD.md"
    write_prd(path, _make_spec())
    content = path.read_text()
    assert "## Problem Statement" in content
    # Should NOT have the old generic text
    assert "defined operational workflow" not in content


def test_prd_has_concrete_personas(tmp_path):
    path = tmp_path / "PRD.md"
    write_prd(path, _make_spec())
    content = path.read_text()
    assert "## Personas" in content
    # Should have role-derived personas, not "Primary User"
    assert "User" in content or "Admin" in content
    assert "create_task" in content or "manage_users" in content


def test_prd_has_scope(tmp_path):
    path = tmp_path / "PRD.md"
    write_prd(path, _make_spec())
    content = path.read_text()
    assert "### In Scope" in content
    assert "### Out of Scope" in content
    assert "authentication" in content.lower() or "login" in content.lower()


def test_prd_does_not_dump_architecture_decisions(tmp_path):
    path = tmp_path / "PRD.md"
    write_prd(path, _make_spec())
    content = path.read_text()
    # Should NOT contain the raw decision dump
    assert "## Architecture Decisions" not in content
    assert "Implement structured logging" not in content


def test_prd_has_stories_section(tmp_path):
    path = tmp_path / "PRD.md"
    write_prd(path, _make_spec())
    content = path.read_text()
    assert "ST-001" in content
    assert "ST-003" in content
    assert "docs/stories/" in content


def test_prd_has_discovery_signals(tmp_path):
    path = tmp_path / "PRD.md"
    write_prd(path, _make_spec())
    content = path.read_text()
    assert "internal-work-organizer" in content
    assert "internal_teams" in content


def test_prd_out_of_scope_reflects_capabilities(tmp_path):
    # No public-site, no cms → should be out of scope
    path = tmp_path / "PRD.md"
    write_prd(path, _make_spec(capabilities=["scheduled-jobs"]))
    content = path.read_text()
    assert "public" in content.lower() or "marketing" in content.lower()


# -------------------------------------------------------
# Architecture tests
# -------------------------------------------------------


def test_architecture_has_components(tmp_path):
    path = tmp_path / "architecture.md"
    write_architecture(path, _make_spec())
    content = path.read_text()
    assert "### frontend" in content
    assert "### api" in content
    assert "### database" in content


def test_architecture_has_communication(tmp_path):
    path = tmp_path / "architecture.md"
    write_architecture(path, _make_spec())
    content = path.read_text()
    assert "frontend → api" in content
    assert "REST API" in content


def test_architecture_has_boundaries(tmp_path):
    path = tmp_path / "architecture.md"
    write_architecture(path, _make_spec())
    content = path.read_text()
    assert "## Responsibility Boundaries" in content
    assert "Business logic" in content


def test_architecture_has_request_flow(tmp_path):
    path = tmp_path / "architecture.md"
    write_architecture(path, _make_spec())
    content = path.read_text()
    assert "## Typical Request Flow" in content
    assert "auth token" in content.lower() or "session" in content.lower()


def test_architecture_has_background_job_flow(tmp_path):
    path = tmp_path / "architecture.md"
    write_architecture(path, _make_spec())
    content = path.read_text()
    assert "Background job execution" in content
    assert "Scheduler triggers" in content


def test_architecture_does_not_dump_decisions(tmp_path):
    path = tmp_path / "architecture.md"
    write_architecture(path, _make_spec())
    content = path.read_text()
    # Decisions should NOT be listed as raw bullet points anymore
    assert "## Architectural Decisions" not in content


def test_architecture_has_key_constraints(tmp_path):
    path = tmp_path / "architecture.md"
    write_architecture(path, _make_spec())
    content = path.read_text()
    assert "## Key Constraints" in content
    assert "src/lib/migrations/" in content
    assert ".env.example" in content
    assert "src/pages/" in content


def test_architecture_mentions_i18n_when_capability(tmp_path):
    path = tmp_path / "architecture.md"
    write_architecture(path, _make_spec(capabilities=["i18n"]))
    content = path.read_text()
    assert "[locale]" in content


# -------------------------------------------------------
# Decisions tests
# -------------------------------------------------------


def test_decisions_has_project_constraints(tmp_path):
    path = tmp_path / "decisions.md"
    write_decisions(path, _make_spec())
    content = path.read_text()
    assert "DEC-001" in content
    assert "spec.json" in content
    assert "DEC-002" in content


def test_decisions_has_stack(tmp_path):
    path = tmp_path / "decisions.md"
    write_decisions(path, _make_spec())
    content = path.read_text()
    assert "nextjs" in content
    assert "node-api" in content
    assert "postgres" in content


def test_decisions_deduplicates(tmp_path):
    path = tmp_path / "decisions.md"
    write_decisions(path, _make_spec())
    content = path.read_text()
    # "SSR or ISR" appears in two decisions but should be deduplicated
    ssr_count = content.lower().count("ssr or isr")
    assert ssr_count <= 1, f"SSR/ISR appears {ssr_count} times, expected <= 1"


def test_decisions_has_real_reasons(tmp_path):
    path = tmp_path / "decisions.md"
    write_decisions(path, _make_spec())
    content = path.read_text()
    # Should NOT have generic "derived in the generated architecture"
    assert "derived in the generated architecture" not in content
    # Should have specific reasons
    assert "Reason:" in content


def test_decisions_categorizes(tmp_path):
    path = tmp_path / "decisions.md"
    write_decisions(path, _make_spec())
    content = path.read_text()
    # Should have category headers
    has_categories = any(
        cat in content
        for cat in ["Security", "Performance", "Operations", "Domain", "Architecture"]
    )
    assert has_categories


def test_decisions_much_shorter_than_before(tmp_path):
    path = tmp_path / "decisions.md"
    spec = _make_spec()
    write_decisions(path, spec)
    content = path.read_text()
    line_count = len(content.strip().split("\n"))
    # Old decisions.md was 310 lines for 9 decisions. New should be under 100.
    assert line_count < 100, f"decisions.md is {line_count} lines, expected < 100"
