# diagnosis.md

## Purpose

This document records what the repository appears to do, what must still be verified from implementation, and what structural problems are already visible.

This is not a redesign document.

It is a diagnosis document based on learning first and changing later.

---

## Diagnosis method

The diagnosis for this repository must follow this order:

1. inspect the implementation to learn current behavior
2. compare current behavior with the intended product model
3. identify structural inconsistencies
4. record evidence and severity
5. prepare safe guidance for a future implementation iteration

---

## What the project appears to do

Based on the repository structure and current project framing, the initializer appears to do the following:

- collect a project description from the user
- ask CLI questions about the target project
- detect a project archetype
- derive stack and features from the archetype
- generate a project spec
- synthesize PRD, architecture, and story artifacts
- run validation and refinement steps
- write outputs to a generated directory

This understanding must still be confirmed against code during execution work.

## CLI flow confirmed from implementation

The current top-level CLI entrypoint is `initializer/__main__.py`, which delegates to `initializer.cli.main()`.

From there, the active initializer path is the `new` subcommand:

- `initializer new` dispatches to `initializer.flow.new_project.run_new_project(args.spec)`
- `run_new_project()` first prompts for the free-text project description with `Describe the project`
- it immediately calls `build_initial_spec(prompt)` and `detect_archetype(prompt)` before asking for structured answers
- it then calls `collect_answers()`, which prompts in this order:
- `Project name`
- `Project slug` with a default derived from `project_name.lower().replace(" ", "-")`
- `One sentence summary`
- `Choose product surface` with options `internal_admin_only` and `admin_plus_public_site` and default `admin_plus_public_site`
- `Choose deploy target` with options `docker` and `docker_and_k8s_later` and default `docker`

The live `new` flow stores the description separately at `spec["prompt"]` and stores structured CLI answers at:

- `spec["answers"]["project_name"]`
- `spec["answers"]["project_slug"]`
- `spec["answers"]["summary"]`
- `spec["answers"]["surface"]`
- `spec["answers"]["deploy_target"]`

---

## What must be explicitly learned from code

The agent must verify at least:

- what `detect_archetype()` returns today
- whether `capabilities` are produced explicitly
- whether capability handlers are invoked from `spec["capabilities"]` or through another path
- whether architecture enrichments survive later generation steps
- whether story generation resets IDs or conflicts with capability-derived stories
- whether downstream engines use canonical names or ad hoc names
- which generated files are actually written today

---

## Confirmed problem patterns

### D-001 — archetype identity contract is unstable

**Description**  
The repository shows signs that archetype identity may not have one stable representation across the pipeline.

**Impact**  
Runtime failures or inconsistent engine behavior can happen when one stage expects a string and another stage expects a structured object or a different key.

**Severity**  
High

**What to verify in code**  
Compare archetype detector output with all consumers of `spec["archetype"]`.

**Evidence confirmed from implementation**  
`initializer/engine/archetype_engine.py` is the active detector imported by `initializer/flow/new_project.py`. Its current `detect_archetype(prompt)` contract is a dict with exactly five keys on every branch: `id`, `name`, `stack`, `features`, and `capabilities`. `initializer/flow/new_project.py` then copies `archetype_data["id"]` into the canonical `spec["archetype"]` string and preserves the full detector payload separately at `spec["archetype_data"]`. Repo-wide search found only three direct readers of `spec["archetype"]`: `initializer/engine/constraint_engine.py`, `initializer/engine/design_system_engine.py`, and `initializer/engine/prd_intelligence_engine.py`; each uses `spec.get("archetype")` and compares the result against the string `"editorial-cms"`. This means the active `new` flow and its current downstream readers now agree on a string-valued `spec["archetype"]`. The remaining mismatch is at the detector layer: `initializer/flow/archetype_detection.py` still defines a separate legacy `detect_archetype(prompt)` that returns a bare string instead of canonical metadata. Archetype identity is therefore stable inside the active `new` flow today, but inconsistent at the repository level because more than one detector contract still exists.

---

### D-002 — capabilities may be consumed without being canonically produced

**Description**  
Some downstream behavior appears to rely on capabilities, but capability production may not be explicit or complete.

**Impact**  
Capability logic may silently never run, and dependent engines may produce incomplete output.

**Severity**  
High

**What to verify in code**  
Check where `spec["capabilities"]` is created, whether it always exists, and whether it aligns with registry keys.

