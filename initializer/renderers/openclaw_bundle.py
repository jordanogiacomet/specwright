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
import re
from pathlib import Path
from typing import Any

from initializer.engine.story_engine import derive_execution_metadata
from initializer.engine.validation_contract import build_validation_bundle, migration_commands


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

_PHASE_PRIORITY = {
    "bootstrap": 0,
    "features": 1,
    "product": 2,
    "domain": 3,
    "automation": 4,
    "operations": 5,
}

_TRACK_ORDER = ("shared", "frontend", "backend", "integration")
_TRACK_LABELS = {
    "shared": "Shared setup",
    "frontend": "Frontend",
    "backend": "Backend",
    "integration": "Integration",
}
_HTTP_CONTRACT_RE = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_./:[\]-]+)"
)


def _ordered_entries(
    entries: dict[str, dict[str, Any]],
    dependency_key: str,
    tie_breaker,
) -> list[dict[str, Any]]:
    completed: set[str] = set()
    ordered: list[dict[str, Any]] = []
    remaining = set(entries.keys())

    while remaining:
        available = [
            entry_id
            for entry_id in remaining
            if all(dep in completed for dep in entries[entry_id].get(dependency_key, []))
        ]

        if not available:
            available = sorted(remaining, key=tie_breaker)

        available.sort(key=tie_breaker)

        for entry_id in available:
            remaining.discard(entry_id)
            completed.add(entry_id)
            ordered.append(entries[entry_id])

    return ordered


def _track_unit_id(track: str, source_story_id: str) -> str:
    prefixes = {
        "shared": "SH",
        "frontend": "FE",
        "backend": "BE",
        "integration": "IN",
    }
    return f"{prefixes[track]}-{source_story_id}"


def _story_execution(story: dict[str, Any]) -> dict[str, Any]:
    execution = story.get("execution", {})
    derived = derive_execution_metadata(story)
    if not isinstance(execution, dict) or not execution.get("tracks"):
        return derived

    merged = dict(execution)
    for field in (
        "tracks",
        "primary_track",
        "parallelizable",
        "contract_domains",
        "frontend_files",
        "backend_files",
        "shared_files",
        "integration_files",
        "modes",
    ):
        if field not in merged:
            merged[field] = derived.get(field)

    return merged


def _story_prompt_rules(track: str, story: dict[str, Any], execution: dict[str, Any]) -> list[str]:
    domains = execution.get("contract_domains", [])
    domain_text = ", ".join(domains) if domains else "the shared contract"

    if track == "shared":
        return [
            "Implement only the shared setup and repo-level scaffolding needed by both loops.",
            "Do not add business logic, API wiring, or production UI beyond the source story.",
            "Keep the workspace ready for frontend and backend loops to proceed independently.",
        ]

    if track == "frontend":
        return [
            "Implement only the frontend-facing slice of the source story.",
            f"Respect `.openclaw/api-contract.json` for {domain_text} and use mocks/stubs that match the contract.",
            "Do not wire real API calls yet unless the owned files explicitly require a frontend route handler.",
            "Do not modify backend-only files outside the owned file list for this slice.",
        ]

    if track == "backend":
        return [
            "Implement only the backend-facing slice of the source story.",
            f"Make endpoints, schema, and response shapes satisfy `.openclaw/api-contract.json` for {domain_text}.",
            "Do not add or change frontend pages/components outside the owned file list for this slice.",
            "Prefer returning stable DTOs/contracts over coupling directly to frontend internals.",
        ]

    return [
        "Replace frontend mocks/stubs with real backend wiring for this story.",
        "Use `.openclaw/api-contract.json` as the non-negotiable interface boundary.",
        "Touch both frontend and backend only where needed to complete the real end-to-end flow.",
        "Remove or retire temporary mock adapters when the real integration path is in place.",
    ]


def _extract_http_endpoints(story: dict[str, Any]) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []

    for criterion in story.get("acceptance_criteria", []):
        if not isinstance(criterion, str):
            continue

        match = _HTTP_CONTRACT_RE.search(criterion)
        if not match:
            continue

        method, path = match.groups()
        statuses = [
            int(status)
            for status in re.findall(r"\b([1-5]\d\d)\b", criterion)
        ]
        entry = {
            "method": method,
            "path": path,
            "statuses": statuses or None,
            "source": criterion,
        }
        if entry not in endpoints:
            endpoints.append(entry)

    return endpoints


