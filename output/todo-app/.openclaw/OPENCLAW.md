# OPENCLAW.md

This is the execution package for **todo-app**.

## Purpose

OpenClaw should treat this folder as a prepared execution package.
All planning is done — the agent's job is to implement.

## Source of truth

- `spec.json` — full project specification
- `PRD.md` — enriched product requirements with intelligence
- `decisions.md` — architectural decisions
- `progress.txt` — execution log
- `.openclaw/execution-plan.json` — ordered implementation plan
- `docs/stories/` — individual story definitions

## Execution model

1. Read `execution-plan.json` to find the next pending story
2. Read the story file in `docs/stories/`
3. Implement the story
4. Validate the work
5. Update `progress.txt`
6. Move to next story

## Constraints

- Do not replace the generated contract with a new architecture
- Do not rewrite unrelated parts of the project
- Do not skip validation when commands are available
- Do not mark work as complete without recording outcomes
- Follow the phase order: bootstrap → features → product → domain → automation → operations
