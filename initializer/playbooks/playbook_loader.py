from pathlib import Path
import yaml

PLAYBOOK_DIR = Path("playbooks")


def load_playbook(archetype: str):

    path = PLAYBOOK_DIR / f"{archetype}.yaml"

    if not path.exists():
        raise ValueError(f"Playbook not found: {archetype}")

    with open(path) as f:
        data = yaml.safe_load(f)

    return data