def _build_api_contract(spec: dict[str, Any]) -> dict[str, Any]:
    architecture = spec.get("architecture", {})
    communication = architecture.get("communication", [])
    boundaries = architecture.get("boundaries", {})
    domains: dict[str, dict[str, Any]] = {}

    for story in spec.get("stories", []):
        if not isinstance(story, dict):
            continue

        execution = _story_execution(story)
        contract_domains = execution.get("contract_domains", [])
        if not contract_domains:
            continue

        endpoints = _extract_http_endpoints(story)
        for domain in contract_domains:
            entry = domains.setdefault(
                domain,
                {
                    "name": domain,
                    "stories": [],
                    "tracks": [],
                    "frontend_files": [],
                    "backend_files": [],
                    "shared_files": [],
                    "http_endpoints": [],
                },
            )

            story_ref = {
                "id": story.get("id", ""),
                "story_key": story.get("story_key", ""),
                "title": story.get("title", ""),
            }
            if story_ref not in entry["stories"]:
                entry["stories"].append(story_ref)

            for field in ("tracks", "frontend_files", "backend_files", "shared_files"):
                for item in execution.get(field, []):
                    if item not in entry[field]:
                        entry[field].append(item)

            for endpoint in endpoints:
                if endpoint not in entry["http_endpoints"]:
                    entry["http_endpoints"].append(endpoint)

    return {
        "version": 1,
        "kind": "specwright-api-contract",
        "strategy": "contract-first-parallel-loops",
        "source_of_truth": [
            "spec.json",
            "architecture.md",
            "docs/stories",
            ".openclaw/execution-plan.json",
        ],
        "tracks": {
            "frontend": {
                "mode": "mock-first",
                "rules": [
                    "Implement UI/components against contract-compatible mocks before real API wiring exists.",
                    "Do not change response shapes locally; update the contract source instead.",
                ],
            },
            "backend": {
                "mode": "contract-first",
                "rules": [
                    "Implement endpoints and persistence so the runtime behavior matches the contract exactly.",
                    "Prefer additive backend changes over leaking implementation details into the contract.",
                ],
            },
            "integration": {
                "mode": "wire-real-data",
                "rules": [
                    "Replace mocks/stubs with real API wiring only after frontend and backend slices are complete.",
                    "Use integration stories to reconcile auth flow, loading states, and real data rendering.",
                ],
            },
        },
        "communication": communication,
        "boundaries": boundaries,
        "domains": list(domains.values()),
    }


