"""Tests for scaffold_engine.py.

Covers:
- File creation for Payload vs node-api backends
- package.json dependencies per backend
- docker-compose per database (postgres, mongodb, sqlite)
- .env.example content per database/backend
- tsconfig Payload-specific paths
- Payload-specific file generation
- Dockerfile and README content
- Port derivation from slug
"""

import json
from pathlib import Path

from initializer.renderers.scaffold_engine import write_scaffold


def _make_spec(**overrides):
    spec = {
        "answers": {
            "project_name": "Test Project",
            "project_slug": "test-project",
            "summary": "A test project.",
            "surface": "internal_admin_only",
            "deploy_target": "docker",
        },
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "capabilities": ["scheduled-jobs"],
        "features": ["authentication", "api"],
    }
    spec.update(overrides)
    return spec


# -------------------------------------------------------
# Core file creation
# -------------------------------------------------------


def test_scaffold_creates_root_config_files(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    for filename in [
        "docker-compose.yml",
        ".env.example",
        ".gitignore",
        "tsconfig.json",
        "next-env.d.ts",
        "vitest.config.ts",
        "package.json",
        "next.config.ts",
        "postcss.config.mjs",
        "eslint.config.mjs",
        "Dockerfile",
        "README.md",
    ]:
        assert (tmp_path / filename).exists(), f"Missing: {filename}"

    assert not (tmp_path / "tsconfig.test.json").exists()


def test_scaffold_creates_nextjs_app_files(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    assert (tmp_path / "src/app/layout.tsx").exists()
    assert (tmp_path / "src/app/page.tsx").exists()
    assert (tmp_path / "src/app/globals.css").exists()
    assert (tmp_path / "src/__tests__/smoke.test.ts").exists()


def test_scaffold_creates_placeholder_dirs(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    assert (tmp_path / "src/lib/.gitkeep").exists()
    assert (tmp_path / "src/components/.gitkeep").exists()
    assert (tmp_path / "public/.gitkeep").exists()


# -------------------------------------------------------
# node-api backend (non-Payload)
# -------------------------------------------------------


def test_node_api_package_json_has_express_deps(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())

    assert "express" in pkg["dependencies"]
    assert "cors" in pkg["dependencies"]
    assert "helmet" in pkg["dependencies"]
    assert "@types/express" in pkg["devDependencies"]
    assert "@types/cors" in pkg["devDependencies"]


def test_node_api_package_json_has_no_payload_deps(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())

    assert "payload" not in pkg["dependencies"]
    assert "@payloadcms/next" not in pkg["dependencies"]


def test_node_api_has_no_npmrc(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    assert not (tmp_path / ".npmrc").exists()


def test_node_api_has_no_payload_files(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    assert not (tmp_path / "src/payload.config.ts").exists()
    assert not (tmp_path / "src/collections/Users.ts").exists()
    assert not (tmp_path / "src/app/(payload)").exists()


def test_node_api_next_config_has_no_payload(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "next.config.ts").read_text()
    assert "withPayload" not in content


# -------------------------------------------------------
# Payload backend
# -------------------------------------------------------


def _payload_spec(**overrides):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "payload",
        "database": "postgres",
    })
    spec.update(overrides)
    return spec


def test_payload_package_json_has_payload_deps(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())

    assert "payload" in pkg["dependencies"]
    assert "@payloadcms/next" in pkg["dependencies"]
    assert "@payloadcms/richtext-lexical" in pkg["dependencies"]
    assert "@payloadcms/db-postgres" in pkg["dependencies"]
    assert "graphql" in pkg["dependencies"]
    assert "pg" in pkg["dependencies"]
    assert "sharp" in pkg["dependencies"]


def test_payload_package_json_has_disable_transpile_scripts(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())
    scripts = pkg["scripts"]

    assert scripts["generate:types"] == "payload --disable-transpile generate:types"
    assert scripts["db:migrate"] == "node ./scripts/payload-migrations.mjs migrate"
    assert scripts["db:migrate:create"] == "node ./scripts/payload-migrations.mjs create"
    assert scripts["db:migrate:status"] == "node ./scripts/payload-migrations.mjs status"


def test_payload_package_json_pins_next_version(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())

    # Payload pins Next.js to an exact version, not ^15
    assert pkg["dependencies"]["next"] == "15.4.11"


def test_payload_package_json_has_no_express_deps(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())

    assert "express" not in pkg["dependencies"]


def test_payload_creates_npmrc(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / ".npmrc").read_text()
    assert "legacy-peer-deps=true" in content


def test_payload_creates_payload_specific_files(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    assert (tmp_path / "src/payload.config.ts").exists()
    assert (tmp_path / "src/collections/Users.ts").exists()
    assert (tmp_path / "src/__tests__/setup-env.ts").exists()
    assert (tmp_path / "src/app/(payload)/admin/[[...segments]]/page.tsx").exists()
    assert (tmp_path / "src/app/(payload)/admin/[[...segments]]/not-found.tsx").exists()
    assert (tmp_path / "src/app/(payload)/layout.tsx").exists()
    assert (tmp_path / "src/app/(payload)/custom.scss").exists()
    assert (tmp_path / "src/app/(payload)/importMap.ts").exists()
    assert (tmp_path / "scripts/payload-migrations.mjs").exists()


def test_node_api_has_no_payload_bootstrap_helpers(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    assert not (tmp_path / "src/__tests__/setup-env.ts").exists()
    assert not (tmp_path / "scripts/payload-migrations.mjs").exists()


def test_payload_admin_page_imports_importmap_from_correct_path(tmp_path):
    """page.tsx lives in admin/[[...segments]]/ — must reach ../../importMap, not ./importMap."""
    write_scaffold(tmp_path, _payload_spec())

    page = (tmp_path / "src/app/(payload)/admin/[[...segments]]/page.tsx").read_text()
    assert '../../importMap' in page, "page.tsx must import importMap via ../../importMap"
    assert './importMap"' not in page.replace("../../importMap", ""), (
        "page.tsx must not use ./importMap (wrong relative path)"
    )

    not_found = (tmp_path / "src/app/(payload)/admin/[[...segments]]/not-found.tsx").read_text()
    assert '../../importMap' in not_found, "not-found.tsx must import importMap via ../../importMap"
    assert 'params, searchParams' in not_found, "not-found.tsx must pass params and searchParams to NotFoundPage"


def test_payload_layout_passes_server_function(tmp_path):
    """Payload v3.79+ requires serverFunction prop on RootLayout."""
    write_scaffold(tmp_path, _payload_spec())

    layout = (tmp_path / "src/app/(payload)/layout.tsx").read_text()
    assert "serverFunction" in layout, "layout must pass serverFunction to RootLayout"
    assert "handleServerFunctions" in layout, "layout must import handleServerFunctions"
    assert '"use server"' in layout, "serverFunction must be a server action"


def test_payload_config_references_database_uri(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / "src/payload.config.ts").read_text()
    assert "DATABASE_URI" in content
    assert "PAYLOAD_SECRET" in content
    assert "postgresAdapter" in content
    assert 'migrationDir: path.resolve(dirname, "lib/migrations")' in content


def test_payload_config_rejects_missing_secret(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / "src/payload.config.ts").read_text()
    assert "PLEASE-CHANGE-ME" not in content
    assert 'throw new Error("PAYLOAD_SECRET env var is required")' in content


def test_payload_config_imports_users_with_runtime_safe_extension(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / "src/payload.config.ts").read_text()
    assert './collections/Users.ts' in content
    assert './collections/Users";' not in content


def test_payload_next_config_uses_with_payload(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / "next.config.ts").read_text()
    assert "withPayload" in content


def test_payload_tsconfig_has_payload_path(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    tsconfig = json.loads((tmp_path / "tsconfig.json").read_text())
    paths = tsconfig["compilerOptions"]["paths"]

    assert "@payload-config" in paths
    assert tsconfig["compilerOptions"]["allowImportingTsExtensions"] is True


def test_payload_cms_variant_also_works(tmp_path):
    """'payload-cms' should be treated identically to 'payload'."""
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "payload-cms",
        "database": "postgres",
    })
    write_scaffold(tmp_path, spec)

    pkg = json.loads((tmp_path / "package.json").read_text())
    assert "payload" in pkg["dependencies"]
    assert (tmp_path / "src/payload.config.ts").exists()


# -------------------------------------------------------
# Database variants (docker-compose & .env.example)
# -------------------------------------------------------


def test_postgres_docker_compose(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "docker-compose.yml").read_text()
    assert "postgres:16-alpine" in content
    assert "pgdata" in content
    assert "POSTGRES_DB" in content


def test_postgres_env_example(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / ".env.example").read_text()
    assert "postgresql://" in content
    assert "test_project" in content  # slug with - replaced by _


def test_mongodb_docker_compose(tmp_path):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "node-api",
        "database": "mongodb",
    })
    write_scaffold(tmp_path, spec)

    content = (tmp_path / "docker-compose.yml").read_text()
    assert "mongo:7" in content
    assert "mongodata" in content


def test_mongodb_env_example(tmp_path):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "node-api",
        "database": "mongodb",
    })
    write_scaffold(tmp_path, spec)

    content = (tmp_path / ".env.example").read_text()
    assert "mongodb://" in content


