"""Shared validation contract for generated and prepared projects.

This module centralizes how Specwright defines:
- ecosystem-specific default commands
- which test runner a project is expected to use
- whether the detected test command is a real runner or a no-op
- which validation steps are blocking vs warning-only
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Node.js ecosystem stacks
_NODE_FRONTENDS = {
    "nextjs", "next.js", "next", "react", "vue", "nuxt", "svelte",
    "sveltekit", "astro", "remix",
}
_NODE_BACKENDS = {
    "payload", "payload-cms", "node-api", "express", "fastify",
    "hono", "nestjs", "adonis", "strapi",
}

# Python ecosystem stacks
_PYTHON_BACKENDS = {"django", "flask", "fastapi", "litestar"}

# Go ecosystem stacks
_GO_BACKENDS = {"go", "golang", "gin", "echo", "fiber"}

_BLOCK_ON = ["test", "build", "typecheck"]
_WARN_ON = ["lint"]

_NOOP_TEST_RE = re.compile(
    r"^\s*(?:echo\b.*|printf\b.*|true\b|exit\s+0\b|:\s*|#.*)?\s*$",
    re.IGNORECASE,
)


def detect_ecosystem(stack: dict[str, Any]) -> str:
    """Detect the primary ecosystem from the stack dict."""
    frontend = (stack.get("frontend") or "").lower().strip()
    backend = (stack.get("backend") or "").lower().strip()

    if backend in _PYTHON_BACKENDS or frontend == "django":
        return "python"

    if backend in _GO_BACKENDS:
        return "go"

    if frontend in _NODE_FRONTENDS or backend in _NODE_BACKENDS or frontend:
        return "node"

    return "unknown"


def _is_noop_test_command(command: str) -> bool:
    text = (command or "").strip()
    if not text:
        return True

    lowered = text.lower()
    runner_tokens = (
        "vitest",
        "jest",
        "node --test",
        "tsx",
        "pytest",
        "go test",
        "mocha",
        "ava",
        "tap ",
    )
    if any(token in lowered for token in runner_tokens):
        return False

    return bool(_NOOP_TEST_RE.fullmatch(text))


def _node_runner_from_package_json(pkg: dict[str, Any]) -> str:
    scripts = pkg.get("scripts", {})
    test_script = scripts.get("test", "")
    deps = {
        **pkg.get("dependencies", {}),
        **pkg.get("devDependencies", {}),
    }
    dep_keys = {str(k).lower() for k in deps}
    lowered = (test_script or "").lower()

    if _is_noop_test_command(test_script):
        return "none"
    if "vitest" in lowered or "vitest" in dep_keys:
        return "vitest"
    if "jest" in lowered or "jest" in dep_keys or any(k.startswith("@jest/") for k in dep_keys):
        return "jest"
    if "node --test" in lowered or ("tsx" in lowered and "--test" in lowered):
        return "node-test"
    if test_script.strip():
        return "custom"
    return "none"


def _python_runner_from_project(project_dir: Path) -> str:
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        if "pytest" in content:
            return "pytest"
        return "custom"
    return "pytest"


def _go_runner_from_project(project_dir: Path) -> str:
    if (project_dir / "go.mod").exists():
        return "go-test"
    return "go-test"


def _notes(capabilities: list[str], extra: list[str] | None = None) -> list[str]:
    notes = [
        "These commands are pre-populated from the project stack. Update them if the actual project setup differs.",
        "The validation contract defines which steps are blocking vs warning-only.",
        "Run 'typecheck' periodically to catch type errors early.",
    ]
    if "scheduled-jobs" in capabilities:
        notes.append(
            "The 'jobs' command starts the background job runner. Configure it after implementing the automation story."
        )
    if extra:
        notes.extend(extra)
    return notes


def _validation_block(ecosystem: str, test_runner: str, requires_real_tests: bool = True) -> dict[str, Any]:
    return {
        "ecosystem": ecosystem,
        "test_runner": test_runner,
        "requires_real_tests": requires_real_tests,
        "block_on": list(_BLOCK_ON),
        "warn_on": list(_WARN_ON),
    }


def build_validation_bundle(spec: dict[str, Any]) -> dict[str, Any]:
    """Generate commands + validation contract from the planned stack."""
    stack = spec.get("stack", {})
    answers = spec.get("answers", {})
    capabilities = spec.get("capabilities", [])

    ecosystem = detect_ecosystem(stack)
    backend = (stack.get("backend") or "").lower().strip()
    database = (stack.get("database") or "").lower().strip()
    deploy_target = answers.get("deploy_target", "docker")

    commands: dict[str, str] = {
        "test": "",
        "lint": "",
        "build": "",
        "typecheck": "",
        "dev": "",
    }
    setup: dict[str, str] = {}

    if ecosystem == "node":
        commands.update({
            "test": "npm test",
            "lint": "npm run lint",
            "build": "npm run build",
            "typecheck": "npm run typecheck",
            "dev": "npm run dev",
        })
        setup.update({
            "install": "npm install",
            "env": "test -f .env.local || cp .env.example .env.local",
        })
        if database == "postgres" and deploy_target in ("docker", "docker_and_k8s_later"):
            commands["db_start"] = "docker compose up -d postgres"
            commands["db_stop"] = "docker compose down"
            setup["db_start"] = "docker compose up -d postgres"
        elif database == "postgres":
            setup["db_start"] = "# Start PostgreSQL manually or via your cloud provider"
        elif database == "mongodb" and deploy_target in ("docker", "docker_and_k8s_later"):
            commands["db_start"] = "docker compose up -d mongo"
            commands["db_stop"] = "docker compose down"
            setup["db_start"] = "docker compose up -d mongo"
        elif database and database != "sqlite":
            setup["db_start"] = f"# Start {database} manually"

        if backend in ("payload", "payload-cms"):
            commands["db_migrate"] = "npx payload migrate"
            commands["db_seed"] = "npx payload seed"
            setup["db_migrate"] = "npx payload migrate"
        elif database:
            commands["db_migrate"] = "npm run db:migrate"
            setup["db_migrate"] = "npm run db:migrate"

        if "scheduled-jobs" in capabilities:
            commands["jobs"] = "npm run jobs"

        validation = _validation_block("node", "vitest", requires_real_tests=True)
        return {
            "commands": commands,
            "setup": setup,
            "notes": _notes(capabilities),
            "validation": validation,
        }

    if ecosystem == "python":
        commands.update({
            "test": "pytest",
            "lint": "ruff check .",
            "build": "python manage.py check --deploy" if backend == "django" else "python -m py_compile app/",
            "typecheck": "mypy .",
            "dev": "python manage.py runserver" if backend == "django" else "uvicorn app.main:app --reload",
        })
        setup.update({
            "install": "pip install -r requirements.txt",
            "env": "cp .env.example .env",
        })
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
            commands["jobs"] = "python manage.py run_jobs" if backend == "django" else "python -m app.jobs"

        validation = _validation_block("python", "pytest", requires_real_tests=True)
        return {
            "commands": commands,
            "setup": setup,
            "notes": _notes(capabilities),
            "validation": validation,
        }

    if ecosystem == "go":
        commands.update({
            "test": "go test ./...",
            "lint": "golangci-lint run",
            "build": "go build ./...",
            "typecheck": "go vet ./...",
            "dev": "go run ./cmd/server",
        })
        setup.update({
            "install": "go mod download",
            "env": "cp .env.example .env",
        })
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

        validation = _validation_block("go", "go-test", requires_real_tests=True)
        return {
            "commands": commands,
            "setup": setup,
            "notes": _notes(capabilities),
            "validation": validation,
        }

    return {
        "commands": commands,
        "setup": {
            "install": "# Configure install command for your stack",
            "env": "cp .env.example .env",
        },
        "notes": _notes(
            capabilities,
            extra=["Unknown ecosystem detected. Validation commands may need manual adjustment."],
        ),
        "validation": _validation_block("unknown", "none", requires_real_tests=False),
    }


def detect_validation_bundle(project_dir: Path, spec: dict[str, Any]) -> dict[str, Any]:
    """Detect the real commands + validation contract from project files when possible."""
    default_bundle = build_validation_bundle(spec)
    commands = dict(default_bundle["commands"])
    setup = dict(default_bundle["setup"])
    notes: list[str] = []
    validation = dict(default_bundle["validation"])

    package_json = project_dir / "package.json"
    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})

            commands["test"] = "npm test" if "test" in scripts else ""
            commands["lint"] = "npm run lint" if "lint" in scripts else ""
            commands["build"] = "npm run build" if "build" in scripts else ""
            commands["typecheck"] = "npm run typecheck" if "typecheck" in scripts else ""
            commands["dev"] = "npm run dev" if "dev" in scripts else ""

            validation["ecosystem"] = "node"
            validation["test_runner"] = _node_runner_from_package_json(pkg)
            validation["requires_real_tests"] = True

            notes.append("Commands and validation contract detected from package.json.")
            if validation["test_runner"] == "none":
                notes.append("Detected test command is missing or a no-op placeholder; generated validation will fail until a real runner is configured.")
            elif validation["test_runner"] == "custom":
                notes.append("Detected a custom Node test runner; validation will use npm test, but runner semantics are not standardized.")

            return {
                "commands": commands,
                "setup": setup,
                "notes": notes,
                "validation": validation,
            }
        except (json.JSONDecodeError, OSError):
            notes.append("package.json exists but could not be parsed. Falling back to stack-based validation defaults.")

    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        validation["ecosystem"] = "python"
        validation["test_runner"] = _python_runner_from_project(project_dir)
        validation["requires_real_tests"] = True
        notes.append("Commands and validation contract detected from pyproject.toml.")
        return {
            "commands": commands,
            "setup": setup,
            "notes": notes,
            "validation": validation,
        }

    go_mod = project_dir / "go.mod"
    if go_mod.exists():
        validation["ecosystem"] = "go"
        validation["test_runner"] = _go_runner_from_project(project_dir)
        validation["requires_real_tests"] = True
        notes.append("Commands and validation contract detected from go.mod.")
        return {
            "commands": commands,
            "setup": setup,
            "notes": notes,
            "validation": validation,
        }

    notes.append("No project manifest found. Validation contract is based on the planned stack.")
    return {
        "commands": commands,
        "setup": setup,
        "notes": notes,
        "validation": validation,
    }


def expected_test_runner(spec: dict[str, Any]) -> str:
    """Return the expected runner label for story wording."""
    ecosystem = detect_ecosystem(spec.get("stack", {}))
    if ecosystem == "node":
        return "vitest"
    if ecosystem == "python":
        return "pytest"
    if ecosystem == "go":
        return "go test"
    return "test runner"
