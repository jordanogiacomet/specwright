import json
from pathlib import Path

import jsonschema

from initializer.validation.prd_validator import validate_prd
from initializer.validation.story_coverage import check_story_coverage


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_schema(data, schema):
    jsonschema.validate(instance=data, schema=schema)


def find_existing_path(root: Path, filenames: list[str]) -> Path | None:
    for filename in filenames:
        path = root / filename

        if path.exists():
            return path

    return None


def find_semantic_schema_path(root: Path) -> Path | None:
    candidates = [
        root / "schemas" / "semantic-spec.schema.json",
        Path(__file__).resolve().parents[2] / "schemas" / "semantic-spec.schema.json",
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def validate_current_spec(root: Path, errors: list[str]) -> bool:
    spec_path = root / "spec.json"

    if not spec_path.exists():
        return False

    print("Checking spec.json")

    try:
        spec = load_json(spec_path)
        spec_errors = validate_prd(spec)
        coverage_errors = check_story_coverage(spec)

        if spec_errors or coverage_errors:
            print("✗ spec.json invalid")

            for error in spec_errors:
                print(" -", error)

            for capability in coverage_errors:
                print(f" - Missing story coverage for capability: {capability}")

            errors.append("spec")
        else:
            print("✓ spec.json valid")

    except Exception as e:
        print("✗ spec.json invalid")
        print(e)
        errors.append("spec")

    return True


def validate_semantic_spec(root: Path, errors: list[str]) -> bool:
    semantic_spec_path = find_existing_path(
        root,
        ["semantic-spec.json", "semantic_spec.json"],
    )

    if semantic_spec_path is None:
        return False

    print(f"Checking {semantic_spec_path.name}")

    try:
        spec = load_json(semantic_spec_path)
        schema_path = find_semantic_schema_path(root)

        if schema_path is not None:
            schema = load_json(schema_path)
            validate_schema(spec, schema)
            print(f"✓ {semantic_spec_path.name} valid")
        else:
            print("⚠ semantic-spec.schema.json not found")

    except Exception as e:
        print(f"✗ {semantic_spec_path.name} invalid")
        print(e)
        errors.append("semantic_spec")

    return True


def run_validate_project(path: str) -> int:

    root = Path(path).resolve()

    print()
    print("Initializer Validate")
    print("--------------------")
    print(f"Checking: {root}")
    print()

    errors = []
    checked_any = False

    if validate_current_spec(root, errors):
        checked_any = True
    elif validate_semantic_spec(root, errors):
        checked_any = True

    prd_json_path = root / "prd.json"

    if prd_json_path.exists():
        checked_any = True

        print("Checking prd.json")

        try:
            load_json(prd_json_path)
            print("✓ prd.json valid JSON")

        except Exception as e:
            print("✗ prd.json invalid")
            print(e)
            errors.append("prd_json")

    if not checked_any:
        print("⚠ No known spec artifact found")
        errors.append("artifacts")

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
