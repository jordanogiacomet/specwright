"""
Capability derivation helpers.

Derives canonical capability identifiers from archetype metadata
and structured answers.
"""

from initializer.engine.archetype_engine import (
    ARCHETYPE_DEFINITIONS,
    canonical_archetype_id,
)
from initializer.engine.capability_registry import CAPABILITY_REGISTRY


def normalize_capabilities(capabilities):
    normalized = []
    seen = set()

    for capability in capabilities or []:
        if capability in CAPABILITY_REGISTRY and capability not in seen:
            normalized.append(capability)
            seen.add(capability)

    return normalized


def default_capabilities_for_archetype(archetype=None, archetype_data=None):
    if isinstance(archetype_data, dict):
        archetype_capabilities = archetype_data.get("capabilities")
        if isinstance(archetype_capabilities, list):
            return normalize_capabilities(archetype_capabilities)

        archetype = archetype_data.get("id") or archetype_data.get("name") or archetype

    if not archetype:
        return []

    definition = ARCHETYPE_DEFINITIONS.get(canonical_archetype_id(archetype), {})

    return normalize_capabilities(definition.get("capabilities", []))


def _lookup_path(data, path):
    current = data

    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]

    return current


def _lookup_first(data, paths):
    for path in paths:
        value = _lookup_path(data, path)
        if value is not None:
            return value

    return None


def _is_enabled(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()

        if lowered in {"1", "true", "yes", "y", "on"}:
            return True

        if lowered in {"0", "false", "no", "n", "off", ""}:
            return False

    return bool(value)


def _is_any_enabled(answers, paths):
    return any(_is_enabled(_lookup_path(answers, path)) for path in paths)


def _append_capability(capabilities, capability):
    if capability in CAPABILITY_REGISTRY and capability not in capabilities:
        capabilities.append(capability)


def derive_capabilities(archetype=None, archetype_data=None, answers=None, existing_capabilities=None):
    capabilities = normalize_capabilities(existing_capabilities)

    for capability in default_capabilities_for_archetype(archetype, archetype_data):
        _append_capability(capabilities, capability)

    answers = answers or {}

    surface = _lookup_first(
        answers,
        [
            ("surface",),
            ("product_surface", "mode"),
            ("guided_answers", "product_surface", "mode"),
        ],
    )

    if surface == "admin_plus_public_site" or _is_any_enabled(
        answers,
        [
            ("public_site",),
            ("guided_answers", "public_site"),
        ],
    ):
        _append_capability(capabilities, "public-site")

    if _is_any_enabled(
        answers,
        [
            ("scheduled_publishing",),
            ("editorial_workflows", "scheduled_publishing"),
            ("guided_answers", "editorial_workflows", "scheduled_publishing"),
            ("background_jobs",),
            ("critical_confirmations", "background_jobs"),
            ("guided_answers", "critical_confirmations", "background_jobs"),
        ],
    ):
        _append_capability(capabilities, "scheduled-jobs")

    if _is_any_enabled(
        answers,
        [
            ("localization",),
            ("i18n",),
            ("critical_confirmations", "i18n"),
            ("guided_answers", "critical_confirmations", "i18n"),
        ],
    ):
        _append_capability(capabilities, "i18n")

    return capabilities


def derive_capabilities_for_spec(spec):
    spec["capabilities"] = derive_capabilities(
        archetype=spec.get("archetype"),
        archetype_data=spec.get("archetype_data"),
        answers=spec.get("answers"),
        existing_capabilities=spec.get("capabilities"),
    )

    return spec
