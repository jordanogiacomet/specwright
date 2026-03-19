# Specwright — Full Repository Analysis

**Date**: 2026-03-18 (updated 2026-03-19)
**Test suite**: 311/311 passed — 137 new tests added across 6 sessions
**Generated projects inspected**: `output/todo-app`, `output/todo-app-design`, `output/taskflow` (node-api), `output/newshub-cms` (Payload), `output/dentaldesk` (--assist flow), `output/editorial-control-center` (Payload editorial)

### Resolution Status

| ID | Status | Summary |
|----|--------|---------|
| BUG-001 | FIXED | StoryGraph now translates `depends_on` from `story_key` to `id` at load time |
| BUG-002 | FIXED | Progress parser extracts story ID from `parts[0]` instead of `parts[1]` |
| BUG-003 | FIXED | Migration commands now use separate `run`/`create`/`status` per backend |
| IMP-001 | FIXED | `node-api` backend now gets Express, cors, helmet dependencies |
| IMP-003 | FIXED | ST-900 and ST-901 now have `story_key` (`operations.monitoring`, `operations.backups`) |
| IMP-004 | FIXED | Codex model configurable via `$CODEX_MODEL` env var (default: `gpt-5.4`) |
| IMP-005 | FIXED | `_has_discovery()` checks `decision_signals` presence, not just `assisted` flag |
| IMP-006 | FIXED | Resolved by BUG-001 fix — cycle detection now works with translated ids |
| IMP-008 | FIXED | Removed redundant `not in completed` check in `topological_order()` |
| IMP-010 | FIXED | ralph.sh exits with code 1 when `$FAILED > 0` |
| BONUS   | FIXED | SyntaxWarnings from invalid escape sequences in codex_bundle.py |
| TESTS   | ADDED | 14 new tests for StoryGraph, StoryScheduler, and `load_completed_from_progress` |
| IMP-002 | FIXED | StoryGraph/Scheduler + scaffold_engine (37 tests) + codex_bundle migration commands (7 tests) now covered |
| IMP-007 | FIXED | `_surface_conflicts()` prints signal conflicts to user after each discovery merge |
| IMP-009 | FIXED | Scaffold now generates `.env.local` alongside `.env.example` for all stacks (5 tests added) |
| IMP-011 | N/A | `output/` already in `.gitignore` — no action needed |
| E2E     | VALIDATED | Full E2E run on 2 fresh projects (taskflow + newshub-cms); all fixes confirmed |
| BUG-004 | FIXED | Backticks in `run_codex_retry` heredoc caused bash to execute `$previous_error` as command; escaped to `\`\`\`` |
| ASSIST  | VALIDATED | `--assist` flow tested interactively (dentaldesk project); signals, conflicts, decisions, design style all captured correctly |
| BUG-005 | FIXED | `.env.example` comment still said "cp .env.example .env.local" after IMP-009; README and docstring also stale |
| BUG-006 | FIXED | `commands_engine.py` and `openclaw_bundle.py` used unconditional `cp` — now `test -f .env.local \|\| cp` |
| GUARD-001 | ADDED | Scope boundary "Do NOT create files in src/pages/" added to bootstrap.repository and bootstrap.frontend stories |
| GUARD-002 | ADDED | Scope boundary "Use env var names exactly as in .env.example" added to bootstrap.repository, backend, and frontend stories |
| DEAD-001 | REMOVED | `initializer/synthesis/stories.py` — orphan file never imported by any module |
| DEAD-002 | REMOVED | `initializer/test_prd_scoring.py` — broken test in wrong location, imports non-existent `ask_llm` |
| INFRA-001 | ADDED | GitHub Actions CI workflow (`.github/workflows/test.yml`) — runs pytest on push/PR |
| INFRA-002 | ADDED | `[project.optional-dependencies] dev = ["pytest"]` in `pyproject.toml` |
| INFRA-003 | FIXED | `.gitignore` expanded (added `__pycache__/`, `*.pyc`, `*.egg-info/`, `.env`, etc.) |
| INFRA-004 | ADDED | `Makefile` with `install`, `test`, `generate`, `clean` targets |
| README   | UPDATED | Virtualenv instructions, 238+ test count, removed stale `cp .env.local`, documented `examples/` and `designs/` folders |
| BUG-007 | FIXED | `prompt_choice()` now re-prompts on invalid input instead of crashing with `ValueError` |
| BUG-008 | FIXED | `_detect_commands()` now always returns the documented `{commands, notes}` shape |
| BUG-009 | FIXED | `prepare` no longer overwrites detected `.openclaw/commands.json` with inferred bundle defaults |
| INFRA-005 | FIXED | Removed tracked `__pycache__/` / `.pyc` artifacts from git index; `.pytest_cache/` ignored |
| BUG-010 | FIXED | Generated Next scaffold lint config now uses `@eslint/eslintrc`; scaffold ships real smoke test + test TS config |
| E2E-002 | VALIDATED | Real generated `taskflow` app passes `npm test`, `npm run lint`, and `npm run build` after scaffold fixes |
| BUG-011 | FIXED | `initializer new --spec` now accepts YAML/YML playbook inputs and normalizes `guided_answers` |
| BUG-012 | FIXED | Payload admin `page.tsx` imported `./importMap` but file is at `../../importMap` — build failed with `Module not found` |
| BUG-013 | FIXED | Payload `layout.tsx` missing `serverFunction` prop required by `RootLayout` in Payload v3.79+ — build failed with type error |
| BUG-014 | FIXED | Payload `not-found.tsx` had unused imports and missing `params`/`searchParams` props — lint warnings and type error |

---

## Session 4 — Editorial Validation and Payload v3.79 Compatibility (2026-03-19)

### What was fixed

1. **Payload admin `page.tsx` wrong importMap path (BUG-012)**
   - `initializer/renderers/scaffold_engine.py`
   - `_payload_page()` generated `import { importMap } from "./importMap"` but `page.tsx` lives in `admin/[[...segments]]/`, two directories deeper than `importMap.ts` at `(payload)/importMap.ts`.
   - Fixed by changing the import to `../../importMap`.
   - `not-found.tsx` already had the correct path.
   - Regression test added: `test_payload_admin_page_imports_importmap_from_correct_path`.

2. **Payload `RootLayout` missing `serverFunction` prop (BUG-013)**
   - `initializer/renderers/scaffold_engine.py`
   - Payload v3.79 added a mandatory `serverFunction` prop to `RootLayout` (server action wrapping `handleServerFunctions`).
   - `_payload_layout()` was generating the older template without this prop, causing a TypeScript build error.
   - Fixed by importing `handleServerFunctions` from `@payloadcms/next/layouts`, creating a `"use server"` action, and passing it to `RootLayout`.
   - Regression test added: `test_payload_layout_passes_server_function`.

3. **Payload `not-found.tsx` template cleanup (BUG-014)**
   - The original template imported `generatePageMetadata`, `config`, and `importMap` but only used `NotFoundPage` — causing 3 lint warnings.
   - `NotFoundPage` also requires `params` and `searchParams` (same signature as `RootPage`).
   - Fixed by generating the canonical Payload v3 not-found template with all props properly wired.
   - Regression test updated in `test_payload_admin_page_imports_importmap_from_correct_path`.

### Real validations performed

