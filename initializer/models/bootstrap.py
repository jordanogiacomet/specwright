from dataclasses import dataclass


@dataclass
class BootstrapInput:

    raw_prompt: str
    project_name: str
    project_slug: str
    project_summary: str

    surface: str
    deploy_target: str

    answers: dict