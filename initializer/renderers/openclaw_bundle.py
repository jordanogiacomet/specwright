"""OpenClaw Bundle Generator.

Generates a rich .openclaw/ bundle inside the output directory that
gives any execution agent (Codex, Claude Code, OpenClaw, Ralph loop)
everything it needs to start implementing story-by-story without
external context.

The bundle includes:
- AGENTS.md — project-specific instructions for the executor
- OPENCLAW.md — handoff document for OpenClaw-specific loops
- manifest.json — machine-readable project metadata
- repo-contract.json — contract rules for the generated package
- commands.json — validation commands derived from the project stack
- execution-plan.json — ordered story list with phases and dependencies
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _get_decision_signals(spec: dict[str, Any]) -> dict[str, Any]:
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


# -------------------------------------------------------------------
# Execution plan
# -------------------------------------------------------------------

def _build_execution_plan(spec: dict[str, Any]) -> dict[str, Any]:
    """Build an ordered execution plan from stories.

    Groups stories into phases:
    1. bootstrap — repository, database, backend, frontend setup
    2. features — authentication, roles, media-library, etc.
    3. product — product-shape stories (dashboard, portal, backoffice)
    4. domain — core work feature stories (deadlines, task-assignment, etc.)
    5. automation — scheduled jobs, background workers
    6. operations — monitoring, backups, operational stories
    """
    stories = spec.get("stories", [])

    phases = {
        "bootstrap": [],
        "features": [],
        "product": [],
        "domain": [],
        "automation": [],
        "operations": [],
    }

    for story in stories:
        if not isinstance(story, dict):
            continue

        story_id = story.get("id", "")
        story_key = story.get("story_key", "")
        title = story.get("title", "")

        entry = {
            "id": story_id,
            "title": title,
            "status": "pending",
        }
        if story_key:
            entry["story_key"] = story_key

        depends_on = story.get("depends_on")
        if isinstance(depends_on, list) and depends_on:
            entry["depends_on"] = depends_on

        if story_key.startswith("bootstrap."):
            phases["bootstrap"].append(entry)
        elif story_key.startswith("feature."):
            phases["features"].append(entry)
        elif story_key.startswith("product."):
            if "automation" in story_key or "scheduled" in story_key:
                phases["automation"].append(entry)
            else:
                if any(
                    kw in story_key
                    for kw in (
                        "deadlines", "progress", "task-assignment",
                        "reminders", "report", "approvals", "team-visibility",
                    )
                ):
                    phases["domain"].append(entry)
                else:
                    phases["product"].append(entry)
        elif story_id in ("ST-900", "ST-901") or "monitoring" in title.lower() or "backup" in title.lower():
            phases["operations"].append(entry)
        else:
            lower_title = title.lower()
            if any(kw in lower_title for kw in ("locale", "i18n", "translation")):
                phases["features"].append(entry)
            elif any(kw in lower_title for kw in ("cms", "content model")):
                phases["features"].append(entry)
            elif any(kw in lower_title for kw in ("cdn", "public site")):
                phases["features"].append(entry)
            elif any(kw in lower_title for kw in ("worker", "scheduler", "automation", "scheduled")):
                phases["automation"].append(entry)
            else:
                phases["features"].append(entry)

    # ---------------------------------------------------------------
    # Sort stories within each phase by dependency order
    # Stories that depend on feature.* come after stories that only
    # depend on bootstrap.* within the features phase.
    # ---------------------------------------------------------------

    def _dependency_depth(entry: dict[str, Any]) -> int:
        """Compute a sorting key based on dependency depth.

        Stories with no depends_on or only bootstrap.* deps sort first (0).
        Stories depending on feature.* sort by their dependency chain depth.
        """
        deps = entry.get("depends_on", [])
        if not deps:
            return 0

        depth = 0
        for dep in deps:
            if dep.startswith("feature."):
                # Find which feature it depends on and check that feature's deps
                dep_depth = 1
                # Look up the dependent story's own deps
                for other in phases.get("features", []):
                    other_key = other.get("story_key", "")
                    if other_key == dep:
                        other_deps = other.get("depends_on", [])
                        if any(d.startswith("feature.") for d in other_deps):
                            dep_depth = 2
                        break
                depth = max(depth, dep_depth)
            elif dep.startswith("bootstrap."):
                depth = max(depth, 0)
            else:
                depth = max(depth, 1)

        return depth

    for phase_name in phases:
        phases[phase_name].sort(key=_dependency_depth)

    ordered: list[dict[str, Any]] = []
    order = 1

    for phase_name in ("bootstrap", "features", "product", "domain", "automation", "operations"):
        phase_stories = phases[phase_name]
        for entry in phase_stories:
            entry["order"] = order
            entry["phase"] = phase_name
            ordered.append(entry)
            order += 1

    return {
        "total_stories": len(ordered),
        "phases": list(phases.keys()),
        "phase_order": [
            {"phase": "bootstrap", "description": "Project setup and infrastructure", "count": len(phases["bootstrap"])},
            {"phase": "features", "description": "Core feature implementation", "count": len(phases["features"])},
            {"phase": "product", "description": "Product shell and navigation", "count": len(phases["product"])},
            {"phase": "domain", "description": "Domain-specific work features", "count": len(phases["domain"])},
            {"phase": "automation", "description": "Background jobs and automation", "count": len(phases["automation"])},
            {"phase": "operations", "description": "Monitoring, backups, operational setup", "count": len(phases["operations"])},
        ],
        "stories": ordered,
    }


# -------------------------------------------------------------------
# Commands — derived from the project stack
# -------------------------------------------------------------------

# Node.js ecosystem stacks
_NODE_FRONTENDS = {"nextjs", "next.js", "next", "react", "vue", "nuxt", "svelte", "sveltekit", "astro", "remix"}
_NODE_BACKENDS = {"payload", "payload-cms", "node-api", "express", "fastify", "hono", "nestjs", "adonis", "strapi"}

# Python ecosystem stacks
_PYTHON_BACKENDS = {"django", "flask", "fastapi", "litestar"}

# Go ecosystem stacks
_GO_BACKENDS = {"go", "golang", "gin", "echo", "fiber"}


def _detect_ecosystem(stack: dict[str, Any]) -> str:
    """Detect the primary ecosystem from the stack dict.

    Returns one of: 'node', 'python', 'go', 'unknown'.
    """
    frontend = (stack.get("frontend") or "").lower().strip()
    backend = (stack.get("backend") or "").lower().strip()

    if backend in _PYTHON_BACKENDS or frontend in ("django",):
        return "python"

    if backend in _GO_BACKENDS:
        return "go"

    if frontend in _NODE_FRONTENDS or backend in _NODE_BACKENDS:
        return "node"

    # Fallback: if there's any frontend listed, assume node
    if frontend:
        return "node"

    return "unknown"


def _node_commands(stack: dict[str, Any], capabilities: list[str], deploy_target: str) -> dict[str, Any]:
    """Generate commands for a Node.js ecosystem project."""
    database = (stack.get("database") or "").lower().strip()
    backend = (stack.get("backend") or "").lower().strip()
    is_payload = backend in ("payload", "payload-cms")

    commands: dict[str, str] = {
        "dev": "npm run dev",
        "build": "npm run build",
        "lint": "npm run lint",
        "test": "npm test",
        "typecheck": "npx tsc --noEmit",
    }

    setup: dict[str, str] = {
        "install": "npm install",
        "env": "test -f .env.local || cp .env.example .env.local",
    }

    if database == "postgres" and deploy_target in ("docker", "docker_and_k8s_later"):
        commands["db_start"] = "docker compose up -d postgres"
        commands["db_stop"] = "docker compose down"
        setup["db_start"] = "docker compose up -d postgres"
    elif database == "postgres":
        setup["db_start"] = "# Start PostgreSQL manually or via your cloud provider"
    elif database in ("mysql", "mariadb") and deploy_target in ("docker", "docker_and_k8s_later"):
        commands["db_start"] = f"docker compose up -d {database}"
        commands["db_stop"] = "docker compose down"
        setup["db_start"] = f"docker compose up -d {database}"
    elif database == "mongodb" and deploy_target in ("docker", "docker_and_k8s_later"):
        commands["db_start"] = "docker compose up -d mongo"
        commands["db_stop"] = "docker compose down"
        setup["db_start"] = "docker compose up -d mongo"
    elif database == "sqlite":
        # No separate service needed
        pass
    elif database:
        setup["db_start"] = f"# Start {database} manually"

    if is_payload:
        commands["db_migrate"] = "npx payload migrate"
        commands["db_seed"] = "npx payload seed"
        setup["db_migrate"] = "npx payload migrate"
    elif database:
        commands["db_migrate"] = "npm run db:migrate"
        setup["db_migrate"] = "npm run db:migrate"

    if "scheduled-jobs" in capabilities:
        commands["jobs"] = "npm run jobs"

    return {"commands": commands, "setup": setup}


def _python_commands(stack: dict[str, Any], capabilities: list[str], deploy_target: str) -> dict[str, Any]:
    """Generate commands for a Python ecosystem project."""
    database = (stack.get("database") or "").lower().strip()
    backend = (stack.get("backend") or "").lower().strip()

    commands: dict[str, str] = {
        "dev": "python manage.py runserver" if backend == "django" else "uvicorn app.main:app --reload",
        "build": "python -m py_compile app/" if backend != "django" else "python manage.py check --deploy",
        "lint": "ruff check .",
        "test": "pytest",
        "typecheck": "mypy .",
    }

    setup: dict[str, str] = {
        "install": "pip install -r requirements.txt",
        "env": "cp .env.example .env",
    }

    if database == "postgres" and deploy_target in ("docker", "docker_and_k8s_later"):
        commands["db_start"] = "docker compose up -d postgres"
        commands["db_stop"] = "docker compose down"
        setup["db_start"] = "docker compose up -d postgres"
    elif database and database != "sqlite":
        setup["db_start"] = f"# Start {database} manually"

    if backend == "django":
        commands["db_migrate"] = "python manage.py migrate"
        setup["db_migrate"] = "python manage.py migrate"
    elif database and database != "sqlite":
        commands["db_migrate"] = "alembic upgrade head"
        setup["db_migrate"] = "alembic upgrade head"

    if "scheduled-jobs" in capabilities:
        if backend == "django":
            commands["jobs"] = "python manage.py run_jobs"
        else:
            commands["jobs"] = "python -m app.jobs"

    return {"commands": commands, "setup": setup}


def _go_commands(stack: dict[str, Any], capabilities: list[str], deploy_target: str) -> dict[str, Any]:
    """Generate commands for a Go ecosystem project."""
    database = (stack.get("database") or "").lower().strip()

    commands: dict[str, str] = {
        "dev": "go run ./cmd/server",
        "build": "go build ./...",
        "lint": "golangci-lint run",
        "test": "go test ./...",
        "typecheck": "go vet ./...",
    }

    setup: dict[str, str] = {
        "install": "go mod download",
        "env": "cp .env.example .env",
    }

    if database == "postgres" and deploy_target in ("docker", "docker_and_k8s_later"):
        commands["db_start"] = "docker compose up -d postgres"
        commands["db_stop"] = "docker compose down"
        setup["db_start"] = "docker compose up -d postgres"
    elif database and database != "sqlite":
        setup["db_start"] = f"# Start {database} manually"

    if database and database != "sqlite":
        commands["db_migrate"] = "go run ./cmd/migrate up"
        setup["db_migrate"] = "go run ./cmd/migrate up"

    if "scheduled-jobs" in capabilities:
        commands["jobs"] = "go run ./cmd/worker"

    return {"commands": commands, "setup": setup}


def _fallback_commands() -> dict[str, Any]:
    """Generate placeholder commands when the ecosystem is unknown."""
    return {
        "commands": {
            "dev": "# Configure dev command for your stack",
            "build": "# Configure build command for your stack",
            "lint": "# Configure lint command for your stack",
            "test": "# Configure test command for your stack",
        },
        "setup": {
            "install": "# Configure install command for your stack",
            "env": "cp .env.example .env",
        },
    }


def generate_commands(spec: dict[str, Any]) -> dict[str, Any]:
    """Generate commands dict from the project spec.

    Returns a dict with:
    - commands: validation and dev commands the executor should use
    - setup: one-time setup commands to bootstrap the project
    - notes: guidance for the executor
    """
    stack = spec.get("stack", {})
    answers = spec.get("answers", {})
    capabilities = spec.get("capabilities", [])
    deploy_target = answers.get("deploy_target", "docker")

    ecosystem = _detect_ecosystem(stack)

    if ecosystem == "node":
        result = _node_commands(stack, capabilities, deploy_target)
    elif ecosystem == "python":
        result = _python_commands(stack, capabilities, deploy_target)
    elif ecosystem == "go":
        result = _go_commands(stack, capabilities, deploy_target)
    else:
        result = _fallback_commands()

    notes: list[str] = [
        "These commands are pre-populated from the project stack. "
        "Update them if the actual project setup differs.",
        "Run 'build' and 'lint' after every story. "
        "Run 'test' when test files exist.",
        "Run 'typecheck' periodically to catch type errors early.",
    ]

    if "scheduled-jobs" in capabilities:
        notes.append(
            "The 'jobs' command starts the background job runner. "
            "Configure it after implementing the automation story."
        )

    result["notes"] = notes
    return result


# -------------------------------------------------------------------
# AGENTS.md
# -------------------------------------------------------------------

def _build_agents_md(spec: dict[str, Any]) -> str:
    """Build a project-specific AGENTS.md."""
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    signals = _get_decision_signals(spec)

    project_name = answers.get("project_name", "Generated Project")
    summary = answers.get("summary", "")
    surface = answers.get("surface", "unknown")
    app_shape = signals.get("app_shape", "unknown")
    primary_audience = signals.get("primary_audience", "unknown")
    core_work_features = signals.get("core_work_features", [])
    if not isinstance(core_work_features, list):
        core_work_features = []

    cap_text = ", ".join(capabilities) if capabilities else "none"
    feat_text = ", ".join(features) if features else "none"
    cwf_text = ", ".join(core_work_features) if core_work_features else "none specified"

    # Build the stack line dynamically
    stack_parts = []
    for key in ("frontend", "backend", "database"):
        val = stack.get(key)
        if val:
            stack_parts.append(val)
    stack_text = " + ".join(stack_parts) if stack_parts else "unknown"

    return f"""# AGENTS.md

