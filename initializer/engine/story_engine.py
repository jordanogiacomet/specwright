"""Story Engine.

Generates implementation stories from features, capabilities,
stack, and structured discovery signals.

Key improvements in this version:
- Acceptance criteria for every story
- Scope boundaries (what NOT to do) for every story
- Expected files derived from stack
- Explicit depends_on for execution ordering
- Validation commands per story
- More core_work_features generate stories (approvals, team-visibility)
- Product shape stories for client-portal, backoffice, content-platform
- Less restrictive condition for automation-jobs story
- Notifications story when feature is present
- Draft-publish story when feature is present
"""

import re

from initializer.engine.validation_contract import (
    build_validation_bundle,
    detect_ecosystem,
    expected_test_runner,
    migration_commands,
)


def _merge_story(existing_story, generated_story):
    merged = dict(existing_story)

    if not merged.get("story_key"):
        merged["story_key"] = generated_story["story_key"]

    if not merged.get("title"):
        merged["title"] = generated_story["title"]
    elif merged["title"] != generated_story["title"]:
        titles = list(merged.get("title_alternatives", []))
        if generated_story["title"] not in titles:
            titles.append(generated_story["title"])
        merged["title_alternatives"] = titles

    if not merged.get("description"):
        merged["description"] = generated_story["description"]
    elif merged["description"] != generated_story["description"]:
        descriptions = list(merged.get("description_alternatives", []))
        if generated_story["description"] not in descriptions:
            descriptions.append(generated_story["description"])
        merged["description_alternatives"] = descriptions

    # Merge new enrichment fields only if not already present
    for key in (
        "acceptance_criteria",
        "scope_boundaries",
        "expected_files",
        "depends_on",
        "validation",
    ):
        if key in generated_story and not merged.get(key):
            merged[key] = generated_story[key]

    return merged


def _find_story_index(stories, story_key, title):
    for index, story in enumerate(stories):
        if story.get("story_key") == story_key:
            return index

    for index, story in enumerate(stories):
        if story.get("title") == title:
            return index

    return None


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _normalize_core_work_features(value):
    if not isinstance(value, list):
        return []

    normalized = []
    for item in value:
        if isinstance(item, str):
            text = item.strip().lower()
            if text and text not in normalized:
                normalized.append(text)

    return normalized


def _guided_answers(spec):
    answers = spec.get("answers", {})
    ga = answers.get("guided_answers", {})
    return ga if isinstance(ga, dict) else {}


def _get_content_model(spec):
    content_model = _guided_answers(spec).get("content_model", {})
    return content_model if isinstance(content_model, dict) else {}


def _get_content_collections(spec):
    collections = _get_content_model(spec).get("collections", [])
    return collections if isinstance(collections, list) else []


def _get_content_globals(spec):
    globals_list = _get_content_model(spec).get("globals", [])
    return globals_list if isinstance(globals_list, list) else []


def _get_media_kinds(spec):
    media_items = _get_content_model(spec).get("media", [])
    if not isinstance(media_items, list):
        return []

    kinds = []
    for item in media_items:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind", "")
        if isinstance(kind, str):
            text = kind.strip().lower()
            if text and text not in kinds:
                kinds.append(text)
    return kinds


def _is_enabled(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    return bool(value)


def _is_editorial_context(spec):
    signals = _get_decision_signals(spec)
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    archetype = spec.get("archetype", "")
    app_shape = signals.get("app_shape")
    return (
        archetype == "editorial-cms"
        or app_shape == "content-platform"
        or "cms" in capabilities
        or "draft-publish" in features
        or "preview" in features
    )


def _get_role_definitions(spec):
    roles = []

    roles_section = _guided_answers(spec).get("roles_and_access", {})
    if isinstance(roles_section, dict):
        admin_roles = roles_section.get("admin_roles", [])
        if isinstance(admin_roles, list):
            roles = admin_roles

    if not roles:
        domain_model = spec.get("domain_model", {})
        if isinstance(domain_model, dict):
            domain_roles = domain_model.get("roles", [])
            if isinstance(domain_roles, list):
                roles = domain_roles

    normalized = []
    seen = set()
    for role in roles:
        if isinstance(role, dict):
            name = role.get("name")
            if isinstance(name, str):
                text = name.strip().lower()
                if text and text not in seen:
                    normalized.append({"name": text, "responsibility": role.get("responsibility", "")})
                    seen.add(text)
        elif isinstance(role, str):
            text = role.strip().lower()
            if text and text not in seen:
                normalized.append({"name": text, "responsibility": ""})
                seen.add(text)

    if normalized:
        return normalized

    if _is_editorial_context(spec):
        return [
            {"name": "admin", "responsibility": "manage users, configuration, and publishing overrides"},
            {"name": "editor", "responsibility": "create and edit drafts, then submit for review"},
            {"name": "reviewer", "responsibility": "review submissions and approve publication"},
        ]

    return [
        {"name": "admin", "responsibility": "manage privileged actions"},
        {"name": "user", "responsibility": "use the main application features"},
    ]


def _get_role_names(spec):
    return [role["name"] for role in _get_role_definitions(spec)]


def _get_storage_backend(spec):
    """Extract storage backend preference from guided_answers.storage_requirements."""
    storage = _guided_answers(spec).get("storage_requirements", {})
    return storage.get("upload_backend", "").lower().strip()


def _get_editorial_workflows(spec):
    workflows = _guided_answers(spec).get("editorial_workflows", {})
    return workflows if isinstance(workflows, dict) else {}


def _lookup_answer_path(spec, path):
    current = spec.get("answers", {})
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _feature_enabled_by_answers(spec, feature):
    feature_flags = {
        "draft-publish": [
            ("guided_answers", "editorial_workflows", "draft_publish"),
            ("critical_confirmations", "draft_publish_workflow"),
        ],
        "preview": [
            ("guided_answers", "editorial_workflows", "preview"),
            ("critical_confirmations", "preview_workflow"),
        ],
        "scheduled-publishing": [
            ("guided_answers", "editorial_workflows", "scheduled_publishing"),
            ("critical_confirmations", "background_jobs"),
        ],
    }

    for path in feature_flags.get(feature, []):
        bool_value = _is_enabled(_lookup_answer_path(spec, path))
        raw_value = _lookup_answer_path(spec, path)
        if raw_value is not None:
            return bool_value

    return feature in spec.get("features", [])


def _supports_public_collection(name):
    return name not in {"media", "authors", "users", "categories", "tags"}


def _public_collection_names(spec):
    names = []
    for collection in _get_content_collections(spec):
        if not isinstance(collection, dict):
            continue
        name = collection.get("name", "")
        if not isinstance(name, str):
            continue
        text = name.strip().lower()
        if text and _supports_public_collection(text) and text not in names:
            names.append(text)
    return names or ["posts", "pages"]


def _pascal_case(value):
    return "".join(part.capitalize() for part in value.replace("_", "-").split("-") if part)


def _collection_file_path(stack, name):
    backend = stack.get("backend", "node-api")
    if backend in ("payload", "payload-cms"):
        return f"src/collections/{_pascal_case(name)}.ts"
    return f"src/models/{_pascal_case(name)}.ts"


def _global_file_path(stack, name):
    backend = stack.get("backend", "node-api")
    if backend in ("payload", "payload-cms"):
        return f"src/globals/{_pascal_case(name)}.ts"
    return f"src/config/{_pascal_case(name)}.ts"


# ---------------------------------------------------------------------------
# Stack-aware path helpers
# ---------------------------------------------------------------------------

def _frontend_page_path(stack, route):
    """Return expected page file path based on frontend stack."""
    frontend = stack.get("frontend", "nextjs")
    if frontend in ("nextjs", "next.js", "next"):
        return f"src/app/{route}/page.tsx"
    return f"src/pages/{route}.tsx"


def _backend_path(stack, name):
    """Return expected backend file path based on backend stack."""
    backend = stack.get("backend", "node-api")
    if backend in ("payload", "payload-cms"):
        return f"src/collections/{name}.ts"
    return f"src/api/{name}.ts"


def _lib_path(name):
    return f"src/lib/{name}.ts"


def _component_path(name):
    return f"src/components/{name}.tsx"


# ---------------------------------------------------------------------------
# Parallel execution metadata
# ---------------------------------------------------------------------------

_HTTP_CONTRACT_RE = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_./:[\]-]+)"
)


