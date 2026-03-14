from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from initializer.ai.discovery_engine import AssistedDiscoveryResult
from initializer.engine.archetype_engine import ARCHETYPE_DEFINITIONS
from initializer.engine.capability_registry import CAPABILITY_REGISTRY


DEFAULT_ALLOWED_ANSWER_KEYS = {
    "project_name",
    "project_slug",
    "summary",
    "surface",
    "deploy_target",
    "tenant_model",
    "workflow",
    "public_experience",
    "auth_model",
    "roles",
    "content_types",
    "requires_i18n",
    "requires_scheduled_jobs",
    "i18n",
    "localization",
    "scheduled_publishing",
    "editorial_workflows",
    "background_jobs",
    "mvp_scope",
    "non_goals",
}

IMMUTABLE_ANSWER_KEYS = {
    "project_name",
    "project_slug",
    "surface",
    "deploy_target",
}

STOPWORDS = {
    "a",
    "an",
    "the",
    "for",
    "my",
    "our",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "with",
    "site",
    "app",
    "platform",
    "system",
    "tool",
}

CAPABILITY_ALIASES = {
    "cms": "cms",
    "public-site": "public-site",
    "public_site": "public-site",
    "public website": "public-site",
    "public-website": "public-site",
    "public_website": "public-site",
    "scheduled-jobs": "scheduled-jobs",
    "scheduled_jobs": "scheduled-jobs",
    "background-jobs": "scheduled-jobs",
    "background_jobs": "scheduled-jobs",
    "background jobs": "scheduled-jobs",
    "i18n": "i18n",
    "localization": "i18n",
}

FEATURE_ALIASES = {
    "authentication": "authentication",
    "auth": "authentication",
    "roles": "roles",
    "rbac": "roles",
    "role-based-access-control": "roles",
    "role_based_access_control": "roles",
    "media-library": "media-library",
    "media_library": "media-library",
    "media library": "media-library",
    "draft-publish": "draft-publish",
    "draft_publish": "draft-publish",
    "draft publish": "draft-publish",
    "preview": "preview",
    "scheduled-publishing": "scheduled-publishing",
    "scheduled_publishing": "scheduled-publishing",
    "scheduled publishing": "scheduled-publishing",
    "search": "search",
    "payments": "payments",
    "reviews": "reviews",
    "notifications": "notifications",
    "billing": "billing",
    "analytics": "analytics",
    "api": "api",
}


def _normalize_string_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue

        text = value.strip()
        if text and text not in normalized:
            normalized.append(text)

    return normalized


def _merge_string_lists(existing: list[str], incoming: list[str]) -> list[str]:
    merged: list[str] = []
    for item in existing + incoming:
        if not isinstance(item, str):
            continue

        text = item.strip()
        if text and text not in merged:
            merged.append(text)

    return merged


def _allowed_answer_keys(spec: dict[str, Any]) -> set[str]:
    existing_answers = spec.get("answers", {})
    if not isinstance(existing_answers, dict):
        existing_answers = {}

    return DEFAULT_ALLOWED_ANSWER_KEYS | set(existing_answers.keys())


def _word_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if token and token not in STOPWORDS
    }


def _extract_followup_signals(spec: dict[str, Any]) -> dict[str, Any]:
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}

    followup_answers = discovery.get("followup_answers", {})
    if not isinstance(followup_answers, dict):
        return {}

    extracted: dict[str, Any] = {}

    for _, answer_data in followup_answers.items():
        if not isinstance(answer_data, dict):
            continue

        signal_key = answer_data.get("signal_key")
        value = answer_data.get("value")

        if isinstance(signal_key, str) and signal_key.strip():
            extracted[signal_key.strip()] = value

    return extracted


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"yes", "y", "true", "1"}:
            return True
        if text in {"no", "n", "false", "0", "2"}:
            return False

    return None


def _coerce_decision_signals(signals: dict[str, Any]) -> dict[str, Any]:
    coerced = dict(signals)

    for key in ("needs_public_site", "needs_cms", "needs_i18n", "needs_scheduled_jobs"):
        if key not in coerced:
            continue

        bool_value = _coerce_bool(coerced[key])
        if bool_value is not None:
            coerced[key] = bool_value

    return coerced


def _summary_mentions_external_clients(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in [
            "external clients",
            "client access",
            "client-facing",
            "public-facing",
            "public site",
            "public website",
            "external users",
        ]
    )


def _summary_mentions_cms(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in [
            "cms",
            "content management",
            "blog posts",
            "pages and blog",
            "editorial",
        ]
    )


