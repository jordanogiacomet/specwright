"""Capability derivation helpers.

Derives canonical capability identifiers from archetype metadata,
structured answers, and structured discovery signals.

Key change in this version: public-site is NOT added from surface alone
when discovery signals exist but needs_public_site was never confirmed.
The rule is: confirmed signals > inferred signals > onboarding defaults.
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
        if lowered in {"0", "false", "no", "n", "off", "", "2"}:
            return False

    return bool(value)


def _is_any_enabled(answers, paths):
    return any(_is_enabled(_lookup_path(answers, path)) for path in paths)


def _append_capability(capabilities, capability):
    if capability in CAPABILITY_REGISTRY and capability not in capabilities:
        capabilities.append(capability)


def _remove_capability(capabilities, capability):
    while capability in capabilities:
        capabilities.remove(capability)


def _get_discovery_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}

    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}

    return dict(signals)


def _get_confirmed_signals(spec):
    """Get signals that were explicitly confirmed by the user via followup."""
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}

    confirmed = discovery.get("confirmed_signals", {})
    if not isinstance(confirmed, dict):
        return {}

    return dict(confirmed)


def _has_discovery(spec):
    """Check if discovery has been run at all."""
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return False
    return discovery.get("assisted", False)


def derive_capabilities(
    archetype=None,
    archetype_data=None,
    answers=None,
    existing_capabilities=None,
    decision_signals=None,
    confirmed_signals=None,
    has_discovery=False,
):
    capabilities = normalize_capabilities(existing_capabilities)

    for capability in default_capabilities_for_archetype(archetype, archetype_data):
        _append_capability(capabilities, capability)

    answers = answers or {}
    decision_signals = decision_signals or {}
    confirmed_signals = confirmed_signals or {}

    surface = _lookup_first(
        answers,
        [
            ("surface",),
            ("product_surface", "mode"),
            ("guided_answers", "product_surface", "mode"),
        ],
    )

    needs_public_site = decision_signals.get("needs_public_site")
    needs_cms = decision_signals.get("needs_cms")
    needs_i18n = decision_signals.get("needs_i18n")
    needs_scheduled_jobs = decision_signals.get("needs_scheduled_jobs")
    primary_audience = decision_signals.get("primary_audience")
    app_shape = decision_signals.get("app_shape")

    ps_confirmed = "needs_public_site" in confirmed_signals

    # --- PUBLIC-SITE (conservative rule) ---
    if ps_confirmed:
        # User explicitly answered the question — respect absolutely
        if needs_public_site is True:
            _append_capability(capabilities, "public-site")
        elif needs_public_site is False:
            _remove_capability(capabilities, "public-site")
    elif needs_public_site is True:
        # AI inferred True but user didn't confirm directly.
        # Be conservative only for internal_teams audience.
        # For external_clients or mixed, inference + surface is sufficient evidence.
        if primary_audience == "internal_teams":
            # Internal audience + unconfirmed public-site → don't add
            pass
        else:
            # External/mixed/unknown audience + AI inferred true → add
            _append_capability(capabilities, "public-site")
    elif needs_public_site is False:
        # AI inferred False — safe to remove
        _remove_capability(capabilities, "public-site")
    else:
        # needs_public_site is None — no signal at all
        if has_discovery:
            # Discovery ran but never produced a signal for public-site.
            # Don't add from surface alone when discovery is active.
            pass
        else:
            # No discovery at all — fall back to surface-based derivation
            if surface == "admin_plus_public_site" or _is_any_enabled(
                answers,
                [
                    ("public_site",),
                    ("guided_answers", "public_site"),
                ],
            ):
                _append_capability(capabilities, "public-site")

    # --- SCHEDULED-JOBS ---
    if needs_scheduled_jobs is True:
        _append_capability(capabilities, "scheduled-jobs")
    elif needs_scheduled_jobs is False:
        _remove_capability(capabilities, "scheduled-jobs")
    elif _is_any_enabled(
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

    # --- I18N ---
    if needs_i18n is True:
        _append_capability(capabilities, "i18n")
    elif needs_i18n is False:
        _remove_capability(capabilities, "i18n")
    elif _is_any_enabled(
        answers,
        [
            ("localization",),
            ("i18n",),
            ("critical_confirmations", "i18n"),
            ("guided_answers", "critical_confirmations", "i18n"),
        ],
    ):
        _append_capability(capabilities, "i18n")

    # --- CMS ---
    if needs_cms is True:
        _append_capability(capabilities, "cms")
    elif needs_cms is False:
        _remove_capability(capabilities, "cms")

    # --- Shape-based cleanup ---
    if app_shape in {"internal-work-organizer", "backoffice", "worker-pipeline"}:
        if needs_cms is not True:
            _remove_capability(capabilities, "cms")

    if primary_audience == "internal_teams" and needs_public_site is not True:
        # For internal audience, remove public-site unless explicitly confirmed True
        _remove_capability(capabilities, "public-site")

    return normalize_capabilities(capabilities)


def derive_capabilities_for_spec(spec):
    spec["capabilities"] = derive_capabilities(
        archetype=spec.get("archetype"),
        archetype_data=spec.get("archetype_data"),
        answers=spec.get("answers"),
        existing_capabilities=spec.get("capabilities"),
        decision_signals=_get_discovery_signals(spec),
        confirmed_signals=_get_confirmed_signals(spec),
        has_discovery=_has_discovery(spec),
    )
    return spec