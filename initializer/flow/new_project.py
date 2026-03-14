from pathlib import Path
import json

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

    for i, o in enumerate(options, start=1):

        if o == default:
            print(f" {i}. {o} (default)")
        else:
            print(f" {i}. {o}")

    value = input("> ").strip()

    if not value and default:
        return default

    idx = int(value) - 1

    return options[idx]


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

    for f in spec["features"]:
        content += f"- {f}\n"

    content += "\n## Architecture Decisions\n"

    for d in spec["architecture"]["decisions"]:
        content += f"- {d}\n"

    with open(path, "w") as f:
        f.write(content)


def write_architecture(path, spec):

    arch = spec["architecture"]

    content = "# Architecture\n\n"

    for c in arch["components"]:

        content += f"### {c['name']}\n"
        content += f"Technology: {c['technology']}\n"
        content += f"Role: {c['role']}\n\n"

    with open(path, "w") as f:
        f.write(content)


def write_stories(path, spec):

    stories_dir = path / "stories"

    stories_dir.mkdir(exist_ok=True)

    for s in spec["stories"]:

        file = stories_dir / f"{s['id']}.md"

        content = f"""
# {s['id']} — {s['title']}

## Description

{s['description']}
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
        project_name.lower().replace(" ", "-")
    )

    summary = prompt_text("One sentence summary")

    surface = prompt_choice(
        "Choose product surface",
        ["internal_admin_only", "admin_plus_public_site"],
        "admin_plus_public_site"
    )

    deploy_target = prompt_choice(
        "Choose deploy target",
        ["docker", "docker_and_k8s_later"],
        "docker"
    )

    return {
        "project_name": project_name,
        "project_slug": project_slug,
        "summary": summary,
        "surface": surface,
        "deploy_target": deploy_target
    }


def run_new_project(spec_path=None):

    prompt = prompt_text("Describe the project")

    spec = build_initial_spec(prompt)

    answers = collect_answers()

    spec["answers"] = answers

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

        for e in errors:
            print("-", e)

    missing = check_story_coverage(spec)

    if missing:

        print("\nMissing story coverage for capabilities:\n")

        for m in missing:
            print("-", m)

    output_dir = create_output_dir(answers["project_slug"])

    write_json(output_dir / "spec.json", spec)

    write_prd(output_dir / "PRD.md", spec)

    write_architecture(output_dir / "architecture.md", spec)

    write_stories(output_dir, spec)

    write_downstream_artifacts(output_dir, spec)

    print("\nProject generated successfully.\n")

    print(output_dir)
