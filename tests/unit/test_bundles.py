"""Tests for the codex and openclaw bundle generators.

Updated to validate:
- commands.json has real commands (not empty strings)
- execution plan includes depends_on when present
- commands are stack-aware
"""

import json
from pathlib import Path

from initializer.ai.refine_engine import refine_spec
from initializer.engine.story_engine import generate_stories
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
            {
                "id": "ST-001",
                "story_key": "bootstrap.repository",
                "title": "Initialize project repository",
                "description": "Create project structure.",
                "depends_on": [],
            },
            {
                "id": "ST-002",
                "story_key": "bootstrap.database",
                "title": "Setup database",
                "description": "Configure database.",
                "depends_on": ["bootstrap.repository"],
            },
            {
                "id": "ST-003",
                "story_key": "feature.authentication",
                "title": "Implement authentication",
                "description": "Add auth.",
                "depends_on": ["bootstrap.backend", "bootstrap.frontend"],
            },
            {
                "id": "ST-900",
                "title": "Setup monitoring and logging",
                "description": "Add monitoring.",
            },
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


def _make_editorial_parallel_spec():
    return {
        "prompt": "editorial platform",
        "archetype": "editorial-cms",
        "archetype_data": {"id": "editorial-cms"},
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication", "draft-publish", "preview"],
        "capabilities": ["cms", "public-site"],
        "architecture": {
            "components": [
                {"name": "frontend", "technology": "nextjs", "role": "public site"},
                {"name": "cms", "technology": "payload", "role": "editorial backend"},
            ],
            "decisions": [],
        },
        "stories": [],
        "answers": {
            "project_name": "Editorial Control Center",
            "project_slug": "editorial-control-center",
            "summary": "Editorial CMS with public site and auth.",
            "surface": "public_website",
            "deploy_target": "docker",
            "guided_answers": {
                "content_model": {
                    "collections": [
                        {"name": "pages", "purpose": "Landing pages"},
                        {"name": "posts", "purpose": "Articles"},
                        {"name": "authors", "purpose": "Author profiles"},
                    ],
                    "globals": [
                        {"name": "homepage", "purpose": "Homepage content"},
                        {"name": "site-settings", "purpose": "Navigation and SEO defaults"},
                    ],
                }
            },
        },
        "discovery": {
            "decision_signals": {
                "app_shape": "content-platform",
                "primary_audience": "external_users",
            }
        },
    }


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

    assert "Do NOT add a public-facing site" in content
    assert "Do NOT add CMS" in content
    assert "Do NOT add i18n" in content
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
    assert 'model_reasoning_effort' in content
    assert "$CODEX_EFFORT" in content
    assert "danger-full-access" in content