You are an execution agent working on **{project_name}**.

## What this project is

{summary}

- **App shape**: {app_shape}
- **Primary audience**: {primary_audience}
- **Surface**: {surface}
- **Stack**: {stack_text}
- **Capabilities**: {cap_text}
- **Features**: {feat_text}
- **Core work features**: {cwf_text}

## Read order

Before changing code, read these files in this order:

1. `spec.json` — structured source of truth
2. `PRD.md` — enriched product requirements
3. `decisions.md` — stable architectural decisions
4. `progress.txt` — append-only execution log
5. `.openclaw/execution-plan.json` — ordered story list with phases
6. `docs/stories/` — individual story files
7. project source files

## Execution rules

- Work **one story at a time**, following the order in `execution-plan.json`
- Start with the **bootstrap phase** — these set up the project structure
- Do not skip ahead to domain stories before features are in place
- Do not silently change architecture or product scope
- Prefer minimal, targeted patches over large rewrites
- Validate after each story when possible
- Append progress to `progress.txt` after meaningful work

## What NOT to do

- Do not add a public-facing site unless `public-site` is in capabilities
- Do not add CMS features unless `cms` is in capabilities
- Do not add i18n unless `i18n` is in capabilities
- Do not redesign the architecture — it was derived from the spec
- Do not merge stories or skip validation steps