def test_sqlite_env_example(tmp_path):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "node-api",
        "database": "sqlite",
    })
    write_scaffold(tmp_path, spec)

    content = (tmp_path / ".env.example").read_text()
    assert "file:./" in content


def test_sqlite_docker_compose_has_no_db_service(tmp_path):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "node-api",
        "database": "sqlite",
    })
    write_scaffold(tmp_path, spec)

    content = (tmp_path / "docker-compose.yml").read_text()
    assert "postgres" not in content
    assert "mongo" not in content


# -------------------------------------------------------
# Port derivation
# -------------------------------------------------------


def test_port_derivation_is_deterministic(tmp_path):
    """Same slug always gets the same port."""
    from initializer.renderers.scaffold_engine import _derive_port

    port1 = _derive_port("my-project")
    port2 = _derive_port("my-project")
    assert port1 == port2


def test_port_derivation_is_in_range(tmp_path):
    from initializer.renderers.scaffold_engine import _derive_port

    for slug in ["a", "my-project", "very-long-project-name-here", "z"]:
        port = _derive_port(slug)
        assert 5433 <= port <= 5499, f"Port {port} for slug '{slug}' out of range"


def test_port_appears_in_docker_compose_and_env(tmp_path):
    from initializer.renderers.scaffold_engine import _derive_port

    spec = _make_spec()
    write_scaffold(tmp_path, spec)

    expected_port = _derive_port("test-project")
    env_content = (tmp_path / ".env.example").read_text()
    assert str(expected_port) in env_content


