import json
from unittest.mock import patch

from initializer.flow.prepare_project import _detect_commands, run_prepare_project
from initializer.renderers.scaffold_engine import write_scaffold


def _make_spec(**overrides) -> dict:
    spec = {
        "answers": {
            "project_name": "Prepared Project",
            "project_slug": "prepared-project",
            "summary": "Test project for prepare flow.",
            "surface": "admin_plus_public_site",
            "deploy_target": "docker",
        },
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "capabilities": ["cms", "public-site"],
        "features": ["authentication"],
        "architecture": {
            "components": [
                {"name": "frontend", "technology": "nextjs"},
                {"name": "api", "technology": "payload"},
                {"name": "database", "technology": "postgres"},
            ],
            "decisions": ["Use Payload for content workflows."],
        },
        "stories": [
            {
                "id": "ST-001",
                "story_key": "bootstrap.repository",
                "title": "Initialize repository",
            }
        ],
    }
    spec.update(overrides)
    return spec


def _write_project_files(project_dir, spec: dict) -> None:
    (project_dir / "docs" / "stories").mkdir(parents=True)
    (project_dir / "spec.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    for filename in ("PRD.md", "architecture.md", "decisions.md", "progress.txt"):
        (project_dir / filename).write_text("placeholder\n", encoding="utf-8")
    for story in spec.get("stories", []):
        story_id = story.get("id")
        if story_id:
            (project_dir / "docs" / "stories" / f"{story_id}.md").write_text(
                f"# {story_id}\n",
                encoding="utf-8",
            )


def test_detect_commands_returns_validation_contract_for_package_json(tmp_path):
    spec = _make_spec()
    _write_project_files(tmp_path, spec)
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test": "vitest run",
                    "lint": "eslint .",
                    "build": "next build",
                    "dev": "next dev",
                },
                "devDependencies": {
                    "vitest": "^3.1.1",
                },
            }
        ),
        encoding="utf-8",
    )

    result = _detect_commands(tmp_path, spec)

    assert result["commands"]["test"] == "npm test"
    assert result["commands"]["lint"] == "npm run lint"
    assert result["commands"]["build"] == "npm run build"
    assert result["commands"]["dev"] == "npm run dev"
    assert result["commands"]["typecheck"] == ""
    assert result["commands"]["db_migrate"] == "npm run db:migrate"
    assert result["validation"] == {
        "ecosystem": "node",
        "test_runner": "vitest",
        "requires_real_tests": True,
        "block_on": ["test", "build", "typecheck"],
        "warn_on": ["lint"],
    }
    assert "package.json" in result["notes"][0]


def test_detect_commands_flags_placeholder_test_script_as_non_reliable(tmp_path):
    spec = _make_spec()
    _write_project_files(tmp_path, spec)
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test": "echo TODO",
                    "lint": "eslint .",
                    "build": "next build",
                    "dev": "next dev",
                }
            }
        ),
        encoding="utf-8",
    )

    result = _detect_commands(tmp_path, spec)

    assert result["commands"]["test"] == "npm test"
    assert result["validation"]["test_runner"] == "none"
    assert any("no-op" in note.lower() for note in result["notes"])