def _summary_conflicts_with_signals(
    summary: str,
    decision_signals: dict[str, Any],
) -> bool:
    if not summary.strip():
        return False

    primary_audience = decision_signals.get("primary_audience")
    needs_public_site = decision_signals.get("needs_public_site")
    needs_cms = decision_signals.get("needs_cms")

    if primary_audience == "internal_teams" and _summary_mentions_external_clients(summary):
        return True

    if needs_public_site is False and _summary_mentions_external_clients(summary):
        return True

    if needs_cms is False and _summary_mentions_cms(summary):
        return True

    return False


def _build_summary_from_signals(
    existing_value: Any,
    prompt: str | None,
    decision_signals: dict[str, Any],
) -> str | None:
    primary_audience = decision_signals.get("primary_audience")
    app_shape = decision_signals.get("app_shape")
    needs_i18n = decision_signals.get("needs_i18n")
    needs_scheduled_jobs = decision_signals.get("needs_scheduled_jobs")
    core_work_features = decision_signals.get("core_work_features", [])

    if not isinstance(core_work_features, list):
        core_work_features = []

    normalized_features = []
    for item in core_work_features:
        if isinstance(item, str) and item.strip():
            normalized_features.append(item.strip())

    subject = None
    if app_shape == "internal-work-organizer":
        subject = "Internal work organization tool"
    elif app_shape == "client-portal":
        subject = "Client portal"
    elif app_shape == "content-platform":
        subject = "Content platform"
    elif app_shape == "backoffice":
        subject = "Internal backoffice application"
    elif app_shape == "worker-pipeline":
        subject = "Internal workflow automation tool"

    if subject is None:
        if primary_audience == "internal_teams":
            subject = "Internal work organization tool"
        elif primary_audience == "external_clients":
            subject = "Client-facing work organization tool"
        elif primary_audience == "mixed":
            subject = "Work organization tool for internal teams and clients"
        else:
            subject = "Work organization tool"

    parts: list[str] = [subject]

    if normalized_features:
        features_text = ", ".join(normalized_features)
        parts.append(f"focused on {features_text}")

    support_bits: list[str] = []
    if needs_i18n is True:
        support_bits.append("multilingual support")
    if needs_scheduled_jobs is True:
        support_bits.append("scheduled automation")

    if support_bits:
        parts.append("with " + " and ".join(support_bits))

    summary = ", ".join(parts).strip()

    if summary.endswith("."):
        return summary

    return summary + "."


def _merge_summary(
    existing_value: Any,
    incoming_value: Any,
    prompt: str | None,
    decision_signals: dict[str, Any],
) -> tuple[Any, bool]:
    existing_text = existing_value.strip() if isinstance(existing_value, str) else ""
    incoming_text = incoming_value.strip() if isinstance(incoming_value, str) else ""

    if not incoming_text:
        if existing_text and _summary_conflicts_with_signals(existing_text, decision_signals):
            derived = _build_summary_from_signals(existing_value, prompt, decision_signals)
            if derived and derived != existing_text:
                return derived, True
        return existing_value, False

    if _summary_conflicts_with_signals(incoming_text, decision_signals):
        if existing_text and not _summary_conflicts_with_signals(existing_text, decision_signals):
            return existing_text, False

        derived = _build_summary_from_signals(existing_value, prompt, decision_signals)
        if derived:
            if existing_text == derived:
                return existing_text, False
            return derived, True

        return existing_value, False

    if not existing_text:
        return incoming_text, True

    if incoming_text == existing_text:
        return existing_text, False

    if _summary_conflicts_with_signals(existing_text, decision_signals):
        return incoming_text, True

    prompt_tokens = _word_tokens(prompt or "")
    existing_tokens = _word_tokens(existing_text)
    incoming_tokens = _word_tokens(incoming_text)

    if prompt_tokens and (existing_tokens & prompt_tokens) and not (incoming_tokens & prompt_tokens):
        return existing_text, False

    if len(incoming_tokens) > len(existing_tokens):
        return incoming_text, True

    if len(incoming_text) > len(existing_text):
        return incoming_text, True

    return existing_text, False


def _merge_dict_values(
    existing_value: Any,
    incoming_value: Any,
) -> tuple[Any, bool]:
    if not isinstance(incoming_value, dict):
        return existing_value, False

    if not isinstance(existing_value, dict):
        return deepcopy(incoming_value), True

    merged = deepcopy(existing_value)
    changed = False

    for key, value in incoming_value.items():
        if value is None:
            continue

        if key not in merged or merged[key] != value:
            merged[key] = value
            changed = True

    return merged, changed