**Evidence confirmed from implementation**  
`initializer/flow/new_project.py` is the active producer path for the live initializer. `build_initial_spec(prompt)` copies `detect_archetype(prompt)["capabilities"]` into `spec["capabilities"]`, and `derive_capabilities_from_answers(spec)` is the only inspected derivation layer that mutates that list before capability application. In the current code, `initializer/engine/archetype_engine.py` produces `["cms"]` for `editorial-cms` and `[]` for marketplace, SaaS, and fallback prompts. `derive_capabilities_from_answers()` adds only `public-site` when `answers["surface"] == "admin_plus_public_site"`. An alternate builder still exists in `initializer/runtime/spec_builder.py`, but it initializes `capabilities` to `[]` unconditionally and does not derive any capability IDs. Capability production is therefore explicit in the active `new` flow, but limited to archetype-default `cms` plus answer-derived `public-site`; the inspected code does not produce `scheduled-jobs` or `i18n` anywhere in the live pipeline.

---

### D-003 — capability application may be bound to the wrong abstraction

**Description**  
Capability execution appears at risk of being keyed off archetype identity instead of the capability list.

**Impact**  
Architectural enrichments may not run even when conceptually required.

**Severity**  
High

**What to verify in code**  
Check whether capability application iterates `spec["capabilities"]` or uses unrelated fields.

**Evidence confirmed from implementation**  
The active capability engine in `initializer/engine/capability_engine.py` now normalizes `spec["architecture"]` and `spec["stories"]`, then iterates `spec["capabilities"]` and resolves each ID through `initializer/engine/capability_registry.py`. The current registry keys are exactly `cms`, `public-site`, `scheduled-jobs`, and `i18n`, mapped to handlers in `initializer/capabilities/`. Runtime reproduction with an editorial prompt plus `surface=admin_plus_public_site` confirmed the live path produces `["cms", "public-site"]` and invokes both handlers, adding CMS decisions, a CDN component, and seeded stories before later generators run. The remaining mismatch is between produced and consumable capability IDs: the engine and downstream consumers can react to `scheduled-jobs` and `i18n`, but no inspected live producer derives those capability IDs, so those handlers are reachable only if a spec is manually populated outside the normal `new` flow.

---

### D-004 — enriched architecture or stories may be overwritten later

**Description**  
The pipeline appears vulnerable to stages that enrich data early and then lose it when later generators assign fresh values.

**Impact**  
The system becomes logically inconsistent and earlier work becomes semantically meaningless.

**Severity**  
High

**What to verify in code**  
Inspect pipeline ordering and whether architecture/stories are merged or replaced.

**Evidence confirmed from implementation**  
The active `new` flow in `initializer/flow/new_project.py` now executes architecture-related stages in this exact order: `build_initial_spec()` seeds `spec["architecture"]` as `{}`, `apply_capabilities(spec)` initializes `decisions` and `components` and lets capability handlers append architecture state, `apply_knowledge(spec)` appends additional architecture decisions, then `spec["architecture"] = generate_architecture(spec)` synthesizes the final architecture object from the current spec before `refine_spec(spec)` appends more decisions. The inspected upstream architecture enrichments in the live path are:

- `initializer/capabilities/cms.py` appends two architecture decisions
- `initializer/capabilities/public_site.py` appends one CDN component and one delivery decision
- `initializer/capabilities/scheduled_jobs.py` appends one worker component and one scheduling decision
- `initializer/capabilities/i18n.py` appends one locale-model decision
- `initializer/engine/knowledge_engine.py` appends stack- and feature-driven decisions to the existing architecture object

`initializer/engine/architecture_engine.py` no longer blindly discards those upstream `components` and `decisions`: it copies `existing_architecture = spec.get("architecture") or {}`, carries forward existing `components` and `decisions`, adds generated entries through `add_component()` and `add_decision()`, and returns a new architecture dict with merged `style`, `components`, and `decisions`. Runtime reproduction confirmed that capability- and knowledge-seeded CDN and decision entries survive the later architecture generation and remain present after `refine_spec(spec)` adds more decisions.

The remaining inconsistency is that this merge behavior is narrow rather than fully generic. `generate_architecture()` only preserves `style`, `components`, and `decisions`, so any future upstream architecture keys outside those fields would still be dropped by the final assignment. It also deduplicates components by exact dict equality only, which means semantically overlapping enrichments can survive as duplicates: when `scheduled-jobs` seeds `{"name": "worker", "technology": "background-worker", ...}` and feature-driven architecture synthesis later adds `{"name": "worker", "technology": backend, ...}`, both worker components remain. The active flow therefore preserves the currently produced architecture enrichments instead of overwriting them, but its merge semantics are still partial and name-based architectural deduplication is not canonical.

---

### D-005 — story ID generation may not be globally stable

**Description**  
Stories may originate from multiple creation paths with different ID assumptions.

