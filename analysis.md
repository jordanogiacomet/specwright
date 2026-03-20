# Specwright — Full Repository Analysis

**Date**: 2026-03-18 (updated 2026-03-20)
**Test suite**: 426/426 passed
**Generated projects inspected**: `output/todo-app`, `output/todo-app-design`, `output/taskflow` (node-api), `output/newshub-cms` (Payload), `output/dentaldesk` (--assist flow), `output/editorial-control-center` (Payload editorial)

### Handoff For Future Agents

If context was compacted or you are resuming this work later, read this file first before touching the codebase. It is the current source of truth for what was fixed, what is still in flight, and which validations already ran.
When the main agent makes code changes, record the new state here before moving on so the next pass can resume from this file instead of reconstructing context from scratch.

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
| BUG-015 | FIXED | Payload CLI on Node 24 hung on default `tsx` path for `migrate*` / `generate:types`; generator now uses `payload --disable-transpile` via npm scripts |
| BUG-016 | FIXED | Payload scaffold claimed migrations live in `src/lib/migrations/` but `postgresAdapter` did not set `migrationDir`, so CLI wrote to `src/migrations/` |
| BUG-017 | FIXED | Playbook/editorial workflow booleans (`draft_publish`, `preview`, `scheduled_publishing`) now remove disabled features before story generation |
| QUALITY-002 | FIXED | CMS/editorial stories now have explicit content-model ownership, tighter dependencies, concrete preview/public/scheduler contracts, and less ambiguous storage/role language |
| IMP-012 | FIXED | i18n capability stories now have stable `story_key`s and CMS i18n no longer overlaps with the generic `feature.i18n-setup` story |
| BUG-018 | FIXED | Generated Vitest config now forces automatic JSX runtime so Next App Router TSX smoke tests do not fail with `React is not defined` |
| BUG-019 | FIXED | `ralph.sh` now writes Codex prompts with literal-safe blocks instead of unquoted heredocs / command substitutions that could execute story markdown backticks in the shell |
| BUG-020 | FIXED | Payload scaffold now routes `db:migrate*` through a helper that normalizes generated migration imports so `MigrateUpArgs` / `MigrateDownArgs` are emitted as `type` imports before Payload loads them under ESM |
| BUG-021 | FIXED | Payload scaffold now generates `src/__tests__/setup-env.ts` and wires Vitest `setupFiles` so `.env.local` loads before importing `payload.config`, without weakening runtime `DATABASE_URI` requirements |
| BUG-022 | FIXED | Payload scaffold now uses a migration wrapper plus `ralph.sh` sentinel handling so the post-story safety-net migrate step stays non-interactive and skips safely on dev-push markers or when no migrations are pending |
| BUG-023 | FIXED | `_build_execution_plan()` now uses true topological sort instead of phase-first ordering — cross-phase dependencies (e.g. feature→product) are respected |
| IMP-013 | FIXED | `CODEX_EFFORT` env var backported to generator — ralph.sh now uses `${CODEX_EFFORT:-medium}` instead of hardcoded `xhigh` |
| SEC-001 | FIXED | `PAYLOAD_SECRET` fallback `"PLEASE-CHANGE-ME"` replaced with runtime throw on missing env var |
| SEC-002 | ADDED | AGENTS.md now includes Security requirements section (password policy minLength:8, rate limiting, no hardcoded secrets) |
| SEC-003 | ADDED | AGENTS.md now includes TypeScript conventions section (no .js/.jsx alongside .ts files) |
| SEC-004 | FIXED | `JWT_SECRET` removed from Payload `.env.example` (Payload uses `PAYLOAD_SECRET`, JWT_SECRET was unused) |
| TESTS-002 | ADDED | 20 new tests for `refine_engine.py` (was 0 tests for 196 lines) |
| TESTS-003 | ADDED | 24 new tests for `discovery_merge.py` (was 3 tests for 1023 lines) |
| TESTS-004 | ADDED | 7 new tests for `openclaw_bundle.py` internals (OPENCLAW.md, repo-contract, manifest, edge cases) |
| TESTS-005 | ADDED | 5 new tests for codex_bundle + scaffold_engine (CODEX_EFFORT, PAYLOAD_SECRET, security, TypeScript, JWT_SECRET) |
| SEC-005 | ADDED | ST-902 (rate limiting) auto-generated when authentication feature is present — closes gap between AGENTS.md guidance and story ACs |
| SEC-006 | ADDED | ST-903 (password policy) auto-generated when authentication feature is present — enforces minLength:8 at story level |
| SPLIT-001 | ADDED | Story-splitting heuristic: stories with >9 ACs or >8 expected files are auto-split into balanced parts with chained dependencies |
| TESTS-006 | ADDED | 24 new tests for ST-902, ST-903, and story-splitting heuristic (refine_engine) |

---

## Session 15 — Security Stories + Story-Splitting Heuristic (Completed, 2026-03-20)

### What was done

1. **Added ST-902 (rate limiting) story (SEC-005)**
   - `initializer/ai/refine_engine.py` — new `_build_rate_limiting_story(spec)`
   - Guard: only generated when `"authentication"` is in `spec["features"]`
   - story_key: `security.rate-limiting`, depends_on: `["feature.authentication"]`
   - Stack-aware: Payload-specific endpoints (`/api/users/login`, `/api/users/create`), Next.js middleware
   - ACs: 429 on threshold breach, sliding window/token bucket, rate limit headers

2. **Added ST-903 (password policy) story (SEC-006)**
   - `initializer/ai/refine_engine.py` — new `_build_password_policy_story(spec)`
   - Guard: only generated when `"authentication"` is in `spec["features"]`
   - story_key: `security.password-policy`, depends_on: `["feature.authentication"]`
   - ACs: server rejects <8 char passwords with 400, client validates before submit, shared validation utility

3. **Added story-splitting heuristic (SPLIT-001)**
   - `initializer/ai/refine_engine.py` — new `_split_complex_stories(spec)` and `_split_story(story)`
   - Thresholds: `MAX_AC_COUNT=9`, `MAX_EXPECTED_FILES=8`, `MIN_AC_PER_PART=4`
   - Part 1 keeps original `id` and `story_key` (preserves downstream dependency resolution)
   - Parts 2+ get suffixed IDs (`{id}b`, `{id}c`) and chained `depends_on`
   - Called from `refine_spec()` after `refine_stories()`

