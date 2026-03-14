# decisions.md

## Purpose

This file records stable decisions for the repository.

Its job is to reduce repeated debate and preserve reasoning across iterations.

Rules:

- append new decisions
- do not rewrite history
- if a decision changes, mark the old one as superseded
- keep entries short and actionable

---

## Status labels

Use one of:

- accepted
- provisional
- superseded

---

## Decision format

Each entry contains:

- ID
- Date
- Status
- Decision
- Reason
- Consequences

---

## Decisions

### DEC-001
- **Date:** 2026-03-13
- **Status:** accepted
- **Decision:** The repository will use an understand-first, diagnosis-first iteration before broad implementation refactors.
- **Reason:** The core product idea appears valid, but implementation behavior and internal contracts must be learned before safe changes can be made.
- **Consequences:** Agents should inspect code behavior and documentation before proposing large refactors.

### DEC-002
- **Date:** 2026-03-13
- **Status:** accepted
- **Decision:** The main product idea must remain unchanged during the diagnosis iteration.
- **Reason:** The repository should be aligned, not reinvented.
- **Consequences:** Refactors must preserve the PRD-driven initializer identity and engine-based architecture.

### DEC-003
- **Date:** 2026-03-13
- **Status:** accepted
- **Decision:** `archetype`, `capabilities`, `features`, and `answers` are distinct domain concepts.
- **Reason:** Current instability is strongly tied to semantic drift between these layers.
- **Consequences:** Future implementation must not collapse these layers into one shared concept or field.

### DEC-004
- **Date:** 2026-03-13
- **Status:** accepted
- **Decision:** Diagnosis must be based on both repository documentation and actual implementation behavior.
- **Reason:** Documentation captures intended direction, while code captures current reality.
- **Consequences:** Agents must compare intent and implementation before classifying a problem.

### DEC-005
- **Date:** 2026-03-13
- **Status:** accepted
- **Decision:** `prd.json` is the source of truth for intended product behavior and iteration scope.
- **Reason:** The repository needs a canonical definition of product purpose, domain model, and current iteration goals.
- **Consequences:** Future implementation changes should be checked against `prd.json`.

### DEC-006
- **Date:** 2026-03-13
- **Status:** accepted
- **Decision:** `architecture.md` is the source of truth for the conceptual internal model of the initializer.
- **Reason:** The main risk in the repository is architectural and semantic misalignment.
- **Consequences:** Engines should be aligned to the conceptual contracts defined there.

### DEC-007
- **Date:** 2026-03-13
- **Status:** provisional
- **Decision:** Capabilities should be explicit and applied by iterating canonical capability identifiers.
- **Reason:** Capability behavior belongs to a separate modeling layer from archetype identity.
- **Consequences:** This should be verified in code and implemented in the next iteration.

### DEC-008
- **Date:** 2026-03-13
- **Status:** provisional
- **Decision:** Architecture and story generation should preserve or merge upstream enrichments rather than blindly replace them.
- **Reason:** Current pipeline behavior appears vulnerable to state loss between stages.
- **Consequences:** The next implementation iteration should define explicit merge behavior.

### DEC-009
- **Date:** 2026-03-14
- **Status:** accepted
- **Decision:** The next implementation iteration will correct canonical contracts in this order: shared spec contract, explicit capability derivation, architecture/story composition, downstream engine alignment, then end-to-end validation.
- **Reason:** Current code still mixes live and legacy producer contracts, so downstream alignment will remain fragile until archetype, answers, and capability production are canonicalized first.
- **Consequences:** Future work should interpret `ST-008` through `ST-012` as an ordered correction sequence and preserve the distinct roles of `archetype`, `capabilities`, `features`, and `answers` while doing so.
