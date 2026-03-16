"""Design Style Inline Flow.

Quick design style selection during the --assist flow.
Lets the user pick a color preset and optionally override the primary color.

This is NOT the full design editor (initializer design) — it's a lightweight
step that runs inline during project generation.

Integration point: called from run_new_project() in new_project.py,
after derive_downstream_artifacts (which generates default design system)
and before _apply_design_reference (which overrides with image analysis).
"""

from __future__ import annotations

from typing import Any


_COLOR_PRESETS = {
    "corporate": {
        "label": "Corporate",
        "vibe": "formal, institutional",
        "colors": {
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
    },
    "modern": {
        "label": "Modern",
        "vibe": "tech, startup",
        "colors": {
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
    },
    "warm": {
        "label": "Warm",
        "vibe": "editorial, approachable",
        "colors": {
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
    },
    "dark": {
        "label": "Dark",
        "vibe": "dark mode, developer",
        "colors": {
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
    },
    "minimal": {
        "label": "Minimal",
        "vibe": "clean, no dominant color",
        "colors": {
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
    },
}

_PRESET_ORDER = ["corporate", "modern", "warm", "dark", "minimal"]


def collect_design_style(spec: dict[str, Any]) -> dict[str, Any]:
    """Present design style options and apply the chosen preset.

    Args:
        spec: The project spec (after derive_downstream_artifacts has
              generated the default design system)

    Returns:
        Updated spec with design system colors overridden by preset
    """
    print(f"\n{'=' * 60}")
    print("  🎨 Design Style")
    print(f"{'=' * 60}")
    print()

    for i, key in enumerate(_PRESET_ORDER, 1):
        preset = _COLOR_PRESETS[key]
        primary = preset["colors"]["primary"]
        bg = preset["colors"]["background"]
        print(f"  {i}. {preset['label']:12s} — {primary}, {bg} ({preset['vibe']})")

    print(f"  {len(_PRESET_ORDER) + 1}. skip         — use defaults for this archetype")
    print()

    default_idx = "6"  # skip by default
    raw = input(f"  Your choice [skip]: ").strip().lower()

    if not raw or raw in ("skip", str(len(_PRESET_ORDER) + 1), "s"):
        print("  → Using archetype defaults.\n")
        return spec

    # Match by number or name
    chosen_key = None
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(_PRESET_ORDER):
            chosen_key = _PRESET_ORDER[idx]
    elif raw in _COLOR_PRESETS:
        chosen_key = raw

    if not chosen_key:
        print("  → Invalid choice, using archetype defaults.\n")
        return spec

    preset = _COLOR_PRESETS[chosen_key]
    print(f"  → {preset['label']}")

    # Ask if they want to override the primary color
    custom_primary = input(f"  Custom primary color? (e.g., blue-600, #2563EB, or Enter to keep {preset['colors']['primary']}): ").strip()

    if custom_primary:
        preset["colors"]["primary"] = custom_primary
        # Derive hover from primary if it's a tailwind color
        if "-" in custom_primary and not custom_primary.startswith("#"):
            parts = custom_primary.rsplit("-", 1)
            if len(parts) == 2 and parts[1].isdigit():
                shade = int(parts[1])
                hover_shade = min(shade + 100, 900)
                preset["colors"]["primary_hover"] = f"{parts[0]}-{hover_shade}"
                ring_shade = shade
                preset["colors"]["focus_ring"] = f"{parts[0]}-{ring_shade}/50"
        print(f"  → Primary: {custom_primary}")

    # Apply preset to design system
    design_system = spec.get("design_system", {})
    tokens = design_system.setdefault("tokens", {})
    tokens["colors"] = dict(preset["colors"])
    design_system["tokens"] = tokens
    design_system["style_preset"] = chosen_key
    spec["design_system"] = design_system

    print(f"\n  ✅ Applied '{preset['label']}' design style.\n")

    return spec