4. **Tuned splitting thresholds**
   - Initial threshold (MAX_AC=7) over-split ST-008 (RBAC, 8 ACs) and ST-009 (media, 9 ACs)
   - Raised to MAX_AC=9 and added MIN_AC_PER_PART=4 floor
   - Result: ST-008 and ST-009 no longer split; ST-001 reduced from 3 parts to 2; ST-012 (the 178-min story) still splits

5. **Added 24 new tests (TESTS-006)**
   - 7 for ST-902 (guard, story_key, depends_on, Payload-specific, Next.js-specific, deduplication)
   - 6 for ST-903 (guard, story_key, depends_on, minLength criteria, deduplication)
   - 9 for splitting (threshold, triggers, part1 key preservation, chaining, scope, titles, high-files-low-ACs skip)
   - 2 for full pipeline (security stories, splitting)

### Files changed

- `initializer/ai/refine_engine.py` — ST-902, ST-903 builders, `_split_complex_stories()`, `_split_story()`, updated `refine_stories()` and `refine_spec()`
- `tests/unit/test_refine_engine.py` — 24 new tests

### Validation performed

1. **Full test suite**: `426 passed in 7.82s` (was 402)
2. **Full regeneration**: `initializer new + prepare` produces 19 stories (14 original + 2 security + 3 from splitting)
3. **Execution plan verified**: ST-902/ST-903 appear after ST-007 (auth); split parts chain correctly
4. **Generated project gates**: `npm install` OK, `npm test` 3/3 passed, `npm run lint` 0 errors, `npm run build` compiled successfully
5. **Splitting tuning verified**: ST-008 (8 ACs) and ST-009 (9 ACs) no longer over-split

### Splitting results on editorial project

| Story | Pre-split ACs | Split? | Parts | Rationale |
|-------|---:|---|---:|---|
| ST-001 (CMS content model) | 18 | Yes | 2 | 18 ACs — justified |
| ST-003 (Init repo) | 10 | Yes | 2 | 10 ACs, 9 files — justified |
| ST-008 (RBAC) | 8 | No | 1 | Below threshold (≤9) |
| ST-009 (Media library) | 9 | No | 1 | At threshold (≤9) |
| ST-012 (Public site) | 10 | Yes | 2 | The 178-min story — justified |

### Remaining work for next session

1. **Live ralph loop re-run** — Regenerated project has 19 stories with splitting + security stories; run the loop to validate split stories and ST-902/ST-903 produce correct code via Codex
2. **Push to remote** — HTTPS auth not configured; needs `gh auth login` or SSH remote
3. **SaaS roadmap** — API layer extraction, multi-tenancy (deferred to later phase)

---

## Session 14 — Generator Hardening + Test Coverage Expansion (Completed, 2026-03-20)

### What was done

1. **Backported CODEX_EFFORT env var to generator (IMP-013)**
   - `initializer/renderers/codex_bundle.py`
   - ralph.sh template now emits `CODEX_EFFORT="${CODEX_EFFORT:-medium}"` alongside existing `CODEX_MODEL`
   - Both `run_codex()` and `run_codex_retry()` use `$CODEX_EFFORT` instead of hardcoded `"xhigh"`
   - Users can now control reasoning effort via env var: `CODEX_EFFORT=xhigh ./ralph.sh`

2. **Fixed PAYLOAD_SECRET security fallback (SEC-001)**
   - `initializer/renderers/scaffold_engine.py`
   - Replaced `process.env.PAYLOAD_SECRET || "PLEASE-CHANGE-ME"` with runtime throw
   - Generated `payload.config.ts` now crashes immediately if `PAYLOAD_SECRET` is not set, instead of running with a known secret

3. **Added security guidance to generated AGENTS.md (SEC-002)**
   - `initializer/renderers/codex_bundle.py` (`_build_agents_md()`)
   - New `## Security requirements` section instructs Codex to:
     - Never hardcode secrets or use fallback values
     - Enforce `minLength: 8` on password fields (client + server)
     - Add rate limiting to auth endpoints
     - Import and use all env vars defined in `.env.example`

4. **Added TypeScript conventions to generated AGENTS.md (SEC-003)**
   - `initializer/renderers/codex_bundle.py` (`_build_agents_md()`)
   - New `## TypeScript conventions` section instructs Codex to:
     - Use `.ts`/`.tsx` exclusively — no `.js`/`.jsx` alongside
     - Never create `.js` re-exports or duplicates of `.ts` modules
   - Addresses the Users.ts/Users.js dual-file fragility from Session 13

5. **Removed unused JWT_SECRET from Payload .env.example (SEC-004)**
   - `initializer/renderers/scaffold_engine.py` (`_env_example()`)
   - Payload projects use `PAYLOAD_SECRET` for auth; `JWT_SECRET` was generated but never imported
   - `JWT_SECRET` now only emitted for `node-api` backend projects

6. **Added 56 new tests across 4 files**
   - `tests/unit/test_refine_engine.py` — **new file**, 20 tests covering `refine_prd`, `refine_stories`, `refine_spec`, ST-900/ST-901 generation, idempotency, stack-specific criteria, deduplication
   - `tests/unit/test_discovery_merge.py` — 24 new tests covering decision signal merging, capability signal application, summary conflict detection, capability canonicalization, feature deduplication, immutable answer preservation, edge cases
   - `tests/unit/test_bundles.py` — 10 new tests for CODEX_EFFORT, security requirements, TypeScript conventions, OPENCLAW.md content, repo-contract, manifest details, edge cases
   - `tests/unit/test_scaffold_engine.py` — 2 new tests for PAYLOAD_SECRET rejection and JWT_SECRET omission in Payload projects

### Files changed

- `initializer/renderers/codex_bundle.py` — CODEX_EFFORT backport, security guidance, TypeScript conventions
- `initializer/renderers/scaffold_engine.py` — PAYLOAD_SECRET throw, JWT_SECRET conditional
- `output/editorial-e2e-test/.codex/AGENTS.md` — regenerated with new sections
- `output/editorial-e2e-test/.env.example` — JWT_SECRET removed
- `output/editorial-e2e-test/ralph.sh` — CODEX_EFFORT variable
- `output/editorial-e2e-test/src/payload.config.ts` — PAYLOAD_SECRET throw
- `tests/unit/test_bundles.py` — 10 new tests
- `tests/unit/test_discovery_merge.py` — 24 new tests
- `tests/unit/test_refine_engine.py` — new file, 20 tests
- `tests/unit/test_scaffold_engine.py` — 2 new tests

### Validation performed

