from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent


@dataclass
class BootstrapInput:
    raw_prompt: str
    project_name: str
    project_slug: str
    project_summary: str
    product_surface: str
    stack_confirmation: bool
    deploy_target: str
    collections: list[str]
    globals_: list[str]
    media_types: list[str]
    roles: list[str]
    internal_users_only: bool
    end_user_auth: bool
    public_signup: bool
    storage_backend: str
    draft_publish: bool
    preview: bool
    scheduled_publishing: bool
    approval_workflow: bool
    multi_tenancy: bool
    audit_logging: bool
    background_jobs: bool
    i18n: bool
    system_constraints: str
    scalability_expectations: str
    non_functional_constraints: str
    output_directory: str


# -----------------------------------------------------
# helpers
# -----------------------------------------------------


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "project"


# -----------------------------------------------------
# semantic spec loading
# -----------------------------------------------------


def load_semantic_spec(path: str) -> BootstrapInput:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return BootstrapInput(**data)


# -----------------------------------------------------
# prompts
# -----------------------------------------------------


def prompt_text(label: str, default: str | None = None, required: bool = True) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value and default is not None:
            return default
        if value or not required:
            return value
        print("This field is required.")


def prompt_yes_no(label: str, default: bool = True) -> bool:
    default_label = "Y/n" if default else "y/N"
    while True:
        value = input(f"{label} [{default_label}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def prompt_choice(label: str, options: list[str], default: str | None = None) -> str:
    print(label)

    for idx, option in enumerate(options, start=1):
        marker = " (default)" if option == default else ""
        print(f"  {idx}. {option}{marker}")

    while True:
        raw = input("> ").strip()

        if not raw and default is not None:
            return default

        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]

        if raw in options:
            return raw

        print("Choose one of the listed options.")


def prompt_list(label: str, default: list[str] | None = None) -> list[str]:
    default_str = ", ".join(default or [])
    raw = prompt_text(label, default=default_str, required=False)
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items


# -----------------------------------------------------
# archetype detection
# -----------------------------------------------------


def detect_archetype(prompt: str) -> str:
    lowered = prompt.lower()
    signals = ["next", "next.js", "payload", "postgres", "postgresql"]

    score = sum(1 for signal in signals if signal in lowered)

    return "next-payload-postgres" if score >= 2 else "unknown"


# -----------------------------------------------------
# filesystem
# -----------------------------------------------------


def create_directories(root: Path) -> None:
    directories = [
        "src/app",
        "src/payload/collections",
        "src/payload/globals",
        "public",
        "docs/stories",
        "docs/architecture",
    ]

    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


# -----------------------------------------------------
# renderers
# -----------------------------------------------------


def render_prd(data: BootstrapInput) -> str:
    return dedent(
        f"""
        # PRD.md

        ## Product name

        **{data.project_name}**

        ---

        ## Version

        `0.1`

        ---

        ## Status

        `bootstrap-generated`

        ---

        ## Product summary

        {data.project_summary}

        ---

        ## Stack

        - Next.js
        - Payload
        - PostgreSQL

        ---

        ## Product surface

        `{data.product_surface}`

        ---

        ## Initial deploy target

        `{data.deploy_target}`

        ---
        """
    ).strip()


def render_decisions(data: BootstrapInput) -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    return dedent(
        f"""
        # decisions.md

        ### DEC-001
        - Date: {today}
        - Decision: Archetype is Next.js + Payload + PostgreSQL
        - Reason: Generated from V0 initializer

        ### DEC-002
        - Date: {today}
        - Decision: Deploy target `{data.deploy_target}`
        """
    ).strip()


def render_progress(data: BootstrapInput) -> str:
    now = utc_now()

    return dedent(
        f"""
        # progress.txt — {data.project_name}

        [{now}] INFO — Bootstrap generated
        [{now}] INFO — Slug: {data.project_slug}
        [{now}] INFO — Review required before implementation
        """
    ).strip()


def render_agents() -> str:
    return dedent(
        """
        # AGENTS.md

        Read order:

        1. PRD.md
        2. decisions.md
        3. progress.txt
        4. docs/stories/

        Rules:

        - work one story at a time
        - validate changes
        - do not silently change architecture
        """
    ).strip()


def render_readme(data: BootstrapInput) -> str:
    return dedent(
        f"""
        # {data.project_name}

        Bootstrap generated by initializer.

        Stack:

        - Next.js
        - Payload
        - PostgreSQL
        """
    ).strip()


# -----------------------------------------------------
# bootstrap writing
# -----------------------------------------------------


def write_bootstrap_files(root: Path, data: BootstrapInput) -> None:

    write_file(root / "PRD.md", render_prd(data))
    write_file(root / "decisions.md", render_decisions(data))
    write_file(root / "progress.txt", render_progress(data))
    write_file(root / "AGENTS.md", render_agents())
    write_file(root / "README.md", render_readme(data))

    write_file(
        root / "docs/stories/ST-001-review-bootstrap.md",
        "# ST-001\n\nReview generated bootstrap and approve implementation start.",
    )

    write_file(
        root / "prd.json",
        json.dumps(asdict(data), indent=2, ensure_ascii=False),
    )


# -----------------------------------------------------
# interactive input
# -----------------------------------------------------


def collect_input() -> BootstrapInput:

    raw_prompt = prompt_text("Describe the project")

    project_name = prompt_text("Project name")

    project_slug = prompt_text(
        "Project slug",
        default=slugify(project_name),
    )

    project_summary = prompt_text("One sentence summary")

    product_surface = prompt_choice(
        "Choose product surface",
        ["internal_admin_only", "admin_plus_public_site"],
        default="admin_plus_public_site",
    )

    deploy_target = prompt_choice(
        "Choose deploy target",
        ["docker", "docker_and_k8s_later"],
        default="docker",
    )

    return BootstrapInput(
        raw_prompt=raw_prompt,
        project_name=project_name,
        project_slug=project_slug,
        project_summary=project_summary,
        product_surface=product_surface,
        stack_confirmation=True,
        deploy_target=deploy_target,
        collections=[],
        globals_=[],
        media_types=[],
        roles=[],
        internal_users_only=True,
        end_user_auth=False,
        public_signup=False,
        storage_backend="local_first",
        draft_publish=True,
        preview=True,
        scheduled_publishing=False,
        approval_workflow=False,
        multi_tenancy=False,
        audit_logging=True,
        background_jobs=False,
        i18n=False,
        system_constraints="",
        scalability_expectations="",
        non_functional_constraints="",
        output_directory=f"./output/{project_slug}",
    )


# -----------------------------------------------------
# main
# -----------------------------------------------------


def run_new_project(spec_path: str | None = None) -> int:

    if spec_path:
        print("Loading semantic spec...")
        data = load_semantic_spec(spec_path)
    else:
        data = collect_input()

    output_dir = Path(data.output_directory).resolve()

    if output_dir.exists():
        print("Output directory already exists.")
        return 1

    create_directories(output_dir)

    write_bootstrap_files(output_dir, data)

    print("Bootstrap generated successfully.")
    print(output_dir)

    return 0