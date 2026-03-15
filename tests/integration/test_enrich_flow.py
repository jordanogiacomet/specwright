import json
from pathlib import Path

from initializer.flow.enrich_project import run_enrich_project


def _create_minimal_project(tmp_path):
    """Create a minimal generated project directory for enrich testing."""
    spec = {
        "prompt": "internal backoffice for operations",
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
        ],
        "answers": {
            "project_name": "Enrich Test",
            "project_slug": "enrich-test",
            "summary": "Test project for enrich.",
            "surface": "internal_admin_only",
            "deploy_target": "docker",
        },
        "discovery": {
            "decision_signals": {
                "app_shape": "backoffice",
                "primary_audience": "internal_teams",
                "core_work_features": ["deadlines", "report-generation"],
                "needs_scheduled_jobs": True,
                "needs_cms": False,
            },
        },
    }

    (tmp_path / "spec.json").write_text(
        json.dumps(spec, indent=2),
        encoding="utf-8",
    )
    (tmp_path / "PRD.md").write_text("# Enrich Test\n\nPlaceholder.\n", encoding="utf-8")

    return spec


def test_enrich_creates_intelligence_files(tmp_path, capsys):
    _create_minimal_project(tmp_path)

    exit_code = run_enrich_project(str(tmp_path))
    assert exit_code == 0

    # Check prd-intelligence.json was created
    docs_dir = tmp_path / "docs"
    intelligence_path = docs_dir / "prd-intelligence.json"
    assert intelligence_path.exists()

    intelligence = json.loads(intelligence_path.read_text())
    assert "problem_statement" in intelligence
    assert "personas" in intelligence
    assert "success_metrics" in intelligence
    assert len(intelligence["personas"]) > 0


def test_enrich_updates_spec_json(tmp_path, capsys):
    _create_minimal_project(tmp_path)

    exit_code = run_enrich_project(str(tmp_path))
    assert exit_code == 0

    spec = json.loads((tmp_path / "spec.json").read_text())
    assert "prd_intelligence" in spec
    assert "problem_statement" in spec["prd_intelligence"]


def test_enrich_rewrites_prd_md(tmp_path, capsys):
    _create_minimal_project(tmp_path)

    exit_code = run_enrich_project(str(tmp_path))
    assert exit_code == 0

    prd_content = (tmp_path / "PRD.md").read_text()

    # Should have enriched sections
    assert "Problem Statement" in prd_content
    assert "Personas" in prd_content
    assert "Success Metrics" in prd_content
    assert "Scope" in prd_content
    assert "Enrich Test" in prd_content


def test_enrich_prd_reflects_signals(tmp_path, capsys):
    _create_minimal_project(tmp_path)

    exit_code = run_enrich_project(str(tmp_path))
    assert exit_code == 0

    prd_content = (tmp_path / "PRD.md").read_text()

    # Should reflect backoffice/internal signals
    assert "backoffice" in prd_content.lower() or "operations" in prd_content.lower()
    assert "internal_teams" in prd_content or "internal" in prd_content.lower()


def test_enrich_fails_gracefully_on_missing_dir(capsys):
    exit_code = run_enrich_project("/nonexistent/path")
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error" in captured.out or "not found" in captured.out.lower()


def test_enrich_fails_gracefully_on_missing_spec(tmp_path, capsys):
    # Directory exists but no spec.json
    exit_code = run_enrich_project(str(tmp_path))
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error" in captured.out or "not found" in captured.out.lower()