1. **Full test suite**: `402 passed in 4.42s` (was 346)
2. **Focused regression**: All new tests pass individually
3. **Branch alignment**: fix/ralph-evidence merged into master (fast-forward)

### Remaining work for next session

1. **Full editorial regeneration validation** — Run `initializer new --spec examples/next-payload-postgres.input.yaml` + `prepare` + `npm build` to verify new security/TypeScript guidance flows through to generated project
2. **Story-splitting heuristic** — ST-012 took 178min in Session 13; design auto-split for complex stories
3. **Rate limiting story** — AGENTS.md now instructs rate limiting, but no story AC explicitly creates the middleware
4. **Password enforcement story** — AGENTS.md says minLength:8, but no story AC enforces it
5. **Push to remote** — HTTPS auth not configured; needs `gh auth login` or SSH remote
6. **SaaS roadmap** — API layer extraction, multi-tenancy (deferred to later phase)

---

## Session 13 — Ralph Loop Completion + Generator Bug Fix (Completed, 2026-03-20)

### What was done

1. **Resumed ralph loop from ST-007** (process had died between sessions)
   - ST-007 (authentication) code was already complete and verified (build OK, 8/8 tests pass)
   - Manually marked ST-007 as DONE in progress.txt after validation
   - Restarted ralph loop with `CODEX_EFFORT=xhigh ./ralph.sh --from ST-008`

2. **Discovered and fixed BUG-023: Execution plan topological sort**
   - **Root cause**: `_build_execution_plan()` in `openclaw_bundle.py` sorted stories by phase first, then by dependency depth within each phase. This caused cross-phase dependency violations — e.g., `ST-009` (feature.media-library, phase=features, order 8) depended on `ST-001` (product.cms-content-model, phase=product, order 11).
   - **Fix**: Replaced phase-first ordering with a true topological sort that uses dependency satisfaction to drive execution order. Phase annotations are preserved for display but don't control ordering. Within each "available" batch, ties are broken by phase priority then story ID for determinism.
   - **Files changed**: `initializer/renderers/openclaw_bundle.py` (new `_classify_phase()` + `_PHASE_PRIORITY` + rewritten `_build_execution_plan()`), `tests/unit/test_bundles.py` (updated phase test + 2 new dependency tests)
   - **Test suite**: 346/346 passed (+2 new tests)
   - **Impact**: Without this fix, ST-009, ST-010, ST-011 would have run before their dependency ST-001, likely causing failures or duplicated work.

3. **Fixed execution plan in generated project**
   - Reordered `.openclaw/execution-plan.json` manually to put ST-001 before ST-009/ST-010
   - Ralph loop correctly picked up the new order

4. **Ralph loop completed all 14/14 stories**

### Ralph loop execution summary

| Story | Duration | Status | Retries | Notes |
|-------|----------|--------|---------|-------|
| ST-003 | ~12 min | DONE | 0 | Init repo |
| ST-004 | ~62 min | DONE | 2 | Database (retries on setup) |
| ST-005 | ~12 min | DONE | 0 | Backend service |
| ST-006 | ~7 min | DONE | 0 | Frontend (fastest) |
| ST-002 | ~10 min | DONE | 0 | Static asset delivery |
| ST-007 | ~28 min | DONE | 0 | Authentication (manually verified) |
| ST-008 | ~16 min | DONE | 0 | RBAC |
| ST-001 | ~18 min | DONE | 0 | CMS content model (4 collections + 2 globals) |
| ST-009 | ~13 min | DONE | 0 | Media library |
| ST-010 | ~20 min | DONE | 1 | Draft/publish (typecheck fix on retry) |
| ST-012 | ~178 min | DONE | 0 | Public site pages (longest — complex SSR) |
| ST-011 | ~10 min | DONE | 0 | Content preview |
| ST-900 | ~19 min | DONE | 0 | Monitoring/logging |
| ST-901 | ~17 min | DONE | 0 | Backups |

**Total runtime**: ~7 hours | **Stories**: 14/14 | **Retries**: 3 total (ST-004×2, ST-010×1) | **Failures**: 0

### Step 4 verification (all gates passed)

- `npm test` → 29/29 passed (5 test files: smoke, auth, content-status, media, preview)
- `npm run lint` → 0 errors, 0 warnings
- `npm run build` → compiled successfully
- Routes verified: `/pages/[slug]`, `/posts/[slug]`, `/api/preview`, `/api/exit-preview`, `/api/health`, `/admin`, `/login`, `/dashboard`

### Benchmark findings

**Code quality (by story)**:

- **ST-007 (auth)**: Well-structured auth helpers with Payload cookie management, proper error mapping, first-user bootstrap pattern. Login page is a polished UI. `serializeAuthUser` strips sensitive fields. Score: 8/10
- **ST-008 (RBAC)**: Excellent permissions module — composable `createRoleAccess()` factory, typed role constants with `as const satisfies`, first-user auto-admin hook. Register endpoint properly gates user creation. Score: 9/10
- **ST-001 (content model)**: Clean collection/global definitions matching story spec exactly. Media uses virtual fields for Payload-internal data. Score: 9/10
- **ST-010 (draft/publish)**: Required 1 retry due to typecheck error in test file (unsafe casts to `AccessArgs`). Fixed on retry by casting through `unknown`. Score: 7/10
- **ST-012 (public site)**: Took 178 minutes (longest story). Created public layout, homepage, pages/[slug], posts/[slug] with SSR/ISR. Score: 7/10 (long duration is concerning)
- **ST-900 (monitoring)**: Added structured JSON logger, request logging middleware (`withRequestLogging`), updated health endpoint. Score: 8/10

**Fragilities identified**:

1. **Users.ts/Users.js dual-file pattern**: Codex created both files, flip-flopping which is source vs re-export across stories. Works but fragile for module resolution.
2. **Hardcoded fallback secret**: `PAYLOAD_SECRET || "PLEASE-CHANGE-ME"` — complete auth bypass if env missing.
3. **No auth migration for ST-007**: Story explicitly requested `db:migrate:create` but Codex relied on Payload auto-schema.
4. **Weak password policy**: Client `minLength={3}`, no server enforcement.
5. **No rate limiting**: Auth endpoints unprotected against brute force.
6. **JWT_SECRET unused**: Defined in env but never imported.

**Positive signals**:

1. All acceptance criteria functionally met across all 14 stories
2. 29 real test assertions (not stubs) covering auth, RBAC, content status, media, preview
3. Proper Next.js App Router patterns throughout (route groups, dynamic routes, SSR)
4. Clean Payload CMS integration with access control, upload config, globals
5. Migrations generated correctly for schema changes (RBAC, content model, draft/publish)
6. Self-healing on ST-010 retry (fixed its own typecheck error)

### Generator test suite

`pytest -q` → 346/346 passed (was 344, +2 new dependency ordering tests)

---

## Session 12 — Full Regeneration + Live Ralph Loop (Completed, 2026-03-20)

### What was done

1. **Baseline confirmed**: `pytest -q` → 344/344 passed (pytest had to be reinstalled in venv)

2. **Full project regeneration from scratch**
   - `rm -rf output/editorial-control-center`
   - `.venv/bin/python -m initializer new --spec examples/next-payload-postgres.input.yaml` → PASS
   - `.venv/bin/python -m initializer prepare output/editorial-control-center` → PASS (14 stories, 4 phases)

3. **Scaffold validation (all 4 gates passed)**
   - `npm install` → 694 packages
   - `npm test` → 3/3 smoke tests passed (Vitest)
   - `npm run lint` → 0 errors, 0 warnings
   - `npm run build` → compiled successfully (`/`, `/_not-found`, `/admin/[[...segments]]`)

4. **Ralph loop started from ST-003 with `xhigh` reasoning effort**
   - `ralph.sh` was modified to accept `CODEX_EFFORT` env var (default `medium`, overridden to `xhigh`)
   - Both `run_codex()` and `run_codex_retry()` now use `${CODEX_EFFORT:-medium}` instead of hardcoded `xhigh`
   - Note: this change is in the generated project only, not backported to the generator yet

5. **Environment constraints**
   - No Docker available → database-dependent operations (migrations) downgrade to WARN per Session 11 fixes
   - Codex CLI v0.115.0 installed, logged in via `codex login`
   - No `OPENAI_API_KEY` env var (uses account login instead)

### Ralph loop progress (as of handoff)

| Story | Status | Duration | Notes |
|-------|--------|----------|-------|
| ST-003 | DONE | ~12 min | Initialize project repository |
| ST-004 | DONE | ~15 min | Setup database |
| ST-005 | DONE | ~12 min | Setup backend service |
| ST-006 | DONE | ~7 min | Create frontend application |
| ST-002 | DONE | ~10 min | Configure static asset delivery |
| ST-007 | RUNNING | — | Implement authentication |
| ST-008 | PENDING | — | Implement RBAC |
| ST-009 | PENDING | — | Implement media library |
| ST-010 | PENDING | — | Implement draft/publish workflow |
| ST-011 | PENDING | — | Implement content preview |
| ST-001 | PENDING | — | Define CMS content model |
| ST-012 | PENDING | — | Implement public site pages |
| ST-900 | PENDING | — | Setup monitoring and logging |
| ST-901 | PENDING | — | Implement backups |

**14/14 stories completed — see Session 13 for full completion details.**

### Code quality analysis (ST-003 through ST-006)

Detailed review of all code generated by Codex for the first 4 completed stories:

**ST-003 (Initialize project repository)**: 11/11 acceptance criteria met
- All expected files present: package.json, tsconfig.json, eslint.config.mjs, vitest.config.ts, .env.example, .env.local, .prettierrc.json
- Smoke test has 3 real assertions (not a no-op)
- No files created in `src/pages/` (correctly uses App Router)
- Environment variable names match `.env.example` exactly

**ST-004 (Setup database)**: 6/6 acceptance criteria met
- `src/lib/db.ts`: Pool config with sensible defaults (max 10, 30s idle, 10s connect timeout)
- `verifyDatabaseConnection()` exported for health checks
- Initial migration creates Payload infrastructure tables (not application tables — correct)
- Migration directory correctly at `src/lib/migrations/`
- docker-compose.yml: Postgres 16-alpine with health check

**ST-005 (Setup backend service)**: 5/5 acceptance criteria met
- `src/payload.config.ts`: Properly configured with `createPayloadDatabaseAdapter()`
- `/api/health` endpoint with database verification
- Admin panel at `/admin` via `(payload)` route group
- Payload REST API catch-all at `/api/[[...slug]]`
- Environment variables correctly referenced

**ST-006 (Create frontend application)**: 4/4 acceptance criteria met
- Root layout at `src/app/layout.tsx`
- Public route group `(app)` with Home page
- `src/components/Layout.tsx` with responsive sidebar + navigation placeholders
- No `src/pages/` directory created
- Bonus: `PublicImage.tsx` utility component

**Cross-story verification**: All dependency chains satisfied. File organization follows AGENTS.md structure. No bugs or misalignments detected.

### Warnings (non-blocking)

1. `.env.local` has placeholder secrets (PAYLOAD_SECRET, JWT_SECRET) — expected for dev
2. `src/collections/` contains only `.gitkeep` — correct, domain collections come in later stories
3. Payload auto-generated files in `(payload)` route group marked as "DO NOT MODIFY" — correct
4. No Docker in this environment, so migration commands will fail/warn during ralph loop validation

### ralph.sh modification (generated project only)

Changed both `run_codex()` and `run_codex_retry()` from:
```bash
--config 'model_reasoning_effort="xhigh"'
```
To:
```bash
--config "model_reasoning_effort=\"${CODEX_EFFORT:-medium}\""
```

This allows controlling reasoning effort via env var. The loop is running with `CODEX_EFFORT=xhigh`.

### Backport needed

The `CODEX_EFFORT` env var pattern should be backported to `initializer/renderers/codex_bundle.py` so future generated projects get this flexibility by default.

---

## Session 11 — Payload Migration / Env Backport For Editorial Loop (Completed, 2026-03-19)

### What was fixed

1. **Payload migration scripts now route through a generated helper (BUG-020, BUG-022)**
   - `initializer/renderers/scaffold_engine.py`
   - Payload projects no longer scaffold raw `payload --disable-transpile migrate*` scripts directly for `db:migrate`, `db:migrate:create`, and `db:migrate:status`.
   - The scaffold now generates `scripts/payload-migrations.mjs` and points the three public npm scripts at it, preserving the external command contract (`npm run db:migrate*`).
   - The helper:
     - loads `.env.local` before invoking Payload;
     - rewrites generated `src/lib/migrations/*.ts` imports so `MigrateUpArgs` / `MigrateDownArgs` are always emitted as `type` imports;
     - checks pending migration files against `payload_migrations`;
     - emits explicit sentinels for `no-pending` and `dev-push` instead of letting `payload migrate` block on a confirmation prompt after dev-mode schema pushes.
   - Added direct `pg` dependency to the Payload scaffold because the generated helper queries `payload_migrations` safely through a Postgres client.

