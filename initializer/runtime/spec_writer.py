import json
from pathlib import Path


def write_spec(spec, output_dir):

    path = Path(output_dir) / "semantic-spec.json"

    with open(path, "w") as f:
        json.dump(spec, f, indent=2)