1. **Full editorial stack validation: `editorial-control-center`**
   - `initializer new --spec examples/next-payload-postgres.input.yaml` — PASS
   - `initializer prepare output/editorial-control-center` — PASS (14 stories, 3 phases)
   - `./ralph.sh --dry-run` — PASS (14/14 stories planned)
   - `npm install` — PASS (648 packages)
   - `docker compose up -d` — PASS (Postgres 16 on port 5478)
   - `npm test` — PASS (2/2 smoke tests)
   - `npm run lint` — PASS (0 errors, 0 warnings)
   - `npm run build` — PASS (all routes compiled, static + dynamic)
   - `npm run dev` — PASS
   - `GET /` — 200 OK
   - `GET /admin` — 200 OK (Payload admin panel served)

2. **Scaffold engine regression suite**
   - `tests/unit/test_scaffold_engine.py` → 54 passed (was 52, +2 new)

### Key product-level findings from this session

- The Payload scaffold was silently broken for `next build` in two ways (wrong import path + missing `serverFunction`). Neither would surface until a real build was attempted — unit tests only checked file existence, not import correctness.
- The editorial-control-center project (Next.js + Payload v3.79 + Postgres) is now the most thoroughly validated generated project: every step from spec to running app was verified.
- Lint is now fully clean (0 warnings) on generated Payload projects.

---

## Session 5 — Story Quality Audit for editorial-control-center (2026-03-19)

### Methodology

Read all 14 generated story files, spec.json, architecture.md, PRD.md, decisions.md, AGENTS.md, ralph.sh, execution-plan.json, commands.json, repo-contract.json, and manifest.json. Assessed each story for: acceptance criteria specificity, testability, scope clarity, expected files, and dependency correctness. Identified cross-story gaps.

### Fully executable stories (no issues)

| Story | Title | Notes |
|-------|-------|-------|
| ST-003 | Initialize project repository | Excellent AC, 14 items, specific and testable |
| ST-004 | Setup database | Good AC, clear migration instructions |
| ST-005 | Setup backend service | Good AC, Payload config + admin panel |
| ST-006 | Create frontend application | Adequate AC, route groups defined |
| ST-007 | Implement authentication | Excellent AC, specific HTTP status codes |
| ST-900 | Setup monitoring and logging | Good AC, health check + structured logging |
| ST-901 | Implement backups | Excellent AC, pg_dump + restore scripts |

### Partially executable stories (ambiguous but Codex can likely resolve)

| Story | Title | Gap |
|-------|-------|-----|
| ST-008 | RBAC | "editor" and "reviewer" roles referenced but not clearly defined — AGENTS.md does define 3 roles but stories are inconsistent |
| ST-010 | Draft/publish workflow | "published content visible through appropriate surface" — no public rendering story exists |
| ST-011 | Content preview | URL scheme not specified, slug field not defined in content model |

### Not executable as written (missing infrastructure or unclear scope)

| Story | Title | Blocker |
|-------|-------|---------|
| ST-001 | Define CMS content model | Does not enumerate which collections to create — spec.json defines 4 collections + 2 globals but story says only "content collections" |
| ST-002 | Configure CDN | References "public assets" and "public routes" that don't exist; untestable locally |
| ST-009 | Implement media library | S3/object storage mentioned in architecture but no story configures it |
| ST-012 | Implement scheduled publishing | Requires background job infrastructure that no story creates |

### Critical cross-story gaps

1. **Public site rendering has no owner** — spec says `admin_plus_public_site` mode; architecture mentions public routes; ST-010/011/012 reference "published content visible" — but no story implements `/posts/[slug]`, `/pages/[slug]`, or any public content page.

2. **S3 object storage not assigned** — architecture.md says media goes to S3-compatible storage; ST-009 (media library) doesn't configure S3 client or env vars; will default to local filesystem or fail.

3. **Background job runner not assigned** — ST-012 (scheduled publishing) needs a cron/job runner; Payload has no built-in background jobs; no story sets up Bull, BullMQ, or node-cron.

4. **Role definitions inconsistent** — AGENTS.md defines admin/editor/reviewer with detailed permissions; ST-008 says "admin and default user"; ST-010 says "reviewer or admin". Codex will get conflicting signals.

5. **ST-001 scope too vague** — spec.json defines collections (pages, posts, authors, media) with fields, globals (site-settings, homepage), and relationships (posts → authors). The story just says "define content collections" without enumerating them.

6. **ST-002 (CDN) is premature** — depends on `bootstrap.frontend` but references "public routes" that won't exist until much later. Likely to produce boilerplate with no real value.

### Recommended fixes before ralph execution

These should be applied to the **generator** (story engine, enrichment templates) for lasting value, or at minimum to the generated story files in `output/editorial-control-center/docs/stories/`:

1. **Enrich ST-001** — enumerate all collections from spec.json (pages, posts, authors, media), list expected fields per collection, define relationships, specify which collections support draft/publish.

2. **Add a public rendering story** (or fold into ST-010) — implement `/posts/[slug]` and `/pages/[slug]` route groups, integrate with draft/publish visibility.

3. **Enrich ST-009** — either configure S3-compatible storage (minio for local dev) or explicitly state "use Payload's local filesystem adapter for initial implementation".

4. **Enrich ST-012** — specify job runner choice (e.g., node-cron for simplicity), define cron expression, add idempotency requirement.

5. **Normalize role definitions** — update ST-008 and ST-010 to reference the canonical 3-role model defined in AGENTS.md (admin, editor, reviewer).

6. **Reconsider ST-002** — either defer CDN to after public site exists, or redefine as "configure Next.js static asset headers and Image component optimization".

---

## Session 3 — Bootstrap Hardening and YAML Spec Support (2026-03-19)

### What was fixed

1. **Interactive CLI robustness**
   - `initializer/flow/new_project.py`
   - `prompt_choice()` used `int(value)` without validation and crashed on invalid input.
   - Fixed by looping until the user enters a valid index or option string.
   - Regression coverage added in `tests/unit/test_new_project_inputs.py`.

2. **prepare/commands contract**
   - `initializer/flow/prepare_project.py`
   - `_detect_commands()` returned only the commands dict for `package.json` projects even though the caller expected `{commands, notes}`.
   - `prepare` also regenerated the bundle after detection and overwrote the project-specific `.openclaw/commands.json`.
   - Fixed by normalizing the return contract and writing detected commands after bundle regeneration.
   - Regression coverage added in `tests/unit/test_prepare_project.py`.

3. **Git hygiene before commit**
   - Root `.gitignore` updated to include `.pytest_cache/`.
   - Removed tracked `__pycache__/` and `.pyc` artifacts from the git index without deleting local files.

4. **Generated Next.js scaffold quality**
   - `initializer/renderers/scaffold_engine.py`
   - Real E2E validation on a generated `taskflow` project exposed that:
     - `npm run lint` failed because `eslint.config.mjs` imported `@eslint/flatcompat` without the package being installed.
     - `npm test` was only a placeholder string, not a real test.
     - Next rewrote `tsconfig.json` on first lint/build because `next-env.d.ts` and expected TS settings were missing.
   - Fixed by:
     - switching lint script to `eslint .`
     - using `FlatCompat` from `@eslint/eslintrc`
     - adding required dev dependencies
     - generating `next-env.d.ts`
     - generating `tsconfig.test.json`
     - generating a real smoke test in `src/__tests__/smoke.test.tsx`
     - avoiding migration-template lint noise with `void pgm;`
   - Coverage expanded in `tests/unit/test_scaffold_engine.py`.

