from pathlib import Path


def check_file(path: Path, label: str, errors: list[str]) -> None:
    if path.exists():
        print(f"✓ {label}")
    else:
        print(f"✗ {label} missing")
        errors.append(label)


def check_directory(path: Path, label: str, errors: list[str]) -> None:
    if path.exists() and path.is_dir():
        print(f"✓ {label}")
    else:
        print(f"✗ {label} missing")
        errors.append(label)


def run_doctor_project(path: str) -> int:

    root = Path(path).resolve()

    print()
    print("Initializer Doctor")
    print("------------------")
    print(f"Checking project: {root}")
    print()

    errors: list[str] = []

    check_file(root / "spec.json", "spec.json", errors)
    check_file(root / "PRD.md", "PRD.md", errors)
    check_file(root / "decisions.md", "decisions.md", errors)
    check_file(root / "progress.txt", "progress.txt", errors)
    check_file(root / "README.md", "README.md", errors)

    check_directory(root / "docs/stories", "docs/stories/", errors)
    check_file(root / ".codex" / "AGENTS.md", ".codex/AGENTS.md", errors)
    check_file(root / ".openclaw" / "AGENTS.md", ".openclaw/AGENTS.md", errors)
    check_file(root / ".openclaw" / "execution-plan.json", ".openclaw/execution-plan.json", errors)
    check_file(root / ".openclaw" / "commands.json", ".openclaw/commands.json", errors)

    if errors:
        print()
        print("Problems detected:")
        for e in errors:
            print(f" - {e}")
        print()
        print("Doctor result: FAIL")
        return 1

    print()
    print("Doctor result: OK")
    print("Project structure looks healthy.")
    print()

    return 0
