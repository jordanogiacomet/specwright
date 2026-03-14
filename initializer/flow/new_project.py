from pathlib import Path
import json
import re
from typing import Any

from initializer.engine.archetype_engine import detect_archetype
from initializer.engine.capability_derivation import derive_capabilities_for_spec
from initializer.engine.capability_engine import apply_capabilities
from initializer.engine.knowledge_engine import apply_knowledge
from initializer.engine.architecture_engine import generate_architecture
from initializer.engine.constraint_engine import generate_constraints
from initializer.engine.design_system_engine import generate_design_system
from initializer.engine.risk_engine import analyze_risks
from initializer.engine.architeture_diagram_engine import (
    generate_architecture_diagram,
)
from initializer.engine.story_engine import generate_stories

from initializer.ai.refine_engine import refine_spec
from initializer.ai.discovery_engine import run_assisted_discovery
from initializer.ai.discovery_merge import merge_assisted_discovery

from initializer.renderers.constraints_renderer import write_constraints
from initializer.renderers.design_system_renderer import write_design_system
from initializer.renderers.risks_renderer import write_risks
from initializer.renderers.architecture_diagram_renderer import (
    write_architecture_diagram,
)

from initializer.validation.prd_validator import validate_prd
from initializer.validation.story_coverage import check_story_coverage


def prompt_text(label, default=None):
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if not value and default:
        return default
    return value


def prompt_choice(label, options, default=None):
    print(label)
    for i, option in enumerate(options, start=1):
        if option == default:
            print(f" {i}. {option} (default)")
        else:
            print(f" {i}. {option}")

    value = input("> ").strip()
    if not value and default:
        return default

    idx = int(value) - 1
    return options[idx]


def prompt_boolean(label: str) -> tuple[str, bool]:
    while True:
        print(label)
        print(" 1. yes")
        print(" 2. no")
        raw = input("Answer: ").strip().lower()

        if raw in {"1", "yes", "y", "true"}:
            return raw, True

        if raw in {"2", "no", "n", "false"}:
            return raw, False

        print("Please answer with 1/2 or yes/no.\n")


def create_output_dir(slug):
    path = Path("output") / slug
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_prd(path, spec):
    content = f"""
# {spec['answers']['project_name']}

## Summary

{spec['answers']['summary']}

## Stack

Frontend: {spec['stack']['frontend']}
Backend: {spec['stack']['backend']}
Database: {spec['stack']['database']}

## Features
"""

    for feature in spec["features"]:
        content += f"- {feature}\n"

    content += "\n## Architecture Decisions\n"
    for decision in spec["architecture"]["decisions"]:
        content += f"- {decision}\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_architecture(path, spec):
    arch = spec["architecture"]
    content = "# Architecture\n\n"

    for component in arch["components"]:
        content += f"### {component['name']}\n"
        content += f"Technology: {component['technology']}\n"
        content += f"Role: {component['role']}\n\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