2. **Payload Vitest bootstrap now loads env before `payload.config` (BUG-021)**
   - `initializer/renderers/scaffold_engine.py`
   - `_vitest_config(...)` is now stack-aware and adds `setupFiles: ["./src/__tests__/setup-env.ts"]` only for Payload backends.
   - Payload scaffolds now generate `src/__tests__/setup-env.ts`, which loads `.env.local` via `process.loadEnvFile(...)` when present.
   - Runtime validation remains strict: `src/lib/db.ts` / `payload.config.ts` still rely on `DATABASE_URI` being present at execution time; the change only ensures test bootstrap order is correct.

3. **`ralph.sh` now interprets Payload migration sentinels**
   - `initializer/renderers/codex_bundle.py`
   - `run_migrations()` still behaves generically for non-Payload stacks.
   - For Payload projects, it now inspects wrapper output and reports:
     - `Migrations: SKIP` when no Payload migrations are pending;
     - `Migrations: WARN` when a dev-mode push marker (`batch = -1`) is present and the safety-net migrate step is skipped deliberately;
     - `Migrations: OK` for real successful runs.
   - This keeps Ralph non-interactive for the editorial/CMS flow without changing the commands shown to the agent in `AGENTS.md`.

4. **Regression coverage was expanded**
   - `tests/unit/test_scaffold_engine.py`
   - Updated Payload script assertions to the new wrapper contract.
   - Added coverage for:
     - Payload-only `setupFiles`;
     - generated `src/__tests__/setup-env.ts`;
     - generated `scripts/payload-migrations.mjs`;
     - helper logic strings for env loading, type-import normalization, and sentinel handling.
   - `tests/unit/test_bundles.py`
   - Added coverage that generated `ralph.sh` recognizes the new Payload sentinels and surfaces `SKIP` / `WARN` correctly.

### Validation performed

1. **Focused scaffold + bundle regression**
   - `.venv/bin/python -m pytest tests/unit/test_scaffold_engine.py tests/unit/test_bundles.py -q`
   - Result: `93 passed`

2. **Full repository suite**
   - `.venv/bin/python -m pytest -q`
   - Result: `344 passed in 5.60s`

3. **Static runtime evidence check**
   - Re-read the already-generated `output/editorial-control-center` hotfix evidence used during the live loop:
     - `src/__tests__/setup-env.ts` already matched the env-bootstrap approach now backported to the scaffold;
     - `src/lib/migrations/20260319_194516.ts` already showed the `type`-import form that the new helper now enforces automatically.
   - No new regeneration of `output/editorial-control-center` was performed in this pass; the fix was implemented in the generator origin and validated via unit coverage.

### Remaining risk

- The generated Payload migration helper currently assumes Postgres-backed Payload projects and checks `public.payload_migrations`; that matches the editorial scaffold and current generator contract, but a future non-public-schema Payload/Postgres variant would need a schema-aware preflight.
- Existing already-generated projects do not receive the new wrapper or Vitest bootstrap automatically; they need regeneration or manual patching to pick up these fixes.

## Session 6 — Pipeline Reliability Contract (Completed, 2026-03-19)

### What has already been implemented

1. **Shared validation contract**
   - Added `initializer/engine/validation_contract.py` as the single source of truth for ecosystem detection, command derivation, runner detection, and validation policy.
   - The contract now carries `commands`, `setup`, `notes`, and a stable `validation` block with `ecosystem`, `test_runner`, `requires_real_tests`, `block_on`, and `warn_on`.

2. **prepare now reconstructs the real contract**
   - `initializer/flow/prepare_project.py` now detects the project's actual command/validation state from files on disk instead of re-deriving a partial commands map.
   - The generated `.openclaw/commands.json` is meant to remain consistent after `prepare`.

3. **OpenClaw bundle now uses the shared contract**
   - `initializer/renderers/openclaw_bundle.py` and `initializer/engine/commands_engine.py` now route through the same contract helper instead of maintaining parallel command logic.
   - `.openclaw/commands.json` now includes a `validation` block, not just plain commands.

4. **Node scaffold moved to Vitest**
   - `initializer/renderers/scaffold_engine.py` now generates `vitest run` as the test script, adds `vitest` to devDependencies, writes `vitest.config.ts`, and emits `src/__tests__/smoke.test.ts`.
   - The scaffold is no longer centered on `tsx --test`/`tsconfig.test.json` as the default testing path.

5. **ralph.sh now reads the validation contract from commands.json**
   - `initializer/renderers/codex_bundle.py` now loads `test`, `lint`, `build`, `typecheck`, `test_runner`, and `requires_real_tests` from `.openclaw/commands.json` at runtime instead of hardcoded Node validation commands.
   - Validation now respects `validation.block_on` / `validation.warn_on`, and a missing or placeholder test runner fails when `requires_real_tests=true`.

6. **Story engine bootstrap wording is stack-aware**
   - `initializer/engine/story_engine.py` now uses the shared validation contract to derive bootstrap runner expectations and validation commands.
   - The bootstrap repository story now uses Vitest-specific wording for Node and generic runner-aware wording for Python and Go.

7. **Unit coverage was updated for the new contract**
   - `tests/unit/test_scaffold_engine.py` now validates the Vitest scaffold (`vitest.config.ts`, `vitest run`, `smoke.test.ts`) and confirms the legacy `tsconfig.test.json` path is gone.
   - `tests/unit/test_prepare_project.py` now validates the full `{commands, setup, notes, validation}` contract, detects placeholder/no-op test scripts, and covers Python/Go detection plus `prepare -> ralph` alignment.
   - `tests/unit/test_bundles.py` now checks the `validation` block in `.openclaw/commands.json` and verifies that `ralph.sh` reads validation commands from `commands.json` instead of hardcoded `npm ... --if-present`.
   - `tests/unit/test_story_engine.py` now validates Node/Python/Go bootstrap wording.

### Validation performed

1. **Focused regression suite**
   - `.venv/bin/python -m pytest tests/unit/test_scaffold_engine.py tests/unit/test_prepare_project.py tests/unit/test_bundles.py tests/unit/test_story_engine.py -q`
   - Result: `121 passed`

2. **Full repository suite**
   - `.venv/bin/python -m pytest -q`
   - Result: `320 passed in 4.68s`