# -------------------------------------------------------
# Layout and page content
# -------------------------------------------------------


def test_layout_contains_project_name(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "src/app/layout.tsx").read_text()
    assert "Test Project" in content


def test_page_contains_project_name(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "src/app/page.tsx").read_text()
    assert "Test Project" in content


def test_globals_css_imports_tailwind(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "src/app/globals.css").read_text()
    assert "tailwindcss" in content


# -------------------------------------------------------
# Dockerfile and README
# -------------------------------------------------------


def test_dockerfile_uses_node_22(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "Dockerfile").read_text()
    assert "node:22-alpine" in content
    assert "npm run build" in content
    assert "EXPOSE 3000" in content


def test_readme_contains_project_name(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "README.md").read_text()
    assert "# Test Project" in content
    assert "npm run dev" in content
    assert "ralph.sh" in content


def test_readme_payload_has_admin_url(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / "README.md").read_text()
    assert "/admin" in content


# -------------------------------------------------------
# package.json structure
# -------------------------------------------------------


def test_package_json_has_required_scripts(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())
    scripts = pkg["scripts"]

    assert "dev" in scripts
    assert "build" in scripts
    assert "start" in scripts
    assert "lint" in scripts
    assert "test" in scripts
    assert "typecheck" in scripts
    assert scripts["lint"] == "eslint ."
    assert scripts["test"] == "vitest run"