def _story_text(story):
    parts = [
        story.get("story_key", ""),
        story.get("title", ""),
        story.get("description", ""),
    ]
    for item in story.get("acceptance_criteria", []):
        if isinstance(item, str):
            parts.append(item)
    return " ".join(part for part in parts if isinstance(part, str)).lower()


def _expand_expected_file_candidates(expected_files):
    candidates = []

    for item in expected_files:
        if not isinstance(item, str):
            continue

        text = item.strip().strip("`")
        if not text:
            continue

        text = text.split(" (", 1)[0].strip()
        parts = [part.strip() for part in text.split(" or ")]
        for part in parts:
            if part:
                candidates.append(part)

    return candidates


def _classify_expected_file_surface(path):
    normalized = path.strip().lower()

    if not normalized:
        return "shared"

    if normalized.startswith(("package.json", "tsconfig", ".env", ".gitignore", "readme", "vitest.config", "eslint.config", ".eslintrc")):
        return "shared"

    if normalized.startswith("src/middleware"):
        return "integration"

    if normalized.startswith(("docker-compose", "src/server", "src/api/", "src/app/api/", "src/collections/", "src/globals/", "src/models/", "src/jobs/", "src/payload.config", "payload.config")):
        return "backend"

    if normalized.startswith(("src/app/", "src/components/", "src/pages/", "public/", "src/styles/")):
        return "frontend"

    if normalized.startswith("src/lib/"):
        leaf = normalized.rsplit("/", 1)[-1]

        if any(keyword in leaf for keyword in ("db", "auth", "permission", "storage", "scheduler", "billing", "content-status", "rate-limit")):
            return "backend"

        if any(keyword in leaf for keyword in ("preview", "public-content", "api-client", "query-client")):
            return "integration"

        return "shared"

    return "shared"


def _derive_contract_domains(story):
    story_key = story.get("story_key", "")
    text = _story_text(story)

    domains = []

    def add(name, keywords):
        if any(keyword in text for keyword in keywords) and name not in domains:
            domains.append(name)

    if story_key.startswith(("feature.authentication", "security.")):
        domains.append("auth")
    add("auth", ("login", "logout", "register", "registration", "session", "users", "password", "credential"))
    add("authorization", ("roles", "permission", "rbac", "access control"))
    add("content", ("content", "cms", "draft", "publish", "preview", "slug", "public site", "media"))
    add("billing", ("payment", "billing", "subscription", "checkout", "invoice"))
    add("todos", ("todo", "task list"))
    add("workflow", ("deadline", "progress", "assignment", "reminder", "approval", "report", "team visibility"))
    add("jobs", ("scheduled", "automation", "worker", "cron", "background job"))
    add("operations", ("monitoring", "logging", "backup", "health"))
    add("notifications", ("notification", "email", "webhook"))

    return domains


def _story_has_http_contract(story):
    acceptance = story.get("acceptance_criteria", [])
    for item in acceptance:
        if not isinstance(item, str):
            continue

        lowered = item.lower()
        if _HTTP_CONTRACT_RE.search(item):
            return True
        if "endpoint" in lowered and ("response" in lowered or re.search(r"\b[1-5]\d\d\b", lowered)):
            return True
    return False


def _derive_execution_tracks(story, frontend_files, backend_files, shared_files, integration_files):
    story_key = story.get("story_key", "")
    text = _story_text(story)

    if story_key == "bootstrap.repository":
        return ["shared"]

    if story_key in {"bootstrap.database", "bootstrap.backend"}:
        return ["backend"]

    if story_key == "bootstrap.frontend":
        return ["frontend"]

    frontend_hints = any(
        keyword in text
        for keyword in (
            "frontend", "shell", "dashboard", "portal", "backoffice",
            "navigation", "layout", "public site", "ui", "rendering",
            "client", "form", "submit", "submission", "browser",
        )
    )
    backend_hints = story_key.startswith(("feature.authentication", "security.")) or any(
        keyword in text
        for keyword in (
            "backend", "database", "model", "api", "roles",
            "permission", "billing", "subscription", "media", "worker",
            "scheduler", "monitoring", "backup", "migration", "server",
            "endpoint", "response", "middleware", "rate limit",
            "login", "register", "password", "credential", "session",
        )
    )

    has_frontend = bool(frontend_files) or frontend_hints
    has_backend = bool(backend_files) or backend_hints or _story_has_http_contract(story)
    has_contract_surface = bool(_derive_contract_domains(story))
    has_integration_surface = bool(integration_files)

    tracks = []

    if has_frontend:
        tracks.append("frontend")

    if has_backend:
        tracks.append("backend")

    if ("frontend" in tracks and ("backend" in tracks or has_contract_surface)) or (
        has_integration_surface and ("frontend" in tracks or "backend" in tracks)
    ):
        tracks.append("integration")

    if not tracks:
        if shared_files:
            tracks.append("shared")
        elif story_key.startswith(("feature.", "operations.", "infra.")):
            tracks.append("backend")
        else:
            tracks.append("shared")

    return tracks


def _build_execution_metadata(story):
    expected_files = story.get("expected_files", [])
    frontend_files = []
    backend_files = []
    shared_files = []
    integration_files = []

    for path in _expand_expected_file_candidates(expected_files):
        surface = _classify_expected_file_surface(path)
        if surface == "frontend":
            frontend_files.append(path)
        elif surface == "backend":
            backend_files.append(path)
        elif surface == "integration":
            integration_files.append(path)
        else:
            shared_files.append(path)

    tracks = _derive_execution_tracks(
        story,
        frontend_files,
        backend_files,
        shared_files,
        integration_files,
    )
    contract_domains = _derive_contract_domains(story)

    if shared_files and "shared" not in tracks:
        if "frontend" in tracks and "backend" in tracks:
            integration_files.extend(shared_files)
        elif "backend" in tracks:
            backend_files.extend(shared_files)
        elif "frontend" in tracks:
            frontend_files.extend(shared_files)
        elif "integration" in tracks:
            integration_files.extend(shared_files)
        shared_files = []

    primary_track = tracks[0]
    if "integration" in tracks:
        primary_track = "integration"

    modes = {}
    if "shared" in tracks:
        modes["shared"] = "shared-setup"
    if "frontend" in tracks:
        modes["frontend"] = "mock-first" if "integration" in tracks else "real-ui"
    if "backend" in tracks:
        modes["backend"] = "contract-first" if "integration" in tracks else "real-service"
    if "integration" in tracks:
        modes["integration"] = "wire-real-data"

    return {
        "tracks": tracks,
        "primary_track": primary_track,
        "parallelizable": primary_track != "shared" or len(tracks) > 1,
        "contract_domains": contract_domains,
        "frontend_files": frontend_files,
        "backend_files": backend_files,
        "shared_files": shared_files,
        "integration_files": integration_files,
        "modes": modes,
    }


def derive_execution_metadata(story):
    """Public wrapper for execution-track heuristics used by benchmarking/reporting."""
    return _build_execution_metadata(story)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_DEFAULT_VALIDATION = {
    "commands": ["npm run build", "npm run lint"],
    "manual_check": None,
}

def _validation(commands=None, manual_check=None):
    return {
        "commands": commands or ["npm run build", "npm run lint"],
        "manual_check": manual_check,
    }