### Remaining limitation

This session closes the validation/test pipeline contract itself. The separate `payload migrate*` compatibility issue on Node 24 was handled in Session 7 below.

## Session 7 — Payload CLI Node 24 Compatibility + General Debug (Completed, 2026-03-19)

### What was fixed

1. **Payload CLI on Node 24 no longer uses the hanging transpile path**
   - Root cause: `payload` CLI under Node `v24.11.1` hung when invoked through its default `tsx`-based transpile path (`payload migrate*`, `payload generate:types`).
   - Reproduction:
     - `./node_modules/.bin/payload migrate:create specwright_test --forceAcceptWarning` → timed out after 20s
     - `./node_modules/.bin/payload --disable-transpile migrate:create specwright_test --forceAcceptWarning` → PASS
   - Fix:
     - `initializer/renderers/scaffold_engine.py` now generates Payload scripts:
       - `generate:types = "payload --disable-transpile generate:types"`
       - `db:migrate = "payload --disable-transpile migrate"`
       - `db:migrate:create = "payload --disable-transpile migrate:create"`
       - `db:migrate:status = "payload --disable-transpile migrate:status"`
     - `initializer/engine/validation_contract.py` now advertises Payload migrations as `npm run db:migrate`
     - `initializer/renderers/codex_bundle.py` now emits migration instructions via the same npm scripts

2. **Payload migration directory is now real, not just documented**
   - Root cause: AGENTS/stories/new-project output said Payload migrations must live in `src/lib/migrations/`, but the scaffolded `postgresAdapter` omitted `migrationDir`, so Payload created migrations under its default `src/migrations/`.
   - Fix:
     - `initializer/renderers/scaffold_engine.py` now sets `migrationDir: path.resolve(dirname, "lib/migrations")` in `src/payload.config.ts`
   - Result:
     - The documented migration path and the actual runtime behavior now match.

3. **Migration wording was normalized across the generator**
   - `initializer/engine/story_engine.py` now derives migration command wording from the stack instead of hardcoding `npm run db:migrate:create` for every backend.
   - `initializer/capabilities/cms.py` and `initializer/capabilities/i18n.py` now emit stack-aware migration acceptance criteria.

4. **Payload command contract is cleaner**
   - Removed the invalid `db_seed` Payload command from the shared validation contract.
   - `initializer/renderers/openclaw_bundle.py` dead-path command helpers were also updated to stop advertising stale `npx payload ...` commands.

### Validation performed

1. **Real runtime reproduction**
   - In `output/editorial-control-center` on Node `v24.11.1`:
     - `./node_modules/.bin/payload migrate:create specwright_test --forceAcceptWarning` → timed out after 20s
     - `./node_modules/.bin/payload --disable-transpile migrate:create specwright_test --forceAcceptWarning` → PASS

2. **Focused regression suite**
   - `.venv/bin/python -m pytest tests/unit/test_scaffold_engine.py tests/unit/test_prepare_project.py tests/unit/test_bundles.py tests/unit/test_story_engine.py -q`
   - Result: `122 passed`

3. **Full repository suite**
   - `.venv/bin/python -m pytest -q`
   - Result: `321 passed in 14.88s`

### General debug pass

- Ran a repo-wide grep for stale `TODO` / `FIXME` / `HACK` markers in `initializer/` and `tests/`.
- No new production bug surfaced beyond the Payload CLI + migrationDir inconsistencies fixed above.
- One remaining marker in `initializer/engine/story_engine.py` (`TODO-APP SPECIFIC STORIES`) is a roadmap note, not a runtime defect.

## Session 8 — Editorial Story Contract Tightening (Completed, 2026-03-19)

### What was fixed

1. **Disabled editorial workflows now truly disappear from the plan**
   - `initializer/flow/new_project.py`
   - Added feature-override normalization for structured playbook answers / critical confirmations.
   - `draft_publish: false`, `preview: false`, and `scheduled_publishing: false` now remove `draft-publish`, `preview`, and `scheduled-publishing` from `spec["features"]` before downstream artifact generation.
   - This closes a real story-ordering issue where `examples/next-payload-postgres.input.yaml` still produced scheduled-publishing despite explicitly disabling it.

2. **CMS content model story is now an actual dependency anchor**
   - `initializer/capabilities/cms.py`
   - Added stable `story_key = product.cms-content-model`.
   - The story now enumerates concrete fields for known editorial collections (`pages`, `posts`, `authors`, `media`), concrete fields for globals (`site-settings`, `homepage`), slug ownership for public surfaces, and explicit relationship notes (`posts -> authors/media`).
   - Expected files now include collection/global files and `src/payload.config.ts`, so later stories can depend on a real owner for schema work.
   - Architecture wording was tightened so local-first storage no longer claims a CDN by default.

3. **Public-site, RBAC, media, draft/publish, preview, and scheduler stories were de-ambiguous**
   - `initializer/engine/story_engine.py`
   - Editorial RBAC now uses the canonical `admin` / `editor` / `reviewer` fallback in CMS contexts and defines concrete responsibilities instead of generic "authorized roles".
   - `feature.media-library` now depends on `product.cms-content-model` in CMS projects and explicitly distinguishes schema ownership from upload/storage configuration.
   - `feature.draft-publish` now depends on the CMS content model, names explicit editorial states (`draft`, `in_review`, `published`), and aligns publishing authority to `reviewer/admin` instead of the older ambiguous role wording.
   - `feature.preview` now becomes a concrete preview contract for CMS/public-site projects (`/api/preview`, `/api/exit-preview`, draft-mode/public-loader reuse) and depends on the public rendering story.
   - `feature.scheduled-publishing` now only appears when enabled, requires draft/publish first, depends on the content model/public rendering in CMS projects, and names concrete job registration/env/logging/idempotency expectations.
   - `product.public-site-rendering` now depends on `product.cms-content-model`, names slug-based loaders, and makes homepage/global ownership explicit.

4. **Static delivery and i18n stories were tightened to avoid premature or overlapping work**
   - `initializer/capabilities/public_site.py`
     - Static-delivery no longer claims public routes already exist; it is now clearly infra-only and expects a reusable public image path instead.
   - `initializer/capabilities/i18n.py`
     - Added stable `story_key`s for CMS and non-CMS i18n stories.
     - CMS+i18n is now split into `feature.cms-localization` and `feature.locale-routing`, with explicit dependencies on content modeling/public rendering.
   - `initializer/engine/story_engine.py`
     - The generic `feature.i18n-setup` story is now only emitted for non-CMS i18n projects, preventing overlapping locale stories.

