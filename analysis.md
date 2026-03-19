# Specwright — Full Repository Analysis

**Date**: 2026-03-18 (updated 2026-03-19)
**Test suite**: 238/238 passed (4.11s) — 81 new tests added
**Generated projects inspected**: `output/todo-app`, `output/todo-app-design`, `output/taskflow` (node-api), `output/newshub-cms` (Payload), `output/dentaldesk` (--assist flow)

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