def _build_parallel_execution(
    spec: dict[str, Any],
    ordered_stories: list[dict[str, Any]],
) -> dict[str, Any]:
    story_by_id = {
        story.get("id", ""): story
        for story in spec.get("stories", [])
        if isinstance(story, dict) and story.get("id")
    }
    story_key_to_id = {
        story.get("story_key", ""): story.get("id", "")
        for story in spec.get("stories", [])
        if isinstance(story, dict) and story.get("story_key") and story.get("id")
    }
    order_map = {story["id"]: story["order"] for story in ordered_stories}
    unit_entries: dict[str, dict[str, dict[str, Any]]] = {track: {} for track in _TRACK_ORDER}
    unit_ids_by_story: dict[str, dict[str, str]] = {}

    for ordered_story in ordered_stories:
        source_story = story_by_id.get(ordered_story["id"], ordered_story)
        execution = _story_execution(source_story)
        tracks = execution.get("tracks", ["shared"])

        unit_ids_by_story[source_story["id"]] = {}

        for track in tracks:
            unit_id = _track_unit_id(track, source_story["id"])
            unit_ids_by_story[source_story["id"]][track] = unit_id
            owned_files = execution.get(f"{track}_files", [])
            if track == "integration":
                owned_files = [
                    *execution.get("integration_files", []),
                    *execution.get("frontend_files", []),
                    *execution.get("backend_files", []),
                ]

            deduped_owned_files = []
            for path in owned_files:
                if path not in deduped_owned_files:
                    deduped_owned_files.append(path)

            unit_entries[track][unit_id] = {
                "id": unit_id,
                "track": track,
                "label": _TRACK_LABELS[track],
                "source_story_id": source_story["id"],
                "source_story_key": source_story.get("story_key", ""),
                "source_story_title": source_story.get("title", ""),
                "title": source_story.get("title", "") if track == "shared" else f"{_TRACK_LABELS[track]} slice — {source_story.get('title', '')}",
                "phase": ordered_story.get("phase", "features"),
                "status": "pending",
                "mode": execution.get("modes", {}).get(track, "real-service"),
                "source_order": order_map.get(source_story["id"], 999),
                "source_depends_on": source_story.get("depends_on", []),
                "contract_domains": execution.get("contract_domains", []),
                "owned_files": deduped_owned_files,
                "prompt_rules": _story_prompt_rules(track, source_story, execution),
                "validation_mode": "partial" if track in {"frontend", "backend"} and "integration" in tracks else "full",
                "needs_migrations": track in {"shared", "backend", "integration"} and any(
                    isinstance(item, str) and "migration" in item.lower()
                    for item in source_story.get("acceptance_criteria", [])
                ),
            }

    for ordered_story in ordered_stories:
        source_story = story_by_id.get(ordered_story["id"], ordered_story)
        source_id = source_story["id"]
        dependency_keys = source_story.get("depends_on", [])
        current_units = unit_ids_by_story.get(source_id, {})

        for track, unit_id in current_units.items():
            dependencies: list[str] = []

            if track == "integration":
                for local_track in ("shared", "frontend", "backend"):
                    dep_id = current_units.get(local_track)
                    if dep_id:
                        dependencies.append(dep_id)

            for dep_key in dependency_keys:
                dep_story_id = story_key_to_id.get(dep_key)
                if not dep_story_id:
                    continue

                dep_units = unit_ids_by_story.get(dep_story_id, {})
                if track == "shared":
                    if dep_units.get("shared"):
                        dependencies.append(dep_units["shared"])
                elif track == "frontend":
                    for candidate in ("shared", "frontend"):
                        dep_id = dep_units.get(candidate)
                        if dep_id:
                            dependencies.append(dep_id)
                elif track == "backend":
                    for candidate in ("shared", "backend"):
                        dep_id = dep_units.get(candidate)
                        if dep_id:
                            dependencies.append(dep_id)
                else:
                    if dep_units.get("integration"):
                        dependencies.append(dep_units["integration"])
                    else:
                        for candidate in ("shared", "frontend", "backend"):
                            dep_id = dep_units.get(candidate)
                            if dep_id:
                                dependencies.append(dep_id)

            deduped = []
            for dep in dependencies:
                if dep not in deduped:
                    deduped.append(dep)
            unit_entries[track][unit_id]["depends_on"] = deduped

    plans = {}
    summaries = []

    for track in _TRACK_ORDER:
        entries = unit_entries[track]
        ordered_units = _ordered_entries(
            entries,
            "depends_on",
            lambda unit_id: (
                entries[unit_id].get("source_order", 999),
                unit_id,
            ),
        )
        for index, unit in enumerate(ordered_units, start=1):
            unit["order"] = index

        plan = {
            "track": track,
            "label": _TRACK_LABELS[track],
            "contract_file": ".openclaw/api-contract.json",
            "total_stories": len(ordered_units),
            "stories": ordered_units,
        }
        plans[track] = plan
        summaries.append(
            {
                "track": track,
                "label": _TRACK_LABELS[track],
                "count": len(ordered_units),
                "plan_file": f".openclaw/{track}-plan.json",
            }
        )

    return {
        "enabled": True,
        "strategy": "shared-setup -> frontend/backend in parallel -> integration",
        "contract_file": ".openclaw/api-contract.json",
        "tracks": summaries,
        "plans": plans,
    }