def _schema_validation(commands=None, manual_check=None):
    """Validation for stories that modify database schema."""
    base_commands = commands or ["npm run build", "npm run lint"]
    return {
        "commands": base_commands,
        "manual_check": manual_check,
    }


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_stories(spec):
    stories = [dict(story) for story in spec.get("stories", [])]
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    stack = spec.get("stack", {})
    signals = _get_decision_signals(spec)

    primary_audience = signals.get("primary_audience")
    app_shape = signals.get("app_shape")
    needs_scheduled_jobs = signals.get("needs_scheduled_jobs")
    core_work_features = _normalize_core_work_features(
        signals.get("core_work_features", [])
    )

    backend = stack.get("backend", "node-api")
    frontend = stack.get("frontend", "nextjs")
    database = stack.get("database", "postgres")
    validation_bundle = build_validation_bundle(spec)
    validation_commands = validation_bundle.get("commands", {})
    ecosystem = detect_ecosystem(stack)
    runner_label = expected_test_runner(spec)
    migration_cmds = migration_commands(spec)
    migration_create_cmd = migration_cmds["create"]
    migration_run_cmd = migration_cmds["run"]
    migration_status_cmd = migration_cmds["status"]

    migration_criteria = (
        f"Database migration is generated and executed for all schema changes "
        f"(run `{migration_create_cmd}` then `{migration_run_cmd}`)"
    )

    if (stack.get("backend") or "").lower().strip() in ("payload", "payload-cms", "node-api"):
        migration_dir_boundary = (
            f"All migrations MUST be created in `src/lib/migrations/` using `{migration_create_cmd}` "
            f"— do NOT create migration files in any other directory (e.g. `src/models/migrations/`)"
        )
    else:
        migration_dir_boundary = (
            f"Use the stack's canonical migration commands (`{migration_create_cmd}` / `{migration_run_cmd}` / "
            f"`{migration_status_cmd}`) and do NOT invent a parallel migration workflow."
        )

    bootstrap_validation_commands = []
    install_cmd = validation_bundle.get("setup", {}).get("install")
    if install_cmd:
        bootstrap_validation_commands.append(install_cmd)
    for key in ("build", "lint", "test"):
        cmd = validation_commands.get(key)
        if cmd:
            bootstrap_validation_commands.append(cmd)

    install_criteria = f"{install_cmd} completes without errors" if install_cmd else "Dependency installation completes without errors"
    build_cmd = validation_commands.get("build")
    test_cmd = validation_commands.get("test")
    build_criteria = f"{build_cmd} passes" if build_cmd else "Build passes"
    test_criteria = f"{test_cmd} passes (must not be a no-op)" if test_cmd else "Test command passes (must not be a no-op)"

    if ecosystem == "node":
        repository_manifest_criteria = "package.json exists with scripts: dev, build, lint, test, typecheck"
        repository_tooling_criteria = "TypeScript is configured with tsconfig.json"
        repository_lint_criteria = "ESLint and Prettier are configured"
        test_framework_criteria = "Vitest is installed and configured so that `npm test` runs a real test runner, not a no-op"
        smoke_test_criteria = "At least one smoke test exists (e.g. a test that imports the app config and asserts it loads)"
        repository_expected_files = [
            "package.json",
            "tsconfig.json",
            ".eslintrc.js or eslint.config.js",
            ".env.example",
            ".env.local",
            ".gitignore",
            "README.md",
            "vitest.config.ts",
            "src/__tests__/smoke.test.ts",
        ]
        repository_scope_boundaries = [
            "Do NOT implement any features yet — this is project scaffolding only",
            "Do NOT add authentication, roles, or any business logic",
            "Do NOT create database tables — that is a separate story",
            "Do NOT create files in src/pages/ — this project uses the App Router (src/app/) exclusively",
            "Use environment variable names exactly as defined in .env.example — do NOT rename or create alternatives",
        ]
        repository_manual_check = "Project directory exists with expected structure; npm test runs a real test suite"
    elif ecosystem == "python":
        repository_manifest_criteria = "pyproject.toml or requirements.txt exists with install, test, lint, and typecheck commands documented"
        repository_tooling_criteria = "Python project tooling is configured for local development"
        repository_lint_criteria = "Linting and formatting tooling are configured for the Python stack"
        test_framework_criteria = (
            f"{runner_label} is installed and configured so that the test command runs a real test runner, not a no-op"
        )
        smoke_test_criteria = "At least one Python smoke test exists for bootstrap validation"
        repository_expected_files = [
            "pyproject.toml or requirements.txt",
            ".env.example",
            ".gitignore",
            "README.md",
            "At least one real smoke test file for the ecosystem",
        ]
        repository_scope_boundaries = [
            "Do NOT implement any features yet — this is project scaffolding only",
            "Do NOT add authentication, roles, or any business logic",
            "Do NOT create database tables — that is a separate story",
            "Use environment variable names exactly as defined in .env.example — do NOT rename or create alternatives",
        ]
        repository_manual_check = "Project directory exists with expected structure; pytest runs a real test suite"
    elif ecosystem == "go":
        repository_manifest_criteria = "go.mod exists and the module layout is initialized"
        repository_tooling_criteria = "Go tooling is configured for local development and validation"
        repository_lint_criteria = "Linting and vet tooling are configured for the Go stack"
        test_framework_criteria = (
            f"{runner_label} is configured so that the test command runs a real test runner, not a no-op"
        )
        smoke_test_criteria = "At least one Go smoke test exists for bootstrap validation"
        repository_expected_files = [
            "go.mod",
            ".env.example",
            ".gitignore",
            "README.md",
            "At least one real smoke test file for the ecosystem",
        ]
        repository_scope_boundaries = [
            "Do NOT implement any features yet — this is project scaffolding only",
            "Do NOT add authentication, roles, or any business logic",
            "Do NOT create database tables — that is a separate story",
            "Use environment variable names exactly as defined in .env.example — do NOT rename or create alternatives",
        ]
        repository_manual_check = "Project directory exists with expected structure; go test ./... runs a real test suite"
    else:
        repository_manifest_criteria = "Project manifest exists with install, test, lint, and build commands documented"
        repository_tooling_criteria = "Project tooling is configured for local development"
        repository_lint_criteria = "Linting and formatting tooling are configured"
        test_framework_criteria = (
            f"A test framework is installed and configured ({runner_label}) so that the test command runs a real test runner, not a no-op"
        )
        smoke_test_criteria = "At least one real smoke test file exists for the ecosystem"
        repository_expected_files = [
            "Project manifest",
            ".env.example",
            ".gitignore",
            "README.md",
            "At least one real smoke test file for the ecosystem",
        ]
        repository_scope_boundaries = [
            "Do NOT implement any features yet — this is project scaffolding only",
            "Do NOT add authentication, roles, or any business logic",
            "Do NOT create database tables — that is a separate story",
            "Use environment variable names exactly as defined in .env.example — do NOT rename or create alternatives",
        ]
        repository_manual_check = "Project directory exists with expected structure; the configured test command runs a real test suite"

    counter = 1
    for story in stories:
        story_id = story.get("id", "")
        if not story_id.startswith("ST-"):
            continue

        suffix = story_id[3:]
        if suffix.isdigit():
            counter = max(counter, int(suffix) + 1)

    def upsert_story(
        story_key,
        title,
        description,
        acceptance_criteria=None,
        scope_boundaries=None,
        expected_files=None,
        depends_on=None,
        validation=None,
    ):
        nonlocal counter

        generated_story = {
            "story_key": story_key,
            "title": title,
            "description": description,
            "acceptance_criteria": acceptance_criteria or [],
            "scope_boundaries": scope_boundaries or [],
            "expected_files": expected_files or [],
            "depends_on": depends_on or [],
            "validation": validation or dict(_DEFAULT_VALIDATION),
        }

        existing_index = _find_story_index(stories, story_key, title)
        if existing_index is not None:
            stories[existing_index] = _merge_story(
                stories[existing_index],
                generated_story,
            )
            return stories[existing_index]

        sid = f"ST-{counter:03d}"
        story = {
            "id": sid,
            **generated_story,
        }
        counter += 1
        stories.append(story)
        return story

    # ===================================================================
    # BOOTSTRAP STORIES
    # ===================================================================

    upsert_story(
        "bootstrap.repository",
        "Initialize project repository",
        f"Create project structure using {frontend} + {backend} + {database}.",
        acceptance_criteria=[
            repository_manifest_criteria,
            ".env.example exists with all required environment variables",
            ".env.local is already generated by the scaffold with working defaults — do NOT overwrite it",
            repository_tooling_criteria,
            repository_lint_criteria,
            test_framework_criteria,
            smoke_test_criteria,
            install_criteria,
            build_criteria,
            test_criteria,
        ],
        scope_boundaries=repository_scope_boundaries,
        expected_files=repository_expected_files,
        depends_on=[],
        validation=_validation(
            commands=bootstrap_validation_commands,
            manual_check=repository_manual_check,
        ),
    )

    if stack.get("database"):
        upsert_story(
            "bootstrap.database",
            "Setup database",
            f"Configure {database} database with connection pool and migrations.",
            acceptance_criteria=[
                f"{database} connection is configured via environment variable",
                "Database client or ORM is installed and configured",
                "Initial migration or schema setup runs without errors",
                "Connection can be verified programmatically",
                "docker-compose.yml includes database service" if database == "postgres" else f"{database} setup is documented",
                migration_criteria,
            ],
            scope_boundaries=[
                "Do NOT create application tables yet — only the connection layer",
                "Do NOT add seed data",
                "Do NOT implement any API endpoints",
                migration_dir_boundary,
            ],
            expected_files=[
                "docker-compose.yml" if database == "postgres" else f"docs/database-setup.md",
                _lib_path("db"),
                ".env.example (updated with DB connection string)",
            ],
            depends_on=["bootstrap.repository"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Database container starts and connection succeeds",
            ),
        )

    if stack.get("backend"):
        backend_ac = [
            f"Backend is initialized using {backend}",
            "Server starts and responds to health check",
            "API is accessible at the configured port",
        ]
        backend_files = []

        if backend in ("payload", "payload-cms"):
            backend_ac.append("Payload config file exists with database adapter configured")
            backend_ac.append("Payload admin panel is accessible at /admin")
            backend_files = [
                "src/payload.config.ts",
                "src/server.ts or src/app/(payload)/layout.tsx",
            ]
        else:
            backend_ac.append("Express or Fastify server starts with basic health endpoint")
            backend_files = [
                "src/server.ts",
                "src/api/health.ts",
            ]

        upsert_story(
            "bootstrap.backend",
            "Setup backend service",
            f"Initialize backend using {backend} with database connection.",
            acceptance_criteria=backend_ac,
            scope_boundaries=[
                "Do NOT implement authentication yet",
                "Do NOT create domain collections or models yet",
                "Do NOT add business logic — only the backend skeleton",
                "Use environment variable names exactly as defined in .env.example — do NOT rename or create alternatives",
            ],
            expected_files=backend_files,
            depends_on=["bootstrap.database"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Backend starts and /api/health or /admin responds",
            ),
        )

    if stack.get("frontend"):
        frontend_ac = [
            f"Frontend application renders using {frontend}",
            "Root page loads without errors",
            "Basic layout component exists (shell, navigation placeholder)",
        ]
        frontend_files = [
            _frontend_page_path(stack, "(app)"),
            _component_path("Layout"),
        ]

        if frontend in ("nextjs", "next.js", "next"):
            frontend_ac.append("Next.js app router is configured with route groups")
            frontend_files.append("src/app/layout.tsx")

        upsert_story(
            "bootstrap.frontend",
            "Create frontend application",
            f"Implement frontend application shell using {frontend}.",
            acceptance_criteria=frontend_ac,
            scope_boundaries=[
                "Do NOT implement pages beyond the root layout and a placeholder home page",
                "Do NOT add authentication UI — that is a separate story",
                "Do NOT style extensively — basic layout only",
                "Do NOT create files in src/pages/ — this project uses the App Router (src/app/) exclusively",
                "Use environment variable names exactly as defined in .env.example — do NOT rename or create alternatives",
            ],
            expected_files=frontend_files,
            depends_on=["bootstrap.backend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Frontend loads in browser without errors",
            ),
        )

    # ===================================================================
    # FEATURE STORIES
    # ===================================================================

    if "authentication" in features:
        auth_ac = [
            "Users can register with email and password — POST /api/auth/register returns 201 on success, 400 on validation error, 409 on duplicate email",
            "Users can log in and receive a valid session — POST /api/auth/login returns 200 with session token on success, 401 on invalid credentials",
            "Users can log out and have their session invalidated — POST /api/auth/logout returns 200 on success",
            "Protected routes return 401 for unauthenticated requests",
            "Passwords are hashed before storage",
        ]
        auth_files = [_lib_path("auth")]

        if backend in ("payload", "payload-cms"):
            auth_ac.append("Payload Users collection has auth enabled")
            auth_files.append(_backend_path(stack, "Users"))
        else:
            auth_files.append("src/api/auth.ts")

        auth_ac.append(migration_criteria)
        auth_files.append(_frontend_page_path(stack, "(auth)/login"))

        upsert_story(
            "feature.authentication",
            "Implement authentication",
            "Add registration, login, logout and session management.",
            acceptance_criteria=auth_ac,
            scope_boundaries=[
                "Do NOT implement OAuth or social login in this story",
                "Do NOT implement password reset or email verification",
                "Do NOT implement MFA",
                migration_dir_boundary,
            ],
            expected_files=auth_files,
            depends_on=["bootstrap.backend", "bootstrap.frontend"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can register, log in, and access protected route",
            ),
        )

    if "roles" in features:
        role_names = _get_role_names(spec)
        role_list_str = ", ".join(role_names)
        role_name_set = set(role_names)
        editorial_roles = {"admin", "editor", "reviewer"}.issubset(role_name_set)

        if editorial_roles:
            roles_ac = [
                f"Role model is defined with the following roles: {role_list_str}",
                "`editor` can create and update drafts but cannot publish, manage users, or change system configuration",
                "`reviewer` can review submissions and publish approved content but cannot manage users or global system configuration",
                "`admin` can manage users, configuration, and override editorial publish/archive actions",
                "Protected endpoints and admin collection/global access rules enforce the role matrix consistently",
                "Unauthorized role access returns 403",
                migration_criteria,
            ]
            roles_manual_check = "Editor can edit drafts but gets 403 on publish-only actions; reviewer can approve/publish; admin can manage users."
        else:
            roles_ac = [
                f"Role model is defined with the following roles: {role_list_str}",
                "Permissions are enforced on protected endpoints",
                "Admin users can manage other users' roles",
                "Unauthorized role access returns 403",
                migration_criteria,
            ]
            roles_manual_check = "Admin can access admin routes; regular user gets 403"

        roles_files = [_lib_path("permissions")]

        if backend in ("payload", "payload-cms"):
            if editorial_roles:
                roles_ac.append("Payload access control functions explicitly gate editorial collections/globals by admin/editor/reviewer responsibilities")
            else:
                roles_ac.append("Payload access control functions use role checks")
            roles_files.append(f"{_backend_path(stack, 'Users')} (updated with roles field)")
        else:
            roles_files.append("src/middleware/authorize.ts")

        upsert_story(
            "feature.roles",
            "Implement role-based access control",
            f"Define roles ({role_list_str}), permissions, and enforce authorization boundaries.",
            acceptance_criteria=roles_ac,
            scope_boundaries=[
                "Do NOT implement granular per-field permissions unless required by spec",
                "Do NOT implement a permissions admin UI — enforce in backend only",
                migration_dir_boundary,
            ],
            expected_files=roles_files,
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check=roles_manual_check,
            ),
        )

    if "media-library" in features:
        storage_backend = _get_storage_backend(spec)
        use_local = storage_backend in ("local_filesystem", "local_first", "local", "")
        media_kinds = _get_media_kinds(spec)
        media_depends = ["feature.authentication"]
        if "cms" in capabilities:
            media_depends.append("product.cms-content-model")

        media_ac = [
            "Users can upload images and files",
            "Uploaded media is stored and retrievable via URL",
            "Media list view shows uploaded assets with thumbnails",
            "File size and type validation is enforced on upload",
            migration_criteria,
        ]
        media_files = []
        media_boundaries = [
            "Do NOT implement image optimization or CDN delivery in this story",
            "Do NOT implement media usage tracking across content",
            migration_dir_boundary,
        ]

        if "cms" in capabilities:
            media_boundaries.insert(
                0,
                "Do NOT redefine the CMS schema here — extend the existing `media` collection from the CMS content model story with upload/storage behavior only",
            )

        if media_kinds:
            media_ac.append(
                f"Upload validation explicitly supports the media kinds required by the spec: {', '.join(media_kinds)}"
            )

        if backend in ("payload", "payload-cms"):
            if use_local:
                media_ac.append(
                    "Payload Media collection uses the local filesystem upload adapter "
                    "(store uploads in a `media/` directory at the project root)"
                )
                media_ac.append(
                    "The local filesystem path is treated as an adapter boundary so object storage can be introduced later without changing callers"
                )
                media_boundaries.append(
                    "Do NOT configure S3 or external object storage — use Payload's local disk adapter for now"
                )
            else:
                media_ac.append(
                    "Payload Media collection is configured with S3-compatible upload adapter"
                )
                media_ac.append(
                    "Storage environment variables are declared explicitly in `.env.example` (bucket, region, endpoint, access key, secret key)"
                )
            media_ac.append("Payload Media collection is configured with upload settings")
            media_files.append(_backend_path(stack, "Media"))
            media_files.append("src/payload.config.ts (updated with upload and storage settings)")
            media_files.append(".env.example (updated with storage configuration)")
        else:
            if use_local:
                media_ac.append(
                    "Uploads are stored on the local filesystem in a `media/` directory"
                )
                media_boundaries.append(
                    "Do NOT configure S3 or external object storage — use local disk for now"
                )
            else:
                media_ac.append(
                    "Uploads are stored in S3-compatible object storage"
                )
                media_ac.append(
                    "Storage environment variables are declared explicitly in `.env.example` (bucket, region, endpoint, access key, secret key)"
                )
            media_files.append("src/api/media.ts")
            media_files.append(_lib_path("storage"))
            media_files.append(".env.example (updated with storage configuration)")

        upsert_story(
            "feature.media-library",
            "Implement media library",
            "Allow uploading, listing, and managing media assets.",
            acceptance_criteria=media_ac,
            scope_boundaries=media_boundaries,
            expected_files=media_files,
            depends_on=media_depends,
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can upload an image or document, retrieve its URL, and see validation reject disallowed file types.",
            ),
        )

    if _feature_enabled_by_answers(spec, "draft-publish"):
        role_names = _get_role_names(spec)
        if {"admin", "editor", "reviewer"}.issubset(set(role_names)):
            publish_roles = [r for r in role_names if r in ("admin", "reviewer")]
        else:
            publish_roles = [r for r in role_names if r in ("admin", "reviewer", "editor")]
        if not publish_roles:
            publish_roles = ["admin"]
        publish_role_str = " or ".join(publish_roles)
        public_collections = _public_collection_names(spec)
        draft_depends = ["feature.roles"] if "roles" in features else ["feature.authentication"]
        if "cms" in capabilities:
            draft_depends.insert(0, "product.cms-content-model")

        if "cms" in capabilities:
            dp_ac = [
                f"Collections intended for public rendering ({', '.join(public_collections)}) support editorial states `draft`, `in_review`, and `published`",
                f"Editors can save drafts and reviewers/admins can transition content to published state ({publish_role_str})",
                "A draft can be sent back from review for changes without creating duplicate entries",
                "The query/filter layer used by future public rendering excludes draft entries unless preview/draft mode is explicitly active",
                "Publishing records a canonical published timestamp or Payload published-state equivalent used by later public rendering",
                migration_criteria,
            ]
        else:
            dp_ac = [
                "Content items have a status field with at least draft and published states",
                "Only authorized roles can transition content to published state",
                "Published content is visible through the appropriate surface",
                f"Draft content is only visible to {publish_role_str}",
                migration_criteria,
            ]

        if "roles" in features:
            dp_ac.append(f"Publishing requires {publish_role_str} role")

        dp_files = [_lib_path("content-status")]
        if "cms" in capabilities:
            dp_files.extend(_collection_file_path(stack, name) for name in public_collections)

        upsert_story(
            "feature.draft-publish",
            "Implement draft and publish workflow",
            "Add draft, review, and publish states with role-based transitions.",
            acceptance_criteria=dp_ac,
            scope_boundaries=[
                "Do NOT implement versioning or revision history",
                "Do NOT implement scheduled publishing — that is a separate story",
                "Do NOT implement approval notifications",
                "Do NOT implement public page components in this story — only the workflow and publish visibility rules",
                migration_dir_boundary,
            ],
            expected_files=dp_files,
            depends_on=draft_depends,
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can create a draft, submit/review it, publish it, and confirm only published entries are returned by the public-facing query/filter path.",
            ),
        )

    if _feature_enabled_by_answers(spec, "preview") and _feature_enabled_by_answers(spec, "draft-publish"):
        preview_depends = ["feature.draft-publish"]
        preview_files = [_lib_path("preview")]
        preview_ac = [
            "Draft content can be previewed through a unique preview URL or mode",
            "Preview renders content as it would appear when published",
            "Preview is only accessible to authenticated users with appropriate roles",
            "Preview does not leak draft content to public or search engines",
        ]
        preview_boundaries = [
            "Do NOT implement live editing or inline editing",
            "Do NOT implement preview for multiple content types — start with the primary type",
        ]
        preview_manual_check = "Can preview draft content via preview URL while logged in"

        if "cms" in capabilities and "public-site" in capabilities:
            preview_collections = _public_collection_names(spec)
            preview_depends.append("product.public-site-rendering")
            preview_files = [
                "src/app/api/preview/route.ts",
                "src/app/api/exit-preview/route.ts",
                _lib_path("preview"),
            ]
            preview_files.extend(
                _frontend_page_path(stack, f"(public)/{name}/[slug]") for name in preview_collections
            )
            preview_ac = [
                "A preview entry route/handler enables draft mode only for authenticated editorial roles",
                f"Preview accepts collection + slug lookup for {', '.join(preview_collections)} and resolves draft content with the same loaders used by public pages",
                "Preview mode can be exited explicitly and public routes immediately return to published-only behavior",
                "Preview responses are marked no-store/noindex and do not leak draft content to anonymous users or search engines",
            ]
            preview_boundaries = [
                "Do NOT implement live editing or inline editing",
                "Do NOT create a separate second public site just for preview",
                "Do NOT allow anonymous preview links in this story",
            ]
            preview_manual_check = "While logged in as an editorial role, enable preview for a draft page/post, verify it renders, then exit preview and confirm the public slug still hides the draft."

        upsert_story(
            "feature.preview",
            "Implement content preview",
            "Allow previewing unpublished content in the frontend.",
            acceptance_criteria=preview_ac,
            scope_boundaries=preview_boundaries,
            expected_files=preview_files,
            depends_on=preview_depends,
            validation=_validation(
                commands=["npm run build"],
                manual_check=preview_manual_check,
            ),
        )

    if _feature_enabled_by_answers(spec, "scheduled-publishing") and _feature_enabled_by_answers(spec, "draft-publish"):
        sched_depends = ["feature.draft-publish"]
        sched_files = [
            _lib_path("scheduler"),
            "src/jobs/publish-scheduled.ts",
            ".env.example (updated with SCHEDULED_PUBLISH_CRON or equivalent scheduler interval)",
        ]
        sched_ac = [
            "node-cron (or equivalent) is installed as a dependency",
            "A cron job is registered from application startup and runs on a configurable interval (default: every minute)",
            "Content items can have a publishAt date/time field",
            "The cron job queries for content where publishAt <= now AND status = 'scheduled', and transitions it to 'published'",
            "Each publish attempt is logged with timestamp, content ID, and outcome",
            "Failed publish attempts are logged and retried on the next cron cycle",
            "The job is idempotent — running it twice does not double-publish",
            migration_criteria,
        ]

        if "cms" in capabilities:
            public_collections = _public_collection_names(spec)
            sched_depends.insert(0, "product.cms-content-model")
            sched_files.extend(_collection_file_path(stack, name) for name in public_collections)
            sched_ac.insert(
                3,
                f"Collections {', '.join(public_collections)} expose scheduling fields/state used by the job without changing slug-based public lookup",
            )

        if "cms" in capabilities and "public-site" in capabilities:
            sched_depends.append("product.public-site-rendering")
            sched_ac.append(
                "Successful scheduled publishes make content visible to the existing public rendering path without requiring a manual republish"
            )
            sched_ac.append(
                "Publish success triggers the existing public-rendering refresh/revalidation path or logs that it must happen immediately"
            )
            sched_files.append(_lib_path("publishing"))
            sched_manual_check = "Set a draft page/post to `scheduled` with a near-future publishAt, wait for one cron cycle, and verify the public route starts serving it automatically."
        else:
            sched_ac.append("Published content appears on the appropriate surface after the scheduled time")
            sched_manual_check = "Set publishAt to the near future, wait for one cron cycle, and verify the item transitions from scheduled to published automatically."

        if backend in ("payload", "payload-cms"):
            sched_files.append("src/server.ts or payload startup entry (updated to register scheduler)")

        upsert_story(
            "feature.scheduled-publishing",
            "Implement scheduled publishing",
            "Install node-cron, create a background job that publishes content at the scheduled time.",
            acceptance_criteria=sched_ac,
            scope_boundaries=[
                "Do NOT implement a full job queue system (Bull, BullMQ) — node-cron is sufficient",
                "Do NOT implement scheduled unpublishing in this story",
                "Do NOT implement a job dashboard or management UI",
                migration_dir_boundary,
            ],
            expected_files=sched_files,
            depends_on=sched_depends,
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check=sched_manual_check,
            ),
        )

    if "search" in features:
        upsert_story(
            "feature.search",
            "Implement search",
            "Add search functionality across the application.",
            acceptance_criteria=[
                "Users can search for content or records via a search input",
                "Search results are relevant and ordered by relevance or date",
                "Search handles empty queries and no-results gracefully",
                "Search responds within acceptable latency for typical dataset sizes",
            ],
            scope_boundaries=[
                "Do NOT implement full-text search engine integration (Elasticsearch, etc.) — use database search",
                "Do NOT implement faceted search or advanced filters in this story",
            ],
            expected_files=[
                _component_path("SearchInput"),
                _frontend_page_path(stack, "search"),
            ],
            depends_on=["bootstrap.frontend", "bootstrap.backend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Can search and see relevant results",
            ),
        )

    if "payments" in features:
        upsert_story(
            "feature.payments",
            "Integrate payment provider",
            "Integrate payment processing for transactions.",
            acceptance_criteria=[
                "Payment provider SDK is installed and configured",
                "Users can initiate a payment flow",
                "Successful payments are recorded in the database",
                "Failed payments are handled gracefully with user feedback",
                "Payment webhooks are handled for async confirmation",
            ],
            scope_boundaries=[
                "Do NOT implement subscription billing — that is a separate story if needed",
                "Do NOT implement refunds in this story",
                "Do NOT store raw card data — use the provider's tokenization",
            ],
            expected_files=[
                _lib_path("payments"),
                "src/api/webhooks/payment.ts",
            ],
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can complete a test payment flow in sandbox/test mode",
            ),
        )

    if "notifications" in features:
        upsert_story(
            "feature.notifications",
            "Implement notification system",
            "Add notification delivery for important events.",
            acceptance_criteria=[
                "Notifications can be created programmatically for events",
                "Users can see their notifications in the UI",
                "Notifications have read/unread state",
                "Notification preferences or rules can be configured per user",
            ],
            scope_boundaries=[
                "Do NOT implement email or push notification delivery in this story",
                "Do NOT implement real-time WebSocket delivery — polling or page-load is sufficient",
            ],
            expected_files=[
                _backend_path(stack, "Notifications") if backend in ("payload", "payload-cms") else "src/api/notifications.ts",
                _component_path("NotificationCenter"),
                _lib_path("notifications"),
            ],
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Can trigger a notification and see it in the UI",
            ),
        )

    if "i18n" in capabilities and "cms" not in capabilities:
        upsert_story(
            "feature.i18n-setup",
            "Setup internationalization routing and locale detection",
            "Configure Next.js middleware for locale-based routing and set up i18n infrastructure.",
            acceptance_criteria=[
                "next-intl or equivalent i18n library is installed and configured",
                "Middleware detects locale from Accept-Language header or URL prefix and redirects accordingly",
                "Default locale is configured (e.g. 'en')",
                "Route group `src/app/[locale]/` exists and serves as the root for all localized pages",
                "ALL existing pages (including todos, reports, dashboard, etc.) are MOVED into `src/app/[locale]/` — no page.tsx files should remain outside `[locale]/` except the root redirect and API routes",
                "A LocaleSwitcher component exists for switching between locales",
                "Translation files or message catalogs exist for at least 2 locales",
            ],
            scope_boundaries=[
                "Do NOT leave any page.tsx files outside `src/app/[locale]/` (except `src/app/page.tsx` which should redirect to `/{defaultLocale}`) — orphan routes will return 404 because middleware redirects all non-API requests to `/{locale}/...`",
                "Do NOT translate all content yet — set up the infrastructure and translate key UI strings only",
                "Do NOT implement locale-specific formatting (dates, numbers) in this story",
                "Do NOT create files in src/pages/ — this project uses the App Router exclusively",
            ],
            expected_files=[
                "src/middleware.ts",
                "src/app/[locale]/layout.tsx",
                "src/app/[locale]/(app)/page.tsx",
                _component_path("LocaleSwitcher"),
                "src/i18n/messages/en.json",
                "src/i18n/messages/pt.json or src/i18n/messages/es.json",
            ],
            depends_on=["bootstrap.frontend"],
            validation=_validation(
                commands=["npm run build", "npm run typecheck"],
                manual_check="Visiting / redirects to /en; visiting /en/todos works; LocaleSwitcher changes locale; no orphan routes outside [locale]/",
            ),
        )

    if "analytics" in features:
        upsert_story(
            "feature.analytics",
            "Implement analytics tracking",
            "Add analytics instrumentation for usage tracking.",
            acceptance_criteria=[
                "Analytics events are tracked for key user actions",
                "Event data is sent to the configured analytics backend",
                "Analytics does not block UI rendering or degrade performance",
                "Page views are tracked automatically",
            ],
            scope_boundaries=[
                "Do NOT implement a custom analytics dashboard",
                "Do NOT implement server-side analytics in this story",
            ],
            expected_files=[
                _lib_path("analytics"),
                _component_path("AnalyticsProvider"),
            ],
            depends_on=["bootstrap.frontend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Analytics events appear in the configured provider",
            ),
        )

    if "billing" in features:
        upsert_story(
            "feature.billing",
            "Implement billing and subscription management",
            "Add billing flows, subscription management, and payment lifecycle.",
            acceptance_criteria=[
                "Users can subscribe to a plan",
                "Subscription status is tracked in the database",
                "Billing portal or management UI exists for users",
                "Subscription webhooks are handled for lifecycle events",
                "Trial periods are supported if configured",
            ],
            scope_boundaries=[
                "Do NOT implement custom invoicing",
                "Do NOT implement multiple payment methods — start with card via provider",
            ],
            expected_files=[
                _lib_path("billing"),
                "src/api/webhooks/billing.ts",
                _frontend_page_path(stack, "(app)/billing"),
            ],
            depends_on=["feature.authentication", "feature.payments"] if "payments" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can subscribe to a plan in sandbox/test mode",
            ),
        )

    # ===================================================================
    # PRODUCT SHAPE STORIES
    # ===================================================================

    if app_shape == "internal-work-organizer" or primary_audience == "internal_teams":
        upsert_story(
            "product.internal-dashboard",
            "Build internal dashboard shell",
            "Create the main internal application shell and navigation for team workflows.",
            acceptance_criteria=[
                "Application shell renders with sidebar navigation",
                "Navigation includes links to main work sections",
                "Dashboard home shows a summary or placeholder content",
                "Shell is responsive and works on common screen sizes",
            ],
            scope_boundaries=[
                "Do NOT implement data tables or work item views — those are separate stories",
                "Do NOT add real data — use placeholder content for the shell",
            ],
            expected_files=[
                _component_path("AppShell"),
                _component_path("SidebarNav"),
                _frontend_page_path(stack, "(app)/dashboard"),
            ],
            depends_on=["feature.authentication", "feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Dashboard shell renders with navigation after login",
            ),
        )

    if app_shape == "client-portal":
        upsert_story(
            "product.client-portal-shell",
            "Build client portal shell",
            "Create the client-facing application shell, navigation, and access control.",
            acceptance_criteria=[
                "Client-facing shell renders with appropriate navigation",
                "Access is restricted to authenticated client users",
                "Navigation includes links to requests, status tracking, and account",
                "Shell distinguishes between client and internal views",
            ],
            scope_boundaries=[
                "Do NOT implement request submission forms — that is a separate story",
                "Do NOT implement internal reviewer views in this story",
            ],
            expected_files=[
                _component_path("PortalShell"),
                _frontend_page_path(stack, "(portal)/dashboard"),
            ],
            depends_on=["feature.authentication", "feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Client portal shell renders after login with client role",
            ),
        )

    if app_shape == "backoffice":
        upsert_story(
            "product.backoffice-shell",
            "Build backoffice application shell",
            "Create the internal backoffice shell with navigation, filtering, and operational views.",
            acceptance_criteria=[
                "Backoffice shell renders with sidebar navigation and top bar",
                "Navigation includes links to operational sections (orders, tasks, reports, etc.)",
                "Filtering and search placeholders are present in the shell",
                "Shell supports compact, data-dense layout suitable for operations",
            ],
            scope_boundaries=[
                "Do NOT implement actual data views or CRUD — only the shell and navigation",
                "Do NOT implement reports or charts in this story",
            ],
            expected_files=[
                _component_path("BackofficeShell"),
                _component_path("SidebarNav"),
                _component_path("TopBar"),
                _frontend_page_path(stack, "(admin)/dashboard"),
            ],
            depends_on=["feature.authentication", "feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Backoffice shell renders with navigation after admin login",
            ),
        )

    if app_shape == "content-platform":
        upsert_story(
            "product.content-platform-shell",
            "Build content platform shell",
            "Create the content management and delivery shell with editorial navigation.",
            acceptance_criteria=[
                "Admin shell renders with editorial navigation (content, media, settings)",
                "Shell supports both admin and public route groups if public-site capability exists",
                "Content list and detail views have placeholder layouts",
            ],
            scope_boundaries=[
                "Do NOT implement actual content CRUD — only the navigation shell",
                "Do NOT implement the public site layout in this story if public-site capability exists",
            ],
            expected_files=[
                _frontend_page_path(stack, "(admin)/content"),
                _component_path("AdminShell"),
            ],
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Admin content shell renders with editorial navigation",
            ),
        )

    # ===================================================================
    # PUBLIC SITE RENDERING (CMS + public-site capability)
    # ===================================================================

    if "public-site" in capabilities and "cms" in capabilities:
        public_col_names = _public_collection_names(spec)
        global_names = [name.get("name", "").strip().lower() for name in _get_content_globals(spec) if isinstance(name, dict) and name.get("name")]

        public_ac = [
            f"Public route `/{name}/[slug]` exists and renders published content for the `{name}` collection"
            for name in public_col_names
        ]
        public_ac.extend([
            "Each public route loads content by unique slug from the matching CMS collection instead of hardcoded page data",
            "Public pages use SSR or ISR for SEO (meta tags, Open Graph)",
            "Only published content is visible on public routes — draft content returns 404",
            "Public pages are accessible without authentication",
            "Published-only filtering is enforced in the data loader/query layer, not just in the UI",
            "Public layout includes navigation derived from site-settings global (if it exists)",
        ])

        if "homepage" in global_names:
            public_ac.append("The public home page (`/`) renders data from the `homepage` global instead of placeholder content")
        if "authors" in [c.get("name", "").strip().lower() for c in _get_content_collections(spec) if isinstance(c, dict)]:
            public_ac.append("Post pages render author attribution from the `authors` collection when author data exists")

        public_files = []
        for name in public_col_names:
            public_files.append(_frontend_page_path(stack, f"(public)/{name}/[slug]"))
        public_files.append(_frontend_page_path(stack, "(public)"))
        # BUG-038: FE-ST-013 must own (app)/page.tsx so it can remove/relocate
        # the placeholder home page created by bootstrap.frontend — otherwise
        # both (app)/page.tsx and (public)/page.tsx resolve to "/" and Next.js
        # rejects the build with a duplicate route error.
        public_files.append(_frontend_page_path(stack, "(app)"))
        public_files.append(_component_path("PublicLayout"))
        public_files.append(_lib_path("public-content"))

        public_depends = ["product.cms-content-model"]
        if _feature_enabled_by_answers(spec, "draft-publish"):
            public_depends.append("feature.draft-publish")
        else:
            public_depends.append("bootstrap.frontend")
        if "infra.static-delivery" in [s.get("story_key") for s in stories]:
            public_depends.append("infra.static-delivery")

        upsert_story(
            "product.public-site-rendering",
            "Implement public site pages",
            f"Create public-facing pages for published content: {', '.join(public_col_names)}.",
            acceptance_criteria=public_ac,
            scope_boundaries=[
                "Do NOT redefine CMS collections or globals in this story — reuse the content model already established",
                "Do NOT implement comments or user interaction on public pages",
                "Do NOT implement search on public pages — that is a separate story",
                "Do NOT implement pagination in this story — show latest items only",
            ],
            expected_files=public_files,
            depends_on=public_depends,
            validation=_validation(
                commands=["npm run build"],
                manual_check="Public pages render published content from CMS data loaders; draft content returns 404; homepage pulls from globals when configured.",
            ),
        )

    # ===================================================================
    # CORE WORK FEATURE STORIES
    # ===================================================================

    if "deadlines" in core_work_features:
        upsert_story(
            "product.deadlines",
            "Model deadlines and due dates",
            "Implement domain support for deadlines, due dates, and related validations.",
            acceptance_criteria=[
                "Work items have a dueDate field",
                "Overdue items are identifiable via query or computed field",
                "UI displays due date and overdue status clearly",
                "Due date can be set and updated by authorized roles",
            ],
            scope_boundaries=[
                "Do NOT implement reminder notifications — that is a separate story",
                "Do NOT implement recurring deadlines",
            ],
            expected_files=[
                _lib_path("deadlines"),
            ],
            depends_on=["product.internal-dashboard"] if app_shape == "internal-work-organizer" else ["bootstrap.backend"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can set a due date and see overdue status",
            ),
        )

    if "progress-tracking" in core_work_features or "progress tracking" in core_work_features or "project-tracking" in core_work_features or "project tracking" in core_work_features:
        upsert_story(
            "product.progress-tracking",
            "Implement progress tracking",
            "Add progress tracking and status transitions for core work items.",
            acceptance_criteria=[
                "Work items have a status field with defined states and valid transitions",
                "Status transitions are enforced — invalid transitions return an error",
                "UI reflects current status with visual indicators",
                "Status history is tracked or at least the last transition is logged",
            ],
            scope_boundaries=[
                "Do NOT implement Kanban or drag-and-drop UI",
                "Do NOT implement automated status transitions",
            ],
            expected_files=[
                _lib_path("status-machine"),
            ],
            depends_on=["product.internal-dashboard"] if app_shape == "internal-work-organizer" else ["bootstrap.backend"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can transition a work item through valid states",
            ),
        )

    if "task-assignment" in core_work_features or "task assignment" in core_work_features:
        upsert_story(
            "product.task-assignment",
            "Implement task assignment",
            "Allow work items to be assigned to owners and teams.",
            acceptance_criteria=[
                "Work items have an assignee field referencing a user",
                "Authorized roles can assign and reassign work items",
                "Assigned user can see their assignments in a filtered view",
                "Unassigned items are identifiable",
            ],
            scope_boundaries=[
                "Do NOT implement workload balancing or auto-assignment",
                "Do NOT implement team-based assignment — start with individual assignment",
            ],
            expected_files=[
                _component_path("AssigneeSelect"),
            ],
            depends_on=["feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can assign a work item and see it in the assignee's view",
            ),
        )

    if "reminders" in core_work_features:
        upsert_story(
            "product.reminders",
            "Implement reminders",
            "Add reminder workflows for approaching deadlines and pending work.",
            acceptance_criteria=[
                "Reminders are generated for work items approaching their due date",
                "Reminders appear in the notification center or a dedicated view",
                "Reminder timing is configurable (e.g., 1 day before, same day)",
                "Completed items do not generate reminders",
            ],
            scope_boundaries=[
                "Do NOT implement email or push delivery for reminders",
                "Do NOT implement custom reminder rules per user",
            ],
            expected_files=[
                "src/jobs/generate-reminders.ts",
                _lib_path("reminders"),
            ],
            depends_on=["product.deadlines"] if "deadlines" in core_work_features else ["bootstrap.backend"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Reminder appears for a work item near its due date",
            ),
        )

    if "report-generation" in core_work_features or "report generation" in core_work_features:
        upsert_story(
            "product.report-generation",
            "Implement report generation",
            "Generate summary reports for work progress and operational visibility.",
            acceptance_criteria=[
                "At least one report type is available (e.g., weekly summary, status distribution)",
                "Report data is queried from the database, not hardcoded",
                "Report is viewable in the UI with appropriate formatting",
                "Report can be filtered by date range or team",
            ],
            scope_boundaries=[
                "Do NOT implement PDF export in this story",
                "Do NOT implement scheduled report delivery",
                "Do NOT implement custom report builder",
            ],
            expected_files=[
                _frontend_page_path(stack, "(app)/reports"),
                "src/api/reports.ts" if backend not in ("payload", "payload-cms") else _lib_path("reports"),
            ],
            depends_on=["product.internal-dashboard"] if app_shape == "internal-work-organizer" else ["bootstrap.backend", "bootstrap.frontend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Report page shows data from the database with date filtering",
            ),
        )

    if "approvals" in core_work_features:
        upsert_story(
            "product.approvals",
            "Implement approval workflows",
            "Add approval steps and sign-off flows for work items that require review.",
            acceptance_criteria=[
                "Work items can be submitted for approval",
                "Designated approvers can approve or reject submissions",
                "Approval status is tracked and visible in the UI",
                "Rejected items can be revised and resubmitted",
            ],
            scope_boundaries=[
                "Do NOT implement multi-step approval chains",
                "Do NOT implement approval delegation or escalation",
            ],
            expected_files=[
                _lib_path("approvals"),
            ],
            depends_on=["feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can submit for approval, approve, and see status change",
            ),
        )

    if "team-visibility" in core_work_features or "team visibility" in core_work_features:
        upsert_story(
            "product.team-visibility",
            "Implement team visibility",
            "Add team-level views showing workload distribution, progress, and capacity.",
            acceptance_criteria=[
                "Team view shows all team members and their assigned work items",
                "Workload distribution is visible (items per person or similar metric)",
                "Team view supports filtering by status or date",
                "Only team leads or admins can see the team view",
            ],
            scope_boundaries=[
                "Do NOT implement capacity planning or forecasting",
                "Do NOT implement cross-team comparisons",
            ],
            expected_files=[
                _frontend_page_path(stack, "(app)/team"),
                _component_path("TeamWorkloadView"),
            ],
            depends_on=[
                "product.task-assignment" if "task-assignment" in core_work_features else "feature.roles",
            ],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Team view shows members and their workload after login as team lead",
            ),
        )

    # ===================================================================
    # AUTOMATION STORIES
    # ===================================================================

    if "scheduled-jobs" in capabilities:
        if app_shape in {"internal-work-organizer", "backoffice", "worker-pipeline"}:
            upsert_story(
                "product.automation-jobs",
                "Implement workflow automation jobs",
                "Implement scheduled jobs for reminders, progress automation, or recurring operational tasks.",
                acceptance_criteria=[
                    "At least one scheduled job runs on a configurable interval",
                    "Job execution is logged with timestamps and outcomes",
                    "Failed jobs are retried or flagged for manual intervention",
                    "Jobs do not block the main application process",
                ],
                scope_boundaries=[
                    "Do NOT implement a full job queue system — a simple scheduler is sufficient for MVP",
                    "Do NOT implement job management UI",
                ],
                expected_files=[
                    "src/jobs/index.ts",
                    _lib_path("scheduler"),
                ],
                depends_on=["bootstrap.backend"],
                validation=_validation(
                    commands=["npm run build", "npm test"],
                    manual_check="Scheduled job runs and logs output on interval",
                ),
            )
        elif needs_scheduled_jobs is True and app_shape not in {"content-platform"}:
            upsert_story(
                "product.automation-jobs",
                "Implement background automation jobs",
                "Implement scheduled and background jobs for application automation workflows.",
                acceptance_criteria=[
                    "At least one background job runs on a configurable interval",
                    "Job execution is logged with timestamps and outcomes",
                    "Failed jobs are retried or flagged",
                    "Jobs run independently of the main application process",
                ],
                scope_boundaries=[
                    "Do NOT implement a distributed job queue",
                    "Do NOT implement job management UI",
                ],
                expected_files=[
                    "src/jobs/index.ts",
                    _lib_path("scheduler"),
                ],
                depends_on=["bootstrap.backend"],
                validation=_validation(
                    commands=["npm run build", "npm test"],
                    manual_check="Background job runs and logs output",
                ),
            )

    # ===================================================================
    # TODO-APP SPECIFIC STORIES
    # ===================================================================

    archetype = spec.get("archetype", "")

    if archetype == "todo-app" or app_shape == "todo-list":
        upsert_story(
            "product.todo-model",
            "Implement Todo data model",
            "Create the Todo entity with all fields and database schema.",
            acceptance_criteria=[
                "Todo model exists with fields: title (required), description (optional), completed (boolean, default false), dueDate (optional), priority (enum: low/medium/high, default medium), createdAt, updatedAt",
                "Database migration creates the todos table with proper types and indexes",
                "Todo belongs to a User via userId foreign key",
                "Database migration is generated and executed for schema changes",
            ],
            scope_boundaries=[
                "Do NOT implement API endpoints yet — only the data model and migration",
                "Do NOT implement tags, categories, or recurring todos",
                "Do NOT implement soft-delete",
                migration_dir_boundary,
            ],
            expected_files=[
                "src/models/todo.ts",
                _lib_path("db"),
            ],
            depends_on=["bootstrap.database", "feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Migration runs and todos table exists in database",
            ),
        )

        upsert_story(
            "product.todo-api",
            "Implement Todo CRUD API",
            "Create REST API endpoints for creating, reading, updating, and deleting todos.",
            acceptance_criteria=[
                "POST /api/todos creates a new todo for the authenticated user",
                "GET /api/todos returns all todos for the authenticated user",
                "PATCH /api/todos/:id updates a todo (title, description, completed, dueDate, priority)",
                "DELETE /api/todos/:id permanently deletes a todo",
                "All endpoints require authentication and enforce owner-only access",
                "Invalid requests return appropriate error responses (400, 401, 404)",
            ],
            scope_boundaries=[
                "Do NOT implement filtering or sorting yet — that is a separate story",
                "Do NOT implement bulk operations",
                "Do NOT implement pagination yet",
            ],
            expected_files=[
                "src/api/todos.ts or src/app/api/todos/route.ts",
                "src/api/todos/[id].ts or src/app/api/todos/[id]/route.ts",
            ],
            depends_on=["product.todo-model"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can create, read, update, delete a todo via API while authenticated",
            ),
        )

        upsert_story(
            "product.todo-ui",
            "Implement Todo list UI",
            "Create the frontend todo list with add, toggle, and delete functionality.",
            acceptance_criteria=[
                "Todo list page shows all todos for the logged-in user",
                "User can add a new todo with title (required) and optional fields",
                "User can toggle a todo between pending and completed",
                "User can delete a todo with confirmation",
                "Completed todos are visually distinct (strikethrough or dimmed)",
                "Empty state is shown when no todos exist",
                "Loading state is shown while fetching",
            ],
            scope_boundaries=[
                "Do NOT implement drag-and-drop reordering",
                "Do NOT implement inline editing — use a form or modal",
                "Do NOT implement filtering UI yet",
            ],
            expected_files=[
                _frontend_page_path(stack, "(app)/todos"),
                _component_path("TodoList"),
                _component_path("TodoItem"),
                _component_path("AddTodoForm"),
            ],
            depends_on=["product.todo-api", "bootstrap.frontend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Can see todo list, add a todo, toggle it, and delete it in the browser",
            ),
        )

        upsert_story(
            "product.todo-filtering",
            "Implement Todo filtering and sorting",
            "Add ability to filter todos by status and sort by date or priority.",
            acceptance_criteria=[
                "User can filter todos: All, Pending, Completed",
                "User can sort todos by: newest first, oldest first, priority (high to low)",
                "Filter and sort state persists during the session (not across page reloads)",
                "API supports query params: ?completed=true|false&sort=createdAt|priority&order=asc|desc",
                "URL reflects current filter state for shareability",
            ],
            scope_boundaries=[
                "Do NOT implement full-text search",
                "Do NOT implement tag-based filtering",
                "Do NOT implement saved filter presets",
            ],
            expected_files=[
                _component_path("TodoFilters"),
            ],
            depends_on=["product.todo-ui"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Can filter by pending/completed and sort by date or priority",
            ),
        )

    for story in stories:
        story["execution"] = _build_execution_metadata(story)

    return stories