def write_decisions(path, spec):
    answers = spec.get("answers", {})
    stack = spec.get("stack", {})
    capabilities = spec.get("capabilities", [])
    architecture = spec.get("architecture", {})
    architecture_decisions = architecture.get("decisions", [])

    content = f"""# decisions.md

## Purpose

This file records stable project decisions for this generated project.

Use it to reduce drift during agent execution.

---

## Status labels

- `accepted`
- `superseded`
- `provisional`

---

## Decisions

### DEC-001
- **Date:** generated
- **Status:** accepted
- **Decision:** `spec.json` is the primary structured source of truth for this generated project.
- **Reason:** This project folder was generated from the initializer and should be implemented from the generated spec.
- **Consequences:** Execution agents should consult `spec.json` before changing architecture or scope.

### DEC-002
- **Date:** generated
- **Status:** accepted
- **Decision:** `docs/stories/` defines the preferred unit of implementation work.
- **Reason:** Story-by-story execution reduces drift and improves validation.
- **Consequences:** Agents should implement one story at a time and record progress after each meaningful iteration.

### DEC-003
- **Date:** generated
- **Status:** accepted
- **Decision:** Generated architecture should remain stable unless a story explicitly changes it.
- **Reason:** The initializer already derived the architecture from the project spec.
- **Consequences:** Agents should not silently redesign the system during routine implementation work.

### DEC-004
- **Date:** generated
- **Status:** accepted
- **Decision:** Use surface `{answers.get("surface", "unknown")}` with deploy target `{answers.get("deploy_target", "unknown")}`.
- **Reason:** These values are explicit project inputs.
- **Consequences:** Implementation should respect product shape and deployment assumptions derived from them.

### DEC-005
- **Date:** generated
- **Status:** accepted
- **Decision:** Use stack frontend=`{stack.get("frontend", "unknown")}`, backend=`{stack.get("backend", "unknown")}`, database=`{stack.get("database", "unknown")}`.
- **Reason:** Stack was derived as part of the generated project contract.
- **Consequences:** Code generation and implementation decisions should remain aligned with this stack.

### DEC-006
- **Date:** generated
- **Status:** accepted
- **Decision:** Capabilities for this generated project are `{", ".join(capabilities) if capabilities else "none"}`.
- **Reason:** Capabilities shape downstream behavior and implementation scope.
- **Consequences:** Agents should not add behaviors that conflict with the generated capability set.
"""

    next_index = 7
    for decision in architecture_decisions:
        content += f"""

### DEC-{next_index:03}
- **Date:** generated
- **Status:** accepted
- **Decision:** {decision}
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.
"""
        next_index += 1

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_progress(path):
    content = """# progress.txt
# Append-only execution log for this generated project
# Format:
# [ISO-8601 timestamp] STORY-ID — STATUS — Description
#
# Statuses:
# START
# DONE
# BLOCKED
# INFO
# VALIDATION
#
# Example:
# [2026-03-14T12:00:00Z] ST-001 — START — Began implementation of authentication flow
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_stories(path, spec):
    stories_dir = path / "docs" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    for story in spec["stories"]:
        file = stories_dir / f"{story['id']}.md"
        content = f"""
# {story['id']} — {story['title']}

## Description

{story['description']}
"""
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)

def write_openclaw_bundle(path, spec):
    openclaw_dir = path / ".openclaw"
    openclaw_dir.mkdir(parents=True, exist_ok=True)

    project_slug = spec.get("answers", {}).get("project_slug", "generated-project")

    agents_md = """# AGENTS.md

You are an execution agent working inside this generated project folder.

## Mission

Implement the project described by the generated spec and planning artifacts.
This folder is the execution package generated by the initializer.
Treat the files in this folder as the contract for implementation work.

## Read order

Before changing code, read these files in this order when present:

1. `spec.json`
2. `PRD.md`
3. `decisions.md`
4. `progress.txt`
5. `architecture.md`
6. `docs/stories/`
7. project source files
8. project tests and config files

## Rules

- work one story at a time
- do not silently change architecture
- do not silently change product scope
- prefer minimal targeted patches
- validate before claiming completion
- append progress after meaningful work
- respect the generated spec as the source of truth

## Contract rules

- `spec.json` is the structured source of truth
- `decisions.md` contains stable decisions unless explicitly superseded
- `progress.txt` is append-only
- stories under `docs/stories/` define execution slices
- implementation must follow the generated architecture unless a story explicitly changes it

## Validation policy

When relevant, validate in this order:

1. targeted test
2. full test suite
3. lint
4. build

If a command is unavailable, record that clearly in `progress.txt`.

## Completion standard

Only consider a story complete when:

- code changed
- validation was attempted
- results were recorded
- the active story is satisfied
"""

    openclaw_md = """# OPENCLAW.md

This generated folder is intended to be consumed by an execution loop.

## Purpose

OpenClaw should treat this folder as a prepared execution package, not as an unstructured code dump.

## Source of truth

Use these files as primary context:

- `spec.json`
- `PRD.md`
- `decisions.md`
- `progress.txt`
- `architecture.md`
- `docs/stories/`
- `.openclaw/manifest.json`
- `.openclaw/repo-contract.json`
- `.openclaw/commands.json`

## Execution model

- select one story at a time
- inspect only relevant files for that story
- patch incrementally
- validate
- append progress
- do not widen scope unless the current story requires it