def test_package_json_slug_and_name(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())

    assert pkg["name"] == "test-project"
    assert pkg["description"] == "Test Project"


def test_package_json_has_base_deps(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())

    assert "react" in pkg["dependencies"]
    assert "react-dom" in pkg["dependencies"]
    assert "next" in pkg["dependencies"]
    assert "typescript" in pkg["devDependencies"]
    assert "tailwindcss" in pkg["devDependencies"]
    assert "@eslint/eslintrc" in pkg["devDependencies"]
    assert "vitest" in pkg["devDependencies"]
    assert "tsx" not in pkg["devDependencies"]


def test_tsconfig_includes_next_plugin_and_generated_types(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    tsconfig = json.loads((tmp_path / "tsconfig.json").read_text())

    assert {"name": "next"} in tsconfig["compilerOptions"]["plugins"]
    assert ".next/types/**/*.ts" in tsconfig["include"]


def test_vitest_config_targets_generated_smoke_tests(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "vitest.config.ts").read_text()

    assert 'defineConfig' in content
    assert 'jsx: "automatic"' in content
    assert 'jsxImportSource: "react"' in content
    assert 'environment: "node"' in content
    assert 'src/**/*.test.ts' in content
    assert 'passWithNoTests: false' in content
    assert 'setupFiles:' not in content


def test_payload_vitest_config_loads_env_setup_file(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / "vitest.config.ts").read_text()
    assert 'setupFiles: ["./src/__tests__/setup-env.ts"]' in content


def test_vitest_config_has_path_alias_for_src(tmp_path):
    """BUG-046: Vitest must resolve @/ alias to src/ so imports like @/lib/permissions work."""
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "vitest.config.ts").read_text()
    assert '"@"' in content
    assert '"src"' in content
    assert "resolve" in content
    assert "alias" in content


def test_eslint_config_uses_eslintrc_compat(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "eslint.config.mjs").read_text()

    assert '@eslint/eslintrc' in content
    assert '@eslint/flatcompat' not in content
    assert 'ignores:' in content


def test_smoke_test_does_not_import_app_page(tmp_path):
    """BUG-029: smoke test must not import app/page to avoid cross-track pollution."""
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / "src/__tests__/smoke.test.ts").read_text()

    assert "app/page" not in content
    assert "renderToStaticMarkup" not in content
    assert 'from "vitest"' in content
    assert "React.createElement" in content


# -------------------------------------------------------
# .env.example common fields
# -------------------------------------------------------


def test_env_example_has_common_fields(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    content = (tmp_path / ".env.example").read_text()
    assert "PORT=3000" in content
    assert "NODE_ENV=development" in content
    assert "JWT_SECRET" in content


def test_env_example_payload_has_payload_secret(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / ".env.example").read_text()
    assert "PAYLOAD_SECRET" in content


def test_env_example_payload_omits_jwt_secret(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / ".env.example").read_text()
    assert "JWT_SECRET" not in content


# -------------------------------------------------------
# .env.local generation (IMP-009)
# -------------------------------------------------------


def test_env_local_is_generated(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    assert (tmp_path / ".env.local").exists()


def test_env_local_matches_env_example(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    example = (tmp_path / ".env.example").read_text()
    local = (tmp_path / ".env.local").read_text()
    assert example == local


def test_env_local_generated_for_payload(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    assert (tmp_path / ".env.local").exists()
    content = (tmp_path / ".env.local").read_text()
    assert "PAYLOAD_SECRET" in content


def test_env_local_generated_for_mongodb(tmp_path):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "node-api",
        "database": "mongodb",
    })
    write_scaffold(tmp_path, spec)

    assert (tmp_path / ".env.local").exists()
    content = (tmp_path / ".env.local").read_text()
    assert "mongodb://" in content


def test_env_local_generated_for_sqlite(tmp_path):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "node-api",
        "database": "sqlite",
    })
    write_scaffold(tmp_path, spec)

    assert (tmp_path / ".env.local").exists()
    content = (tmp_path / ".env.local").read_text()
    assert "file:./" in content