5. **Story coverage validation was taught the new canonical story keys**
   - `initializer/validation/story_coverage.py`
   - Coverage now recognizes `product.cms-content-model`, `product.public-site-rendering`, `infra.static-delivery`, and the new i18n story keys.

### Validation performed

1. **Focused story-generation regression suite**
   - `.venv/bin/python -m pytest tests/unit/test_story_engine.py tests/unit/test_cms_capability.py tests/unit/test_public_site_capability.py tests/unit/test_spec_loader.py tests/unit/test_i18n_capability.py -q`
   - Result: `60 passed`

2. **Full repository suite**
   - `.venv/bin/python -m pytest -q`
   - Result: `337 passed in 11.54s`

3. **Editorial playbook smoke validation (generator-level)**
   - Loaded `examples/next-payload-postgres.input.yaml`, applied capability handlers, and regenerated stories in-process.
   - Verified:
     - `product.cms-content-model` is present and owns the schema with explicit fields/relations/globals.
     - `feature.media-library`, `feature.draft-publish`, and `product.public-site-rendering` now depend on the content-model story.
     - `feature.preview` now depends on `product.public-site-rendering` and expects preview route handlers.
     - `feature.scheduled-publishing` is **absent** for this playbook because `scheduled_publishing: false`.
     - Final features for the playbook are now `authentication`, `roles`, `media-library`, `draft-publish`, `preview` (no premature scheduler story).

### Remaining limitation

- This session validated the generator/contracts thoroughly, but it did **not** rerun a fresh end-to-end `initializer new` + `prepare` + generated-project `npm build` / `ralph.sh` cycle after the new preview/public/scheduler wording changes.
- The new CMS preview contract assumes the generated implementation will use explicit preview route handlers plus draft/public loader reuse; that contract is unit-tested but not yet runtime-verified in a freshly generated project.

## Session 9 — Bootstrap Smoke Test Fix For Payload/Next Scaffold (Completed, 2026-03-19)

### What was fixed

1. **Vitest now compiles generated Next.js TSX with automatic JSX runtime**
   - `initializer/renderers/scaffold_engine.py`
   - Root cause: the generated smoke test imported `src/app/page.tsx` and rendered it through Vitest, but the generated `vitest.config.ts` did not force JSX automatic runtime for TSX imported from the Next App Router scaffold.
   - Resulting failure in real generated project:
     - `ReferenceError: React is not defined`
     - failure site: `src/app/page.tsx`
     - failing command: `npm test`
   - Fix:
     - generated `vitest.config.ts` now includes:
       - `esbuild.jsx = "automatic"`
       - `esbuild.jsxImportSource = "react"`

2. **Regression coverage updated**
   - `tests/unit/test_scaffold_engine.py`
   - Added assertions that the generated Vitest config includes the automatic JSX runtime settings.

3. **Real generated editorial project was patched and revalidated**
   - `output/editorial-control-center/vitest.config.ts`
   - Applied the same runtime setting in the already-generated project to confirm the failure disappeared without requiring full regeneration.

### Validation performed

1. **Focused scaffold regression**
   - `.venv/bin/python -m pytest tests/unit/test_scaffold_engine.py -q`
   - Result: `56 passed`

2. **Full repository suite**
   - `.venv/bin/python -m pytest -q`
   - Result: `337 passed in 5.80s`

3. **Real generated project validation (`output/editorial-control-center`)**
   - `npm test` — PASS
   - `npm run typecheck` — PASS
   - `npm run build` — PASS

### Remaining limitation

- The Next.js build still prints a lockfile-selection warning because the repo root also has a `package-lock.json`. This is noisy but not a blocker for the generated project or the `ralph` loop.

## Session 10 — Live Ralph Loop Findings On Editorial Control Center (In Progress, 2026-03-19)

### What was fixed

1. **Codex prompt generation in `ralph.sh` is now literal-safe**
   - `initializer/renderers/codex_bundle.py`
   - Root cause: `run_codex()` and `run_codex_retry()` built prompt files with unquoted heredocs and injected story markdown / retry errors inline. Story files such as `ST-004` contain backticks (for commands like `npm run db:migrate:create`), so bash could execute story markdown while constructing the prompt.
   - Real symptom during live loop:
     - `./ralph.sh --from ST-004` showed Payload / Node warnings before Codex produced any useful output
     - `.ralph-prompt.*.md` and `.codex-last-message.*.txt` from failed attempts were empty
     - `progress.txt` showed repeated `START` lines and a retry with `Codex execution failed`
   - Fix:
     - prompt files are now assembled with `printf`, literal quoted heredocs, and direct `cat "$STORIES_DIR/$story_id.md"` blocks
     - retry error text is inserted with `printf '```\\n%s\\n```\\n\\n' "$previous_error"` instead of being interpolated inside an unquoted heredoc

2. **Regression coverage added for prompt safety**
   - `tests/unit/test_bundles.py`
   - Added assertions that generated `ralph.sh` no longer uses the old `cat > "$prompt_file" <<PROMPT_EOF` pattern with inline `$(if [[ -f ... ]]` story interpolation, and that retry errors are written via `printf`.

3. **Generated project was patched so the live loop could continue**
   - `output/editorial-control-center/ralph.sh`
   - Applied the same literal-safe prompt fix to the already-generated project before resuming the live loop from `ST-004`.

### Validation performed

1. **Focused bundle regression**
   - `.venv/bin/python -m pytest tests/unit/test_bundles.py -q`
   - Result: `32 passed`

2. **Full repository suite**
   - `.venv/bin/python -m pytest -q`
   - Result: `339 passed in 7.82s`

3. **Live editorial loop evidence (`output/editorial-control-center`)**
   - Resumed `./ralph.sh --from ST-004` outside the sandbox
   - Confirmed the loop progressed past the previous prompt-construction failure
   - Observed Codex complete the story work for `ST-004` and report green story-local validation:
     - `DATABASE_URI=postgresql://postgres:postgres@localhost:5480/editorial_control_center npm run db:migrate` — PASS
     - `DATABASE_URI=postgresql://postgres:postgres@localhost:5480/editorial_control_center npm run db:migrate:status` — PASS
     - live `verifyDatabaseConnection()` call — PASS
     - `npm test` — PASS
     - `npm run lint` — PASS
     - `npm run build` — PASS

### New runtime findings from the live loop

