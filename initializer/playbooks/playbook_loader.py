from pathlib import Path
import yaml

from initializer.engine.archetype_engine import canonical_archetype_id

PLAYBOOK_DIR = Path("playbooks")


def load_playbook(archetype: str):

    path = PLAYBOOK_DIR / f"{canonical_archetype_id(archetype)}.yaml"

    if not path.exists():
        raise ValueError(f"Playbook not found: {canonical_archetype_id(archetype)}")

    with open(path) as f:
        data = yaml.safe_load(f)

    return data