def test_detect_commands_python_stack_uses_pytest(tmp_path):
    spec = _make_spec(
        stack={"frontend": "", "backend": "django", "database": "postgres"},
    )
    _write_project_files(tmp_path, spec)
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.pytest.ini_options]
testpaths = ["tests"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = _detect_commands(tmp_path, spec)

    assert result["commands"]["test"] == "pytest"
    assert result["commands"]["lint"] == "ruff check ."
    assert result["commands"]["build"] == "python manage.py check --deploy"
    assert result["validation"]["ecosystem"] == "python"
    assert result["validation"]["test_runner"] == "pytest"


def test_detect_commands_go_stack_uses_go_test(tmp_path):
    spec = _make_spec(
        stack={"frontend": "", "backend": "gin", "database": "postgres"},
    )
    _write_project_files(tmp_path, spec)
    (tmp_path / "go.mod").write_text(
        "module example.com/prepared-project\n\ngo 1.22\n",
        encoding="utf-8",
    )

    result = _detect_commands(tmp_path, spec)

    assert result["commands"]["test"] == "go test ./..."
    assert result["commands"]["lint"] == "golangci-lint run"
    assert result["commands"]["build"] == "go build ./..."
    assert result["validation"]["ecosystem"] == "go"
    assert result["validation"]["test_runner"] == "go-test"


def test_prepare_preserves_detected_commands_after_bundle_regeneration(tmp_path):
    spec = _make_spec()
    _write_project_files(tmp_path, spec)
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "test": "vitest run",
                    "lint": "eslint .",
                    "build": "next build",
                    "dev": "next dev",
                },
                "devDependencies": {
                    "vitest": "^3.1.1",
                },
            }
        ),
        encoding="utf-8",
    )

    def fake_write_openclaw_bundle(output_dir, _spec):
        openclaw_dir = output_dir / ".openclaw"
        openclaw_dir.mkdir(parents=True, exist_ok=True)
        (openclaw_dir / "commands.json").write_text(
            json.dumps(
                {
                    "commands": {
                        "test": "stale-command",
                        "lint": "stale-command",
                        "build": "stale-command",
                        "dev": "stale-command",
                    },
                    "notes": ["stale data"],
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

    with patch(
        "initializer.flow.prepare_project.write_openclaw_bundle",
        side_effect=fake_write_openclaw_bundle,
    ), patch(
        "initializer.flow.prepare_project.write_codex_bundle",
    ), patch(
        "initializer.flow.prepare_project._print_execution_preview",
    ):
        exit_code = run_prepare_project(str(tmp_path))

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert commands["commands"]["test"] == "npm test"
    assert commands["commands"]["lint"] == "npm run lint"
    assert commands["commands"]["build"] == "npm run build"
    assert commands["commands"]["dev"] == "npm run dev"
    assert commands["validation"]["test_runner"] == "vitest"
    assert commands["validation"]["requires_real_tests"] is True
    assert "package.json" in commands["notes"][0]


def test_prepare_re_derives_stale_execution_metadata(tmp_path):
    """BUG-040: prepare must re-derive execution metadata so fixes in
    story_engine apply even to specs generated before those fixes existed."""
    spec = _make_spec(
        stories=[
            {
                "id": "ST-001",
                "story_key": "bootstrap.repository",
                "title": "Initialize repository",
                "expected_files": [],
            },
            {
                "id": "ST-010",
                "story_key": "product.public-site-rendering",
                "title": "Public site rendering",
                "expected_files": [
                    "src/app/(public)/page.tsx",
                    "src/app/(public)/layout.tsx",
                    "src/components/PublicNav.tsx",
                ],
                # Stale execution metadata — missing frontend_files
                "execution": {
                    "tracks": ["frontend"],
                    "primary_track": "frontend",
                    "parallelizable": False,
                    "contract_domains": [],
                    "frontend_files": [],
                    "backend_files": [],
                    "shared_files": [],
                    "integration_files": [],
                    "modes": {"frontend": "full"},
                },
            },
        ],
    )
    _write_project_files(tmp_path, spec)
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"build": "next build", "dev": "next dev"}}),
        encoding="utf-8",
    )

    with patch("initializer.flow.prepare_project._print_execution_preview"):
        exit_code = run_prepare_project(str(tmp_path))

    assert exit_code == 0

    plan = json.loads(
        (tmp_path / ".openclaw" / "execution-plan.json").read_text(encoding="utf-8")
    )
    parallel = plan.get("parallel_execution", {})
    fe_plan = parallel.get("plans", {}).get("frontend", {})
    fe_stories = fe_plan.get("stories", [])

    # Find the public-site-rendering unit
    pub_unit = None
    for unit in fe_stories:
        if unit.get("source_story_id") == "ST-010":
            pub_unit = unit
            break

    assert pub_unit is not None, "ST-010 frontend unit not found in plan"
    owned = pub_unit.get("owned_files", [])
    # After re-derivation, frontend_files should contain the expected_files
    # including BUG-038 fix: (app)/page.tsx must be owned by public-site story
    assert "src/app/(public)/page.tsx" in owned
    assert "src/app/(app)/page.tsx" in owned


def test_prepare_node_pipeline_contract_stays_aligned_with_ralph(tmp_path):
    spec = _make_spec(
        stack={"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        capabilities=["scheduled-jobs"],
    )
    _write_project_files(tmp_path, spec)
    write_scaffold(tmp_path, spec)

    with patch("initializer.flow.prepare_project._print_execution_preview"):
        exit_code = run_prepare_project(str(tmp_path))

    commands = json.loads((tmp_path / ".openclaw" / "commands.json").read_text(encoding="utf-8"))
    ralph = (tmp_path / "ralph.sh").read_text(encoding="utf-8")

    assert exit_code == 0
    assert commands["commands"]["test"] == "npm test"
    assert commands["commands"]["build"] == "npm run build"
    assert commands["commands"]["typecheck"] == "npm run typecheck"
    assert commands["validation"]["test_runner"] == "vitest"
    assert 'COMMANDS_FILE="$SCRIPT_DIR/.openclaw/commands.json"' in ralph
    assert 'API_CONTRACT_FILE="$SCRIPT_DIR/.openclaw/api-contract.json"' in ralph
    assert 'TEST_CMD=$(jq -r \'.commands.test // ""\' "$COMMANDS_FILE")' in ralph
    assert 'run_validation_command "test" "$TEST_CMD" "Tests" "warn"' in ralph
    assert 'run_track_plan "frontend" "$FRONTEND_PLAN_FILE" "$START_FROM" &' in ralph
    assert "npm test --if-present" not in ralph
    assert "npm run lint --if-present" not in ralph