5. **YAML support for `initializer new --spec`**
   - `initializer/flow/new_project.py`
   - README documented `examples/next-payload-postgres.input.yaml`, but the loader only did `json.loads(...)`.
   - Fixed by:
     - supporting `.json`, `.yaml`, and `.yml`
     - resolving `spec.yaml` / `spec.yml` when `--spec` points to a directory
     - normalizing playbook-style YAML (`playbook_id`, `guided_answers`, `critical_confirmations`) into the internal `answers` contract
     - using playbook detection hints to preserve correct archetype inference for playbook-based specs
   - Coverage added in `tests/unit/test_spec_loader.py`.

### Real validations performed

1. **Repository tests after CLI/prepare fixes**
   - `282 passed in 21.86s`

2. **Real generated app validation: `taskflow`**
   - `initializer new`
   - `initializer prepare`
   - `./ralph.sh --dry-run`
   - `npm install`
   - `docker compose config -q`
   - `npm test`
   - `npm run typecheck`
   - `npm run lint`
   - `npm run build`
   - `npm run start`
   - HTTP check on `/` returned `200 OK`

3. **Focused scaffold test after lint/test fixes**
   - `tests/unit/test_scaffold_engine.py` → `52 passed`
   - regenerated `taskflow` project now passes:
     - `npm test`
     - `npm run lint`
     - `npm run build`

4. **Focused YAML loader validation**
   - `tests/unit/test_spec_loader.py tests/unit/test_new_project_inputs.py tests/unit/test_spec_contract.py` → `7 passed`
   - smoke test with `.venv/bin/python -m initializer new --spec <yaml>` generated a project successfully

### Key product-level findings from this session

- The highest-value real-world test remains: generate a project, run `prepare`, then validate the generated app with real package install, lint, tests, build, and startup.
- The previous `--spec` path was not trustworthy for documented YAML playbooks; this is now fixed.
- The generated scaffold is materially stronger after this session because it now ships a real test and a working lint configuration instead of placeholders.

---

## Session 2 — Ralph Execution Analysis (2026-03-19)

### Full ralph.sh execution on todo-app: 25/25 stories DONE

Analyzed 21 Codex sessions from `ralph-evidence/todo-app/20260318T233312Z/`.

**Execution time**: ~4h05m (23:29 → 03:34 UTC)
**Static validation pass rate**: 100% (typecheck, lint, build — after self-corrections)
**Database migration blockers**: 12 stories (Postgres not running in environment — not code bugs)

### Bugs introduced by Codex (not Specwright)

| # | Severity | Bug | Root cause | Specwright mitigation |
|---|----------|-----|-----------|----------------------|
| 1 | CRITICAL | `.env` defines `NEXT_PUBLIC_API_URL` but code uses `NEXT_PUBLIC_API_BASE_URL` | Codex invented a different variable name | GUARD-002: scope boundary now enforces using `.env.example` names exactly |
| 2 | CRITICAL | `import Layout` (default) but component exports `export function Layout` (named) | Codex import error | Not preventable via story — code-level mistake |
| 3 | HIGH | `src/pages/_app.tsx` and `_document.tsx` created — Pages Router in App Router project | Codex used wrong Next.js pattern | GUARD-001: scope boundary now explicitly prohibits `src/pages/` |
| 4 | HIGH | Non-localized route `src/app/(app)/page.tsx` unreachable (middleware redirects to `[locale]/`) | Codex left orphan route after adding i18n | Not preventable via story — requires runtime validation |
| 5 | MEDIUM | `.env.local` missing for `--env-file=.env.local` scripts in package.json | Scaffold comment was misleading | BUG-005/BUG-006: fixed in Specwright |

### Recurring pattern: migration lint cleanup

Auto-generated migration stubs from ST-008 had unused `pgm` parameters. Every subsequent story (15+) had to clean this lint warning, wasting Codex tokens and time.

**Potential Specwright fix**: Generate migration stubs with `/* eslint-disable @typescript-eslint/no-unused-vars */` or use `_pgm` parameter naming convention.

### What still needs runtime verification

Once Postgres + Docker available:
1. `npm run db:migrate` — 12 migration files generated but never executed
2. Auth flow — login/register/logout against live DB
3. Backup/restore scripts — need `pg_dump`/`pg_restore`
4. Worker scheduler — needs live execution interval test

---

## E2E Validation (2026-03-18)

Two projects generated from scratch via `initializer new --spec`:

### taskflow (node-api + postgres)
| Check | Status |
|-------|--------|
| `.env.local` gerado e idêntico ao `.env.example` | PASS |
| Express/cors/helmet em `package.json` | PASS |
| `ralph.sh` usa `${CODEX_MODEL:-gpt-5.4}` | PASS |
| `ralph.sh` tem `exit 1` em falha | PASS |
| ST-900/ST-901 com `story_key` correto | PASS |
| StoryGraph — order topológica sem ciclos (8 stories) | PASS |
| BUG-002 — progress parser retorna IDs corretos | PASS |
| StoryScheduler — identifica próxima story corretamente | PASS |

### newshub-cms (Payload + postgres)
| Check | Status |
|-------|--------|
| `.env.local` com `PAYLOAD_SECRET` | PASS |
| `payload` / `@payloadcms/next` em deps; sem express | PASS |
| `src/payload.config.ts`, `src/collections/Users.ts`, `.npmrc` presentes | PASS |
| Migration commands separados (`payload migrate:create/status`) | PASS |
| `${CODEX_MODEL:-gpt-5.4}` e `exit 1` em `ralph.sh` | PASS |
| ST-900/ST-901 com `story_key` | PASS |
| StoryGraph carrega e ordena 14 stories sem ciclos | PASS |

---

## 1. Generated Projects Health Report

### todo-app (archetype: todo-app, stack: Next.js + node-api + Postgres)

| Check | Status | Notes |
|-------|--------|-------|
| spec.json present & valid | PASS | 879 lines, all required keys present |
| architecture.md generated | PASS | 3 components documented |
| decisions.md generated | PASS | Architecture decisions captured |
| PRD.md generated | PASS | Project description present |
| .codex/AGENTS.md present | PASS | Codex agent instructions generated |
| .openclaw/ bundle complete | PASS | 6 files: manifest, execution-plan, commands, AGENTS.md, OPENCLAW.md, repo-contract |
| docs/stories/ complete | PASS | 11 story files (ST-001 through ST-009, ST-900, ST-901) |
| ralph.sh executable | PASS | 500 lines, chmod +x |
| docker-compose.yml present | PASS | Postgres service configured |
| Dockerfile present | PASS | Multi-stage build |
| package.json present | PASS | Dependencies installed |
| Enriched stories (acceptance criteria) | PASS | All 11 stories have acceptance_criteria |
| Enriched stories (scope boundaries) | PASS | All 11 stories have scope_boundaries |
| Enriched stories (expected files) | PASS | All stories have expected_files |
| Enriched stories (validation commands) | PASS | All stories have validation.commands |
| Enriched stories (depends_on) | PASS | Dependency chains correct |
| Execution plan phases | PASS | 6 phases: bootstrap(4), features(1), product(4), domain(0), automation(0), operations(2) |
| ralph.sh full run | PASS | 11/11 stories completed, all DONE in progress.txt |
| Progress tracking | PASS | All stories logged with START → DONE timestamps |

**Result: 19/19 checks passed**

### todo-app-design (archetype: todo-app, Payload CMS variant)

