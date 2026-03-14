import json

from initializer.flow.validate_project import run_validate_project


def test_regression_validate_reads_real_spec_json_from_generated_output(capsys):
    exit_code = run_validate_project("output/editorial-e2e-test")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Checking spec.json" in captured.out
    assert "✓ spec.json valid" in captured.out
    assert "Validation OK" in captured.out


def test_regression_validate_fails_when_no_known_spec_artifact_exists(tmp_path, capsys):
    exit_code = run_validate_project(str(tmp_path))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "No known spec artifact found" in captured.out
    assert "Validation failed:" in captured.out
    assert " - artifacts" in captured.out


def test_regression_validate_uses_spec_json_even_if_prd_json_is_invalid(tmp_path, capsys):
    spec = {
        "prompt": "Editorial CMS with admin panel and public website",
        "archetype": "editorial-cms",
        "archetype_data": {
            "id": "editorial-cms",
            "name": "editorial-cms",
            "stack": {
                "frontend": "nextjs",
                "backend": "payload",
                "database": "postgres",
            },
            "features": ["authentication"],
            "capabilities": ["cms"],
        },
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication"],
        "capabilities": ["cms"],
        "architecture": {
            "components": [
                {"name": "frontend", "technology": "nextjs"},
                {"name": "api", "technology": "payload"},
                {"name": "database", "technology": "postgres"},
            ],
            "decisions": ["Content managed through CMS workflows."],
        },
        "stories": [
            {
                "id": "ST-001",
                "title": "Implement CMS content management",
                "description": "Implement cms content management workflows.",
            }
        ],
        "answers": {
            "project_name": "Validate Spec Contract",
            "project_slug": "validate-spec-contract",
            "summary": "Regression test",
            "surface": "internal_admin_only",
            "deploy_target": "docker",
        },
    }

    (tmp_path / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    (tmp_path / "prd.json").write_text("{not-valid-json", encoding="utf-8")

    exit_code = run_validate_project(str(tmp_path))
    captured = capsys.readouterr()

    assert "Checking spec.json" in captured.out
    assert "✓ spec.json valid" in captured.out
    assert "Checking prd.json" in captured.out
    assert "✗ prd.json invalid" in captured.out
    assert "Validation failed:" in captured.out
    assert " - prd_json" in captured.out
    assert exit_code == 1