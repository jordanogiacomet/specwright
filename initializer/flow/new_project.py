from pathlib import Path
import json
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
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


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

    with open(path, "w") as f:
        f.write(content)


def write_architecture(path, spec):
    arch = spec["architecture"]
    content = "# Architecture\n\n"

    for component in arch["components"]:
        content += f"### {component['name']}\n"
        content += f"Technology: {component['technology']}\n"
        content += f"Role: {component['role']}\n\n"

    with open(path, "w") as f:
        f.write(content)


def write_stories(path, spec):
    stories_dir = path / "stories"
    stories_dir.mkdir(exist_ok=True)

    for story in spec["stories"]:
        file = stories_dir / f"{story['id']}.md"
        content = f"""
# {story['id']} — {story['title']}

## Description

{story['description']}
"""
        with open(file, "w") as f:
            f.write(content)


def write_downstream_artifacts(path, spec):
    write_constraints(path, spec["constraints"])
    write_design_system(path, spec["design_system"])
    write_risks(path, spec["risks"])
    write_architecture_diagram(path, spec["diagram"])


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
    seen = set()
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

        if question_id in seen:
            continue

        seen.add(question_id)
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

    question_objects = [question.to_dict() for question in first_result.additional_questions]
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
    write_stories(output_dir, spec)
    write_downstream_artifacts(output_dir, spec)

    print("\nProject generated successfully.\n")
    print(output_dir)