## Constraints

- do not replace the generated contract with a new architecture
- do not rewrite unrelated parts of the project
- do not skip validation when commands are available
- do not mark work as complete without recording outcomes

## Expected handoff to coding executor

The coding executor should be able to answer:

- what the product is
- what the architecture is
- what story is active
- what commands validate the work
- what decisions must remain stable
"""

    manifest = {
        "project_root_type": "generated-project-package",
        "project_slug": project_slug,
        "source_of_truth": [
            "spec.json",
            "PRD.md",
            "decisions.md",
            "progress.txt",
            "architecture.md",
            "docs/stories",
            ".openclaw/AGENTS.md",
            ".openclaw/OPENCLAW.md",
        ],
        "execution_mode": "story-by-story",
        "primary_input": "spec.json",
        "policies": {
            "one_story_at_a_time": True,
            "must_validate_before_done": True,
            "append_progress": True,
            "avoid_architecture_drift": True,
        },
    }

    repo_contract = {
        "contract": {
            "kind": "generated-project",
            "primary_spec": "spec.json",
            "primary_prd": "PRD.md",
            "primary_architecture": "architecture.md",
            "primary_decisions": "decisions.md",
            "primary_progress_log": "progress.txt",
            "stories_dir": "docs/stories",
        },
        "execution_expectations": {
            "story_driven": True,
            "validate_changes": True,
            "record_progress": True,
            "preserve_generated_scope": True,
        },
    }

    commands = {
        "commands": {
            "test": "",
            "lint": "",
            "build": "",
        },
        "notes": [
            "This generated project package may not yet contain source code or runnable commands.",
            "Before execution, OpenClaw or the coding agent should detect actual project commands from the generated repository.",
        ],
    }

    with open(openclaw_dir / "AGENTS.md", "w", encoding="utf-8") as f:
        f.write(agents_md)

    with open(openclaw_dir / "OPENCLAW.md", "w", encoding="utf-8") as f:
        f.write(openclaw_md)

    with open(openclaw_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    with open(openclaw_dir / "repo-contract.json", "w", encoding="utf-8") as f:
        json.dump(repo_contract, f, indent=2, ensure_ascii=False)

    with open(openclaw_dir / "commands.json", "w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2, ensure_ascii=False)

def write_downstream_artifacts(path, spec):
    docs_dir = path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    write_constraints(docs_dir, spec["constraints"])
    write_design_system(docs_dir, spec["design_system"])
    write_risks(docs_dir, spec["risks"])
    write_architecture_diagram(docs_dir, spec["diagram"])




def build_initial_spec(prompt):
    archetype_data = detect_archetype(prompt)
    spec = {
        "prompt": prompt,
        "archetype": archetype_data["id"],
        "archetype_data": archetype_data,
        "stack": archetype_data["stack"],
        "features": archetype_data["features"],
        "capabilities": archetype_data.get("capabilities", []),
        "architecture": {},
        "stories": [],
        "answers": {},
    }
    return spec


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "generated-project"


def _safe_choice(value: Any, options: list[str], default: str) -> str:
    if isinstance(value, str) and value in options:
        return value
    return default


def _resolve_spec_input_path(spec_path: str) -> Path:
    candidate = Path(spec_path).expanduser()
    if candidate.is_dir():
        candidate = candidate / "spec.json"
    return candidate


def load_project_spec(spec_path: str) -> dict[str, Any]:
    path = _resolve_spec_input_path(spec_path)

    if not path.exists():
        raise ValueError(f"Spec file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Spec file is not valid JSON: {path} ({exc})"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Spec file must contain a JSON object: {path}")

    answers = data.get("answers")
    if not isinstance(answers, dict):
        answers = {}

    project_name = (
        answers.get("project_name")
        or data.get("project_name")
        or "Generated Project"
    )

    summary = (
        answers.get("summary")
        or data.get("summary")
        or data.get("prompt")
        or project_name
    )

    project_slug = (
        answers.get("project_slug")
        or data.get("project_slug")
        or _slugify(project_name)
    )

    normalized_answers = {
        "project_name": project_name,
        "project_slug": project_slug,
        "summary": summary,
        "surface": _safe_choice(
            answers.get("surface") or data.get("surface"),
            ["internal_admin_only", "admin_plus_public_site"],
            "admin_plus_public_site",
        ),
        "deploy_target": _safe_choice(
            answers.get("deploy_target") or data.get("deploy_target"),
            ["docker", "docker_and_k8s_later"],
            "docker",
        ),
    }

    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        prompt = summary or project_name

    archetype_data = data.get("archetype_data")
    if not isinstance(archetype_data, dict) or not archetype_data.get("id"):
        archetype_data = detect_archetype(prompt)

    stack = data.get("stack")
    if not isinstance(stack, dict):
        stack = dict(archetype_data.get("stack") or {})

    features = data.get("features")
    if not isinstance(features, list):
        features = list(archetype_data.get("features") or [])

    capabilities = data.get("capabilities")
    if not isinstance(capabilities, list):
        capabilities = list(archetype_data.get("capabilities") or [])

    spec = dict(data)
    spec["prompt"] = prompt
    spec["archetype"] = data.get("archetype") or archetype_data["id"]
    spec["archetype_data"] = archetype_data
    spec["stack"] = stack
    spec["features"] = features
    spec["capabilities"] = capabilities
    spec["answers"] = normalized_answers

    if not isinstance(spec.get("architecture"), dict):
        spec["architecture"] = {}

    if not isinstance(spec.get("stories"), list):
        spec["stories"] = []

    if not isinstance(spec.get("discovery"), dict):
        spec["discovery"] = {}

    return spec


def derive_capabilities_from_answers(spec):
    return derive_capabilities_for_spec(spec)


def derive_downstream_artifacts(spec):
    spec["constraints"] = generate_constraints(spec)
    spec["design_system"] = generate_design_system(spec)
    spec["risks"] = analyze_risks(spec)
    spec["diagram"] = generate_architecture_diagram(spec)
    return spec


def collect_answers():
    project_name = prompt_text("Project name")
    project_slug = prompt_text(
        "Project slug",
        project_name.lower().replace(" ", "-"),
    )
    summary = prompt_text("One sentence summary")
    surface = prompt_choice(
        "Choose product surface",
        ["internal_admin_only", "admin_plus_public_site"],
        "admin_plus_public_site",
    )
    deploy_target = prompt_choice(
        "Choose deploy target",
        ["docker", "docker_and_k8s_later"],
        "docker",
    )

    return {
        "project_name": project_name,
        "project_slug": project_slug,
        "summary": summary,
        "surface": surface,
        "deploy_target": deploy_target,
    }


def _normalize_list_input(value: str) -> list[str]:
    parts = [part.strip() for part in value.split(",")]
    return [part for part in parts if part]


def _prompt_question_answer(question: dict[str, Any]) -> tuple[str, Any, str]:
    question_text = question["question"]
    answer_type = question.get("answer_type", "text")
    choices = question.get("choices", [])

    if answer_type == "boolean":
        raw_answer, value = prompt_boolean(question_text)
        return raw_answer, value, answer_type

    print(question_text)

    if answer_type == "enum" and choices:
        for index, choice in enumerate(choices, start=1):
            print(f" {index}. {choice}")

        while True:
            raw_answer = input("Answer: ").strip()

            if raw_answer.isdigit():
                idx = int(raw_answer) - 1
                if 0 <= idx < len(choices):
                    return raw_answer, choices[idx], answer_type

            if raw_answer in choices:
                return raw_answer, raw_answer, answer_type

            print("Please choose one of the listed options.\n")

    raw_answer = input("Answer: ").strip()

    if answer_type == "list":
        return raw_answer, _normalize_list_input(raw_answer), answer_type

    return raw_answer, raw_answer, answer_type


def _unique_question_objects(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate questions by both id and signal_key."""
    seen_ids: set[str] = set()
    seen_signal_keys: set[str] = set()
    unique: list[dict[str, Any]] = []

    for question in questions:
        if not isinstance(question, dict):
            continue

        question_id = question.get("id")
        question_text = question.get("question")

        if not isinstance(question_id, str) or not question_id.strip():
            continue

        if not isinstance(question_text, str) or not question_text.strip():
            continue

        if question_id in seen_ids:
            continue

        signal_key = question.get("signal_key")
        if isinstance(signal_key, str) and signal_key.strip():
            sk = signal_key.strip()
            if sk in seen_signal_keys:
                continue
            seen_signal_keys.add(sk)

        seen_ids.add(question_id)
        unique.append(question)

    return unique