def test_codex_bundle_ralph_sh_has_auth_check(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "codex auth login" in content
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
    assert (openclaw_dir / "api-contract.json").exists()
    assert (openclaw_dir / "shared-plan.json").exists()
    assert (openclaw_dir / "frontend-plan.json").exists()
    assert (openclaw_dir / "backend-plan.json").exists()
    assert (openclaw_dir / "integration-plan.json").exists()


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

    stories = plan["stories"]

    # Each story should have a phase annotation
    for story in stories:
        assert "phase" in story

    # Bootstrap stories should generally come early
    bootstrap_indices = [i for i, s in enumerate(stories) if s["phase"] == "bootstrap"]
    if bootstrap_indices:
        assert min(bootstrap_indices) == 0


def test_openclaw_bundle_execution_plan_respects_dependencies(tmp_path):
    """Dependencies must be scheduled before their dependents."""
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    plan = json.loads((tmp_path / ".openclaw" / "execution-plan.json").read_text())
    stories = plan["stories"]

    # Build order map: story_key -> order
    key_to_order = {}
    for s in stories:
        if "story_key" in s:
            key_to_order[s["story_key"]] = s["order"]

    # Every dependency must have a lower order than its dependent
    for s in stories:
        for dep_key in s.get("depends_on", []):
            if dep_key in key_to_order:
                assert key_to_order[dep_key] < s["order"], (
                    f"{s['id']} (order {s['order']}) depends on {dep_key} "
                    f"(order {key_to_order[dep_key]}) but runs before it"
                )


def test_openclaw_bundle_execution_plan_cross_phase_deps(tmp_path):
    """Product stories that are depended on by feature stories must run first."""
    spec = _make_spec(
        stories=[
            {
                "id": "ST-001",
                "story_key": "bootstrap.repository",
                "title": "Initialize project repository",
                "depends_on": [],
            },
            {
                "id": "ST-002",
                "story_key": "bootstrap.backend",
                "title": "Setup backend",
                "depends_on": ["bootstrap.repository"],
            },
            {
                "id": "ST-010",
                "story_key": "product.cms-content-model",
                "title": "Define CMS content model",
                "depends_on": ["bootstrap.backend"],
            },
            {
                "id": "ST-011",
                "story_key": "feature.media-library",
                "title": "Implement media library",
                "depends_on": ["product.cms-content-model"],
            },
        ],
    )
    write_openclaw_bundle(tmp_path, spec)

    plan = json.loads((tmp_path / ".openclaw" / "execution-plan.json").read_text())
    stories = plan["stories"]

    key_to_order = {s["story_key"]: s["order"] for s in stories if "story_key" in s}

    # product.cms-content-model must come before feature.media-library
    assert key_to_order["product.cms-content-model"] < key_to_order["feature.media-library"]


def test_openclaw_bundle_parallel_execution_includes_track_plans(tmp_path):
    spec = _make_spec(
        stories=[
            {
                "id": "ST-001",
                "story_key": "bootstrap.repository",
                "title": "Initialize project repository",
                "description": "Create project structure.",
                "depends_on": [],
                "execution": {"tracks": ["shared"], "contract_domains": [], "frontend_files": [], "backend_files": [], "shared_files": ["package.json"], "integration_files": [], "modes": {"shared": "shared-setup"}},
            },
            {
                "id": "ST-002",
                "story_key": "feature.authentication",
                "title": "Implement authentication",
                "description": "Add auth.",
                "depends_on": ["bootstrap.repository"],
                "execution": {
                    "tracks": ["frontend", "backend", "integration"],
                    "contract_domains": ["auth"],
                    "frontend_files": ["src/app/(auth)/login/page.tsx"],
                    "backend_files": ["src/api/auth.ts"],
                    "shared_files": [],
                    "integration_files": [],
                    "modes": {
                        "frontend": "mock-first",
                        "backend": "contract-first",
                        "integration": "wire-real-data",
                    },
                },
                "acceptance_criteria": ["POST /api/auth/login returns 200 on success"],
            },
        ],
    )
    write_openclaw_bundle(tmp_path, spec)

    plan = json.loads((tmp_path / ".openclaw" / "execution-plan.json").read_text())
    parallel = plan["parallel_execution"]

    assert parallel["enabled"] is True
    assert parallel["contract_file"] == ".openclaw/api-contract.json"
    assert {item["track"] for item in parallel["tracks"]} == {"shared", "frontend", "backend", "integration"}

    frontend_plan = json.loads((tmp_path / ".openclaw" / "frontend-plan.json").read_text())
    backend_plan = json.loads((tmp_path / ".openclaw" / "backend-plan.json").read_text())
    integration_plan = json.loads((tmp_path / ".openclaw" / "integration-plan.json").read_text())

    assert frontend_plan["stories"][0]["id"] == "FE-ST-002"
    assert backend_plan["stories"][0]["id"] == "BE-ST-002"
    assert integration_plan["stories"][0]["id"] == "IN-ST-002"
    assert integration_plan["stories"][0]["depends_on"] == ["FE-ST-002", "BE-ST-002", "SH-ST-001"]


def test_openclaw_bundle_writes_api_contract_domains_and_endpoints(tmp_path):
    spec = _make_spec(
        stories=[
            {
                "id": "ST-003",
                "story_key": "feature.authentication",
                "title": "Implement authentication",
                "description": "Add auth.",
                "depends_on": [],
                "acceptance_criteria": [
                    "POST /api/auth/register returns 201 on success, 400 on validation error, 409 on duplicate email",
                    "POST /api/auth/login returns 200 with session token on success, 401 on invalid credentials",
                ],
                "execution": {
                    "tracks": ["frontend", "backend", "integration"],
                    "contract_domains": ["auth"],
                    "frontend_files": ["src/app/(auth)/login/page.tsx"],
                    "backend_files": ["src/api/auth.ts"],
                    "shared_files": [],
                    "integration_files": [],
                    "modes": {
                        "frontend": "mock-first",
                        "backend": "contract-first",
                        "integration": "wire-real-data",
                    },
                },
            }
        ],
    )
    write_openclaw_bundle(tmp_path, spec)

    contract = json.loads((tmp_path / ".openclaw" / "api-contract.json").read_text())
    auth_domain = next(domain for domain in contract["domains"] if domain["name"] == "auth")

    assert contract["strategy"] == "contract-first-parallel-loops"
    assert auth_domain["tracks"] == ["frontend", "backend", "integration"]
    assert auth_domain["frontend_files"] == ["src/app/(auth)/login/page.tsx"]
    assert auth_domain["backend_files"] == ["src/api/auth.ts"]
    assert auth_domain["http_endpoints"][0]["method"] == "POST"
    assert auth_domain["http_endpoints"][0]["path"] == "/api/auth/register"


def test_openclaw_bundle_pipeline_preserves_parallel_classification_for_editorial_spec(tmp_path):
    spec = _make_editorial_parallel_spec()
    spec["stories"] = generate_stories(spec)
    spec = refine_spec(spec)

    write_openclaw_bundle(tmp_path, spec)

    by_key = {story["story_key"]: story for story in spec["stories"]}
    assert by_key["product.public-site-rendering"]["execution"]["tracks"] == ["frontend", "integration"]
    assert by_key["product.public-site-rendering-part-2"]["execution"]["tracks"] == ["frontend", "integration"]
    assert by_key["security.rate-limiting"]["execution"]["tracks"] == ["backend", "integration"]
    assert by_key["security.password-policy"]["execution"]["tracks"] == ["frontend", "backend", "integration"]

    frontend_plan = json.loads((tmp_path / ".openclaw" / "frontend-plan.json").read_text())
    backend_plan = json.loads((tmp_path / ".openclaw" / "backend-plan.json").read_text())
    integration_plan = json.loads((tmp_path / ".openclaw" / "integration-plan.json").read_text())

    frontend_keys = {story["source_story_key"] for story in frontend_plan["stories"]}
    backend_keys = {story["source_story_key"] for story in backend_plan["stories"]}
    integration_keys = {story["source_story_key"] for story in integration_plan["stories"]}

    assert "product.public-site-rendering" in frontend_keys
    assert "product.public-site-rendering-part-2" in frontend_keys
    assert "product.public-site-rendering" not in backend_keys
    assert "product.public-site-rendering-part-2" not in backend_keys
    assert "product.public-site-rendering" in integration_keys
    assert "product.public-site-rendering-part-2" in integration_keys

    assert "security.rate-limiting" in backend_keys
    assert "security.rate-limiting" not in frontend_keys
    assert "security.rate-limiting" in integration_keys

    assert "security.password-policy" in frontend_keys
    assert "security.password-policy" in backend_keys
    assert "security.password-policy" in integration_keys


def test_openclaw_bundle_uses_story_engine_fallback_when_execution_is_missing(tmp_path):
    spec = _make_spec(
        stories=[
            {
                "id": "ST-903",
                "story_key": "security.password-policy",
                "title": "Enforce password policy",
                "description": "Enforce minimum password length of 8 characters on both client and server.",
                "depends_on": ["feature.authentication"],
                "acceptance_criteria": [
                    "Registration endpoint rejects passwords shorter than 8 characters with a 400 response and descriptive error message",
                    "Login form validates minimum password length of 8 characters on the client before submission",
                    "Password validation logic is centralized in a shared utility importable by both client and server",
                ],
                "expected_files": ["src/lib/validation.ts"],
            }
        ],
    )

    write_openclaw_bundle(tmp_path, spec)

    frontend_plan = json.loads((tmp_path / ".openclaw" / "frontend-plan.json").read_text())
    backend_plan = json.loads((tmp_path / ".openclaw" / "backend-plan.json").read_text())
    integration_plan = json.loads((tmp_path / ".openclaw" / "integration-plan.json").read_text())

    frontend_keys = {story["source_story_key"] for story in frontend_plan["stories"]}
    backend_keys = {story["source_story_key"] for story in backend_plan["stories"]}
    integration_keys = {story["source_story_key"] for story in integration_plan["stories"]}

    assert "security.password-policy" in frontend_keys
    assert "security.password-policy" in backend_keys
    assert "security.password-policy" in integration_keys


def test_openclaw_bundle_execution_plan_all_stories_pending(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    plan = json.loads((tmp_path / ".openclaw" / "execution-plan.json").read_text())

    for story in plan["stories"]:
        assert story["status"] == "pending"
        assert "order" in story
        assert "phase" in story


def test_openclaw_bundle_execution_plan_includes_depends_on(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    plan = json.loads((tmp_path / ".openclaw" / "execution-plan.json").read_text())

    db_story = next((s for s in plan["stories"] if s["id"] == "ST-002"), None)
    assert db_story is not None
    assert "depends_on" in db_story
    assert "bootstrap.repository" in db_story["depends_on"]


def test_openclaw_bundle_manifest_reflects_capabilities(tmp_path):
    spec = _make_spec(capabilities=["scheduled-jobs", "i18n"])
    write_openclaw_bundle(tmp_path, spec)

    manifest = json.loads((tmp_path / ".openclaw" / "manifest.json").read_text())

    assert manifest["capabilities"] == ["scheduled-jobs", "i18n"]
    assert manifest["app_shape"] == "backoffice"
    assert manifest["primary_audience"] == "internal_teams"
    assert manifest["policies"]["follow_phase_order"] is True


# -------------------------------------------------------
# Commands.json — stack-aware (no longer empty)
# -------------------------------------------------------


def test_openclaw_commands_json_has_real_commands_for_node(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text())

    assert commands["commands"]["build"] == "npm run build"
    assert commands["commands"]["lint"] == "npm run lint"
    assert commands["commands"]["test"] == "npm test"
    assert commands["commands"]["dev"] == "npm run dev"

    # Not empty strings
    for key, value in commands["commands"].items():
        assert value != "", f"Command '{key}' should not be empty"

    assert commands["validation"] == {
        "ecosystem": "node",
        "test_runner": "vitest",
        "requires_real_tests": True,
        "block_on": ["test", "build", "typecheck"],
        "warn_on": ["lint"],
    }


def test_openclaw_commands_json_has_setup_commands(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text())

    assert "setup" in commands
    assert commands["setup"]["install"] == "npm install"
    assert "env" in commands["setup"]


def test_openclaw_commands_json_includes_db_commands_for_postgres_docker(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text())

    assert "docker compose" in commands["commands"].get("db_start", "")


def test_openclaw_commands_json_includes_jobs_for_scheduled_jobs_capability(tmp_path):
    spec = _make_spec(capabilities=["scheduled-jobs"])
    write_openclaw_bundle(tmp_path, spec)

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text())

    assert "jobs" in commands["commands"]
    assert commands["commands"]["jobs"] != ""


def test_openclaw_commands_json_payload_backend_has_payload_migrate(tmp_path):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "payload",
        "database": "postgres",
    })
    write_openclaw_bundle(tmp_path, spec)

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text())

    assert commands["commands"].get("db_migrate") == "npm run db:migrate"


