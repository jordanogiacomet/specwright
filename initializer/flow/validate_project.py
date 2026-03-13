import json
from pathlib import Path

import jsonschema


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data, schema):
    jsonschema.validate(instance=data, schema=schema)


def run_validate_project(path: str) -> int:

    root = Path(path).resolve()

    print()
    print("Initializer Validate")
    print("--------------------")
    print(f"Checking: {root}")
    print()

    errors = []

    schema_dir = root / "schemas"

    semantic_schema_path = schema_dir / "semantic-spec.schema.json"

    semantic_spec_path = root / "semantic_spec.json"

    if semantic_spec_path.exists():

        print("Checking semantic_spec.json")

        try:
            spec = load_json(semantic_spec_path)

            if semantic_schema_path.exists():

                schema = load_json(semantic_schema_path)

                validate_schema(spec, schema)

                print("✓ semantic_spec.json valid")

            else:
                print("⚠ semantic-spec.schema.json not found")

        except Exception as e:
            print("✗ semantic_spec.json invalid")
            print(e)
            errors.append("semantic_spec")

    else:
        print("⚠ semantic_spec.json not found")

    prd_json_path = root / "prd.json"

    if prd_json_path.exists():

        print("Checking prd.json")

        try:
            load_json(prd_json_path)
            print("✓ prd.json valid JSON")

        except Exception as e:
            print("✗ prd.json invalid")
            print(e)
            errors.append("prd_json")

    else:
        print("⚠ prd.json not found")

    if errors:

        print()
        print("Validation failed:")
        for e in errors:
            print(" -", e)

        print()
        return 1

    print()
    print("Validation OK")
    print()

    return 0