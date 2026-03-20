"""Scaffold Engine.

Generates real, executable project files so that the generated project
can be started with:

    npm install
    docker compose up -d
    npm run dev

The scaffold is stack-aware and generates different files based on
the detected backend (payload vs node-api) and database.

This is NOT a template copy — each file is generated from the spec
so that names, ports, capabilities, and features are wired correctly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _derive_port(slug: str, base: int = 5433) -> int:
    """Derive a unique port from the project slug.

    Maps slug to a port in the range 5433-5499 so that
    multiple projects can run docker simultaneously.
    """
    h = sum(ord(c) for c in slug) % 67  # 0-66
    return base + h


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _write(base: Path, relative: str, content: str) -> None:
    """Write a file, creating parent directories as needed."""
    target = base / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _slug(spec: dict[str, Any]) -> str:
    return spec.get("answers", {}).get("project_slug", "generated-project")


def _name(spec: dict[str, Any]) -> str:
    return spec.get("answers", {}).get("project_name", "Generated Project")


def _backend(spec: dict[str, Any]) -> str:
    return (spec.get("stack", {}).get("backend") or "node-api").lower().strip()


def _database(spec: dict[str, Any]) -> str:
    return (spec.get("stack", {}).get("database") or "postgres").lower().strip()


def _is_payload(spec: dict[str, Any]) -> bool:
    return _backend(spec) in ("payload", "payload-cms")


# -------------------------------------------------------------------
# docker-compose.yml
# -------------------------------------------------------------------

def _docker_compose(spec: dict[str, Any]) -> str:
    slug = _slug(spec)
    db = _database(spec)
    capabilities = spec.get("capabilities", [])
    port = _derive_port(slug)

    services = []

    # --- Postgres ---
    if db == "postgres":
        services.append(f"""  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: {slug.replace("-", "_")}
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "${{POSTGRES_PORT:-{port}}}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5""")

    # --- MongoDB ---
    elif db == "mongodb":
        services.append("""  mongo:
    image: mongo:7
    restart: unless-stopped
    ports:
      - "27017:27017"
    volumes:
      - mongodata:/data/db""")

    # --- Volumes ---
    volumes = []
    if db == "postgres":
        volumes.append("  pgdata:")
    elif db == "mongodb":
        volumes.append("  mongodata:")

    compose = f"""# Docker Compose for {_name(spec)}
# Start: docker compose up -d
# Stop:  docker compose down

services:
"""
    compose += "\n\n".join(services)

    if volumes:
        compose += "\n\nvolumes:\n" + "\n".join(volumes) + "\n"

    return compose


# -------------------------------------------------------------------
# .env.example / .env.local
# -------------------------------------------------------------------

def _env_example(spec: dict[str, Any]) -> str:
    slug = _slug(spec)
    db = _database(spec)
    is_payload = _is_payload(spec)

    lines = [
        f"# Environment variables for {_name(spec)}",
        f"# .env.local is auto-generated — edit it for local overrides",
        "",
    ]

    if db == "postgres":
        db_name = slug.replace("-", "_")
        port = _derive_port(slug)
        lines.append(f"DATABASE_URI=postgresql://postgres:postgres@localhost:{port}/{db_name}")
        lines.append(f"POSTGRES_PORT={port}  # Unique per project — change if {port} is in use")
    elif db == "mongodb":
        lines.append(f"DATABASE_URI=mongodb://localhost:27017/{slug}")
    elif db == "sqlite":
        lines.append(f"DATABASE_URI=file:./{slug}.db")

    lines.append("")

    if is_payload:
        lines.append("PAYLOAD_SECRET=change-me-to-a-random-secret-at-least-32-chars")
        lines.append("")

    lines.append("# Server")
    lines.append("PORT=3000")
    lines.append("NODE_ENV=development")
    lines.append("")

    if not is_payload:
        lines.append("# Auth")
        lines.append("JWT_SECRET=change-me-to-a-random-secret")
        lines.append("")

    return "\n".join(lines)


