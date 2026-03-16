"""Architect Flow.

Interactive command for manually defining or editing the project architecture.

Usage:
    initializer architect <path-to-project>

This command loads an existing spec.json, lets the user interactively
add/remove/edit components, communication contracts, and boundaries,
then writes the updated spec and architecture.md back.

The user can:
1. Add/remove/edit components (name, technology, role)
2. Add/remove communication contracts (from, to, protocol, pattern)
3. Edit responsibility boundaries (frontend, backend, shared)
4. Add/remove architectural decisions
5. Save and regenerate architecture.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_spec(project_path: str) -> tuple[Path, dict[str, Any]]:
    """Load spec.json from a project directory."""
    path = Path(project_path).expanduser()
    if path.is_dir():
        spec_file = path / "spec.json"
    else:
        spec_file = path

    if not spec_file.exists():
        raise ValueError(f"spec.json not found at {spec_file}")

    data = json.loads(spec_file.read_text(encoding="utf-8"))
    return spec_file.parent, data


def _save_spec(project_dir: Path, spec: dict[str, Any]) -> None:
    """Save spec.json back to the project directory."""
    spec_file = project_dir / "spec.json"
    spec_file.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"  {label}{suffix}: ").strip()
    return value or default


def _show_components(architecture: dict[str, Any]) -> None:
    components = architecture.get("components", [])
    if not components:
        print("\n  No components defined.\n")
        return

    print(f"\n  Components ({len(components)}):")
    for i, comp in enumerate(components, 1):
        name = comp.get("name", "?")
        tech = comp.get("technology", "?")
        role = comp.get("role", "?")
        print(f"    {i}. {name} ({tech}) — {role}")
    print()


def _show_communication(architecture: dict[str, Any]) -> None:
    comms = architecture.get("communication", [])
    if not comms:
        print("\n  No communication contracts defined.\n")
        return

    print(f"\n  Communication contracts ({len(comms)}):")
    for i, contract in enumerate(comms, 1):
        source = contract.get("from", "?")
        target = contract.get("to", "?")
        protocol = contract.get("protocol", "?")
        pattern = contract.get("pattern", "")
        print(f"    {i}. {source} → {target} [{protocol}] {pattern}")
    print()


def _show_boundaries(architecture: dict[str, Any]) -> None:
    boundaries = architecture.get("boundaries", {})
    if not boundaries:
        print("\n  No boundaries defined.\n")
        return

    print("\n  Responsibility Boundaries:")
    for layer, items in boundaries.items():
        if items:
            print(f"    {layer}:")
            for item in items:
                print(f"      - {item}")
    print()


def _show_decisions(architecture: dict[str, Any]) -> None:
    decisions = architecture.get("decisions", [])
    if not decisions:
        print("\n  No architectural decisions.\n")
        return

    print(f"\n  Architectural Decisions ({len(decisions)}):")
    for i, d in enumerate(decisions, 1):
        print(f"    {i}. {d}")
    print()


def _add_component(architecture: dict[str, Any]) -> None:
    print("\n  Add a new component:")
    name = _prompt("Name (e.g., redis, queue, cdn)")
    if not name:
        print("  Cancelled.")
        return

    technology = _prompt("Technology (e.g., redis, bullmq, cloudflare)")
    role = _prompt("Role (e.g., caching, job queue, edge delivery)")

    components = architecture.setdefault("components", [])

    # Check for existing by name
    for existing in components:
        if existing.get("name") == name:
            print(f"  Component '{name}' already exists. Updating.")
            existing["technology"] = technology or existing.get("technology", "")
            existing["role"] = role or existing.get("role", "")
            return

    components.append({"name": name, "technology": technology, "role": role})
    print(f"  ✅ Added component: {name}")


def _remove_component(architecture: dict[str, Any]) -> None:
    _show_components(architecture)
    components = architecture.get("components", [])
    if not components:
        return

    raw = input("  Remove component # (or name): ").strip()
    if not raw:
        return

    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(components):
            removed = components.pop(idx)
            print(f"  ✅ Removed: {removed.get('name')}")
            return
    else:
        for i, comp in enumerate(components):
            if comp.get("name") == raw:
                components.pop(i)
                print(f"  ✅ Removed: {raw}")
                return

    print("  Not found.")


def _add_communication(architecture: dict[str, Any]) -> None:
    component_names = [c.get("name", "") for c in architecture.get("components", [])]
    if len(component_names) < 2:
        print("  Need at least 2 components to define communication.")
        return

    print(f"\n  Available components: {', '.join(component_names)}")
    source = _prompt("From")
    target = _prompt("To")
    protocol = _prompt("Protocol (http, tcp, amqp, etc.)", "http")
    pattern = _prompt("Pattern (e.g., REST API, message queue, connection pool)")
    auth = _prompt("Auth (optional, e.g., JWT bearer token)", "")

    contract: dict[str, str] = {
        "from": source,
        "to": target,
        "protocol": protocol,
        "pattern": pattern,
    }
    if auth:
        contract["auth"] = auth

    comms = architecture.setdefault("communication", [])
    comms.append(contract)
    print(f"  ✅ Added: {source} → {target}")


def _remove_communication(architecture: dict[str, Any]) -> None:
    _show_communication(architecture)
    comms = architecture.get("communication", [])
    if not comms:
        return

    raw = input("  Remove contract #: ").strip()
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(comms):
            removed = comms.pop(idx)
            print(f"  ✅ Removed: {removed.get('from')} → {removed.get('to')}")
            return

    print("  Not found.")


def _edit_boundaries(architecture: dict[str, Any]) -> None:
    boundaries = architecture.setdefault("boundaries", {"frontend": [], "backend": [], "shared": []})

    print("\n  Edit boundaries. Enter one responsibility per line.")
    print("  Empty line finishes a section.\n")

    for layer in ("frontend", "backend", "shared"):
        current = boundaries.get(layer, [])
        print(f"  {layer} (current: {len(current)} items):")
        for item in current:
            print(f"    - {item}")

        print(f"\n  Add to {layer} (empty to skip):")
        while True:
            item = input("    + ").strip()
            if not item:
                break
            if item not in current:
                current.append(item)

        boundaries[layer] = current

    architecture["boundaries"] = boundaries
    print("  ✅ Boundaries updated.")


def _add_decision(architecture: dict[str, Any]) -> None:
    decision = _prompt("New architectural decision")
    if not decision:
        return

    decisions = architecture.setdefault("decisions", [])
    if decision not in decisions:
        decisions.append(decision)
        print("  ✅ Decision added.")
    else:
        print("  Already exists.")


def _remove_decision(architecture: dict[str, Any]) -> None:
    _show_decisions(architecture)
    decisions = architecture.get("decisions", [])
    if not decisions:
        return

    raw = input("  Remove decision #: ").strip()
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(decisions):
            removed = decisions.pop(idx)
            print(f"  ✅ Removed: {removed[:60]}...")
            return

    print("  Not found.")


def _write_architecture_md(project_dir: Path, spec: dict[str, Any]) -> None:
    """Regenerate architecture.md from the current spec."""
    # Import here to avoid circular imports
    from initializer.flow.new_project import write_architecture
    write_architecture(project_dir / "architecture.md", spec)


def run_architect(project_path: str) -> int:
    """Interactive architecture editor."""
    try:
        project_dir, spec = _load_spec(project_path)
    except ValueError as exc:
        print(f"\nError: {exc}\n")
        return 1

    architecture = spec.setdefault("architecture", {})
    project_name = spec.get("answers", {}).get("project_name", "Project")

    print(f"\n{'=' * 60}")
    print(f"  🏗️  Architecture Editor — {project_name}")
    print(f"{'=' * 60}")

    while True:
        print("\n  What do you want to do?")
        print("    1. View current architecture")
        print("    2. Add component")
        print("    3. Remove component")
        print("    4. Add communication contract")
        print("    5. Remove communication contract")
        print("    6. Edit boundaries")
        print("    7. Add architectural decision")
        print("    8. Remove architectural decision")
        print("    9. Save and exit")
        print("    0. Exit without saving")

        choice = input("\n  > ").strip()

        if choice == "1":
            _show_components(architecture)
            _show_communication(architecture)
            _show_boundaries(architecture)
            _show_decisions(architecture)

        elif choice == "2":
            _add_component(architecture)

        elif choice == "3":
            _remove_component(architecture)

        elif choice == "4":
            _add_communication(architecture)

        elif choice == "5":
            _remove_communication(architecture)

        elif choice == "6":
            _edit_boundaries(architecture)

        elif choice == "7":
            _add_decision(architecture)

        elif choice == "8":
            _remove_decision(architecture)

        elif choice == "9":
            spec["architecture"] = architecture
            _save_spec(project_dir, spec)
            _write_architecture_md(project_dir, spec)
            print(f"\n  ✅ Architecture saved to {project_dir}/spec.json")
            print(f"  ✅ architecture.md regenerated.\n")
            return 0

        elif choice == "0":
            print("\n  Exiting without saving.\n")
            return 0

        else:
            print("  Invalid choice.")

    return 0