| Check | Status | Notes |
|-------|--------|-------|
| spec.json present & valid | PASS | |
| Scaffold files present | PASS | package.json, docker-compose, Dockerfile, etc. |
| Story files present | PASS | 11 story files generated |
| ralph.sh present | PASS | |
| Execution (ST-001 to ST-005) | PASS | Bootstrap + auth completed |
| Execution (ST-006) | PASS | Succeeded on retry (build error: `_document` page not found) |
| Execution (ST-007) | PASS | Succeeded on retry (webpack module error) |
| Execution (ST-008) | PASS | Completed |
| Execution (ST-009) | PASS | Succeeded on retry (same `_document` build error) |
| Execution (ST-900) | **FAIL** | Codex execution failed 3 times (not a Specwright bug — Codex runtime error) |
| Execution (ST-901) | SKIP | Blocked by ST-900 failure (ralph.sh stops on failure) |

**Result: 9/11 stories completed. Failure at ST-900 is a Codex runtime issue, not a Specwright generation bug.**

The recurring build error (`Cannot find module for page: /_document`) in retries is a Next.js Pages Router artifact when using App Router. Stories self-healed via retry, but it points to an opportunity: the scaffold could add `--turbopack` or configure build to avoid this.

---

## 2. Issues & Improvements

### BUG-001: StoryGraph indexes by `id` but `depends_on` uses `story_key` (CRITICAL)

