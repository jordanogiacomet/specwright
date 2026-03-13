import json
from pathlib import Path


def load_semantic_spec(project_dir):

    path = Path(project_dir) / "semantic-spec.json"

    if not path.exists():
        raise FileNotFoundError("semantic-spec.json not found")

    with open(path) as f:
        return json.load(f)