# -------------------------------------------------------------------
# .gitignore
# -------------------------------------------------------------------

def _gitignore() -> str:
    return """node_modules/
.next/
dist/
build/
.env
.env.local
.env.*.local
*.log
.DS_Store
pgdata/
"""


# -------------------------------------------------------------------
# tsconfig.json
# -------------------------------------------------------------------

def _tsconfig(spec: dict[str, Any]) -> str:
    config = {
        "compilerOptions": {
            "target": "ES2022",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True,
            "skipLibCheck": True,
            "strict": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "plugins": [{"name": "next"}],
            "paths": {
                "@/*": ["./src/*"],
            },
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
        "exclude": ["node_modules"],
    }

    if _is_payload(spec):
        config["compilerOptions"]["paths"]["@payload-config"] = ["./src/payload.config.ts"]
        config["compilerOptions"]["allowImportingTsExtensions"] = True

    return json.dumps(config, indent=2) + "\n"


# -------------------------------------------------------------------
# package.json
# -------------------------------------------------------------------

def _package_json(spec: dict[str, Any]) -> str:
    slug = _slug(spec)
    name = _name(spec)
    is_payload = _is_payload(spec)

    pkg: dict[str, Any] = {
        "name": slug,
        "version": "0.1.0",
        "private": True,
        "description": name,
        "scripts": {
            "dev": "next dev",
            "build": "flock .build.lock next build",
            "start": "next start",
            "lint": "eslint .",
            "test": "vitest run",
            "typecheck": "tsc --noEmit",
        },
        "dependencies": {
            "next": "^15",
            "react": "^19",
            "react-dom": "^19",
        },
        "devDependencies": {
            "typescript": "^5",
            "@types/node": "^22",
            "@types/react": "^19",
            "@types/react-dom": "^19",
            "eslint": "^9",
            "@eslint/eslintrc": "^3",
            "eslint-config-next": "^15",
            "tailwindcss": "^4",
            "@tailwindcss/postcss": "^4",
            "vitest": "^3.1.1",
        },
    }

    if is_payload:
        # Pin Next.js to range compatible with Payload 3
        pkg["dependencies"]["next"] = "15.4.11"
        pkg["devDependencies"]["eslint-config-next"] = "15.4.11"
        pkg["scripts"]["generate:types"] = "payload --disable-transpile generate:types"
        pkg["scripts"]["db:migrate"] = "node ./scripts/payload-migrations.mjs migrate"
        pkg["scripts"]["db:migrate:create"] = "node ./scripts/payload-migrations.mjs create"
        pkg["scripts"]["db:migrate:status"] = "node ./scripts/payload-migrations.mjs status"
        pkg["dependencies"]["@payloadcms/next"] = "^3"
        pkg["dependencies"]["@payloadcms/richtext-lexical"] = "^3"
        pkg["dependencies"]["@payloadcms/db-postgres"] = "^3"
        pkg["dependencies"]["payload"] = "^3"
        pkg["dependencies"]["graphql"] = "^16"
        pkg["dependencies"]["pg"] = "^8"
        pkg["dependencies"]["sharp"] = "^0.33"
    else:
        # Generic node-api: Express for standalone API routes
        pkg["dependencies"]["express"] = "^4"
        pkg["dependencies"]["cors"] = "^2"
        pkg["dependencies"]["helmet"] = "^7"
        pkg["devDependencies"]["@types/express"] = "^4"
        pkg["devDependencies"]["@types/cors"] = "^2"

    # Add node-pg-migrate for non-Payload postgres projects
    db = _database(spec)
    if not is_payload and db == "postgres":
        pkg["dependencies"]["node-pg-migrate"] = "^8"
        pkg["dependencies"]["pg"] = "^8"
        pkg["scripts"]["db:migrate"] = (
            "node-pg-migrate up --migrations-dir src/lib/migrations "
            "--migration-file-language cjs "
            "--template-file-name src/lib/migration-template.cjs "
            "--envPath .env.local"
        )
        pkg["scripts"]["db:migrate:create"] = (
            "node-pg-migrate create --migrations-dir src/lib/migrations "
            "--migration-file-language cjs "
            "--template-file-name src/lib/migration-template.cjs"
        )
        pkg["scripts"]["db:migrate:status"] = (
            "node-pg-migrate up --migrations-dir src/lib/migrations "
            "--envPath .env.local --dry-run"
        )

    return json.dumps(pkg, indent=2) + "\n"


# -------------------------------------------------------------------
# next.config.ts
# -------------------------------------------------------------------

def _next_config(spec: dict[str, Any]) -> str:
    is_payload = _is_payload(spec)

    if is_payload:
        return """import { withPayload } from "@payloadcms/next/withPayload";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    reactCompiler: false,
  },
};

export default withPayload(nextConfig);
"""
    else:
        return """import type { NextConfig } from "next";

const nextConfig: NextConfig = {};

export default nextConfig;
"""


# -------------------------------------------------------------------
# postcss.config.mjs (Tailwind v4)
# -------------------------------------------------------------------

def _postcss_config() -> str:
    return """/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
"""


# -------------------------------------------------------------------
# ESLint config
# -------------------------------------------------------------------

def _eslint_config() -> str:
    return """import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  {
    ignores: [".next/**", "node_modules/**", "dist/**", "build/**", "coverage/**"],
  },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
];

export default eslintConfig;
"""


# -------------------------------------------------------------------
# Payload config (only for payload backend)
# -------------------------------------------------------------------

def _payload_config(spec: dict[str, Any]) -> str:
    slug = _slug(spec)

    return f"""import {{ buildConfig }} from "payload";
import {{ postgresAdapter }} from "@payloadcms/db-postgres";
import {{ lexicalEditor }} from "@payloadcms/richtext-lexical";
import path from "path";
import {{ fileURLToPath }} from "url";

import {{ Users }} from "./collections/Users.ts";

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);

export default buildConfig({{
  admin: {{
    user: Users.slug,
  }},
  collections: [Users],
  editor: lexicalEditor(),
  secret: (() => {{
    const s = process.env.PAYLOAD_SECRET;
    if (!s) throw new Error("PAYLOAD_SECRET env var is required");
    return s;
  }})(),
  typescript: {{
    outputFile: path.resolve(dirname, "payload-types.ts"),
  }},
  db: postgresAdapter({{
    migrationDir: path.resolve(dirname, "lib/migrations"),
    pool: {{
      connectionString: process.env.DATABASE_URI || "",
    }},
  }}),
}});
"""


# -------------------------------------------------------------------
# Users collection (payload)
# -------------------------------------------------------------------

def _payload_users_collection() -> str:
    return """import type { CollectionConfig } from "payload";

export const Users: CollectionConfig = {
  slug: "users",
  auth: true,
  admin: {
    useAsTitle: "email",
  },
  fields: [
    {
      name: "name",
      type: "text",
      required: true,
    },
    {
      name: "role",
      type: "select",
      options: [
        { label: "Admin", value: "admin" },
        { label: "User", value: "user" },
      ],
      defaultValue: "user",
      required: true,
    },
  ],
};
"""


# -------------------------------------------------------------------
# Next.js app files
# -------------------------------------------------------------------

def _root_layout(spec: dict[str, Any]) -> str:
    name = _name(spec)
    is_payload = _is_payload(spec)

    imports = 'import type { Metadata } from "next";\nimport "./globals.css";\n'

    if is_payload:
        imports += ""

    return f"""{imports}
export const metadata: Metadata = {{
  title: "{name}",
  description: "{name}",
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="en">
      <body>{{children}}</body>
    </html>
  );
}}
"""


def _root_page(spec: dict[str, Any]) -> str:
    name = _name(spec)
    return f"""export default function Home() {{
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4">{name}</h1>
      <p className="text-gray-600">Project generated by Specwright. Run the stories to build it out.</p>
    </main>
  );
}}
"""


def _globals_css() -> str:
    return """@import "tailwindcss";
"""


def _next_env_d_ts() -> str:
    return """/// <reference types="next" />
/// <reference types="next/image-types/global" />

// This file is automatically generated by Next.js and should not be edited.
"""


def _vitest_config(spec: dict[str, Any]) -> str:
    setup_files = ""
    if _is_payload(spec):
        setup_files = '    setupFiles: ["./src/__tests__/setup-env.ts"],\n'

    return (
        'import { defineConfig } from "vitest/config";\n\n'
        "export default defineConfig({\n"
        "  esbuild: {\n"
        '    jsx: "automatic",\n'
        '    jsxImportSource: "react",\n'
        "  },\n"
        "  test: {\n"
        '    environment: "node",\n'
        '    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],\n'
        '    passWithNoTests: false,\n'
        f"{setup_files}"
        "  },\n"
        "});\n"
    )


def _tsconfig_test() -> str:
    config = {
        "extends": "./tsconfig.json",
        "compilerOptions": {
            "jsx": "react-jsx",
        },
    }

    return json.dumps(config, indent=2) + "\n"


def _smoke_test(spec: dict[str, Any]) -> str:
    name = _name(spec)
    is_payload = _is_payload(spec)

    payload_lines = ""
    payload_test = ""
    if is_payload:
        payload_lines = 'import payloadConfig from "../payload.config";\n'
        payload_test = """
  it("loads the payload config", async () => {
    const config = await payloadConfig;

    expect(config).toBeDefined();
    expect(config).toHaveProperty("db");
    expect(config).toHaveProperty("secret");
  });
"""

    return f"""import React from "react";
import {{ renderToStaticMarkup }} from "react-dom/server";
import {{ describe, expect, it }} from "vitest";

import Home from "../app/page";
{payload_lines}
describe("bootstrap smoke", () => {{
{payload_test}
  it("home page smoke render includes the project title", () => {{
  const html = renderToStaticMarkup(React.createElement(Home));

  expect(html).toContain("{name}");
  expect(html).toContain("Project generated by Specwright");
  }});

  it("home page module exports a renderable component", () => {{
    expect(typeof Home).toBe("function");
  }});
}});
"""


# -------------------------------------------------------------------
# Payload-specific Next.js files
# -------------------------------------------------------------------

def _payload_layout() -> str:
    return """/* THIS FILE WAS GENERATED AUTOMATICALLY BY PAYLOAD. */
/* DO NOT MODIFY IT BECAUSE IT COULD BE REWRITTEN AT ANY TIME. */
import config from "@payload-config";
import { importMap } from "./importMap";
import { RootLayout, handleServerFunctions } from "@payloadcms/next/layouts";
import type { ServerFunctionClient } from "payload";
import React from "react";

import "./custom.scss";

type Args = {
  children: React.ReactNode;
};

const serverFunction: ServerFunctionClient = async (args) => {
  "use server";
  return handleServerFunctions({
    ...args,
    config,
    importMap,
  });
};

const Layout = ({ children }: Args) => (
  <RootLayout config={config} importMap={importMap} serverFunction={serverFunction}>
    {children}
  </RootLayout>
);

export default Layout;
"""


def _payload_page() -> str:
    return """/* THIS FILE WAS GENERATED AUTOMATICALLY BY PAYLOAD. */
/* DO NOT MODIFY IT BECAUSE IT COULD BE REWRITTEN AT ANY TIME. */
import config from "@payload-config";
import { importMap } from "../../importMap";
import {
  RootPage,
  generatePageMetadata,
} from "@payloadcms/next/views";

type Args = {
  params: Promise<{ segments: string[] }>;
  searchParams: Promise<{ [key: string]: string | string[] }>;
};

export const generateMetadata = ({ params, searchParams }: Args) =>
  generatePageMetadata({ config, params, searchParams });

const Page = ({ params, searchParams }: Args) =>
  RootPage({ config, importMap, params, searchParams });

export default Page;
"""


def _payload_custom_scss() -> str:
    return """/* Add custom admin panel styles here */
"""


def _payload_import_map() -> str:
    return """// This file is auto-generated by Payload during build.
// Placeholder for development — Payload will populate this.
export const importMap = {};
"""


def _payload_test_env_setup() -> str:
    return """import fs from "node:fs";
import path from "node:path";

const localEnvPath = path.resolve(process.cwd(), ".env.local");

if (fs.existsSync(localEnvPath) && typeof process.loadEnvFile === "function") {
  process.loadEnvFile(localEnvPath);
}
"""


def _payload_migration_helper() -> str:
    return """import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import pg from "pg";

const require = createRequire(import.meta.url);
const { Client } = pg;
const SENTINEL_PREFIX = "__SPECWRIGHT_PAYLOAD_MIGRATIONS__:";

function emitSentinel(result, message) {
  if (message) {
    console.log(message);
  }
  console.log(`${SENTINEL_PREFIX}${result}`);
}

function loadLocalEnv() {
  const localEnvPath = path.resolve(process.cwd(), ".env.local");
  if (fs.existsSync(localEnvPath) && typeof process.loadEnvFile === "function") {
    process.loadEnvFile(localEnvPath);
  }
}

function getMigrationDir() {
  return path.resolve(process.cwd(), "src/lib/migrations");
}

function getMigrationFiles() {
  const migrationDir = getMigrationDir();
  if (!fs.existsSync(migrationDir)) {
    return [];
  }

  return fs
    .readdirSync(migrationDir)
    .filter((file) => file.endsWith(".ts") && file !== "index.ts")
    .sort();
}

function normalizeSpecifier(specifier) {
  const trimmed = specifier.trim();
  if (!trimmed) {
    return trimmed;
  }

  const withoutType = trimmed.replace(/^type\\s+/, "");
  const baseName = withoutType.split(/\\s+as\\s+/)[0];
  if (baseName === "MigrateUpArgs" || baseName === "MigrateDownArgs") {
    return `type ${withoutType}`;
  }

  return trimmed;
}

function normalizeMigrationImports() {
  const migrationDir = getMigrationDir();

  for (const file of getMigrationFiles()) {
    const fullPath = path.join(migrationDir, file);
    const content = fs.readFileSync(fullPath, "utf8");
    const nextContent = content.replace(
      /import\\s*\\{([^}]*)\\}\\s*from\\s*['"]@payloadcms\\/db-postgres['"]/g,
      (_match, specifiers) => {
        const normalized = specifiers
          .split(",")
          .map((specifier) => normalizeSpecifier(specifier))
          .filter(Boolean);

        return `import { ${normalized.join(", ")} } from "@payloadcms/db-postgres"`;
      },
    );

    if (nextContent !== content) {
      fs.writeFileSync(fullPath, nextContent);
    }
  }
}

async function readMigrationState() {
  const connectionString = process.env.DATABASE_URI?.trim();
  if (!connectionString) {
    return null;
  }

  const client = new Client({ connectionString });

  try {
    await client.connect();

    const existsResult = await client.query(
      "SELECT to_regclass('public.payload_migrations') AS table_name",
    );
    if (!existsResult.rows[0]?.table_name) {
      return { rows: [] };
    }

    const result = await client.query('SELECT name, batch FROM "payload_migrations"');
    return { rows: result.rows };
  } catch {
    return null;
  } finally {
    await client.end().catch(() => {});
  }
}

function getPendingMigrationNames(migrationFiles, rows) {
  const completed = new Set(rows.map((row) => String(row.name)));
  return migrationFiles
    .map((file) => file.replace(/\\.ts$/, ""))
    .filter((name) => !completed.has(name));
}

function resolvePayloadBin() {
  const payloadEntry = require.resolve("payload");
  return path.resolve(payloadEntry, "..", "..", "bin.js");
}

function runPayloadCLI(commandArgs) {
  const result = spawnSync(
    process.execPath,
    [resolvePayloadBin(), "--disable-transpile", ...commandArgs],
    {
      cwd: process.cwd(),
      env: process.env,
      stdio: "inherit",
    },
  );

  if (result.error) {
    throw result.error;
  }

  return result.status ?? 1;
}

async function main() {
  loadLocalEnv();
  normalizeMigrationImports();

  const [command, ...args] = process.argv.slice(2);
  if (!command) {
    console.error("Usage: node ./scripts/payload-migrations.mjs <migrate|create|status>");
    process.exit(1);
  }

  if (command === "create") {
    const status = runPayloadCLI(["migrate:create", ...args]);
    if (status === 0) {
      normalizeMigrationImports();
    }
    process.exit(status);
  }

  if (command === "status") {
    process.exit(runPayloadCLI(["migrate:status", ...args]));
  }

  if (command !== "migrate") {
    console.error("Usage: node ./scripts/payload-migrations.mjs <migrate|create|status>");
    process.exit(1);
  }

  const migrationFiles = getMigrationFiles();
  if (migrationFiles.length == 0) {
    emitSentinel("no-pending", "Specwright: no pending Payload migrations.");
    return;
  }

  const state = await readMigrationState();
  if (state) {
    const pending = getPendingMigrationNames(migrationFiles, state.rows);
    if (pending.length === 0) {
      emitSentinel("no-pending", "Specwright: no pending Payload migrations.");
      return;
    }

    if (state.rows.some((row) => Number(row.batch) === -1)) {
      emitSentinel(
        "dev-push",
        "Specwright: skipping Payload migrate because payload_migrations contains a dev-mode push marker (batch -1).",
      );
      return;
    }
  }

  process.exit(runPayloadCLI(["migrate", ...args]));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
"""


# -------------------------------------------------------------------
# Migration template (node-pg-migrate)
# -------------------------------------------------------------------

def _migration_template() -> str:
    """Custom migration template that stays lint-clean in generated projects."""
    return """/**
 * @type {import('node-pg-migrate').ColumnDefinitions | undefined}
 */
exports.shorthands = undefined;

/**
 * @param {import('node-pg-migrate').MigrationBuilder} pgm
 */
exports.up = (pgm) => {
  void pgm;
};

/**
 * @param {import('node-pg-migrate').MigrationBuilder} pgm
 */
exports.down = (pgm) => {
  void pgm;
};
"""


# -------------------------------------------------------------------
# Dockerfile
# -------------------------------------------------------------------

def _dockerfile(spec: dict[str, Any]) -> str:
    return f"""FROM node:22-alpine AS base

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Production
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=base /app/.next ./.next
COPY --from=base /app/node_modules ./node_modules
COPY --from=base /app/package.json ./package.json
COPY --from=base /app/public ./public

EXPOSE 3000
CMD ["npm", "start"]
"""


# -------------------------------------------------------------------
# README for the generated project
# -------------------------------------------------------------------

def _project_readme(spec: dict[str, Any]) -> str:
    name = _name(spec)
    slug = _slug(spec)
    db = _database(spec)
    is_payload = _is_payload(spec)

    admin_url = "http://localhost:3000/admin" if is_payload else "http://localhost:3000"

    return f"""# {name}

Generated by [Specwright](https://github.com/specwright).

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Start database
docker compose up -d

# 3. Run dev server (`.env.local` is already generated)
npm run dev
```

Open [{admin_url}]({admin_url}) in your browser.

## Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run lint` | Run ESLint |
| `npm run typecheck` | Run TypeScript check |
| `npm test` | Run tests |
| `docker compose up -d` | Start {db} |
| `docker compose down` | Stop {db} |

## Project Structure

See `spec.json` for the full project specification and `docs/stories/` for implementation stories.

## Execution

This project is designed to be implemented story-by-story using an AI coding agent:

```bash
./ralph.sh --dry-run    # Preview execution plan
./ralph.sh              # Run with Codex CLI
```
"""


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

def write_scaffold(output_dir: Path, spec: dict[str, Any]) -> None:
    """Generate executable scaffold files for the project.

    After this runs, the project can be started with:
        npm install
        docker compose up -d
        npm run dev
    """
    is_payload = _is_payload(spec)

    # --- Root config files ---
    _write(output_dir, "docker-compose.yml", _docker_compose(spec))
    env_content = _env_example(spec)
    _write(output_dir, ".env.example", env_content)
    _write(output_dir, ".env.local", env_content)
    _write(output_dir, ".gitignore", _gitignore())
    _write(output_dir, "tsconfig.json", _tsconfig(spec))
    _write(output_dir, "package.json", _package_json(spec))
    _write(output_dir, "next.config.ts", _next_config(spec))
    _write(output_dir, "next-env.d.ts", _next_env_d_ts())
    _write(output_dir, "vitest.config.ts", _vitest_config(spec))
    _write(output_dir, "postcss.config.mjs", _postcss_config())
    _write(output_dir, "eslint.config.mjs", _eslint_config())
    _write(output_dir, "Dockerfile", _dockerfile(spec))
    _write(output_dir, "README.md", _project_readme(spec))

    if is_payload:
        _write(output_dir, ".npmrc", "legacy-peer-deps=true\n")

    # --- Next.js app ---
    _write(output_dir, "src/app/layout.tsx", _root_layout(spec))
    _write(output_dir, "src/app/page.tsx", _root_page(spec))
    _write(output_dir, "src/app/globals.css", _globals_css())
    _write(output_dir, "src/__tests__/smoke.test.ts", _smoke_test(spec))

    # --- Payload-specific files ---
    if is_payload:
        _write(output_dir, "src/payload.config.ts", _payload_config(spec))
        _write(output_dir, "src/collections/Users.ts", _payload_users_collection())
        _write(output_dir, "src/__tests__/setup-env.ts", _payload_test_env_setup())
        _write(output_dir, "src/app/(payload)/admin/[[...segments]]/page.tsx", _payload_page())
        _write(output_dir, "src/app/(payload)/admin/[[...segments]]/not-found.tsx",
               '/* THIS FILE WAS GENERATED AUTOMATICALLY BY PAYLOAD. */\n/* DO NOT MODIFY IT BECAUSE IT COULD BE REWRITTEN AT ANY TIME. */\nimport config from "@payload-config";\nimport { importMap } from "../../importMap";\nimport { NotFoundPage, generatePageMetadata } from "@payloadcms/next/views";\n\ntype Args = {\n  params: Promise<{ segments: string[] }>;\n  searchParams: Promise<{ [key: string]: string | string[] }>;\n};\n\nexport const generateMetadata = ({ params, searchParams }: Args) =>\n  generatePageMetadata({ config, params, searchParams });\n\nconst NotFound = ({ params, searchParams }: Args) =>\n  NotFoundPage({ config, importMap, params, searchParams });\n\nexport default NotFound;\n')
        _write(output_dir, "src/app/(payload)/layout.tsx", _payload_layout())
        _write(output_dir, "src/app/(payload)/custom.scss", _payload_custom_scss())
        _write(output_dir, "src/app/(payload)/importMap.ts", _payload_import_map())
        _write(output_dir, "scripts/payload-migrations.mjs", _payload_migration_helper())

    # --- Migration template for node-pg-migrate (non-Payload postgres) ---
    if not is_payload and _database(spec) == "postgres":
        _write(output_dir, "src/lib/migration-template.cjs", _migration_template())

    # --- Lib placeholder ---
    _write(output_dir, "src/lib/.gitkeep", "")

    # --- Components placeholder ---
    _write(output_dir, "src/components/.gitkeep", "")

    # --- Public dir ---
    _write(output_dir, "public/.gitkeep", "")