def _classify_phase(story_id: str, story_key: str, title: str) -> str:
    """Assign a story to a phase for display/annotation purposes."""
    if story_key.startswith("bootstrap."):
        return "bootstrap"
    if story_key.startswith("feature.") or story_key.startswith("infra."):
        return "features"
    if story_key.startswith("product."):
        if "automation" in story_key or "scheduled" in story_key:
            return "automation"
        if any(
            kw in story_key
            for kw in (
                "deadlines", "progress", "task-assignment",
                "reminders", "report", "approvals", "team-visibility",
            )
        ):
            return "domain"
        return "product"
    if story_key.startswith("operations."):
        return "operations"
    if story_id in ("ST-900", "ST-901") or "monitoring" in title.lower() or "backup" in title.lower():
        return "operations"
    lower_title = title.lower()
    if any(kw in lower_title for kw in ("locale", "i18n", "translation")):
        return "features"
    if any(kw in lower_title for kw in ("cms", "content model")):
        return "features"
    if any(kw in lower_title for kw in ("cdn", "public site")):
        return "features"
    if any(kw in lower_title for kw in ("worker", "scheduler", "automation", "scheduled")):
        return "automation"
    return "features"


def _build_execution_plan(spec: dict[str, Any]) -> dict[str, Any]:
    """Build an ordered execution plan from stories.

    Uses topological sort to respect dependency ordering.  Stories are
    annotated with phases for display, but execution order is driven
    entirely by dependencies.  Within each "available" batch (stories
    whose dependencies are all satisfied), ties are broken by phase
    priority then story ID for determinism.

    Phases (for annotation):
    1. bootstrap — repository, database, backend, frontend setup
    2. features — authentication, roles, media-library, etc.
    3. product — product-shape stories (dashboard, portal, backoffice)
    4. domain — core work feature stories (deadlines, task-assignment, etc.)
    5. automation — scheduled jobs, background workers
    6. operations — monitoring, backups, operational stories
    """
    stories = spec.get("stories", [])

    # Build entries with phase annotation
    entries: dict[str, dict[str, Any]] = {}
    key_to_id: dict[str, str] = {}

    for story in stories:
        if not isinstance(story, dict):
            continue

        story_id = story.get("id", "")
        story_key = story.get("story_key", "")
        title = story.get("title", "")

        phase = _classify_phase(story_id, story_key, title)

        entry: dict[str, Any] = {
            "id": story_id,
            "title": title,
            "status": "pending",
            "phase": phase,
        }
        if story_key:
            entry["story_key"] = story_key
            key_to_id[story_key] = story_id

        depends_on = story.get("depends_on")
        if isinstance(depends_on, list) and depends_on:
            entry["depends_on"] = depends_on

        entries[story_id] = entry

    # ------------------------------------------------------------------
    # Topological sort — dependencies drive order, phases break ties
    # ------------------------------------------------------------------
    serial_entries: dict[str, dict[str, Any]] = {}
    for story_id, entry in entries.items():
        dependency_ids = []
        for dep_key in entry.get("depends_on", []):
            dep_id = key_to_id.get(dep_key)
            if dep_id:
                dependency_ids.append(dep_id)

        serial_entry = dict(entry)
        serial_entry["_dependency_ids"] = dependency_ids
        serial_entries[story_id] = serial_entry

    ordered = _ordered_entries(
        serial_entries,
        "_dependency_ids",
        lambda sid: (
            _PHASE_PRIORITY.get(serial_entries[sid]["phase"], 99),
            sid,
        ),
    )

    # Assign sequential order numbers
    phase_counts: dict[str, int] = {}
    for idx, entry in enumerate(ordered, start=1):
        entry.pop("_dependency_ids", None)
        entry["order"] = idx
        phase_counts[entry["phase"]] = phase_counts.get(entry["phase"], 0) + 1

    parallel_execution = _build_parallel_execution(spec, ordered)

    return {
        "total_stories": len(ordered),
        "phases": list(_PHASE_PRIORITY.keys()),
        "phase_order": [
            {"phase": "bootstrap", "description": "Project setup and infrastructure", "count": phase_counts.get("bootstrap", 0)},
            {"phase": "features", "description": "Core feature implementation", "count": phase_counts.get("features", 0)},
            {"phase": "product", "description": "Product shell and navigation", "count": phase_counts.get("product", 0)},
            {"phase": "domain", "description": "Domain-specific work features", "count": phase_counts.get("domain", 0)},
            {"phase": "automation", "description": "Background jobs and automation", "count": phase_counts.get("automation", 0)},
            {"phase": "operations", "description": "Monitoring, backups, operational setup", "count": phase_counts.get("operations", 0)},
        ],
        "stories": ordered,
        "parallel_execution": parallel_execution,
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
        commands["db_migrate"] = migration_commands({"stack": stack})["run"]
        setup["db_migrate"] = migration_commands({"stack": stack})["run"]
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
    """Generate commands + validation contract from the project spec."""
    return build_validation_bundle(spec)


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
5. `.openclaw/api-contract.json` — shared frontend/backend contract for parallel execution
6. `.openclaw/execution-plan.json` — ordered story list with phases plus parallel track metadata
7. `.openclaw/{{shared,frontend,backend,integration}}-plan.json` — track-specific plans
8. `docs/stories/` — individual story files
9. project source files

## Execution rules

- Work **one story at a time**, following the order in `execution-plan.json`
- Start with the **bootstrap phase** — these set up the project structure
- In parallel mode, run `shared` first, then `frontend` and `backend`, then `integration`
- Frontend slices must respect `.openclaw/api-contract.json` and use contract-compatible mocks until integration
- Backend slices must satisfy the same contract before integration starts
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
- `.openclaw/api-contract.json` is the shared interface contract between frontend and backend loops
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
- Contract changes were reflected in `.openclaw/api-contract.json` when relevant
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
- `.openclaw/api-contract.json` — frontend/backend contract for parallel slices
- `.openclaw/execution-plan.json` — ordered implementation plan
- `.openclaw/shared-plan.json` / `.openclaw/frontend-plan.json` / `.openclaw/backend-plan.json` / `.openclaw/integration-plan.json` — loop-specific plans
- `docs/stories/` — individual story definitions

## Execution model

1. Run the shared setup plan first
2. Run frontend and backend track plans in parallel against `.openclaw/api-contract.json`
3. Run the integration plan after both parallel tracks finish
4. Read the source story file in `docs/stories/`
5. Implement the slice
6. Validate the work
7. Update `progress.txt`

## Constraints

- Do not replace the generated contract with a new architecture
- Do not rewrite unrelated parts of the project
- Do not skip validation when commands are available
- Do not mark work as complete without recording outcomes
- Follow the phase order: bootstrap → features → product → domain → automation → operations
- Treat `.openclaw/api-contract.json` as the handshake between frontend and backend slices
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

    # --- api-contract.json ---
    api_contract = _build_api_contract(spec)
    (openclaw_dir / "api-contract.json").write_text(
        json.dumps(api_contract, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- track plans ---
    parallel_execution = execution_plan.get("parallel_execution", {})
    for track, plan in parallel_execution.get("plans", {}).items():
        (openclaw_dir / f"{track}-plan.json").write_text(
            json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
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
            ".openclaw/api-contract.json",
            ".openclaw/execution-plan.json",
            ".openclaw/shared-plan.json",
            ".openclaw/frontend-plan.json",
            ".openclaw/backend-plan.json",
            ".openclaw/integration-plan.json",
            ".openclaw/AGENTS.md",
        ],
        "execution_mode": "parallel-contract-loops",
        "primary_input": "spec.json",
        "policies": {
            "one_story_at_a_time": True,
            "must_validate_before_done": True,
            "append_progress": True,
            "avoid_architecture_drift": True,
            "follow_phase_order": True,
            "contract_first_parallelism": True,
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
            "api_contract": ".openclaw/api-contract.json",
            "execution_plan": ".openclaw/execution-plan.json",
            "parallel_plans": {
                "shared": ".openclaw/shared-plan.json",
                "frontend": ".openclaw/frontend-plan.json",
                "backend": ".openclaw/backend-plan.json",
                "integration": ".openclaw/integration-plan.json",
            },
        },
        "execution_expectations": {
            "story_driven": True,
            "validate_changes": True,
            "record_progress": True,
            "preserve_generated_scope": True,
            "follow_phase_order": True,
            "respect_shared_contract": True,
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