def _merge_list_values(
    existing_value: Any,
    incoming_value: Any,
) -> tuple[Any, bool]:
    if not isinstance(incoming_value, list):
        return existing_value, False

    existing_list = existing_value if isinstance(existing_value, list) else []
    merged = _merge_string_lists(existing_list, incoming_value)

    return merged, merged != existing_list


def _merge_answer_value(
    *,
    key: str,
    existing_value: Any,
    incoming_value: Any,
    prompt: str | None,
    decision_signals: dict[str, Any],
) -> tuple[Any, bool]:
    if key in IMMUTABLE_ANSWER_KEYS:
        return existing_value, False

    if key == "summary":
        return _merge_summary(existing_value, incoming_value, prompt, decision_signals)

    if isinstance(incoming_value, dict):
        return _merge_dict_values(existing_value, incoming_value)

    if isinstance(incoming_value, list):
        return _merge_list_values(existing_value, incoming_value)

    if incoming_value is None:
        return existing_value, False

    if existing_value == incoming_value:
        return existing_value, False

    return incoming_value, True


def _merge_answer_updates(
    spec: dict[str, Any],
    answer_updates: dict[str, Any],
    decision_signals: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    existing_answers = spec.get("answers", {})
    if not isinstance(existing_answers, dict):
        existing_answers = {}

    merged_answers = deepcopy(existing_answers)
    applied_updates: dict[str, Any] = {}
    allowed_keys = _allowed_answer_keys(spec)
    prompt = spec.get("prompt")

    for key, value in answer_updates.items():
        if not isinstance(key, str):
            continue

        key_text = key.strip()
        if not key_text or key_text not in allowed_keys:
            continue

        merged_value, changed = _merge_answer_value(
            key=key_text,
            existing_value=merged_answers.get(key_text),
            incoming_value=value,
            prompt=prompt,
            decision_signals=decision_signals,
        )
        if not changed:
            continue

        merged_answers[key_text] = merged_value
        applied_updates[key_text] = merged_value

    if "summary" not in applied_updates:
        current_summary = merged_answers.get("summary")
        if isinstance(current_summary, str) and _summary_conflicts_with_signals(current_summary, decision_signals):
            derived = _build_summary_from_signals(current_summary, prompt, decision_signals)
            if derived and derived != current_summary:
                merged_answers["summary"] = derived
                applied_updates["summary"] = derived

    return merged_answers, applied_updates


def _canonicalize_capability(candidate: str) -> str | None:
    key = candidate.strip().lower()
    if not key:
        return None

    canonical = CAPABILITY_ALIASES.get(key, key)
    if canonical not in CAPABILITY_REGISTRY:
        return None

    return canonical


def _normalize_capability_candidates(candidates: list[str]) -> list[str]:
    normalized: list[str] = []

    for candidate in candidates:
        if not isinstance(candidate, str):
            continue

        canonical = _canonicalize_capability(candidate)
        if not canonical:
            continue

        if canonical not in normalized:
            normalized.append(canonical)

    return normalized


def _feature_allowlist(spec: dict[str, Any]) -> set[str]:
    allowed = set(FEATURE_ALIASES.values())

    for archetype_definition in ARCHETYPE_DEFINITIONS.values():
        allowed.update(archetype_definition.get("features", []))

    existing_features = spec.get("features", [])
    if isinstance(existing_features, list):
        allowed.update(
            feature.strip()
            for feature in existing_features
            if isinstance(feature, str) and feature.strip()
        )

    return allowed


def _canonicalize_feature(
    candidate: str,
    *,
    allowed_features: set[str],
) -> str | None:
    key = candidate.strip().lower()
    if not key:
        return None

    canonical = FEATURE_ALIASES.get(key, key)
    if canonical not in allowed_features:
        return None

    return canonical


def _normalize_feature_candidates(
    spec: dict[str, Any],
    candidates: list[str],
) -> list[str]:
    allowed_features = _feature_allowlist(spec)
    normalized: list[str] = []

    for candidate in candidates:
        if not isinstance(candidate, str):
            continue

        canonical = _canonicalize_feature(
            candidate,
            allowed_features=allowed_features,
        )
        if not canonical:
            continue

        if canonical not in normalized:
            normalized.append(canonical)

    return normalized


def _merge_decision_signals(
    spec: dict[str, Any],
    incoming_signals: dict[str, Any],
) -> dict[str, Any]:
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        discovery = {}

    existing_signals = discovery.get("decision_signals", {})
    if not isinstance(existing_signals, dict):
        existing_signals = {}

    followup_signals = _extract_followup_signals(spec)

    merged = deepcopy(existing_signals)
    for key, value in incoming_signals.items():
        merged[key] = value

    for key, value in followup_signals.items():
        merged[key] = value

    return _coerce_decision_signals(merged)


def _apply_capability_signals(
    capabilities: list[str],
    decision_signals: dict[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    current = []
    for capability in capabilities:
        if not isinstance(capability, str):
            continue
        capability_id = capability.strip()
        if capability_id in CAPABILITY_REGISTRY and capability_id not in current:
            current.append(capability_id)

    added: list[str] = []
    removed: list[str] = []

    def ensure_present(capability_id: str):
        nonlocal current, added
        if capability_id not in current:
            current.append(capability_id)
            added.append(capability_id)

    def ensure_absent(capability_id: str):
        nonlocal current, removed
        if capability_id in current:
            current = [item for item in current if item != capability_id]
            removed.append(capability_id)

    needs_cms = decision_signals.get("needs_cms")
    needs_public_site = decision_signals.get("needs_public_site")
    needs_i18n = decision_signals.get("needs_i18n")
    needs_scheduled_jobs = decision_signals.get("needs_scheduled_jobs")
    app_shape = decision_signals.get("app_shape")
    primary_audience = decision_signals.get("primary_audience")

    if needs_cms is True:
        ensure_present("cms")
    elif needs_cms is False:
        ensure_absent("cms")

    if needs_public_site is True:
        ensure_present("public-site")
    elif needs_public_site is False:
        ensure_absent("public-site")

    if needs_i18n is True:
        ensure_present("i18n")
    elif needs_i18n is False:
        ensure_absent("i18n")

    if needs_scheduled_jobs is True:
        ensure_present("scheduled-jobs")
    elif needs_scheduled_jobs is False:
        ensure_absent("scheduled-jobs")

    if app_shape in {"internal-work-organizer", "backoffice", "worker-pipeline"}:
        if needs_cms is not True:
            ensure_absent("cms")

    if primary_audience == "internal_teams" and needs_public_site is False:
        ensure_absent("public-site")

    return current, added, removed


def _merge_features(
    existing_features: list[str],
    feature_candidates: list[str],
) -> tuple[list[str], list[str]]:
    merged: list[str] = []
    applied: list[str] = []

    for feature in existing_features:
        if not isinstance(feature, str):
            continue

        feature_id = feature.strip()
        if feature_id and feature_id not in merged:
            merged.append(feature_id)

    for feature in feature_candidates:
        if feature not in merged:
            merged.append(feature)
            applied.append(feature)

    return merged, applied


def _derive_signal_conflicts(
    spec: dict[str, Any],
    decision_signals: dict[str, Any],
    incoming_conflicts: list[str],
) -> list[str]:
    conflicts = _normalize_string_list(incoming_conflicts)

    answers = spec.get("answers", {})
    if not isinstance(answers, dict):
        answers = {}

    surface = answers.get("surface")
    primary_audience = decision_signals.get("primary_audience")
    needs_public_site = decision_signals.get("needs_public_site")
    needs_cms = decision_signals.get("needs_cms")

    if (
        surface == "admin_plus_public_site"
        and primary_audience == "internal_teams"
        and needs_public_site is False
    ):
        message = (
            "Initial surface indicates admin_plus_public_site, but follow-up signals indicate an internal-first product without a public site."
        )
        if message not in conflicts:
            conflicts.append(message)

    if primary_audience == "internal_teams" and needs_cms is False:
        message = (
            "Follow-up signals indicate an internal work organizer rather than a CMS-oriented product."
        )
        if message not in conflicts:
            conflicts.append(message)

    return conflicts


def _merge_additional_questions(
    existing_value: Any,
    incoming_questions: list[Any],
) -> list[Any]:
    existing_questions = existing_value if isinstance(existing_value, list) else []
    merged: list[Any] = []
    seen_ids: set[str] = set()

    for item in existing_questions + incoming_questions:
        if not isinstance(item, dict):
            continue

        question_id = item.get("id")
        question_text = item.get("question")
        if not isinstance(question_id, str) or not question_id.strip():
            continue
        if not isinstance(question_text, str) or not question_text.strip():
            continue
        if question_id in seen_ids:
            continue

        seen_ids.add(question_id)
        merged.append(item)

    return merged


def _merge_discovery_metadata(
    spec: dict[str, Any],
    result: AssistedDiscoveryResult,
    *,
    merged_decision_signals: dict[str, Any],
    normalized_capability_candidates: list[str],
    normalized_feature_candidates: list[str],
    applied_answer_updates: dict[str, Any],
    applied_capability_candidates: list[str],
    removed_capabilities: list[str],
    applied_feature_candidates: list[str],
    merged_conflicts: list[str],
) -> dict[str, Any]:
    existing = spec.get("discovery", {})
    if not isinstance(existing, dict):
        existing = {}

    merged = dict(existing)
    merged["assisted"] = True
    merged["decision_signals"] = merged_decision_signals
    merged["assumptions"] = _merge_string_lists(
        existing.get("assumptions", []),
        result.assumptions,
    )
    merged["open_questions"] = _merge_string_lists(
        existing.get("open_questions", []),
        result.open_questions,
    )
    merged["deployment_considerations"] = _merge_string_lists(
        existing.get("deployment_considerations", []),
        result.deployment_considerations,
    )
    merged["capability_candidates"] = _merge_string_lists(
        existing.get("capability_candidates", []),
        normalized_capability_candidates,
    )
    merged["feature_candidates"] = _merge_string_lists(
        existing.get("feature_candidates", []),
        normalized_feature_candidates,
    )
    merged["conflicts"] = merged_conflicts
    merged["applied_answer_updates"] = applied_answer_updates
    merged["applied_capability_candidates"] = applied_capability_candidates
    merged["removed_capabilities"] = removed_capabilities
    merged["applied_feature_candidates"] = applied_feature_candidates
    merged["influenced_spec"] = bool(
        applied_answer_updates
        or applied_capability_candidates
        or removed_capabilities
        or applied_feature_candidates
    )

    merged["additional_questions"] = _merge_additional_questions(
        existing.get("additional_questions", []),
        [question.to_dict() for question in result.additional_questions],
    )

    if isinstance(existing.get("followup_answers"), dict):
        merged["followup_answers"] = existing["followup_answers"]

    return merged


def merge_assisted_discovery(
    spec: dict[str, Any],
    result: AssistedDiscoveryResult,
) -> dict[str, Any]:
    merged_spec = deepcopy(spec)
    merged_spec.setdefault("answers", {})
    merged_spec.setdefault("capabilities", [])
    merged_spec.setdefault("features", [])

    merged_decision_signals = _merge_decision_signals(
        merged_spec,
        result.decision_signals,
    )

    merged_answers, applied_answer_updates = _merge_answer_updates(
        merged_spec,
        result.answer_updates,
        merged_decision_signals,
    )
    merged_spec["answers"] = merged_answers

    normalized_capability_candidates = _normalize_capability_candidates(
        result.capability_candidates
    )

    existing_capabilities = merged_spec.get("capabilities", [])
    if not isinstance(existing_capabilities, list):
        existing_capabilities = []

    merged_capabilities = []
    applied_capability_candidates: list[str] = []

    for capability in existing_capabilities:
        if not isinstance(capability, str):
            continue
        capability_id = capability.strip()
        if capability_id in CAPABILITY_REGISTRY and capability_id not in merged_capabilities:
            merged_capabilities.append(capability_id)

    for capability in normalized_capability_candidates:
        if capability not in merged_capabilities:
            merged_capabilities.append(capability)
            applied_capability_candidates.append(capability)

    reconciled_capabilities, signal_added_capabilities, removed_capabilities = _apply_capability_signals(
        merged_capabilities,
        merged_decision_signals,
    )
    merged_spec["capabilities"] = reconciled_capabilities

    applied_capability_candidates = _merge_string_lists(
        applied_capability_candidates,
        signal_added_capabilities,
    )

    normalized_feature_candidates = _normalize_feature_candidates(
        merged_spec,
        result.feature_candidates,
    )
    existing_features = merged_spec.get("features", [])
    if not isinstance(existing_features, list):
        existing_features = []

    merged_features, applied_feature_candidates = _merge_features(
        existing_features,
        normalized_feature_candidates,
    )
    merged_spec["features"] = merged_features

    merged_conflicts = _derive_signal_conflicts(
        merged_spec,
        merged_decision_signals,
        result.conflicts,
    )

    merged_spec["discovery"] = _merge_discovery_metadata(
        merged_spec,
        result,
        merged_decision_signals=merged_decision_signals,
        normalized_capability_candidates=normalized_capability_candidates,
        normalized_feature_candidates=normalized_feature_candidates,
        applied_answer_updates=applied_answer_updates,
        applied_capability_candidates=applied_capability_candidates,
        removed_capabilities=removed_capabilities,
        applied_feature_candidates=applied_feature_candidates,
        merged_conflicts=merged_conflicts,
    )

    return merged_spec