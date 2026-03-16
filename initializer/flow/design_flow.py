"""Design Flow.

Interactive command for manually defining or editing the project design system.

Usage:
    initializer design <path-to-project>

This command loads an existing spec.json, lets the user interactively
edit colors, spacing, typography, border radius, and component list,
then writes the updated spec and design-system.md back.

The user can:
1. View current design system
2. Edit color palette (primary, background, surface, text, etc.)
3. Edit typography (fonts, sizes)
4. Edit spacing scale
5. Edit border radius scale
6. Add/remove components
7. Save and regenerate design-system.md
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


# -------------------------------------------------------------------
# Display helpers
# -------------------------------------------------------------------

def _show_colors(tokens: dict[str, Any]) -> None:
    colors = tokens.get("colors", {})
    if not colors:
        print("\n  No colors defined.\n")
        return

    print("\n  Color Palette:")
    for key, value in colors.items():
        print(f"    {key:20s} → {value}")
    print()


def _show_typography(tokens: dict[str, Any]) -> None:
    font = tokens.get("font", {})
    font_size = tokens.get("font_size", {})

    print("\n  Typography:")
    if font:
        print("    Fonts:")
        for key, value in font.items():
            print(f"      {key:12s} → {value}")
    if font_size:
        print("    Sizes:")
        for key, value in font_size.items():
            print(f"      {key:12s} → {value}")
    print()


def _show_spacing(tokens: dict[str, Any]) -> None:
    spacing = tokens.get("spacing", {})
    if not spacing:
        print("\n  No spacing scale defined.\n")
        return

    print("\n  Spacing Scale:")
    for key, value in spacing.items():
        print(f"    {key:6s} → {value}")
    print()


def _show_border_radius(tokens: dict[str, Any]) -> None:
    border_radius = tokens.get("border_radius", {})
    if not border_radius:
        print("\n  No border radius scale defined.\n")
        return

    print("\n  Border Radius:")
    for key, value in border_radius.items():
        print(f"    {key:6s} → {value}")
    print()


def _show_components(design_system: dict[str, Any]) -> None:
    components = design_system.get("components", [])
    if not components:
        print("\n  No components defined.\n")
        return

    print(f"\n  Components ({len(components)}):")
    for i, comp in enumerate(components, 1):
        if isinstance(comp, dict):
            name = comp.get("name", "?")
            purpose = comp.get("purpose", "")
            variants = comp.get("variants", [])
            variant_text = f" [{', '.join(variants)}]" if variants else ""
            print(f"    {i:2d}. {name}{variant_text}")
            if purpose:
                print(f"        {purpose}")
        else:
            print(f"    {i:2d}. {comp}")
    print()


def _show_full(design_system: dict[str, Any]) -> None:
    tokens = design_system.get("tokens", {})

    philosophy = design_system.get("philosophy", [])
    if philosophy:
        print("\n  Philosophy:")
        for p in philosophy:
            print(f"    - {p}")

    _show_colors(tokens)
    _show_typography(tokens)
    _show_spacing(tokens)
    _show_border_radius(tokens)
    _show_components(design_system)

    patterns = design_system.get("patterns", [])
    if patterns:
        print(f"  UX Patterns ({len(patterns)}):")
        for p in patterns:
            print(f"    - {p}")
        print()

    recommendations = design_system.get("recommendations", [])
    if recommendations:
        print(f"  Recommendations ({len(recommendations)}):")
        for r in recommendations:
            print(f"    - {r}")
        print()


# -------------------------------------------------------------------
# Edit operations
# -------------------------------------------------------------------

def _edit_colors(tokens: dict[str, Any]) -> None:
    colors = tokens.setdefault("colors", {})

    print("\n  Edit colors. For each color, enter new value or press Enter to keep current.")
    print("  Use Tailwind color names (e.g., blue-600, indigo-500) or hex (#2563EB).")
    print("  Type 'add' to add a new color, 'remove' to remove one, 'done' to finish.\n")

    # Show and edit existing colors
    for key in list(colors.keys()):
        current = colors[key]
        new_value = _prompt(f"{key}", current)
        if new_value != current:
            colors[key] = new_value

    # Add/remove loop
    while True:
        action = input("\n  [add/remove/done]: ").strip().lower()

        if action == "done" or action == "":
            break

        if action == "add":
            name = _prompt("Color name (e.g., accent, warning_light)")
            if not name:
                continue
            value = _prompt(f"Value for {name}")
            if value:
                colors[name] = value
                print(f"  ✅ Added: {name} → {value}")

        elif action == "remove":
            name = _prompt("Color name to remove")
            if name in colors:
                del colors[name]
                print(f"  ✅ Removed: {name}")
            else:
                print(f"  Not found: {name}")

    tokens["colors"] = colors
    print("  ✅ Colors updated.")


def _edit_typography(tokens: dict[str, Any]) -> None:
    font = tokens.setdefault("font", {})
    font_size = tokens.setdefault("font_size", {})

    print("\n  Edit typography. Enter new value or press Enter to keep current.\n")

    print("  Fonts:")
    for key in list(font.keys()):
        current = font[key]
        new_value = _prompt(f"  {key}", current)
        if new_value != current:
            font[key] = new_value

    add_font = _prompt("\n  Add custom font? (name or Enter to skip)")
    if add_font:
        font_key = _prompt("  Font key (e.g., display, accent)")
        if font_key:
            font[font_key] = add_font
            print(f"  ✅ Added font: {font_key} → {add_font}")

    print("\n  Font sizes:")
    for key in list(font_size.keys()):
        current = font_size[key]
        new_value = _prompt(f"  {key}", current)
        if new_value != current:
            font_size[key] = new_value

    tokens["font"] = font
    tokens["font_size"] = font_size
    print("  ✅ Typography updated.")


def _edit_spacing(tokens: dict[str, Any]) -> None:
    spacing = tokens.setdefault("spacing", {})

    print("\n  Edit spacing scale. Enter new value or press Enter to keep current.\n")

    for key in list(spacing.keys()):
        current = spacing[key]
        new_value = _prompt(f"{key}", current)
        if new_value != current:
            spacing[key] = new_value

    print("\n  Add custom spacing? (Enter key like '3xl', or empty to skip)")
    while True:
        key = input("    Key: ").strip()
        if not key:
            break
        value = _prompt(f"  Value for {key}")
        if value:
            spacing[key] = value
            print(f"  ✅ Added: {key} → {value}")

    tokens["spacing"] = spacing
    print("  ✅ Spacing updated.")


def _edit_border_radius(tokens: dict[str, Any]) -> None:
    border_radius = tokens.setdefault("border_radius", {})

    print("\n  Edit border radius. Enter new value or press Enter to keep current.\n")

    for key in list(border_radius.keys()):
        current = border_radius[key]
        new_value = _prompt(f"{key}", current)
        if new_value != current:
            border_radius[key] = new_value

    tokens["border_radius"] = border_radius
    print("  ✅ Border radius updated.")


def _add_component(design_system: dict[str, Any]) -> None:
    components = design_system.setdefault("components", [])

    print("\n  Add a component:")
    name = _prompt("Name (e.g., Accordion, Tabs, Badge)")
    if not name:
        print("  Cancelled.")
        return

    # Check if exists
    for comp in components:
        existing_name = comp.get("name") if isinstance(comp, dict) else comp
        if existing_name == name:
            print(f"  Component '{name}' already exists.")
            return

    purpose = _prompt("Purpose (e.g., Collapsible content sections)")
    variants_raw = _prompt("Variants (comma-separated, e.g., sm,md,lg)", "")
    variants = [v.strip() for v in variants_raw.split(",") if v.strip()] if variants_raw else []

    comp: dict[str, Any] = {"name": name}
    if purpose:
        comp["purpose"] = purpose
    if variants:
        comp["variants"] = variants

    components.append(comp)
    print(f"  ✅ Added: {name}")


def _remove_component(design_system: dict[str, Any]) -> None:
    _show_components(design_system)
    components = design_system.get("components", [])
    if not components:
        return

    raw = input("  Remove component # (or name): ").strip()
    if not raw:
        return

    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(components):
            comp = components.pop(idx)
            name = comp.get("name") if isinstance(comp, dict) else comp
            print(f"  ✅ Removed: {name}")
            return
    else:
        for i, comp in enumerate(components):
            comp_name = comp.get("name") if isinstance(comp, dict) else comp
            if comp_name == raw:
                components.pop(i)
                print(f"  ✅ Removed: {raw}")
                return

    print("  Not found.")


def _edit_philosophy(design_system: dict[str, Any]) -> None:
    philosophy = design_system.setdefault("philosophy", [])

    print("\n  Current philosophy:")
    for i, p in enumerate(philosophy, 1):
        print(f"    {i}. {p}")

    print("\n  Add a principle (empty to finish):")
    while True:
        principle = input("    + ").strip()
        if not principle:
            break
        if principle not in philosophy:
            philosophy.append(principle)

    print("\n  Remove a principle? Enter # or press Enter to skip:")
    while True:
        raw = input("    - ").strip()
        if not raw:
            break
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(philosophy):
                removed = philosophy.pop(idx)
                print(f"  ✅ Removed: {removed[:50]}...")

    design_system["philosophy"] = philosophy
    print("  ✅ Philosophy updated.")


# -------------------------------------------------------------------
# Presets
# -------------------------------------------------------------------

_COLOR_PRESETS = {
    "corporate": {
        "primary": "blue-700",
        "primary_hover": "blue-800",
        "background": "gray-50",
        "surface": "white",
        "text": "gray-900",
        "text_secondary": "gray-600",
        "muted": "gray-500",
        "border": "gray-200",
        "destructive": "red-700",
        "success": "green-700",
        "warning": "amber-600",
        "info": "blue-600",
        "focus_ring": "blue-700/50",
    },
    "modern": {
        "primary": "violet-600",
        "primary_hover": "violet-700",
        "background": "slate-50",
        "surface": "white",
        "text": "slate-900",
        "text_secondary": "slate-500",
        "muted": "slate-400",
        "border": "slate-200",
        "destructive": "rose-600",
        "success": "emerald-500",
        "warning": "amber-500",
        "info": "sky-500",
        "focus_ring": "violet-500/50",
    },
    "warm": {
        "primary": "orange-600",
        "primary_hover": "orange-700",
        "background": "stone-50",
        "surface": "white",
        "text": "stone-900",
        "text_secondary": "stone-600",
        "muted": "stone-400",
        "border": "stone-200",
        "destructive": "red-600",
        "success": "green-600",
        "warning": "yellow-500",
        "info": "blue-500",
        "focus_ring": "orange-500/50",
    },
    "dark": {
        "primary": "indigo-400",
        "primary_hover": "indigo-300",
        "background": "gray-950",
        "surface": "gray-900",
        "text": "gray-100",
        "text_secondary": "gray-400",
        "muted": "gray-500",
        "border": "gray-800",
        "destructive": "red-400",
        "success": "green-400",
        "warning": "amber-400",
        "info": "sky-400",
        "focus_ring": "indigo-400/50",
    },
    "minimal": {
        "primary": "gray-900",
        "primary_hover": "gray-800",
        "background": "white",
        "surface": "white",
        "text": "gray-900",
        "text_secondary": "gray-500",
        "muted": "gray-400",
        "border": "gray-200",
        "destructive": "red-600",
        "success": "green-600",
        "warning": "amber-500",
        "info": "blue-500",
        "focus_ring": "gray-900/30",
    },
}


def _apply_preset(tokens: dict[str, Any]) -> None:
    print("\n  Available color presets:")
    presets = list(_COLOR_PRESETS.keys())
    for i, name in enumerate(presets, 1):
        colors = _COLOR_PRESETS[name]
        print(f"    {i}. {name:12s} — primary: {colors['primary']}, bg: {colors['background']}")

    raw = input(f"\n  Choose preset [1-{len(presets)}]: ").strip()

    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(presets):
            preset_name = presets[idx]
            tokens["colors"] = dict(_COLOR_PRESETS[preset_name])
            print(f"  ✅ Applied '{preset_name}' color preset.")
            return

    if raw in _COLOR_PRESETS:
        tokens["colors"] = dict(_COLOR_PRESETS[raw])
        print(f"  ✅ Applied '{raw}' color preset.")
        return

    print("  Invalid choice.")


# -------------------------------------------------------------------
# Write design-system.md
# -------------------------------------------------------------------

def _write_design_system_md(project_dir: Path, design_system: dict[str, Any]) -> None:
    """Regenerate design-system.md from the current design system."""
    from initializer.renderers.design_system_renderer import write_design_system
    write_design_system(project_dir, design_system)


# -------------------------------------------------------------------
# Main command
# -------------------------------------------------------------------

def run_design(project_path: str) -> int:
    """Interactive design system editor."""
    try:
        project_dir, spec = _load_spec(project_path)
    except ValueError as exc:
        print(f"\nError: {exc}\n")
        return 1

    design_system = spec.setdefault("design_system", {})
    tokens = design_system.setdefault("tokens", {})
    project_name = spec.get("answers", {}).get("project_name", "Project")

    print(f"\n{'=' * 60}")
    print(f"  🎨 Design System Editor — {project_name}")
    print(f"{'=' * 60}")

    while True:
        print("\n  What do you want to do?")
        print("     1. View full design system")
        print("     2. Edit colors")
        print("     3. Apply color preset (corporate, modern, warm, dark, minimal)")
        print("     4. Edit typography (fonts, sizes)")
        print("     5. Edit spacing scale")
        print("     6. Edit border radius")
        print("     7. Add component")
        print("     8. Remove component")
        print("     9. Edit design philosophy")
        print("    10. Save and exit")
        print("     0. Exit without saving")

        choice = input("\n  > ").strip()

        if choice == "1":
            _show_full(design_system)

        elif choice == "2":
            _edit_colors(tokens)

        elif choice == "3":
            _apply_preset(tokens)

        elif choice == "4":
            _edit_typography(tokens)

        elif choice == "5":
            _edit_spacing(tokens)

        elif choice == "6":
            _edit_border_radius(tokens)

        elif choice == "7":
            _add_component(design_system)

        elif choice == "8":
            _remove_component(design_system)

        elif choice == "9":
            _edit_philosophy(design_system)

        elif choice == "10":
            spec["design_system"] = design_system
            _save_spec(project_dir, spec)
            _write_design_system_md(project_dir, design_system)
            print(f"\n  ✅ Design system saved to {project_dir}/spec.json")
            print(f"  ✅ docs/design-system.md regenerated.\n")
            return 0

        elif choice == "0":
            print("\n  Exiting without saving.\n")
            return 0

        else:
            print("  Invalid choice.")

    return 0