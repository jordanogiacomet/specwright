# architecture.md

## Purpose

This document explains the internal conceptual architecture of the repository.

It describes how the initializer is supposed to work as a system.

It is not the architecture of a generated user project.

It is the architecture of the initializer itself.

---

## High-level role of the repository

The repository is a project initializer.

Its purpose is to transform a user's project description plus CLI answers into structured project artifacts.

That transformation should happen through a sequence of specialized engines rather than through one monolithic step.

---

## First principle of this iteration

Before changing implementation, the system must be understood.

That means any agent or maintainer must learn:

- what the current code actually does
- what the system is intended to do
- where those two diverge

Diagnosis is the comparison between those layers.

---

## Expected input-to-output flow

### Inputs

The initializer consumes:

- a free-text project description
- structured CLI answers

### Derived internal state

The initializer should then derive:

- archetype
- stack
- features
- capabilities
- architecture
- stories
- other optional derived artifacts

### Outputs

The initializer should write:

- a structured spec
- PRD documentation
- architecture documentation
- story files

---

## Core conceptual entities

### Prompt

The free-text project description.

This is the starting signal for archetype detection.

Example:

- Editorial CMS with admin panel and public website for publishing articles and media

---

### Answers

Structured CLI selections such as:

- project name
- slug
- summary
- surface
- deploy target

Answers are user choices.

They are not equivalent to archetypes or capabilities unless a derivation layer explicitly maps them.

---

### Archetype

The product-type classification.

Examples:

- `editorial-cms`
- `marketplace`
- `saas-app`
- `generic-web-app`

An archetype should determine at least:

- canonical identity
- default stack
- default features
- default capabilities when appropriate

---

### Capabilities

Capabilities are architectural enrichments.

Examples:

- `cms`
- `public-site`
- `scheduled-jobs`
- `i18n`

Capabilities may affect:

- architecture decisions
- architecture components
- story seeds
- constraints
- risks

Capabilities are not the same as features.

---

### Features

Features are product functionalities expected in output planning.

Examples:

- `authentication`
- `roles`
- `media-library`
- `preview`
- `scheduled-publishing`

Features usually influence:

- story generation
- architecture implications
- validation coverage

Features should not be confused with capabilities.

---

### Spec

The spec is the canonical in-memory structure used across the pipeline.

Minimum expected fields:

- `prompt`
- `archetype`
- `stack`
- `features`
- `capabilities`
- `architecture`
- `stories`
- `answers`

Optional derived sections may include:

- `constraints`
- `risks`
- `design_system`
- `intelligence`
- `diagram`

---

## Intended engine pipeline

A conceptually correct pipeline looks like this:

1. collect prompt
2. detect archetype
3. build initial spec
4. collect answers
5. derive or confirm capabilities
6. apply capabilities
7. apply knowledge
8. generate architecture
9. generate stories
10. derive constraints, design guidance, risks, and intelligence
11. refine and validate
12. write outputs

---

## Understanding-vs-diagnosis model

### What must be learned from code

The agent should inspect implementation to determine:

- actual CLI flow
- actual fields returned by the archetype detector
- actual capability registry behavior
- actual pipeline ordering
- actual file outputs
- actual consumers of `spec`

### What must be compared

The agent should compare:

- intended conceptual contracts
- actual implemented contracts

### What must be diagnosed

The agent should identify:

- mismatched names
- missing fields
- inconsistent contracts
- overwritten state
- stages that do not cooperate semantically

---

## Required contract rules

### Rule 1 — canonical archetype identity

`spec["archetype"]` must be a stable canonical identifier.

It must not be a dict in one place and a string in another.

---

### Rule 2 — explicit capabilities

`spec["capabilities"]` must exist explicitly if downstream systems rely on it.

It must not be assumed without a producer.

---

### Rule 3 — preserved enriched state

If capabilities or knowledge enrich `architecture` or `stories`, later stages must preserve or intentionally merge those enrichments.

Blind overwrite is architecturally invalid.

---

### Rule 4 — story identity consistency

If stories can come from multiple sources, the repository must use one stable strategy for story identifiers.

---

### Rule 5 — downstream naming alignment

Constraints, design, risks, and diagrams must consume canonical naming.

They must not rely on names that upstream code does not actually produce.

---

## Canonical naming recommendation

### Archetypes
- `editorial-cms`
- `marketplace`
- `saas-app`
- `generic-web-app`

### Capabilities
- `cms`
- `public-site`
- `scheduled-jobs`
- `i18n`

### Features
- `authentication`
- `roles`
- `media-library`
- `draft-publish`
- `preview`
- `scheduled-publishing`

---

## Engine responsibilities

### archetype_engine
Detect the project archetype and return canonical metadata.

### capability_engine
Apply enrichments by iterating explicit capabilities.

### knowledge_engine
Append best-practice guidance without breaking canonical naming.

### architecture_engine
Synthesize final architecture while preserving or merging prior enrichments.

### story_engine
Generate implementation stories while maintaining stable IDs and compatibility with capability-derived story inputs.

### constraint_engine
Derive system constraints from archetype, capabilities, and answers.

### design_system_engine
Produce design guidance when relevant to archetype and surface.

### risk_engine
Analyze risks derived from selected capabilities and project structure.

### validation
Check structural integrity and coverage expectations.

---

## Known high-risk areas

The most likely instability areas are:

1. archetype identity contract
2. capability production and capability consumption
3. overwritten architecture/stories after enrichment
4. mismatched naming across downstream engines
5. lack of a single canonical story ID strategy

---

## Goal of the next iteration

The next implementation iteration should align code to this model without changing the product’s main idea.