**Impact**  
IDs may conflict, duplicate, or become order-dependent in fragile ways.

**Severity**  
Medium

**What to verify in code**  
Inspect all story producers and compare ID generation strategies.

**Evidence confirmed from implementation**  
The active `new` flow seeds `spec["stories"]` as `[]` in `initializer/flow/new_project.py`, then mutates that list through three live producer stages:

- `initializer/engine/capability_engine.py` runs first and iterates `spec["capabilities"]` in list order, handing the current story list to capability handlers in `initializer/capabilities/cms.py`, `initializer/capabilities/public_site.py`, `initializer/capabilities/scheduled_jobs.py`, and `initializer/capabilities/i18n.py`
- `initializer/engine/story_engine.py` runs next through `spec["stories"] = generate_stories(spec)` in the active `new` flow and appends bootstrap, stack, and feature stories
- `initializer/ai/refine_engine.py` runs last through `refine_spec(spec)` and `refine_stories(spec)`, appending fixed operational stories `ST-900` and `ST-901` when absent

A separate legacy producer still exists at `initializer/synthesis/stories.py`, but repo search found no imports or call sites from the active `new` flow, so it is not part of the live initializer path.

The repository therefore does not have one canonical story ID allocator. Capability handlers assign IDs with `f"ST-{len(stories)+1:03}"`, which makes identity depend on the incoming list length and on capability order. `initializer/engine/story_engine.py` instead scans the incoming stories for numeric `ST-###` IDs, initializes its counter to `max(existing_numeric_suffix) + 1`, ignores non-`ST-` IDs entirely, and appends stories in a hardcoded order driven by stack fields and feature membership. `initializer/ai/refine_engine.py` bypasses both strategies with fixed IDs `ST-900` and `ST-901`. Repo search also found no live producer that emits `depends_on`, so the current story order is append order only; `initializer/graph/story_graph.py` can consume dependencies, but the active generator never produces them.

Runtime repros confirmed the contract is fragile in several ways. Reversing the capability list from `['cms', 'public-site']` to `['public-site', 'cms']` swapped which concern received `ST-001` and `ST-002`. Reapplying `apply_capabilities()` appended duplicate capability stories with new IDs, and rerunning `generate_stories()` on an already populated spec appended duplicate bootstrap and feature stories instead of reconciling existing ones. After `refine_stories()` added `ST-900` and `ST-901`, a second call to `generate_stories()` resumed numbering at `ST-902`, showing that later high-numbered fixed IDs can shift the entire generated range. A noncanonical pre-seeded story ID such as `CUSTOM-1` is preserved, but because `generate_stories()` ignores it when computing the next counter, the final list can mix incompatible identity schemes.

There is also a documented mismatch between capability-derived stories and downstream coverage logic. `initializer/validation/story_coverage.py` marks a capability as covered only when the literal capability token with hyphens replaced by spaces appears in a story description. That matches the current CMS and public-site descriptions, but direct repros showed that `scheduled-jobs` and `i18n` capability handlers still fail coverage even after seeding stories, because their descriptions talk about scheduled publishing or locale behavior rather than the literal capability names. The `scheduled-jobs` capability also overlaps semantically with the feature-driven `Implement scheduled publishing` story from `initializer/engine/story_engine.py`, so a spec carrying both can produce multiple scheduler-related stories without a canonical merge rule.

---

### D-006 — downstream engines may assume names that are never produced upstream

**Description**  
Downstream engines are only partially aligned to the live spec contract: some consume canonical upstream fields correctly, some are not wired into the active initializer at all, and the diagram engine depends on component names that the live architecture producer does not emit.

**Impact**  
Silent omissions, empty results, or misleading outputs may occur.

**Severity**  
Medium to High

**What to verify in code**  
Compare producer names and consumer expectations across the full pipeline.

**Evidence confirmed from implementation**  
The active initializer path in `initializer/flow/new_project.py` imports only `detect_archetype`, `apply_capabilities`, `apply_knowledge`, `generate_architecture`, `generate_stories`, `refine_spec`, `validate_prd`, and `check_story_coverage`. It writes `spec.json`, `PRD.md`, `architecture.md`, and story markdown files. Repo-wide search found no live call sites for `initializer/engine/constraint_engine.py`, `initializer/engine/risk_engine.py`, `initializer/engine/design_system_engine.py`, `initializer/engine/architeture_diagram_engine.py`, or their renderer modules, so the live initializer never generates or writes `constraints`, `risks`, `design_system`, or `diagram` outputs even though `architecture.md` lists those sections as optional derived artifacts.

Field-level comparison shows partial alignment rather than universal drift:

- `initializer/engine/constraint_engine.py` consumes `spec["archetype"]`, `spec["capabilities"]`, and `spec["answers"]["deploy_target"]`. Those names match the canonical fields produced by `build_initial_spec()` and `collect_answers()` in the active `new` flow.
- `initializer/engine/risk_engine.py` consumes `spec["capabilities"]` and resolves canonical capability IDs through `initializer/risks/registry.py` with keys `cms`, `public-site`, `scheduled-jobs`, and `i18n`. This matches the capability vocabulary established elsewhere in the repository, even though the live producer path still emits only a subset of those IDs automatically.
- `initializer/engine/design_system_engine.py` consumes `spec["archetype"]` plus `spec["answers"]["surface"]`. Those names also match the active producer contract.
- `initializer/engine/architeture_diagram_engine.py` consumes `spec["architecture"]["components"][*]["name"]`, but its edge logic hardcodes node names `frontend`, `cms`, `database`, `worker`, and `cdn`. The active architecture producer in `initializer/engine/architecture_engine.py` emits `frontend`, `api`, `database`, and `object-storage`, while capability handlers may append `cdn` and `worker`; no inspected upstream producer emits a `cms` component name.

A targeted live-pipeline repro with an editorial prompt, `surface=admin_plus_public_site`, and `deploy_target=docker` confirmed the mismatch. The final spec contained keys `prompt`, `archetype`, `stack`, `features`, `capabilities`, `architecture`, `stories`, `answers`, and `archetype_data`, but no `constraints`, `risks`, `design_system`, or `diagram` sections. The synthesized architecture component names were `['cdn', 'frontend', 'api', 'database', 'object-storage', 'worker']`. Running `generate_architecture_diagram(spec)` on that spec produced only the edges `worker -> database` and `cdn -> frontend`, because the engine looks for a `cms` node instead of the actual `api` component. The confirmed downstream alignment problems are therefore:

- the downstream constraint, risk, design, and diagram engines are defined but not wired into the active initializer or output-writing path
- live specs omit the optional downstream sections those engines would generate
- the diagram engine has a broken naming dependency on `cms`, which is not a component name produced by the active architecture synthesis flow

---

### D-007 — capability handlers may not normalize input shape consistently

**Description**  
Some capability handlers may assume architecture sections already exist while others initialize them defensively.

**Impact**  
Order-dependent runtime errors are possible.

**Severity**  
Medium

**What to verify in code**  
Inspect every capability handler for shape normalization behavior.

---

## Suspected problem patterns

### D-008 — feature and capability naming overlap may be causing hidden coupling

**Description**  
Related concepts appear to use different vocabularies, which may partially align in one engine and diverge in another.

**Impact**  
A fix in one module may fail to propagate to the rest of the system.

**Severity**  
Medium

---

### D-009 — answers may imply capabilities without a formal derivation step

**Description**  
Some CLI choices may logically imply architectural capabilities, but only the public-site surface is currently modeled through a central derivation step.

**Impact**  
Expected outputs may be missing despite correct user choices.

**Severity**  
Medium

---

### D-010 — architecture generation may act as replacement instead of synthesis

**Description**  
Architecture generation may behave as though it owns the whole output instead of composing with prior enrichments.

**Impact**  
The pipeline becomes fragile and staging loses value.

**Severity**  
Medium to High

---

### D-011 — exposed CLI contracts drift from the live prompt implementation

**Description**  
The CLI advertises entrypoints and argument shapes that do not consistently match the live prompt flow or the helper contracts behind it.

**Impact**  
Users and downstream maintainers cannot rely on the exposed CLI surface, and answer-field naming is not canonical across CLI-related modules.

**Severity**  
High

**What to verify in code**  
Compare `initializer.cli` subcommands and arguments with the live `new` and `plan` flow implementations and with the answer fields they consume.

**Evidence confirmed from implementation**  
`initializer/cli.py` exposes `new --spec` and passes the value into `initializer.flow.new_project.run_new_project(spec_path=None)`, but `run_new_project()` never reads `spec_path` and always prompts interactively. A live repro with `python -m initializer new --spec /tmp/ignored-spec` still prompted for `Describe the project`, `Project name`, `Project slug`, `One sentence summary`, `Choose product surface`, and `Choose deploy target`, then generated output from those answers. `initializer/cli.py` also exposes `plan`, but `initializer/flow/plan_project.py` imports `collect_input`, `render_prd`, and `render_decisions` from `initializer.flow.new_project`, and those helpers do not exist there; `python -m initializer plan --spec prd.json` therefore fails immediately with `ImportError`. The drift is reinforced by `initializer/models/bootstrap.py`, which still models a `project_summary` field while the live `new` flow stores the answer under `summary`.