1. **Payload migration file import bug in generated project**
   - `output/editorial-control-center/src/lib/migrations/20260319_194516.ts`
   - The migration originally imported `MigrateUpArgs` / `MigrateDownArgs` as runtime values from `@payloadcms/db-postgres`.
   - Real failure:
     - `SyntaxError: The requested module '@payloadcms/db-postgres' does not provide an export named 'MigrateDownArgs'`
   - The live story fixed this in-project by converting those imports to `type` imports.
   - This was backported to the generator in **Session 11**.

2. **Vitest env bootstrap gap for Payload server config**
   - `output/editorial-control-center/src/__tests__/setup-env.ts`
   - `output/editorial-control-center/vitest.config.ts`
   - After `ST-004` introduced a shared DB helper, `npm test` failed because `payload.config.ts` imported DB config before `DATABASE_URI` was loaded in the test environment.
   - The live story fixed this in-project with a Vitest `setupFiles` entry that loads `.env.local`.
   - This was backported to the generator in **Session 11**.

3. **`run_migrations()` is still interactive / noisy for Payload**
   - `output/editorial-control-center/ralph.sh`
   - After the story completed, Ralph’s safety-net migration step blocked on:
     - `Would you like to proceed? (y/N)`
   - After manual confirmation, the step warned because the initial migration was rerun against a state where Payload had already pushed schema changes:
     - `type "enum_users_role" already exists`
   - Ralph downgraded this to `Migrations: WARN`, so the loop did not hard-fail, but this remained a real automation bug for non-interactive runs at the time.
   - This was backported to the generator in **Session 11**.

4. **Local environment conflict, not a generator bug**
   - The default Postgres port `5478` was already occupied on this machine during the live run.
   - The Codex story used `POSTGRES_PORT=5480` for validation without changing the checked-in defaults.
   - This is environmental noise, not a Specwright bug.

### Remaining limitation

- At the time of Session 10, the live loop still exposed three generator gaps. Those gaps were subsequently backported in **Session 11** above.
- `progress.txt` in `output/editorial-control-center` still reflects the interrupted historical loop state until that generated project is regenerated or patched manually.

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

### Current working tree (updated after Session 15)

Current repo state:

```text
Branch: master
HEAD: 3e78b93 + uncommitted Session 15 changes
Test suite: 426/426 passed
Uncommitted files: initializer/ai/refine_engine.py, tests/unit/test_refine_engine.py, analysis.md
```

Session 15 changes are ready to commit: ST-902/ST-903 security stories, story-splitting heuristic, 24 new tests, analysis.md update.

### Most relevant validations already run

```text
311 passed (full pytest suite — 20 new tests added in Session 6)
39 passed in the 3 files directly testing the 6 fixes
```

### Session 6 generator validation completed (2026-03-19)

Regenerated `output/editorial-control-center` from `examples/next-payload-postgres.input.yaml` using:

```text
.venv/bin/python -m initializer new --spec examples/next-payload-postgres.input.yaml
.venv/bin/python -m initializer prepare output/editorial-control-center
```

Observed generated story changes:

- ST-001 now enumerates collections `pages`, `posts`, `authors`, `media` and globals `site-settings`, `homepage`
- ST-002 is now `Configure static asset delivery` with story key `infra.static-delivery`
- ST-009 now explicitly uses Payload local disk adapter / local filesystem storage
- ST-012 now specifies `node-cron`, configurable interval, logging, retry behavior, and idempotency
- ST-013 now exists: `Implement public site pages` with routes for `/pages/[slug]` and `/posts/[slug]`

Real generated-project validation on regenerated `editorial-control-center`:

```text
npm install     PASS
npm test        PASS (required unsandboxed rerun because tsx IPC pipe creation hit EPERM inside sandbox)
npm run lint    PASS
npm run build   PASS
```

Build output included:

```text
Route (app)
○ /
○ /_not-found
ƒ /admin/[[...segments]]
```

### Ralph execution follow-up (2026-03-19)

After the regenerated project passed install/test/lint/build, `./ralph.sh` was run outside the sandbox to validate real Codex execution.

New fixes added at generator level before the real run:

- `initializer/renderers/codex_bundle.py`
  - `ralph.sh` now uses installed `codex exec` instead of `npx -y @openai/codex@latest exec`
  - this removed the network/DNS blocker that previously failed on ST-003 before any real implementation work
- `initializer/renderers/scaffold_engine.py`
  - Payload scaffold now imports `Users` via `./collections/Users.ts`
  - Payload scaffold tsconfig now enables `allowImportingTsExtensions`
- tests added/updated:
  - `tests/unit/test_bundles.py`
  - `tests/unit/test_scaffold_engine.py`
  - focused regression suite: `84 passed`

Real `ralph.sh` results:

```text
ST-003 — DONE
ST-004 — START, then interrupted manually after confirming the loop progressed
```

What ST-003 proved:

- Codex can now run from `ralph.sh` without the previous `@openai/codex` network install failure
- The generated project can be modified by Codex and validated end-to-end inside the loop
- ST-003 completed with:
  - `npm install`
  - `npm run lint`
  - `npm test`
  - `npm run typecheck`
  - `npm run build`

Remaining runtime issue found during `ralph`:

- Payload migration commands still emit a warning on Node `v24.11.1`:

```text
ERR_REQUIRE_ASYNC_MODULE
require() cannot be used on an ESM graph with top-level await
Requiring .../src/payload.config.ts
```

- This does **not** currently stop `ralph.sh`, because `run_migrations()` already downgrades migration command failures to `WARN`.
- It does remain a real product issue for Payload-based projects because manual `payload migrate`, `payload migrate:create`, and `payload migrate:status` are not reliable yet in this environment.

### What still remains valuable to do next

1. **Commit the new generator follow-up fixes**:
   - `initializer/renderers/codex_bundle.py`
   - `initializer/renderers/scaffold_engine.py`
   - `tests/unit/test_bundles.py`
   - `tests/unit/test_scaffold_engine.py`
   - `analysis.md`

2. **Fix Payload migration CLI compatibility on Node 24** so `npx payload migrate*` works reliably from generated projects and from `ralph.sh`.

3. **Resume `./ralph.sh --from ST-004`** after the migration/runtime issue is addressed, or continue if accepting migration warnings for now.

4. Add a targeted validation for the new public routes after story execution:
   - `/pages/[slug]`
   - `/posts/[slug]`
   - draft content returns `404`

5. Consider pinning Payload version range in `_payload_package_json()` to reduce future API drift.