## Contract

- `spec.json` is the structured source of truth
- `decisions.md` contains stable decisions unless explicitly superseded
- `progress.txt` is append-only
- Stories under `docs/stories/` define execution slices
- Implementation must follow the generated architecture

## Validation

When relevant, validate in this order:

1. Targeted test for the current story
2. Full test suite
3. Lint
4. Build

If a command is unavailable, record that in `progress.txt`.

## Completion standard

A story is complete when:

- Code is changed and working
- Validation was attempted
- Results were recorded in `progress.txt`
- The story requirements are satisfied
"""


# -------------------------------------------------------------------
# OPENCLAW.md
# -------------------------------------------------------------------

def _build_openclaw_md(spec: dict[str, Any]) -> str:
    """Build a project-specific OPENCLAW.md."""
    answers = spec.get("answers", {})
    project_name = answers.get("project_name", "Generated Project")

    return f"""# OPENCLAW.md

This is the execution package for **{project_name}**.

## Purpose

OpenClaw should treat this folder as a prepared execution package.
All planning is done — the agent's job is to implement.

## Source of truth

- `spec.json` — full project specification
- `PRD.md` — enriched product requirements with intelligence
- `decisions.md` — architectural decisions
- `progress.txt` — execution log
- `.openclaw/execution-plan.json` — ordered implementation plan
- `docs/stories/` — individual story definitions

