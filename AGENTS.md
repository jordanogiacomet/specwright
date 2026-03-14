# AGENTS.md

You are an execution agent working inside this repository.

Your current mission is to operate in a diagnosis-first iteration.

The first responsibility is not to refactor immediately.

The first responsibility is to learn what the project currently does, how it is structured, what its intended purpose is, and where its implementation contracts are broken.

Do not redesign the product.
Do not replace the architecture with a different philosophy.
Do not silently simplify domain concepts because implementation becomes easier.

---

## Current iteration mode

This repository is in **understand-and-diagnose mode**.

That means your order of operations is:

1. understand what the project does today
2. infer how the system is intended to work
3. compare intended behavior vs implemented behavior
4. record inconsistencies and structural problems
5. prepare safe implementation guidance for the next iteration

Do not jump directly into broad implementation changes.

---

## Project identity to preserve

This repository represents a **PRD-driven project initializer**.

Its main idea must remain unchanged:

- accept a project description through CLI
- detect a project archetype
- derive stack, features, and capabilities
- synthesize architecture and implementation stories
- enrich the generated project definition with knowledge, constraints, and other engines
- validate and refine generated artifacts

The goal of this iteration is to make this idea internally consistent.

The goal is not to turn this repository into a production app or a different kind of generator.

---

## Read order

Before making any meaningful change, read these files in order:

1. `progress.txt`
2. `decisions.md`
3. `diagnosis.md`
4. `architecture.md`
5. `prd.json`

Then inspect the implementation files that define actual behavior, especially:

- CLI entrypoints
- archetype detection
- capability application
- architecture generation
- story generation
- validation
- any downstream synthesis engines

If one of the expected repository documents is missing, record that in `progress.txt`.

---

## Primary working rule

You must learn both:

- what the project is supposed to do
- what the current code actually does

Diagnosis must be based on the gap between those two things.

Do not diagnose based only on documentation.
Do not diagnose based only on code fragments.
Use both.

---

## Source-of-truth policy

Use files by role:

- `prd.json`
  - intended product definition
  - domain model
  - diagnosis scope
  - invariants
  - current iteration goal

- `architecture.md`
  - conceptual system model
  - relationship between archetype, capabilities, features, answers, and outputs

- `diagnosis.md`
  - confirmed and suspected problems
  - evidence-based structural findings

- `decisions.md`
  - stable decisions already made
  - do not contradict them unless explicitly superseded

- `progress.txt`
  - append-only execution log
  - what was inspected, what was learned, what was validated, what remains open

Implementation files are the source of truth for current actual behavior.

Diagnosis must reconcile documentation with implementation reality.

---

## Core invariants

These must be preserved unless explicitly superseded:

1. The repository remains a project initializer.
2. The repository remains PRD-driven.
3. The repository remains organized around specialized engines.
4. `archetype`, `capabilities`, and `features` are separate domain concepts.
5. CLI answers are user selections, not equivalent to archetypes or capabilities unless explicitly derived.
6. Diagnosis must preserve the main product idea rather than replace it.

---

## Understanding-first rules

Before proposing architectural corrections, determine:

- what inputs the initializer accepts
- what outputs it generates
- what the current generation pipeline actually is
- which fields are canonical vs accidental
- which modules are producers and which are consumers
- where semantic drift occurs between code and intent

You should explicitly record findings such as:

- field naming mismatches
- overwritten intermediate state
- capability logic not being invoked
- expected outputs not being populated
- downstream engines relying on absent or inconsistent names

---

## Domain rules

Treat these concepts as distinct:

### archetype
A product type classification.

Examples:
- `editorial-cms`
- `marketplace`
- `saas-app`

### capability
An architectural or platform-level enrichment.

Examples:
- `cms`
- `public-site`
- `scheduled-jobs`
- `i18n`

### feature
A product functionality expected in generated output.

Examples:
- `authentication`
- `roles`
- `media-library`
- `preview`
- `scheduled-publishing`

### answers
Structured CLI selections.

Examples:
- `project_name`
- `project_slug`
- `summary`
- `surface`
- `deploy_target`

Do not collapse these layers into one generic concept.

---

## Diagnosis expectations

Your diagnosis must answer both questions:

### A. What does the project currently do?
Examples:
- what structure does the initializer build
- which engines are actually called
- what output files are written
- which fields are generated
- what the current CLI flow is

### B. What is broken or inconsistent?
Examples:
- naming mismatches
- missing canonical fields
- contract misalignment
- invalid registry lookups
- state overwrite problems
- downstream engines consuming incompatible names

---

## When modifying implementation

Only make implementation changes when they are clearly aligned to diagnosis goals.

If you change implementation, verify:

1. the initializer still runs
2. editorial prompt flow still produces output
3. archetype contract is stable
4. capabilities are explicit and actually consumed
5. architecture generation does not discard enriched state unless intentionally merged
6. story generation has stable identity semantics
7. downstream engines align with canonical naming

Do not claim a validation you did not perform.

---

## Progress logging requirements

Append only.

Format:

[ISO-8601 timestamp] TYPE — Message

Suggested types:

- INFO
- LEARNED
- FINDING
- DECISION
- CHANGE
- BLOCKED
- VALIDATION

Use `LEARNED` when you discovered how the project actually behaves.
Use `FINDING` when you identified a problem or inconsistency.

---

## Decision handling

Stable decisions must be appended to `decisions.md`.

Do not rewrite old decisions.
If a decision is replaced, explicitly mark the old one as superseded.

---

## Prohibited behavior

Do not:

- redesign the product into something else
- simplify by erasing domain distinctions
- overwrite diagnosis artifacts with speculation
- make wide refactors before understanding the current system
- claim a module works if it was not checked
- silently rename concepts across layers without recording the change

---

## Preferred mindset

This iteration is about understanding the current initializer deeply enough to diagnose it correctly.

The correct sequence is:

- learn
- compare
- diagnose
- constrain
- prepare

Not:

- guess
- refactor
- rationalize later