def test_payload_setup_env_loads_dotenv_local_via_node_api(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / "src/__tests__/setup-env.ts").read_text()
    assert 'process.loadEnvFile(localEnvPath);' in content
    assert 'fs.existsSync(localEnvPath)' in content


def test_payload_migration_helper_loads_env_normalizes_type_imports_and_emits_sentinels(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    content = (tmp_path / "scripts/payload-migrations.mjs").read_text()
    assert 'process.loadEnvFile(localEnvPath);' in content
    assert 'type ${withoutType}' in content
    assert '@payloadcms/db-postgres' in content
    assert 'const SENTINEL_PREFIX = "__SPECWRIGHT_PAYLOAD_MIGRATIONS__:";' in content
    assert 'emitSentinel("no-pending"' in content
    assert 'emitSentinel(' in content
    assert '"dev-push"' in content
    assert 'payload_migrations contains a dev-mode push marker' in content
    assert 'SELECT name, batch FROM "payload_migrations"' in content
    assert 'node ./scripts/payload-migrations.mjs <migrate|create|status>' in content


# -------------------------------------------------------
# Migration template (LINT-001)
# -------------------------------------------------------


def test_node_api_postgres_has_migration_template(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    template_path = tmp_path / "src/lib/migration-template.cjs"
    assert template_path.exists()
    content = template_path.read_text()
    assert "void pgm;" in content
    assert "exports.up" in content
    assert "exports.down" in content


def test_node_api_postgres_package_json_has_migration_deps(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())
    assert "node-pg-migrate" in pkg["dependencies"]
    assert "pg" in pkg["dependencies"]


def test_node_api_postgres_package_json_has_migration_scripts(tmp_path):
    write_scaffold(tmp_path, _make_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())
    assert "db:migrate" in pkg["scripts"]
    assert "db:migrate:create" in pkg["scripts"]
    assert "db:migrate:status" in pkg["scripts"]
    assert "migration-template.cjs" in pkg["scripts"]["db:migrate:create"]


def test_payload_has_no_migration_template(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    assert not (tmp_path / "src/lib/migration-template.cjs").exists()


def test_payload_package_json_has_no_node_pg_migrate(tmp_path):
    write_scaffold(tmp_path, _payload_spec())

    pkg = json.loads((tmp_path / "package.json").read_text())
    assert "node-pg-migrate" not in pkg.get("dependencies", {})


def test_sqlite_has_no_migration_template(tmp_path):
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "node-api",
        "database": "sqlite",
    })
    write_scaffold(tmp_path, spec)

    assert not (tmp_path / "src/lib/migration-template.cjs").exists()


# -------------------------------------------------------
# BUG-030: Payload projects must NOT get src/app/page.tsx
# -------------------------------------------------------


def test_scaffold_payload_skips_root_page(tmp_path):
    """Payload uses route groups (app)/(payload) — root page.tsx conflicts."""
    spec = _make_spec(stack={
        "frontend": "nextjs",
        "backend": "payload",
        "database": "postgres",
    })
    write_scaffold(tmp_path, spec)

    # Root page must NOT exist for Payload — FE-ST-006 creates (app)/page.tsx
    assert not (tmp_path / "src/app/page.tsx").exists()
    # But layout and globals should still exist
    assert (tmp_path / "src/app/layout.tsx").exists()
    assert (tmp_path / "src/app/globals.css").exists()
    # Payload admin pages should exist
    assert (tmp_path / "src/app/(payload)/admin/[[...segments]]/page.tsx").exists()


def test_scaffold_node_api_still_has_root_page(tmp_path):
    """Non-Payload projects should still get the root page placeholder."""
    write_scaffold(tmp_path, _make_spec())

    assert (tmp_path / "src/app/page.tsx").exists()