---

## Root cause themes

### 1. Missing canonical contracts
Multiple engines appear to rely on assumed field names instead of one shared contract.

### 2. Semantic drift
Archetype, capability, and feature seem conceptually separate but implementation may blur them.

### 3. Incomplete composition
The pipeline has multiple stages but may not preserve the work of earlier stages.

### 4. Repository knowledge gap
The project cannot be safely refactored until actual behavior is learned from code, not inferred only from intent.

---

## Canonical correction plan

### Canonical roles to preserve

- `prompt` is the free-text project description that starts archetype detection.
- `answers` are structured CLI selections stored under canonical keys such as `project_name`, `project_slug`, `summary`, `surface`, and `deploy_target`; they are user input, not inferred architecture.
- `archetype` is the canonical product classification stored as the string `spec["archetype"]`; richer detector metadata belongs in `spec["archetype_data"]` or another explicitly separate structure.
- `capabilities` are explicit architectural enrichments stored as canonical IDs in `spec["capabilities"]`; they are derived from archetype defaults and explicit answer-mapping rules, then consumed by capability and downstream engines.
- `features` are expected product functions stored in `spec["features"]`; they influence planning and synthesis, but they are not aliases for capabilities.

These roles match the intended model in `architecture.md` and `prd.json`, and they also match the current live `new` flow more closely than the remaining legacy modules do.

### Ordered next implementation targets

1. `ST-008` should consolidate the shared spec contract before more consumer work happens.
   The immediate correction targets are `initializer/engine/archetype_engine.py`, `initializer/flow/archetype_detection.py`, `initializer/runtime/spec_builder.py`, `initializer/flow/plan_project.py`, `initializer/models/bootstrap.py`, and `initializer/flow/new_project.py`.
   The goal is one canonical archetype identity contract and one canonical answer vocabulary across live and legacy paths, while preserving the current initializer product idea.

2. `ST-009` should centralize capability derivation after the shared contract is stable.
   The correction target is one explicit derivation layer that combines archetype defaults with answer-derived capability rules and emits only canonical registry IDs such as `cms`, `public-site`, `scheduled-jobs`, and `i18n`.
   Builders that currently seed `capabilities` as an empty list without derivation should be aligned to that same contract instead of carrying parallel behavior.

3. `ST-010` should formalize composition rules for architecture and stories.
   The correction targets are `initializer/engine/capability_engine.py`, `initializer/capabilities/*.py`, `initializer/engine/architecture_engine.py`, `initializer/engine/story_engine.py`, `initializer/ai/refine_engine.py`, and `initializer/validation/story_coverage.py`.
   The goal is one explicit merge strategy for enriched architecture, one stable story identity strategy across all producers, and coverage checks based on canonical story/capability semantics rather than fragile substring matching.

4. `ST-011` should align downstream engines only after upstream naming and composition contracts are stable.
   The correction targets are `initializer/engine/constraint_engine.py`, `initializer/engine/design_system_engine.py`, `initializer/engine/risk_engine.py`, `initializer/engine/architeture_diagram_engine.py`, plus any output-writing path that is meant to expose their results.
   This stage should remove broken naming dependencies such as the diagram engine's expectation of a `cms` component when the live architecture producer emits `api`, and it should explicitly decide which optional derived sections belong in the active initializer flow.

5. `ST-012` should validate the editorial reference flow only after the prior contract corrections are in place.
   The validation target is the live `initializer new` path with an editorial prompt and representative answers.
   The success condition is a coherent generated spec whose archetype, capabilities, features, architecture, stories, and any intentionally wired downstream outputs all follow the canonical contract.

### Sequencing rationale

- Shared producer contracts must be corrected before downstream consumers are aligned to them.
- Capability derivation must be explicit before architecture, stories, risks, or constraints can reliably depend on capabilities.
- Composition semantics must be stabilized before downstream engines or validation can treat architecture and stories as canonical outputs.
- End-to-end validation should be the final check, not the mechanism that discovers unresolved contract drift.

This plan preserves the repository identity as a PRD-driven initializer with specialized engines. It constrains the next iteration toward contract alignment rather than redesign.

---

## What must not change in diagnosis phase

These elements should remain stable:

- PRD-driven initialization
- engine-based synthesis
- archetype detection
- capability enrichment
- architecture synthesis
- story generation
- validation/refinement layers

The issue is alignment, not concept replacement.

---

## Exit condition for this phase

This phase is complete when:

- the project’s actual behavior is understood
- the intended model is documented
- the main inconsistencies are recorded with evidence
- implementation can proceed without redefining the project
