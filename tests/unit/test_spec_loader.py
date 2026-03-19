import json
from textwrap import dedent

from initializer.flow.new_project import (
    derive_capabilities_from_answers,
    load_project_spec,
)


def test_load_project_spec_reads_json_contract(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "prompt": "Task manager for small teams",
                "answers": {
                    "project_name": "TaskFlow",
                    "project_slug": "taskflow",
                    "summary": "Internal task tracking",
                    "surface": "internal_admin_only",
                    "deploy_target": "docker",
                },
                "stack": {
                    "frontend": "nextjs",
                    "backend": "node-api",
                    "database": "postgres",
                },
            }
        ),
        encoding="utf-8",
    )

    spec = load_project_spec(str(spec_path))

    assert spec["prompt"] == "Task manager for small teams"
    assert spec["answers"]["project_name"] == "TaskFlow"
    assert spec["answers"]["project_slug"] == "taskflow"
    assert spec["answers"]["summary"] == "Internal task tracking"
    assert spec["answers"]["surface"] == "internal_admin_only"
    assert spec["answers"]["deploy_target"] == "docker"


def test_load_project_spec_reads_yaml_playbook_input(tmp_path):
    spec_path = tmp_path / "editorial.input.yaml"
    spec_path.write_text(
        dedent(
            """
            playbook_id: next-payload-postgres

            guided_answers:
              project_identity:
                name: Editorial Control Center
                slug: editorial-control-center
                summary: Internal editorial control center for content, media, and newsroom operations.
              product_surface:
                mode: admin_plus_public_site
              deploy_target:
                runtime: docker
              editorial_workflows:
                scheduled_publishing: false

            critical_confirmations:
              background_jobs: false
              i18n: false
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    spec = load_project_spec(str(spec_path))
    spec = derive_capabilities_from_answers(spec)

    assert spec["playbook_id"] == "next-payload-postgres"
    assert spec["prompt"] == (
        "Internal editorial control center for content, media, and newsroom operations."
    )
    assert spec["archetype"] == "editorial-cms"
    assert spec["stack"]["frontend"] == "nextjs"
    assert spec["stack"]["backend"] == "payload"
    assert spec["stack"]["database"] == "postgres"
    assert spec["answers"]["project_name"] == "Editorial Control Center"
    assert spec["answers"]["project_slug"] == "editorial-control-center"
    assert spec["answers"]["surface"] == "admin_plus_public_site"
    assert spec["answers"]["deploy_target"] == "docker"
    assert spec["answers"]["guided_answers"]["product_surface"]["mode"] == "admin_plus_public_site"
    assert spec["answers"]["critical_confirmations"]["background_jobs"] is False
    assert "cms" in spec["capabilities"]
    assert "public-site" in spec["capabilities"]
    assert "scheduled-jobs" not in spec["capabilities"]
    assert "i18n" not in spec["capabilities"]


def test_load_project_spec_resolves_spec_yaml_from_directory(tmp_path):
    spec_path = tmp_path / "spec.yaml"
    spec_path.write_text(
        dedent(
            """
            guided_answers:
              project_identity:
                name: Directory Spec
                slug: directory-spec
                summary: Directory-based YAML spec
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    spec = load_project_spec(str(tmp_path))

    assert spec["answers"]["project_name"] == "Directory Spec"
    assert spec["answers"]["project_slug"] == "directory-spec"
    assert spec["prompt"] == "Directory-based YAML spec"