def collect_followup_answers(
    questions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    normalized_questions = _unique_question_objects(questions)
    if not normalized_questions:
        return {}

    print("\nAdditional discovery questions\n")

    followup_answers: dict[str, dict[str, Any]] = {}

    for index, question in enumerate(normalized_questions, start=1):
        print(f"{index}.")
        raw_answer, value, answer_type = _prompt_question_answer(question)
        print()

        if raw_answer == "":
            continue

        question_id = question["id"]
        followup_answers[question_id] = {
            "question": question["question"],
            "answer_type": answer_type,
            "raw_answer": raw_answer,
            "value": value,
            "signal_key": question.get("signal_key"),
        }

    return followup_answers


def apply_followup_answers_to_spec(
    spec: dict[str, Any],
    followup_answers: dict[str, dict[str, Any]],
    additional_questions: list[dict[str, Any]],
) -> dict[str, Any]:
    if not followup_answers and not additional_questions:
        return spec

    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        discovery = {}

    existing_followups = discovery.get("followup_answers", {})
    if not isinstance(existing_followups, dict):
        existing_followups = {}

    merged_followups = dict(existing_followups)
    merged_followups.update(followup_answers)

    discovery["followup_answers"] = merged_followups
    discovery["additional_questions"] = additional_questions
    spec["discovery"] = discovery
    return spec


def run_optional_assisted_discovery(
    spec: dict[str, Any],
    assist: bool = False,
) -> dict[str, Any]:
    if not assist:
        return spec

    first_result = run_assisted_discovery(spec)
    merged_spec = merge_assisted_discovery(spec, first_result)

    question_objects = [
        question.to_dict() for question in first_result.additional_questions
    ]
    followup_answers = collect_followup_answers(question_objects)

    merged_spec = apply_followup_answers_to_spec(
        merged_spec,
        followup_answers,
        question_objects,
    )

    if not followup_answers:
        return merged_spec

    second_result = run_assisted_discovery(merged_spec)
    merged_spec = merge_assisted_discovery(merged_spec, second_result)

    return merged_spec


def run_new_project(spec_path=None, assist: bool = False):
    if spec_path:
        try:
            spec = load_project_spec(spec_path)
        except ValueError as exc:
            print(f"\nError: {exc}\n")
            return 1

        if assist:
            print("Ignoring --assist because --spec was provided.")
    else:
        prompt = prompt_text("Describe the project")
        spec = build_initial_spec(prompt)

        answers = collect_answers()
        spec["answers"] = answers

        spec = run_optional_assisted_discovery(spec, assist=assist)

    spec = derive_capabilities_from_answers(spec)
    spec = apply_capabilities(spec)
    spec = apply_knowledge(spec)
    spec["architecture"] = generate_architecture(spec)
    spec["stories"] = generate_stories(spec)
    spec = refine_spec(spec)
    spec = derive_downstream_artifacts(spec)

    errors = validate_prd(spec)
    if errors:
        print("\nPRD validation errors:\n")
        for error in errors:
            print("-", error)

    missing = check_story_coverage(spec)
    if missing:
        print("\nMissing story coverage for capabilities:\n")
        for item in missing:
            print("-", item)

    output_dir = create_output_dir(spec["answers"]["project_slug"])
    write_json(output_dir / "spec.json", spec)
    write_prd(output_dir / "PRD.md", spec)
    write_architecture(output_dir / "architecture.md", spec)
    write_decisions(output_dir / "decisions.md", spec)
    write_progress(output_dir / "progress.txt")
    write_stories(output_dir, spec)
    write_downstream_artifacts(output_dir, spec)
    write_openclaw_bundle(output_dir, spec)


    print("\nProject generated successfully.\n")
    print(output_dir)
    return 0