def test_openclaw_commands_json_python_stack(tmp_path):
    spec = _make_spec(stack={
        "frontend": "",
        "backend": "django",
        "database": "postgres",
    })
    write_openclaw_bundle(tmp_path, spec)

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text())

    assert "pytest" in commands["commands"]["test"]
    assert "ruff" in commands["commands"]["lint"]
    assert "manage.py" in commands["commands"]["dev"]
    assert commands["validation"]["ecosystem"] == "python"
    assert commands["validation"]["test_runner"] == "pytest"


def test_openclaw_commands_json_go_stack(tmp_path):
    spec = _make_spec(stack={
        "frontend": "",
        "backend": "gin",
        "database": "postgres",
    })
    write_openclaw_bundle(tmp_path, spec)

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text())

    assert "go test" in commands["commands"]["test"]
    assert "golangci-lint" in commands["commands"]["lint"]
    assert "go build" in commands["commands"]["build"]
    assert commands["validation"]["ecosystem"] == "go"
    assert commands["validation"]["test_runner"] == "go-test"


# -------------------------------------------------------
# OpenClaw bundle — OPENCLAW.md content
# -------------------------------------------------------


def test_openclaw_md_contains_project_name(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    content = (tmp_path / ".openclaw" / "OPENCLAW.md").read_text()
    assert "Test Project" in content
    assert "execution package" in content.lower()
    assert "spec.json" in content


def test_openclaw_md_contains_execution_model(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    content = (tmp_path / ".openclaw" / "OPENCLAW.md").read_text()
    assert "execution-plan.json" in content
    assert "docs/stories/" in content
    assert "progress.txt" in content


# -------------------------------------------------------
# OpenClaw bundle — repo-contract.json
# -------------------------------------------------------


def test_openclaw_repo_contract_has_expected_paths(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    contract = json.loads((tmp_path / ".openclaw" / "repo-contract.json").read_text())

    assert contract["contract"]["kind"] == "generated-project"
    assert contract["contract"]["primary_spec"] == "spec.json"
    assert contract["contract"]["stories_dir"] == "docs/stories"
    assert contract["contract"]["api_contract"] == ".openclaw/api-contract.json"
    assert contract["contract"]["parallel_plans"]["frontend"] == ".openclaw/frontend-plan.json"
    assert contract["execution_expectations"]["story_driven"] is True
    assert contract["execution_expectations"]["follow_phase_order"] is True
    assert contract["execution_expectations"]["respect_shared_contract"] is True


# -------------------------------------------------------
# OpenClaw bundle — manifest.json details
# -------------------------------------------------------


def test_openclaw_manifest_has_source_of_truth_list(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    manifest = json.loads((tmp_path / ".openclaw" / "manifest.json").read_text())

    assert "spec.json" in manifest["source_of_truth"]
    assert "PRD.md" in manifest["source_of_truth"]
    assert ".openclaw/execution-plan.json" in manifest["source_of_truth"]
    assert ".openclaw/api-contract.json" in manifest["source_of_truth"]
    assert ".openclaw/frontend-plan.json" in manifest["source_of_truth"]
    assert manifest["execution_mode"] == "parallel-contract-loops"


def test_openclaw_manifest_policies_all_true(tmp_path):
    spec = _make_spec()
    write_openclaw_bundle(tmp_path, spec)

    manifest = json.loads((tmp_path / ".openclaw" / "manifest.json").read_text())

    for key, value in manifest["policies"].items():
        assert value is True, f"Policy {key} should be True"


# -------------------------------------------------------
# OpenClaw bundle — edge cases
# -------------------------------------------------------


def test_openclaw_bundle_empty_stories(tmp_path):
    spec = _make_spec(stories=[])
    write_openclaw_bundle(tmp_path, spec)

    plan = json.loads((tmp_path / ".openclaw" / "execution-plan.json").read_text())
    assert plan["stories"] == []
    assert plan["total_stories"] == 0


def test_openclaw_bundle_empty_capabilities(tmp_path):
    spec = _make_spec(capabilities=[])
    write_openclaw_bundle(tmp_path, spec)

    manifest = json.loads((tmp_path / ".openclaw" / "manifest.json").read_text())
    assert manifest["capabilities"] == []


# -------------------------------------------------------
# Codex bundle — migration commands (BUG-003 fix)
# -------------------------------------------------------


def test_codex_migration_commands_payload(tmp_path):
    from initializer.renderers.codex_bundle import _detect_migration_commands

    spec = _make_spec(stack={"frontend": "nextjs", "backend": "payload", "database": "postgres"})
    cmds = _detect_migration_commands(spec)

    assert cmds["run"] == "npm run db:migrate"
    assert cmds["create"] == "npm run db:migrate:create"
    assert cmds["status"] == "npm run db:migrate:status"


def test_codex_migration_commands_django(tmp_path):
    from initializer.renderers.codex_bundle import _detect_migration_commands

    spec = _make_spec(stack={"frontend": "", "backend": "django", "database": "postgres"})
    cmds = _detect_migration_commands(spec)

    assert cmds["run"] == "python manage.py migrate"
    assert cmds["create"] == "python manage.py makemigrations"
    assert cmds["status"] == "python manage.py showmigrations"


def test_codex_migration_commands_node_api(tmp_path):
    from initializer.renderers.codex_bundle import _detect_migration_commands

    spec = _make_spec()
    cmds = _detect_migration_commands(spec)

    assert cmds["run"] == "npm run db:migrate"
    assert cmds["create"] == "npm run db:migrate:create"
    assert cmds["status"] == "npm run db:migrate:status"


# -------------------------------------------------------
# Codex bundle — ralph.sh features
# -------------------------------------------------------


def test_codex_ralph_sh_has_configurable_model(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "CODEX_MODEL" in content
    assert "${CODEX_MODEL:-gpt-5.4}" in content


def test_codex_ralph_sh_has_configurable_effort(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "CODEX_EFFORT" in content
    assert '${CODEX_EFFORT:-medium}' in content
    assert 'model_reasoning_effort="xhigh"' not in content


def test_codex_ralph_sh_exits_nonzero_on_failure(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "exit 1" in content
    assert "FAILURES=0" in content


def test_codex_ralph_sh_uses_separate_migration_commands(tmp_path):
    spec = _make_spec(stack={"frontend": "nextjs", "backend": "payload", "database": "postgres"})
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "npm run db:migrate:create" in content
    assert "npm run db:migrate:status" in content


def test_codex_ralph_sh_uses_installed_codex_cli(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "codex exec" in content
    assert "@openai/codex@latest" not in content


def test_codex_ralph_sh_writes_story_prompt_without_shell_eval(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert 'cat > "$prompt_file" <<PROMPT_EOF' not in content
    assert '$(if [[ -f "$STORIES_DIR/$story_id.md"' not in content
    assert "printf '# Task: Implement %s — %s\\n\\n' \"$unit_id\" \"$unit_title\"" in content
    assert "cat <<'PROMPT_EOF'" in content
    assert 'cat "$STORIES_DIR/$source_story_id.md"' in content


def test_codex_ralph_sh_writes_retry_error_without_shell_eval(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert 'printf \'```\\n%s\\n```\\n\\n\' "$previous_error"' in content
    assert '$previous_error\n\\`\\`\\`' not in content
    assert '$(if [[ -f "$STORIES_DIR/$story_id.md"' not in content


def test_codex_ralph_sh_reads_validation_contract_from_commands_json(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert 'COMMANDS_FILE="$SCRIPT_DIR/.openclaw/commands.json"' in content
    assert 'TEST_CMD=$(jq -r \'.commands.test // ""\' "$COMMANDS_FILE")' in content
    assert 'TEST_RUNNER=$(jq -r \'.validation.test_runner // "none"\' "$COMMANDS_FILE")' in content
    assert 'REQUIRES_REAL_TESTS=$(jq -r \'.validation.requires_real_tests // false\' "$COMMANDS_FILE")' in content
    assert 'validation_policy_contains() {' in content
    assert 'run_validation_command "test" "$TEST_CMD" "Tests" "warn"' in content
    assert 'run_validation_command "test" "$TEST_CMD" "Tests" "contract"' in content
    assert "npm test --if-present" not in content
    assert "npm run lint --if-present" not in content


def test_codex_ralph_sh_orchestrates_parallel_tracks(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert 'SHARED_PLAN_FILE="$SCRIPT_DIR/.openclaw/shared-plan.json"' in content
    assert 'FRONTEND_PLAN_FILE="$SCRIPT_DIR/.openclaw/frontend-plan.json"' in content
    assert 'BACKEND_PLAN_FILE="$SCRIPT_DIR/.openclaw/backend-plan.json"' in content
    assert 'INTEGRATION_PLAN_FILE="$SCRIPT_DIR/.openclaw/integration-plan.json"' in content
    assert 'TRACK="all"' in content
    assert 'run_track_plan "frontend" "$FRONTEND_PLAN_FILE" "$START_FROM" &' in content
    assert 'run_track_plan "backend" "$BACKEND_PLAN_FILE" "$START_FROM" &' in content
    assert 'run_track_plan "integration" "$INTEGRATION_PLAN_FILE" "$START_FROM"' in content
    assert 'API_CONTRACT_FILE="$SCRIPT_DIR/.openclaw/api-contract.json"' in content


def test_codex_ralph_sh_defaults_to_sequential_tracks(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # Default mode is sequential — backend first, then frontend
    assert 'PARALLEL_TRACKS:-false' in content
    # Sequential path runs backend then frontend without &
    seq_idx = content.index('# Sequential mode (default)')
    be_idx = content.index('run_track_plan "backend" "$BACKEND_PLAN_FILE"', seq_idx)
    fe_idx = content.index('run_track_plan "frontend" "$FRONTEND_PLAN_FILE"', be_idx + 1)
    assert fe_idx > be_idx
    # Parallel path is gated behind PARALLEL_TRACKS=true
    assert 'PARALLEL_TRACKS:-false' in content[:content.index('run_track_plan "frontend" "$FRONTEND_PLAN_FILE" "$START_FROM" &')]


def test_codex_ralph_sh_only_requires_npx_outside_dry_run(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert content.count("if ! command -v npx &> /dev/null; then") == 1
    assert content.index('if [[ "$DRY_RUN" == false ]]; then') < content.index("if ! command -v npx &> /dev/null; then")


def test_codex_ralph_sh_quotes_contract_domain_join_for_jq(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert r'contract_domains=$(jq -r ".stories[$index].contract_domains | join(\", \")" "$plan_file")' in content


def test_codex_ralph_sh_short_circuits_bootstrap_when_scaffold_is_ready(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "bootstrap_scaffold_ready() {" in content
    assert '[[ "$source_story_key" == "bootstrap.repository" || "$source_story_key" == "bootstrap.repository-part-2" ]]' in content
    assert 'append_progress "$track" "$unit_id" "$source_story_id" "DONE" "$unit_title (scaffold already satisfied)"' in content
    assert content.index('if bootstrap_scaffold_ready "$plan_file" "$i"; then') < content.index('if run_codex_unit "$track" "$plan_file" "$i"; then')


def test_codex_ralph_sh_bootstrap_preflight_accepts_existing_eslint_config_mjs(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert '[[ -f "$SCRIPT_DIR/eslint.config.mjs" ]]' in content
    assert '[[ -f "$SCRIPT_DIR/eslint.config.js" ]]' in content
    assert '[[ -f "$SCRIPT_DIR/.eslintrc.cjs" ]]' in content
    assert 'case "$owned_file" in' in content
    assert '".eslintrc.js"|"eslint.config.js")' in content


def test_codex_ralph_sh_adds_bootstrap_scaffold_preservation_guardrails_to_prompt(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert 'append_bootstrap_prompt_guardrails "$plan_file" "$index"' in content
    assert "This slice starts from the scaffold already generated by `initializer prepare`" in content
    assert "Treat `eslint.config.mjs`, `eslint.config.js`, and `.eslintrc.*` as equivalent lint config starting points" in content
    assert "Do NOT modify files outside `Owned Files` unless a failing validation points directly to them." in content


def test_codex_ralph_sh_tells_parallel_slices_to_leave_heavy_validation_to_runner(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "Do NOT proactively run repo-wide validation or shared-runtime commands" in content
    assert "`ralph.sh` will run serialized migrations and official validation for this slice after Codex exits" in content
    assert "If the source story lists manual validation outside this slice's owned files or track" in content
    assert "Avoid commands that mutate shared build artifacts or shared runtime state" in content
    assert "Let `ralph.sh` rerun serialized migrations and official validation after you finish" in content


def test_codex_ralph_sh_does_not_delete_next_during_validation(tmp_path):
    """BUG-026 (revised): rm -rf .next during validation caused races.

    Deleting .next while a parallel Codex process writes build artifacts
    triggers clientReferenceManifest corruption.  next build already does
    a full recompile from source, so the deletion is both unnecessary and
    harmful.  The generated ralph.sh must NOT contain rm -rf .next.
    """
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert 'rm -rf "$SCRIPT_DIR/.next"' not in content


def test_codex_ralph_sh_handles_payload_migration_sentinels(tmp_path):
    spec = _make_spec(stack={"frontend": "nextjs", "backend": "payload", "database": "postgres"})
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert 'local is_payload_backend=false' in content
    assert 'output=$(eval "cd \\"$SCRIPT_DIR\\" && $MIGRATION_CMD" 2>&1)' in content
    assert '__SPECWRIGHT_PAYLOAD_MIGRATIONS__:no-pending' in content
    assert '__SPECWRIGHT_PAYLOAD_MIGRATIONS__:dev-push' in content
    assert 'Migrations: SKIP (no pending Payload migrations)' in content
    assert 'Migrations: WARN (skipped Payload migrate: dev-mode push marker found in payload_migrations)' in content


# -------------------------------------------------------
# QUALITY-001: AGENTS.md quality improvements
# -------------------------------------------------------


def test_codex_agents_md_has_migration_directory(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert "src/lib/migrations/" in content


def test_codex_agents_md_uses_separate_migration_commands(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert "npm run db:migrate:create" in content
    assert "npm run db:migrate:status" in content
    # Should NOT use old concatenation pattern
    assert "`npm run db:migrate`:create" not in content


def test_codex_agents_md_forbids_src_pages(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert "src/pages/" in content
    assert "App Router" in content


def test_codex_agents_md_enforces_env_var_names(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert ".env.example" in content
    assert "do NOT rename" in content.lower() or "do not rename" in content.lower()


def test_codex_agents_md_has_security_requirements(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert "Security requirements" in content
    assert "rate limiting" in content.lower()
    assert "minLength: 8" in content
    assert "NEVER hardcode secrets" in content


def test_codex_agents_md_has_typescript_conventions(tmp_path):
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / ".codex" / "AGENTS.md").read_text()
    assert "TypeScript conventions" in content
    assert ".js" in content
    assert "do NOT create" in content


# -------------------------------------------------------
# Session 23: Architectural hardening tests
# -------------------------------------------------------


def test_codex_ralph_sh_enforces_owned_files_after_codex_exec(tmp_path):
    """Owned-files enforcement: after Codex exec, unauthorized file changes are reverted."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # The enforce_owned_files function must exist
    assert "enforce_owned_files()" in content
    # It must be called after Codex succeeds
    assert 'enforce_owned_files "$plan_file" "$i" "$track"' in content
    # It must use git checkout to revert unauthorized files
    assert 'git checkout HEAD --' in content
    # It must compare against owned_files from the plan
    assert "owned_files[]" in content


def test_codex_ralph_sh_has_integration_gate_before_integration_track(tmp_path):
    """Integration gate: full validation runs between parallel tracks and integration."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "Integration Gate: cross-track validation" in content
    assert 'run_track_validation "integration-gate" "full"' in content
    # Gate must block integration on failure
    assert "Integration gate FAILED" in content
    assert "Integration gate PASSED" in content
    # Gate must appear before integration track in the 'all' orchestration block
    # (not the individual --track integration selector)
    gate_pos = content.index("Integration Gate")
    # Find the integration run that comes after the gate
    integration_pos = content.index('run_track_plan "integration"', gate_pos)
    assert integration_pos > gate_pos


def test_codex_ralph_sh_extracts_error_loci_for_retries(tmp_path):
    """Locus extraction: validation errors include file:line information."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # extract_error_loci function must exist
    assert "extract_error_loci()" in content
    # Retry prompt must include structured loci
    assert "Error Locations" in content
    assert "start here" in content
    # append_validation_error must call extract_error_loci
    assert "loci=$(extract_error_loci" in content


def test_codex_ralph_sh_extract_error_loci_filters_node_modules(tmp_path):
    """ARCH-003-REFINE: error loci extraction must filter out node_modules paths."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "grep -v node_modules" in content


def test_codex_ralph_sh_initializes_git_repo_for_owned_files(tmp_path):
    """BUG-028: generated project must have git init so enforce_owned_files works."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "git_init_scaffold()" in content
    assert "git init" in content
    assert "git commit" in content
    assert '"scaffold"' in content


def test_codex_ralph_sh_commits_after_each_successful_slice(tmp_path):
    """BUG-028: each successful slice is committed so next git diff is scoped."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "git add -A" in content
    assert "slice: $unit_id" in content
    assert 'acquire_lock "git"' in content


def test_codex_ralph_sh_extract_error_loci_filters_next_paths(tmp_path):
    """BUG-031: error loci extraction must filter out .next/ build artifact paths."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # Both grep pipelines in extract_error_loci must filter .next paths
    assert "grep -v '\\.next'" in content


def test_codex_ralph_sh_skips_typecheck_on_build_failure(tmp_path):
    """BUG-032: typecheck must be gated on build success to avoid phantom TS6053."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # Both partial and full validation modes must gate typecheck on VALIDATION_OK
    assert 'if [[ "$VALIDATION_OK" == true ]]; then' in content
    # Typecheck must appear inside the conditional, not unconditionally
    idx_build = content.index('"Build" "block"')
    idx_gate = content.index('if [[ "$VALIDATION_OK" == true ]]; then', idx_build)
    idx_typecheck = content.index('"Typecheck" "block"', idx_build)
    assert idx_gate < idx_typecheck


# -------------------------------------------------------
# Velocity & token optimizations
# -------------------------------------------------------


def test_codex_ralph_sh_removes_tsbuildinfo_before_typecheck(tmp_path):
    """BUG-037: stale tsconfig.tsbuildinfo can reference .next/types/ entries
    from a previous build, causing TS6053 on typecheck. Must rm -f before tsc."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # Every typecheck invocation must be preceded by rm -f tsconfig.tsbuildinfo
    idx = 0
    while True:
        try:
            idx_tc = content.index('"Typecheck"', idx)
        except ValueError:
            break
        # Look backwards for rm -f tsconfig.tsbuildinfo within preceding 600 chars
        # (BUG-037b added .next/types guard + comments that widen the gap)
        preceding = content[max(0, idx_tc - 600):idx_tc]
        assert "rm -f tsconfig.tsbuildinfo" in preceding, (
            f"Typecheck at offset {idx_tc} is not preceded by rm -f tsconfig.tsbuildinfo"
        )
        idx = idx_tc + 1


def test_codex_ralph_sh_retry_sleep_is_one_second(tmp_path):
    """Retry backoff should be 1s, not 5s."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # Find retry block context (after "Retry $((attempt")
    idx_retry = content.index("Retry $((attempt")
    # sleep 1 should be near the retry block, not sleep 5
    sleep_region = content[idx_retry:idx_retry + 200]
    assert "sleep 1" in sleep_region
    assert "sleep 5" not in sleep_region


def test_codex_ralph_sh_retry_effort_downshift(tmp_path):
    """Retries should use CODEX_RETRY_EFFORT (default low) for faster/cheaper retries."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert 'CODEX_RETRY_EFFORT="${CODEX_RETRY_EFFORT:-low}"' in content
    # The retry codex exec should use CODEX_RETRY_EFFORT, not CODEX_EFFORT
    idx_retry_func = content.index("run_codex_retry_unit()")
    retry_section = content[idx_retry_func:idx_retry_func + 3000]
    assert "CODEX_RETRY_EFFORT" in retry_section


def test_codex_ralph_sh_error_output_capped(tmp_path):
    """Validation error output should be capped to avoid bloating retry prompts."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "tail -10 | head -c 1500" in content


def test_codex_ralph_sh_retry_does_not_reembed_story(tmp_path):
    """Retry prompt should reference story file, not re-embed it."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    idx_retry_func = content.index("run_codex_retry_unit()")
    retry_section = content[idx_retry_func:idx_retry_func + 3000]
    assert "unchanged from first attempt" in retry_section
    # Should NOT cat the story file in retry
    assert 'cat "$STORIES_DIR/$source_story_id.md"' not in retry_section


def test_codex_ralph_sh_partial_validation_unlocked_typecheck_lint_test(tmp_path):
    """Partial validation should only lock around build, not typecheck/lint/test."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # Find the SECOND partial validation block (inline in main loop, not run_track_validation)
    first = content.index('if [[ "$validation_mode" == "partial" ]]; then')
    idx_partial = content.index('if [[ "$validation_mode" == "partial" ]]; then', first + 1)
    partial_block = content[idx_partial:idx_partial + 2000]
    # Build should be inside lock
    assert 'acquire_lock "validation"' in partial_block
    assert "release_lock" in partial_block
    # Typecheck/lint/test should be OUTSIDE the lock (after release_lock)
    idx_release = partial_block.index("release_lock")
    after_release = partial_block[idx_release:]
    assert '"Typecheck"' in after_release
    assert '"Lint"' in after_release
    assert '"Tests"' in after_release


def test_codex_ralph_sh_partial_validation_scoped_lint(tmp_path):
    """Partial validation should lint only owned files via npx eslint."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "npx eslint $owned_lint_files" in content


def test_codex_ralph_sh_enforce_owned_files_allows_package_lock(tmp_path):
    """BUG-034: package-lock.json must be always-allowed in enforce_owned_files.
    BUG-039: progress.txt and .openclaw/progress must also be always-allowed."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # enforce_owned_files should have an always_allowed list containing
    # package-lock.json (BUG-034), progress.txt and .openclaw/progress (BUG-039)
    assert "package-lock.json" in content
    assert "progress.txt" in content
    assert ".openclaw/progress" in content


def test_codex_ralph_sh_no_trap_cleanup_return(tmp_path):
    """BUG-035: trap _cleanup RETURN causes unbound variable when scope leaks."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # Must NOT use trap _cleanup RETURN pattern (causes unbound variable with set -u)
    assert "trap _cleanup RETURN" not in content
    # Must still clean up temp files (rm -f before each return)
    assert 'rm -f "$prompt_file" "$output_file"' in content


def test_codex_ralph_sh_auto_skip_empty_owned_files(tmp_path):
    """BUG-036: Slices with owned_files: [] should be auto-skipped, not sent to Codex."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # run_track_plan should check owned_files length and skip when 0
    assert 'owned_count=$(jq -r ".stories[$i].owned_files | length"' in content
    assert "no owned files — auto-skip" in content


def test_codex_ralph_sh_ensures_node_modules(tmp_path):
    """OPT: ralph.sh auto-installs deps if node_modules is missing."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert "ensure_node_modules" in content
    assert "node_modules" in content
    assert "npm ci" in content
    assert "npm install" in content


def test_codex_ralph_sh_recommits_scaffold_on_existing_git(tmp_path):
    """OPT: git_init_scaffold commits scaffold updates when .git already exists."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    assert '"scaffold update"' in content
    assert "git diff --quiet HEAD" in content
    assert "git ls-files --others --exclude-standard" in content


def test_codex_ralph_sh_starts_postgres_before_integration_gate(tmp_path):
    """IN-ST-013: Docker Postgres must start before integration gate validation."""
    spec = _make_spec()
    write_codex_bundle(tmp_path, spec)

    content = (tmp_path / "ralph.sh").read_text()
    # Postgres startup must appear before integration gate validation
    pg_idx = content.find("docker compose up -d postgres")
    gate_idx = content.find('run_track_validation "integration-gate"')
    assert pg_idx != -1, "ralph.sh must start Postgres before integration gate"
    assert gate_idx != -1, "ralph.sh must have integration gate validation"
    assert pg_idx < gate_idx, "Postgres startup must come before integration gate validation"
    assert "pg_isready" in content