- **Location**: [story_graph.py:29](initializer/graph/story_graph.py#L29), [story_graph.py:68](initializer/graph/story_graph.py#L68)
- **Severity**: Critical
- **Type**: Bug

**Description**: `StoryGraph.load()` builds the dict keyed by story `id` (e.g. `ST-001`), but `depends_on` arrays contain `story_key` values (e.g. `bootstrap.repository`). The `available()` method checks `all(dep in completed for dep in deps)` — since `completed` contains `id`s but deps contain `story_key`s, dependency resolution never matches, making every story appear "available" simultaneously.

```python
# story_graph.py:29 — indexes by id
stories = {story["id"]: story for story in data["stories"]}

# spec.json — depends_on uses story_key
"depends_on": ["bootstrap.repository"]  # not "ST-001"
```

**Impact**: `StoryGraph` and `StoryScheduler` are currently unused by ralph.sh (which uses its own sequential loop), so this doesn't break generated projects. But these classes are dead code / broken infrastructure.

**Suggested fix**: Either:
1. Index by `story_key` instead of `id`, or
2. Build a `story_key → id` lookup and translate `depends_on` at load time, or
3. Change story generation to use `id` in `depends_on`

---

### BUG-002: `load_completed_from_progress()` extracts "DONE" instead of story ID (HIGH)

- **Location**: [story_scheduler.py:32](initializer/runtime/story_scheduler.py#L32)
- **Severity**: High
- **Type**: Bug

**Description**: The progress.txt format is:
```
[2026-03-17T12:14:20Z] ST-001 — DONE — Initialize project repository
```

The parser splits on `—` and takes `parts[1].strip().split()[0]`:
- `parts[0]` = `[2026-03-17T12:14:20Z] ST-001 `
- `parts[1]` = ` DONE `
- `parts[1].strip().split()[0]` = `DONE` (not `ST-001`)

The story ID is in `parts[0]`, not `parts[1]`.

**Impact**: Same as BUG-001 — `StoryScheduler` is currently unused by ralph.sh, so no runtime impact yet. But this function returns `{"DONE"}` instead of `{"ST-001", "ST-002", ...}`.

**Suggested fix**:
```python
parts = line.split("—")
if len(parts) > 1 and "DONE" in parts[1]:
    # Story ID is the last word before the first —
    story = parts[0].strip().split()[-1]
    completed.add(story)
```

---

### BUG-003: Migration command suffix concatenation doesn't work for all backends (MEDIUM)

- **Location**: [codex_bundle.py:423](initializer/renderers/codex_bundle.py#L423), [codex_bundle.py:512](initializer/renderers/codex_bundle.py#L512)
- **Severity**: Medium
- **Type**: Bug

**Description**: The generated prompt tells the AI agent to run `$MIGRATION_CMD:create`, which works for Payload (`npx payload migrate:create`) but not for:
- `npm run db:migrate` → `npm run db:migrate:create` (only works if the npm script exists)
- `python manage.py migrate` → `python manage.py migrate:create` (invalid)

**Suggested fix**: Have `_detect_migration_command()` return a dict with separate `run`, `create`, and `status` commands per backend:
```python
def _detect_migration_command(spec):
    backend = ...
    if backend in ("payload", "payload-cms"):
        return {"run": "npx payload migrate", "create": "npx payload migrate:create", "status": "npx payload migrate:status"}
    elif backend == "django":
        return {"run": "python manage.py migrate", "create": "python manage.py makemigrations", "status": "python manage.py showmigrations"}
    else:
        return {"run": "npm run db:migrate", "create": "npm run db:migrate:create", "status": "npm run db:migrate:status"}
```

---

### IMP-001: `_package_json()` has empty `pass` for non-Payload backends (HIGH)

- **Location**: [scaffold_engine.py:275-277](initializer/renderers/scaffold_engine.py#L275-L277)
- **Severity**: High
- **Type**: Missing implementation

**Description**: When backend is `node-api` (not Payload), the `else` branch does nothing:
```python
else:
    # Generic node-api: Express for API routes if not using Next.js API routes
    pass
```

This means `node-api` projects get no backend-specific dependencies (no Express, no body-parser, no cors). The todo-app still works because Next.js API routes handle everything, but any project that needs a standalone Express backend gets an empty dependency set.

**Suggested fix**: Add Express + common middleware dependencies:
```python
else:
    pkg["dependencies"]["express"] = "^4"
    pkg["dependencies"]["cors"] = "^2"
    pkg["dependencies"]["helmet"] = "^7"
```

---

### IMP-002: No tests for scaffold generation (MEDIUM)

- **Location**: `tests/` directory
- **Severity**: Medium
- **Type**: Missing test coverage

**Description**: The 157-test suite covers archetype detection, capability derivation, story engine, spec contract, and project structure — but has zero tests for `scaffold_engine.py`, `codex_bundle.py`, or `openclaw_bundle.py`. These are the most complex renderers (684, 757, and 648 lines respectively).

**Suggested fix**: Add tests that:
1. Generate scaffold for each backend type and assert key files exist
2. Verify `package.json` has correct dependencies per stack
3. Verify `ralph.sh` is executable and contains correct migration commands
4. Verify execution-plan.json matches spec stories

---

### IMP-003: ST-900 and ST-901 lack `story_key` field (MEDIUM)

- **Location**: [refine_engine.py](initializer/ai/refine_engine.py)
- **Severity**: Medium
- **Type**: Consistency gap

**Description**: All stories from `story_engine.py` have a `story_key` (e.g. `bootstrap.repository`), but ST-900 and ST-901 from `refine_engine.py` don't. The `openclaw_bundle.py` phase classifier works around this with hardcoded ID checks:
```python
# Hardcoded fallback for ST-900, ST-901
```

Without `story_key`, these stories can't be referenced in `depends_on` by key, and phase classification is fragile.

**Suggested fix**: Add `story_key` to refine engine stories:
- ST-900: `"story_key": "operations.monitoring"`
- ST-901: `"story_key": "operations.backups"`

---

### IMP-004: ralph.sh hardcodes `--model gpt-5.4` (LOW)

- **Location**: [codex_bundle.py](initializer/renderers/codex_bundle.py) (ralph.sh template)
- **Severity**: Low
- **Type**: Hardcoded value

**Description**: The model is hardcoded in the generated ralph.sh. Users can't override it without editing the script.

**Suggested fix**: Accept `$CODEX_MODEL` env var with a default:
```bash
CODEX_MODEL="${CODEX_MODEL:-gpt-5.4}"
```

---

### IMP-005: `_has_discovery()` may miss manual discovery signals (LOW)

- **Location**: [capability_derivation.py](initializer/engine/capability_derivation.py)
- **Severity**: Low
- **Type**: Edge case

**Description**: `_has_discovery()` checks `discovery.get("assisted", False)`, meaning only AI-assisted discovery counts. If a user manually provides `decision_signals` without `assisted: true`, the signal governance rules fall back to weaker defaults.

**Suggested fix**: Check for the presence of `decision_signals` directly, not just the `assisted` flag.

---

### IMP-006: Cycle detection traverses `depends_on` keys that don't exist in graph (MEDIUM)

- **Location**: [story_graph.py:93](initializer/graph/story_graph.py#L93)
- **Severity**: Medium
- **Type**: Bug (latent, masked by BUG-001)

**Description**: `detect_cycles()` calls `self.dependencies(node)` which returns `story_key` values, then recursively calls `visit(dep)` which calls `self.dependencies(dep)` — but `dep` is a `story_key` not in `self.stories` (which is keyed by `id`). This raises `KeyError`. Currently masked because `detect_cycles` would fail on any graph with dependencies.

**Impact**: Loading a `StoryGraph` from any spec with dependencies would crash. Masked because `StoryGraph` is unused in production paths.

---

### IMP-007: Signal conflict detection is silent (LOW)

- **Location**: [discovery_merge.py](initializer/ai/discovery_merge.py)
- **Severity**: Low
- **Type**: Improvement

**Description**: When surface answers conflict with discovery signals (e.g., surface says `needs_cms: true` but discovery says `false`), the merge follows the hierarchy but doesn't warn the user about the conflict.

**Suggested fix**: Collect conflicts and emit a summary after merge.

---

### IMP-008: `topological_order()` adds all available stories per round (LOW)

- **Location**: [story_graph.py:121-123](initializer/graph/story_graph.py#L121-L123)
- **Severity**: Low
- **Type**: Inefficiency

**Description**: The inner loop checks `if story not in completed` but `available()` already excludes completed stories. The check is redundant.

---

### IMP-009: Scaffold doesn't configure `.env.local` for all stacks (LOW)

- **Location**: [scaffold_engine.py](initializer/renderers/scaffold_engine.py)
- **Severity**: Low
- **Type**: Incomplete

**Description**: The uncommitted changes add `.env.local` to bootstrap story expected files, but the scaffold engine may not generate it for all backend types. This could cause the first story to fail validation if it checks for `.env.local`.

---

### IMP-010: ralph.sh `break 2` exits the story loop but doesn't distinguish retry-exhausted from hard failure (LOW)

- **Location**: Generated ralph.sh lines 415, 489
- **Severity**: Low
- **Type**: UX improvement

**Description**: When either Codex crashes or validation fails after max retries, the script exits with the same flow. The exit message is clear, but the exit code is 0 in both cases (falls through to the summary). A non-zero exit code would help CI/CD pipelines.

---

### IMP-011: `editorial-e2e-test` output directory not cleaned up (LOW)

- **Location**: `output/editorial-e2e-test/`
- **Severity**: Low
- **Type**: Cleanup

**Description**: A third generated project exists in `output/` that appears to be a test artifact. Should either be in `.gitignore` or cleaned up.

---

## 3. Prioritized Action Plan

| Priority | ID | Effort | Impact | Action | Status |
|----------|----|--------|--------|--------|--------|
| 1 | BUG-001 | Small | Critical | Fix StoryGraph to use `story_key` as index or translate `depends_on` | DONE |
| 2 | BUG-002 | Small | High | Fix progress parser to extract story ID from correct split position | DONE |
| 3 | IMP-001 | Small | High | Add Express/cors/helmet deps for `node-api` backend in scaffold | DONE |
| 4 | IMP-006 | Small | Medium | Fix is same as BUG-001 — cycle detection inherits the key mismatch | DONE |
| 5 | BUG-003 | Medium | Medium | Refactor migration commands to per-backend dicts with run/create/status | DONE |
| 6 | IMP-003 | Small | Medium | Add `story_key` to ST-900 and ST-901 in refine engine | DONE |
| 7 | IMP-002 | Large | Medium | Add scaffold/bundle test coverage | DONE |
| 8 | IMP-005 | Small | Low | Check `decision_signals` presence instead of `assisted` flag | DONE |
| 9 | IMP-004 | Small | Low | Make Codex model configurable via env var | DONE |
| 10 | IMP-010 | Small | Low | Exit with non-zero code on failure in ralph.sh | DONE |
| 11 | IMP-007 | Medium | Low | Surface signal conflicts to user after merge | DONE |
| 12 | IMP-009 | Small | Low | Ensure `.env.local` scaffold generation for all stacks | DONE |
| 13 | IMP-008 | Tiny | Low | Remove redundant `not in completed` check | DONE |
| 14 | IMP-011 | Tiny | Low | Clean up or gitignore test output directories | N/A |

**All 14 original items resolved.** 13 implemented, 1 already covered by existing `.gitignore`.

### Session 2 additions (2026-03-19)

| Priority | ID | Effort | Impact | Action | Status |
|----------|----|--------|--------|--------|--------|
| 15 | BUG-005 | Tiny | Medium | Remove stale "cp .env.example" from scaffold comments/README/docstring | DONE |
| 16 | BUG-006 | Tiny | Medium | Guard `.env.local` copy with `test -f` in commands_engine and openclaw_bundle | DONE |
| 17 | GUARD-001 | Tiny | High | Add "Do NOT create files in src/pages/" scope boundary to bootstrap stories | DONE |
| 18 | GUARD-002 | Tiny | High | Add "Use env var names exactly as in .env.example" scope boundary | DONE |
| 19 | DEAD-001 | Tiny | Low | Remove orphan `synthesis/stories.py` | DONE |
| 20 | DEAD-002 | Tiny | Low | Remove broken `test_prd_scoring.py` | DONE |
| 21 | INFRA-001 | Small | Medium | GitHub Actions CI workflow | DONE |
| 22 | INFRA-002 | Tiny | Medium | Add pytest to `[project.optional-dependencies]` | DONE |
| 23 | INFRA-003 | Tiny | Low | Expand `.gitignore` | DONE |
| 24 | INFRA-004 | Small | Low | Add Makefile | DONE |
| 25 | README | Medium | High | Full README update (venv, test count, examples, designs) | DONE |

### Open items (session 3)

| Priority | ID | Effort | Impact | Action | Status |
|----------|----|--------|--------|--------|--------|
| 1 | RUNTIME-001 | Medium | High | Run `docker compose up -d && npm run dev` on a generated project to validate Dockerfile/docker-compose | DONE |
| 2 | LINT-001 | Tiny | Medium | Generate migration stubs with `_pgm` or eslint-disable to prevent recurring lint cleanup | DONE |
| 3 | TAG-001 | Tiny | Medium | Create v0.1.0 tag and GitHub release with notes | PENDING (gh CLI not installed; tag 0.1.0 already exists on master) |
| 4 | CODEX-001 | Medium | Medium | Investigate if ralph.sh validation can catch orphan routes and import mismatches | DONE |

#### RUNTIME-001 Results (2026-03-19)

| Check | Status | Notes |
|-------|--------|-------|
| `docker compose up -d` | PASS | Postgres healthy on port 5433 |
| `npm run dev` (Next.js) | PASS | Server starts, ready in 22.4s |
| `/api/health` | PASS | 200 OK, database: "up" |
| `node-pg-migrate up` | PASS | Migrations complete |
| Root page `/` | FAIL | Codex bug #2 (named vs default import of Layout) — not a Specwright bug |

#### LINT-001 Changes

- Scaffold now generates `src/lib/migration-template.cjs` with `_pgm` parameter naming for non-Payload postgres projects
- `package.json` now includes `node-pg-migrate`, `pg` dependencies and `db:migrate`, `db:migrate:create`, `db:migrate:status` scripts with `--template-file-name` pointing to the custom template
- AGENTS.md now instructs Codex to use `_pgm` in migration function signatures
- 6 new tests added (244 total)

#### CODEX-001 Changes

ralph.sh validation now includes two new checks:

1. **`npm run typecheck` (blocking)**: Runs `tsc --noEmit` when a `typecheck` script exists in `package.json`. Catches import mismatches (TS2613: named vs default) that `next build` misses because SWC does not enforce TypeScript import shape rules.

2. **Orphan route detection (warning)**: When `middleware.ts` exists and contains locale-based redirects, scans for `page.tsx` files outside `[locale]/` and `api/` paths. Reports them as possibly unreachable due to middleware interception. Non-blocking (warning only).

Also fixed pre-existing SyntaxWarnings from invalid escape sequences (`\`` and `\.`) in the ralph.sh f-string template.

#### AUTH-001: ralph.sh auth check updated

ralph.sh no longer checks for `OPENAI_API_KEY`. Codex CLI uses account login (`codex auth login`), not API keys. The auth check now verifies the `codex` CLI is installed and guides the user to log in. (The enrichment pipeline — prd_review, design_reference — still correctly uses `OPENAI_API_KEY` via API.)

#### TODO-APP: Runtime bug fixes (Codex-generated code, not Specwright)

Fixed 9 bugs in `output/todo-app` to make the demo project functional:

| Fix | Root cause |
|-----|-----------|
| `import { Layout }` (named, not default) | Codex used default import for named export |
| `migration-status.ts` — `closeDatabasePool` + `getDbPool` | Codex invented wrong function names |
| `usePathname()` / `useSearchParams()` null guards | Codex assumed Next.js 15 hooks never return null |
| Deleted `src/pages/_app.tsx` + `_document.tsx` | Codex created Pages Router files in App Router project |
| `npm install` — express/cors/helmet missing | Dependencies listed but never installed |
| DB reset + ran `src/models/migrations/` (31 migrations) | Two migration directories conflicted; `assignee_id` column never created |
| Deleted orphan `src/lib/migrations/` (3 files) | Dead migrations that conflicted with `src/models/migrations/` |
| `NEXT_PUBLIC_API_URL` → `NEXT_PUBLIC_API_BASE_URL` | Codex used wrong env var name on home page |
| Logout `status !== 204` → `!response.ok` | Server returns 200, client expected 204 |

#### Remaining todo-app bugs (Codex-generated, not Specwright)

| Severity | Bug |
|----------|-----|
| HIGH | `/todos` and `/reports` return 404 — middleware redirects to `/en/todos` but `[locale]/(app)/todos/page.tsx` doesn't exist |
| MEDIUM | `src/app/(app)/page.tsx` is orphan — middleware redirects `/` to `/en` |
| LOW | `next.config.ts` missing (ST-001 CDN not implemented) |
| LOW | `npm test` is a no-op — no test framework installed |

### Open items (next session)

| Priority | ID | Effort | Impact | Action | Status |
|----------|----|--------|--------|--------|--------|
| 1 | STORY-001 | Medium | High | Stories must specify migration directory (`src/lib/migrations/`) explicitly in scope boundaries — Codex created `src/models/migrations/` diverging from scaffold | DONE |
| 2 | STORY-002 | Medium | High | i18n story must instruct "move ALL existing pages into `[locale]/`" — Codex only duplicated the home page, leaving `/todos` and `/reports` as 404s | DONE |
| 3 | STORY-003 | Small | Medium | Stories should specify API response contracts (status codes) in acceptance criteria — Codex returned 200 but client expected 204 for logout | DONE |
| 4 | STORY-004 | Small | Medium | Bootstrap story should set up a test framework (vitest/jest) so `npm test` isn't a no-op — every subsequent story validation relies on it | DONE |
| 5 | TAG-001 | Tiny | Medium | Create v0.1.0 tag and GitHub release with notes | SKIPPED (tag 0.1.0 already exists; gh CLI not available) |
| 6 | SCAFFOLD-001 | Small | Medium | `package.json` migration scripts must use same `--migrations-dir` as the template file path to prevent directory divergence | DONE (already consistent) |
| 7 | QUALITY-001 | Medium | High | Audit quality of generated PRD.md, architecture.md, decisions.md, story files, AGENTS.md, execution-plan.json, and all ralph loop inputs — verify enrichment pipeline produces sufficient context for Codex to implement without ambiguity (migration paths, API contracts, route structure, env var names, test setup) | DONE |

---

## Session 4 — Quality Audit & Story Gaps (2026-03-19)

**Test suite**: 256/256 passed — 12 new tests added

### QUALITY-001: Generated Artifact Audit

Audited all artifacts (PRD.md, architecture.md, decisions.md, stories, AGENTS.md, execution-plan.json) against the 9 Codex bugs from Session 2. Root cause analysis:

| Codex Bug | Root Cause in Artifacts | Fix Applied |
|-----------|------------------------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` instead of `NEXT_PUBLIC_API_URL` | AGENTS.md did not enforce env var naming | Added scope boundary: "Use env var names exactly as in .env.example" to AGENTS.md |
| Named vs default import (`Layout`) | Not preventable via story (code-level mistake) | — |
| `src/pages/_app.tsx` and `_document.tsx` created | AGENTS.md lacked explicit App Router instruction | Added "Do NOT create files in src/pages/" to AGENTS.md global scope boundaries |
| Orphan route `/page.tsx` outside `[locale]/` | No i18n story existed at all | STORY-002: Created `feature.i18n-setup` story with explicit instructions |
| `.env.local` missing | Already fixed in Session 2 (BUG-005/BUG-006) | — |
| Migration in `src/models/migrations/` instead of `src/lib/migrations/` | Stories lacked migration directory specification | STORY-001: Added `_MIGRATION_DIR_BOUNDARY` to all schema-changing stories |
| `migration_cmd:create` concatenation in AGENTS.md | AGENTS.md used old `{migration_cmd}:create` pattern | Fixed to use separate `{migration_create}` variable |
| Logout returned 200 but client expected 204 | Auth story had no status code contracts | STORY-003: Added HTTP status codes to auth acceptance criteria |
| `npm test` was a no-op throughout | Bootstrap story didn't set up test framework | STORY-004: Added vitest/jest requirement to bootstrap.repository |

### Changes Applied

#### STORY-001: Migration directory scope boundary
- Added `_MIGRATION_DIR_BOUNDARY` constant to story_engine.py
- Applied to: `bootstrap.database`, `feature.authentication`, `feature.roles`, `feature.media-library`, `product.todo-model`
- Text: "All migrations MUST be created in `src/lib/migrations/` using `npm run db:migrate:create`"

#### STORY-002: i18n story generation
- Created new `feature.i18n-setup` story (generated when `i18n` in capabilities)
- Acceptance criteria: middleware setup, ALL pages moved into `[locale]/`, LocaleSwitcher, translation files
- Scope boundary: explicitly warns that orphan routes outside `[locale]/` will return 404
- Expected files: `middleware.ts`, `[locale]/layout.tsx`, `LocaleSwitcher`, message catalogs

#### STORY-003: API response contracts
- Auth story acceptance criteria now include HTTP status codes:
  - `POST /api/auth/register` → 201 success, 400 validation, 409 duplicate
  - `POST /api/auth/login` → 200 + token success, 401 invalid
  - `POST /api/auth/logout` → 200 success

#### STORY-004: Test framework in bootstrap
- `bootstrap.repository` now requires vitest (or jest) installation
- Acceptance criteria: real test runner, at least one smoke test
- Expected files: `vitest.config.ts`, `src/__tests__/smoke.test.ts`
- Validation: `npm test` added to commands

#### SCAFFOLD-001: Migration directory consistency
- Already consistent — scaffold_engine.py uses `--migrations-dir src/lib/migrations` in all three scripts
- Stories now enforce the same path via `_MIGRATION_DIR_BOUNDARY`

#### AGENTS.md quality improvements
- Fixed migration workflow to use separate `{migration_create}` and `{migration_status}` variables (not concatenation)
- Added migration directory instruction: `src/lib/migrations/`
- Added global scope boundaries: no `src/pages/`, enforce `.env.example` variable names

#### Tests added (12 new, 256 total)
- `test_database_story_has_migration_dir_boundary`
- `test_auth_story_has_migration_dir_boundary`
- `test_todo_model_has_migration_dir_boundary`
- `test_i18n_capability_generates_story`
- `test_i18n_story_warns_about_orphan_routes`
- `test_i18n_story_requires_moving_all_pages`
- `test_auth_story_has_status_codes`
- `test_bootstrap_repo_requires_test_framework`
- `test_codex_agents_md_has_migration_directory`
- `test_codex_agents_md_uses_separate_migration_commands`
- `test_codex_agents_md_forbids_src_pages`
- `test_codex_agents_md_enforces_env_var_names`

### PRD / Architecture / Decisions Generator Rewrite

**Test suite**: 278/278 passed — 22 new tests added for generators

#### Problem
- **PRD.md** (4/10): Generic problem statement, placeholder personas, no scope, dumped 37 architecture decisions
- **architecture.md** (7/10 → degraded by decisions dump): Good structural content but duplicated decisions from decisions.md
- **decisions.md** (3/10): 37 decisions where DEC-007 to DEC-037 all had "This decision was derived in the generated architecture" as reason

#### Changes

**`write_prd()` rewritten:**
- Problem statement derived from `app_shape` (concrete text per archetype, not generic)
- Personas derived from `domain_model.roles` (e.g. "User: Can create_task, read_own_tasks") instead of "Primary User: Accomplish core workflows"
- Scope in/out derived from features + capabilities (e.g. "Out of Scope: Public-facing marketing site" when no public-site capability)
- Architecture decisions dump REMOVED — lives in decisions.md only
- Discovery signals and story overview kept (compact)

**`write_architecture()` rewritten:**
- Components, communication, boundaries, request flows: KEPT (these were good)
- Raw decisions dump at end: REMOVED
- New "Key Constraints" section added: migration directory, env var naming, App Router rule, i18n routing
- Cross-references `decisions.md` instead of duplicating

**`write_decisions()` rewritten:**
- DEC-001 to DEC-004: meta-decisions (source of truth, architecture stability, stack, capabilities) — compact format
- Architecture decisions: deduplicated with word-overlap algorithm (70% threshold), categorized (Security, Domain, Performance, Operations, Architecture)
- Each decision has a real reason derived from content (e.g. "Reduces latency and server load for static content" instead of "derived in the generated architecture")
- Result: ~60 lines instead of 310 lines for the same input

**Tests added (22 new, 278 total):**
- PRD: project name, concrete problem statement, concrete personas, scope, no decision dump, stories, signals
- Architecture: components, communication, boundaries, request flow, background jobs, no decision dump, key constraints, i18n
- Decisions: project constraints, stack, deduplication, real reasons, categories, line count < 100

---

## 4. SaaS Roadmap

### Product Positioning

**What Specwright is**: A specification compiler — it takes a one-line prompt through a structured pipeline (archetype detection → signal governance → capability derivation → architecture/story/domain engines) and produces an executable project specification with enriched stories, scaffold code, and AI-agent-ready bundles.

**Target customer**: Development agencies and teams that spin up new projects frequently. The value proposition is: "Describe what you want, get a project that an AI agent can build story-by-story."

**Pricing model**: Per-project generation + optional seat-based access for team features (shared archetypes, custom pipelines, project history).

### Gap Analysis: CLI → SaaS

| CLI Assumption | SaaS Requirement |
|---------------|-------------------|
| Interactive terminal prompts (`input()`) | Web form / API endpoint for answers |
| Filesystem writes (`Path.write_text()`) | Object storage (S3) or ZIP download |
| Local `.venv` execution | Containerized or serverless compute |
| Single-user, single-machine | Multi-tenant with auth, isolation, quotas |
| OpenAI API key from user's env | Platform-managed API keys with usage metering |
| Output directory on disk | Downloadable artifact or Git repo push |

### Minimum Viable SaaS (3-screen app)

1. **New Project**: Form for prompt + archetype override + stack preferences → calls pipeline → shows progress
2. **Project View**: Spec viewer with stories, architecture, domain model → download bundle (ZIP) or push to GitHub
3. **Dashboard**: List of generated projects with status, re-run, clone

### Architecture Advantage

The core engines are already API-shaped:
- `generate_stories(spec: dict) → dict` — pure dict-in, dict-out
- `derive_capabilities(spec: dict) → list` — no I/O
- `detect_archetype(prompt: str) → dict` — stateless
- `build_scaffold(spec: dict) → dict[filename, content]` — pure mapping

The I/O layer (CLI prompts in `new_project.py`, filesystem writes in renderers) is the only part that needs abstraction.

### Roadmap Phases

| Phase | Focus | Key Deliverables |
|-------|-------|-----------------|
| **1. Solidify Core** (now) | Fix bugs, add scaffold tests, stabilize pipeline | BUG-001/002/003 fixes, scaffold test suite, StoryGraph working |
| **2. API Layer** | Extract HTTP API from CLI flow | FastAPI wrapper around pipeline, async job queue, artifact storage |
| **3. Multi-Tenancy** | Auth, isolation, usage tracking | User accounts, project isolation, API key management, usage metering |
| **4. Agent Integration** | Direct integration with AI coding agents | GitHub App for auto-PR, webhook for story completion, agent-agnostic bundle format |
| **5. Ecosystem** | Custom archetypes, marketplace, team features | User-contributed archetypes, shared signal governance rules, team workspaces |

### Biggest Risks

1. **Value capture**: The spec is a commodity once generated — users may generate once, then never return. Mitigation: make the spec a living document (re-run on scope changes, track drift).

2. **"Good enough" AI**: As LLMs get better at generating projects from scratch, the structured pipeline may seem unnecessary. Mitigation: the pipeline's value is determinism and repeatability — an LLM gives different output each time, Specwright gives the same output for the same input.

3. **Archetype lock-in**: 9 archetypes cover common cases but can't handle novel projects. Mitigation: the `generic-web-app` fallback + custom archetype support in Phase 5.

4. **OpenAI dependency**: ralph.sh is tightly coupled to Codex CLI and `gpt-5.4`. Mitigation: IMP-004 (configurable model) + agent-agnostic bundle format in Phase 4.

5. **Premature complexity**: Adding SaaS features before the core pipeline is bulletproof risks building on a shaky foundation. Mitigation: Phase 1 first — fix the 3 bugs, add test coverage, validate with more archetypes.

---

## Appendix: Test Suite Summary

```
238 passed in 4.11s

Coverage areas:
- Archetype detection (keyword scoring, canonical IDs)
- Capability derivation (signal governance, normalize)
- Story engine (generation, merge, enrichment, dependencies, stack-aware paths)
- Story engine signals (backoffice, client-portal, project-tracking, boolean guard)
- Spec contract (initial spec shape, capability derivation updates)
- Project structure engine (Node, Python, Go structures, output shape)
- StoryGraph (load, cycle detection, topological order, dependency translation)
- StoryScheduler (next_story, load_completed_from_progress)
- Scaffold engine (37 tests: file creation, Payload vs node-api, database variants,
  package.json deps, .env.local generation, port derivation, layout/page content)
- Codex bundle (24 tests: AGENTS.md, ralph.sh, scope boundaries, migration commands,
  configurable model, exit codes, per-backend migration dicts)
- OpenClaw bundle (execution plan, phases, commands.json, manifest, stack-aware commands)

- Assist flow (discovery, conflicts, challenge decisions — 19 tests)

Remaining without dedicated tests:
- openclaw_bundle.py internals (_build_agents_md, _build_openclaw_md)
- discovery_merge.py (1024 lines — covered by 3 integration tests)
- refine_engine.py (195 lines)
```

---

## Current Handoff Snapshot (2026-03-19)

### Everything completed in the latest Codex pass

1. Reviewed project quality and identified concrete product issues:
   - `prompt_choice()` crashed on invalid input.
   - `_detect_commands()` broke its own return contract.
   - `prepare` overwrote detected `.openclaw/commands.json`.
   - tracked `__pycache__/` / `.pyc` polluted git.
   - generated Next scaffold had broken lint setup and fake tests.
   - documented YAML playbook input for `--spec` did not work.

2. Fixed the onboarding / prepare flow:
   - `initializer/flow/new_project.py`
   - `initializer/flow/prepare_project.py`
   - `tests/unit/test_new_project_inputs.py`
   - `tests/unit/test_prepare_project.py`

3. Cleaned git hygiene:
   - `.gitignore` updated to ignore `.pytest_cache/`
   - tracked bytecode artifacts removed from git index

4. Ran a real generated-project validation on a `taskflow` app and found a real scaffold bug:
   - `npm run lint` failed because generated `eslint.config.mjs` depended on a missing package.
   - `npm test` was only a placeholder.
   - Next auto-rewrote `tsconfig.json` on first tooling run.

5. Fixed the generated Next.js scaffold:
   - `initializer/renderers/scaffold_engine.py`
   - `tests/unit/test_scaffold_engine.py`
   - lint now uses `eslint .`
   - `eslint.config.mjs` now uses `FlatCompat` from `@eslint/eslintrc`
   - scaffold now ships `next-env.d.ts`
   - scaffold now ships `tsconfig.test.json`
   - scaffold now ships a real smoke test
   - migration template no longer emits lint noise

6. Ran a second real generated-project validation:
   - generated `taskflow` project passed:
     - `npm test`
     - `npm run lint`
     - `npm run build`

7. Tried the documented editorial YAML playbook flow and found another real product bug:
   - `initializer new --spec examples/next-payload-postgres.input.yaml`
   - failed because `load_project_spec()` only accepted JSON.

8. Fixed YAML / YML support for `initializer new --spec`:
   - `initializer/flow/new_project.py`
   - new coverage in `tests/unit/test_spec_loader.py`
   - supports `.json`, `.yaml`, `.yml`
   - if `--spec` points to a directory, resolves `spec.json`, `spec.yaml`, or `spec.yml`
   - normalizes playbook-style YAML (`playbook_id`, `guided_answers`, `critical_confirmations`) into the internal `answers` contract
   - uses playbook detection hints to preserve archetype inference

9. Verified the YAML fix with:
   - focused pytest run: `7 passed`
   - smoke run: `.venv/bin/python -m initializer new --spec <yaml>` succeeded and generated a project

10. Updated this `analysis.md` with the fixes, validations, and handoff notes.

### Current working tree (updated after Session 6)

At the time of this handoff, `git status --short` shows:

```text
 M analysis.md
 M initializer/capabilities/cms.py
 M initializer/capabilities/public_site.py
 M initializer/engine/story_engine.py
 ?? tests/unit/test_cms_capability.py
 ?? tests/unit/test_public_site_capability.py
```

All 6 story quality issues from Session 5 have been fixed at the **generator level**. Tests: 311/311 passed. Changes are unstaged — need commit + regenerate editorial-control-center + re-validate.

### Most relevant validations already run

```text
311 passed (full pytest suite — 20 new tests added in Session 6)
39 passed in the 3 files directly testing the 6 fixes
```

### What still remains valuable to do next

1. **Commit Session 6 changes** — all 6 generator fixes + 20 new tests.

2. **Regenerate editorial-control-center** — `initializer new --spec examples/next-payload-postgres.input.yaml --output output/editorial-control-center --force` and then `initializer prepare output/editorial-control-center`.

3. **Re-validate** — npm install/test/lint/build on the regenerated project. Verify the new stories appear (public site rendering, enriched content model, etc.).

4. **Run `ralph.sh`** (not `--dry-run`) to execute all stories with Codex.

5. Consider pinning Payload version range in `_payload_package_json()` to avoid future API drift.

### Prompt for Codex

Use this prompt verbatim in Codex:

```text
You are continuing work on the Specwright repository.

Read analysis.md — focus on "Session 6" and "Current Handoff Snapshot".

Context:
- Branch: fix/ralph-evidence
- Last commit: 8c944f7. Session 6 changes are unstaged.
- 311 tests pass. All 6 story quality issues from Session 5 are fixed at generator level.

Session 6 completed (all generator-level fixes):
1. CMS capability (cms.py): enumerates collections/globals from spec.guided_answers.content_model in acceptance criteria and expected_files
2. Role normalization (story_engine.py): _get_role_names() pulls roles from spec.answers.guided_answers.roles_and_access.admin_roles; used in feature.roles and feature.draft-publish
3. Media library (story_engine.py): _get_storage_backend() reads spec storage_requirements; local_filesystem → "use Payload local disk adapter", else → S3
4. Scheduled publishing (story_engine.py): acceptance criteria now specify node-cron, cron interval, idempotency, logging; scope says no Bull/BullMQ
5. CDN → static delivery (public_site.py): renamed to "Configure static asset delivery" with story_key "infra.static-delivery"; criteria: Next.js Image, cache headers, no external CDN
6. Public site rendering (story_engine.py): new story "product.public-site-rendering" when cms + public-site capabilities; enumerates routes from content_model collections (excludes media/authors); depends on draft-publish

New test files:
- tests/unit/test_cms_capability.py (6 tests)
- tests/unit/test_public_site_capability.py (5 tests)
- tests/unit/test_story_engine.py (9 new tests appended)

Your tasks:
1. Stage and commit all Session 6 changes (cms.py, public_site.py, story_engine.py, test files, analysis.md)
2. Regenerate editorial-control-center: `python -m initializer new --spec examples/next-payload-postgres.input.yaml --output output/editorial-control-center --force`
3. Run `python -m initializer prepare output/editorial-control-center`
4. Validate: cd into the generated project and run npm install, npm test, npm run lint, npm run build
5. Verify the new stories appear in the generated spec.json (search for "public-site-rendering", "static-delivery", collection names in content model story)
6. If validation passes, update analysis.md with Session 6 validation results

Do not restart from scratch. Build directly on the current state.
```