## Execution model

1. Read `execution-plan.json` to find the next pending story
2. Read the story file in `docs/stories/`
3. Implement the story
4. Validate the work
5. Update `progress.txt`
6. Move to next story

## Constraints

- Do not replace the generated contract with a new architecture
- Do not rewrite unrelated parts of the project
- Do not skip validation when commands are available
- Do not mark work as complete without recording outcomes
- Follow the phase order: bootstrap → features → product → domain → automation → operations
"""


# -------------------------------------------------------------------
# Bundle writer
# -------------------------------------------------------------------

def write_openclaw_bundle(output_dir: Path, spec: dict[str, Any]) -> None:
    """Generate the .openclaw/ bundle with project-specific context."""
    openclaw_dir = output_dir / ".openclaw"
    openclaw_dir.mkdir(parents=True, exist_ok=True)

    project_slug = spec.get("answers", {}).get("project_slug", "generated-project")
    signals = _get_decision_signals(spec)

    # --- AGENTS.md ---
    agents_md = _build_agents_md(spec)
    (openclaw_dir / "AGENTS.md").write_text(agents_md, encoding="utf-8")

    # --- OPENCLAW.md ---
    openclaw_md = _build_openclaw_md(spec)
    (openclaw_dir / "OPENCLAW.md").write_text(openclaw_md, encoding="utf-8")

    # --- execution-plan.json ---
    execution_plan = _build_execution_plan(spec)
    (openclaw_dir / "execution-plan.json").write_text(
        json.dumps(execution_plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- manifest.json ---
    manifest = {
        "project_root_type": "generated-project-package",
        "project_slug": project_slug,
        "app_shape": signals.get("app_shape", "unknown"),
        "primary_audience": signals.get("primary_audience", "unknown"),
        "capabilities": spec.get("capabilities", []),
        "features": spec.get("features", []),
        "source_of_truth": [
            "spec.json",
            "PRD.md",
            "decisions.md",
            "progress.txt",
            "architecture.md",
            "docs/stories",
            ".openclaw/execution-plan.json",
            ".openclaw/AGENTS.md",
        ],
        "execution_mode": "story-by-story",
        "primary_input": "spec.json",
        "policies": {
            "one_story_at_a_time": True,
            "must_validate_before_done": True,
            "append_progress": True,
            "avoid_architecture_drift": True,
            "follow_phase_order": True,
        },
    }
    (openclaw_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- repo-contract.json ---
    repo_contract = {
        "contract": {
            "kind": "generated-project",
            "primary_spec": "spec.json",
            "primary_prd": "PRD.md",
            "primary_architecture": "architecture.md",
            "primary_decisions": "decisions.md",
            "primary_progress_log": "progress.txt",
            "stories_dir": "docs/stories",
            "execution_plan": ".openclaw/execution-plan.json",
        },
        "execution_expectations": {
            "story_driven": True,
            "validate_changes": True,
            "record_progress": True,
            "preserve_generated_scope": True,
            "follow_phase_order": True,
        },
    }
    (openclaw_dir / "repo-contract.json").write_text(
        json.dumps(repo_contract, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- commands.json ---
    commands = generate_commands(spec)
    (openclaw_dir / "commands.json").write_text(
        json.dumps(commands, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )