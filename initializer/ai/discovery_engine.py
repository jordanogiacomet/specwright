from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from initializer.ai.client import AIClient, AIClientConfig


BOOLEAN_SIGNAL_KEYS = {
    "needs_public_site",
    "needs_cms",
    "needs_i18n",
    "needs_scheduled_jobs",
}

ENUM_SIGNAL_VALUES = {
    "primary_audience": {
        "internal_teams",
        "external_clients",
        "mixed",
        "unknown",
    },
    "app_shape": {
        "generic-web-app",
        "internal-work-organizer",
        "client-portal",
        "content-platform",
        "backoffice",
        "worker-pipeline",
        "knowledge-base",
        "ecommerce",
        "marketplace",
        "unknown",
    },
}


@dataclass(slots=True)
class AssistedDiscoveryQuestion:
    id: str
    question: str
    answer_type: str = "text"  # boolean | enum | list | text
    choices: list[str] = field(default_factory=list)
    signal_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "question": self.question,
            "answer_type": self.answer_type,
        }
        if self.choices:
            data["choices"] = self.choices
        if self.signal_key:
            data["signal_key"] = self.signal_key
        return data


@dataclass(slots=True)
class AssistedDiscoveryResult:
    additional_questions: list[AssistedDiscoveryQuestion] = field(default_factory=list)
    answer_updates: dict[str, Any] = field(default_factory=dict)
    decision_signals: dict[str, Any] = field(default_factory=dict)
    capability_candidates: list[str] = field(default_factory=list)
    feature_candidates: list[str] = field(default_factory=list)
    deployment_considerations: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "additional_questions": [
                question.to_dict() for question in self.additional_questions
            ],
            "answer_updates": self.answer_updates,
            "decision_signals": self.decision_signals,
            "capability_candidates": self.capability_candidates,
            "feature_candidates": self.feature_candidates,
            "deployment_considerations": self.deployment_considerations,
            "assumptions": self.assumptions,
            "open_questions": self.open_questions,
            "conflicts": self.conflicts,
        }


def build_discovery_payload(spec: dict[str, Any]) -> dict[str, Any]:
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        discovery = {}

    return {
        "prompt": spec.get("prompt"),
        "archetype": spec.get("archetype"),
        "archetype_data": {
            "id": spec.get("archetype_data", {}).get("id"),
            "name": spec.get("archetype_data", {}).get("name"),
            "features": spec.get("archetype_data", {}).get("features", []),
            "capabilities": spec.get("archetype_data", {}).get("capabilities", []),
            "stack": spec.get("archetype_data", {}).get("stack", {}),
        },
        "stack": spec.get("stack", {}),
        "features": spec.get("features", []),
        "capabilities": spec.get("capabilities", []),
        "answers": spec.get("answers", {}),
        "existing_discovery": {
            "decision_signals": discovery.get("decision_signals", {}),
            "followup_answers": discovery.get("followup_answers", {}),
            "assumptions": discovery.get("assumptions", []),
            "open_questions": discovery.get("open_questions", []),
            "conflicts": discovery.get("conflicts", []),
            "additional_questions": discovery.get("additional_questions", []),
        },
    }


def build_discovery_instructions() -> str:
    return (
        "You are assisting a PRD-driven project initializer.\n"
        "\n"
        "Your job is to refine the canonical spec safely.\n"
        "\n"
        "Core principles:\n"
        "- Prefer structured decisions over vague inference.\n"
        "- Ask high-value product-shape questions before system-design questions.\n"
        "- Do not rewrite the archetype.\n"
        "- Do not rewrite the stack.\n"
        "- Do not invent implementation details without evidence.\n"
        "- Preserve explicit user answers over prior inference.\n"
        "- Negative evidence matters: if the user says 'no CMS', do not keep CMS implied.\n"
        "\n"
        "You must return JSON only.\n"
        "\n"
        "Return these keys:\n"
        "- additional_questions: array of objects\n"
        "- answer_updates: object\n"
        "- decision_signals: object\n"
        "- capability_candidates: string[]\n"
        "- feature_candidates: string[]\n"
        "- deployment_considerations: string[]\n"
        "- assumptions: string[]\n"
        "- open_questions: string[]\n"
        "- conflicts: string[]\n"
        "\n"
        "Rules for additional_questions:\n"
        "- Ask only questions that could materially change the spec.\n"
        "- Each question must be an object with:\n"
        "  - id\n"
        "  - question\n"
        "  - answer_type: boolean | enum | list | text\n"
        "  - choices: optional array, only for enum\n"
        "  - signal_key: optional string when the answer should map into decision_signals\n"
        "- Do not repeat questions already answered in followup_answers.\n"
        "- Prefer product-shape questions before architecture questions.\n"
        "\n"
        "Rules for decision_signals:\n"
        "- Supported boolean keys: needs_public_site, needs_cms, needs_i18n, needs_scheduled_jobs\n"
        "- Supported enum keys:\n"
        "  primary_audience: internal_teams | external_clients | mixed | unknown\n"
        "  app_shape: generic-web-app | internal-work-organizer | client-portal | content-platform | backoffice | worker-pipeline | knowledge-base | ecommerce | marketplace | unknown\n"
        "- Supported list keys:\n"
        "  core_work_features\n"
        "\n"
        "Rules for core_work_features:\n"
        "- Use product/domain capabilities, not technical plumbing.\n"
        "- Good examples: deadlines, progress-tracking, task-assignment, reminders, report-generation, approvals, team-visibility\n"
        "- Bad examples: authentication, api, database, frontend\n"
        "\n"
        "Rules for capability_candidates:\n"
        "- Allowed capability IDs are: cms, public-site, scheduled-jobs, i18n\n"
        "- Only include a capability if supported by evidence.\n"
        "\n"
        "Rules for feature_candidates:\n"
        "- Use canonical feature IDs when justified.\n"
        "- Examples: authentication, roles, media-library, draft-publish, preview, scheduled-publishing, search, payments, reviews, notifications, billing, analytics, api\n"
        "\n"
        "Rules for answer_updates:\n"
        "- Improve weak fields like summary.\n"
        "- Preserve domain specificity from the prompt.\n"
        "- Do not silently override project_name, project_slug, surface, or deploy_target.\n"
        "\n"
        "Rules for conflicts:\n"
        "- Add a conflict when structured signals disagree with earlier onboarding choices.\n"
        "- Example: surface suggests public-site but follow-up answers indicate internal-only.\n"
    )


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue

        text = item.strip()
        if text and text not in normalized:
            normalized.append(text)

    return normalized


def _normalize_answer_updates(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            continue

        key_text = key.strip()
        if not key_text:
            continue

        normalized[key_text] = item

    return normalized


def _normalize_question(value: Any) -> AssistedDiscoveryQuestion | None:
    if not isinstance(value, dict):
        return None

    question_id = value.get("id")
    question_text = value.get("question")
    answer_type = value.get("answer_type", "text")
    choices = value.get("choices", [])
    signal_key = value.get("signal_key")

    if not isinstance(question_id, str) or not question_id.strip():
        return None

    if not isinstance(question_text, str) or not question_text.strip():
        return None

    if not isinstance(answer_type, str) or not answer_type.strip():
        answer_type = "text"

    answer_type = answer_type.strip().lower()
    if answer_type not in {"boolean", "enum", "list", "text"}:
        answer_type = "text"

    normalized_choices = _normalize_string_list(choices)

    normalized_signal_key: str | None = None
    if isinstance(signal_key, str) and signal_key.strip():
        normalized_signal_key = signal_key.strip()

    return AssistedDiscoveryQuestion(
        id=question_id.strip(),
        question=question_text.strip(),
        answer_type=answer_type,
        choices=normalized_choices,
        signal_key=normalized_signal_key,
    )


def _normalize_questions(value: Any) -> list[AssistedDiscoveryQuestion]:
    if not isinstance(value, list):
        return []

    normalized: list[AssistedDiscoveryQuestion] = []
    seen_ids: set[str] = set()

    for item in value:
        question = _normalize_question(item)
        if not question:
            continue

        if question.id in seen_ids:
            continue

        seen_ids.add(question.id)
        normalized.append(question)

    return normalized


def _normalize_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"yes", "true", "y", "1"}:
            return True
        if text in {"no", "false", "n", "0", "2"}:
            return False

    return None


def _normalize_decision_signals(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    normalized: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(key, str):
            continue

        signal_key = key.strip()
        if not signal_key:
            continue

        if signal_key in BOOLEAN_SIGNAL_KEYS:
            bool_value = _normalize_bool(item)
            if bool_value is not None:
                normalized[signal_key] = bool_value
            continue

        if signal_key in ENUM_SIGNAL_VALUES:
            if isinstance(item, str):
                enum_value = item.strip()
                if enum_value in ENUM_SIGNAL_VALUES[signal_key]:
                    normalized[signal_key] = enum_value
            continue

        if signal_key == "core_work_features":
            items = []
            for raw_item in _normalize_string_list(item):
                lowered = raw_item.lower()
                if lowered in {"authentication", "api", "database", "frontend", "backend"}:
                    continue
                if lowered not in items:
                    items.append(lowered)
            normalized[signal_key] = items
            continue

        if isinstance(item, (str, bool, int, float, list, dict)):
            normalized[signal_key] = item

    return normalized


def _answered_question_ids(payload: dict[str, Any]) -> set[str]:
    existing = payload.get("existing_discovery", {})
    if not isinstance(existing, dict):
        return set()

    followup_answers = existing.get("followup_answers", {})
    if not isinstance(followup_answers, dict):
        return set()

    return {
        key.strip()
        for key in followup_answers.keys()
        if isinstance(key, str) and key.strip()
    }


def _existing_signal_values(payload: dict[str, Any]) -> dict[str, Any]:
    existing = payload.get("existing_discovery", {})
    if not isinstance(existing, dict):
        return {}

    signals = existing.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}

    return dict(signals)


def _question_ids(questions: list[AssistedDiscoveryQuestion]) -> set[str]:
    return {question.id for question in questions}


def _append_question_if_missing(
    questions: list[AssistedDiscoveryQuestion],
    existing_ids: set[str],
    answered_ids: set[str],
    question: AssistedDiscoveryQuestion,
):
    if question.id in existing_ids or question.id in answered_ids:
        return

    questions.append(question)
    existing_ids.add(question.id)


def _augment_questions_from_context(
    payload: dict[str, Any],
    result: AssistedDiscoveryResult,
) -> AssistedDiscoveryResult:
    answered_ids = _answered_question_ids(payload)
    existing_ids = _question_ids(result.additional_questions)

    signals = result.decision_signals
    existing_signal_values = _existing_signal_values(payload)

    primary_audience = signals.get("primary_audience") or existing_signal_values.get("primary_audience")
    app_shape = signals.get("app_shape") or existing_signal_values.get("app_shape")
    needs_public_site = signals.get("needs_public_site")
    needs_cms = signals.get("needs_cms")
    needs_i18n = signals.get("needs_i18n")
    needs_scheduled_jobs = signals.get("needs_scheduled_jobs")
    core_work_features = signals.get("core_work_features")

    answers = payload.get("answers", {})
    if not isinstance(answers, dict):
        answers = {}

    surface = answers.get("surface")

    _append_question_if_missing(
        result.additional_questions,
        existing_ids,
        answered_ids,
        AssistedDiscoveryQuestion(
            id="primary_audience",
            question="Is the primary audience for this tool internal teams, external clients, or both equally?",
            answer_type="enum",
            choices=["internal_teams", "external_clients", "mixed", "unknown"],
            signal_key="primary_audience",
        ),
    ) if primary_audience in (None, "unknown") else None

    if needs_public_site is None and surface == "admin_plus_public_site":
        _append_question_if_missing(
            result.additional_questions,
            existing_ids,
            answered_ids,
            AssistedDiscoveryQuestion(
                id="needs_public_site",
                question="Will the application include a public-facing site accessible without authentication?",
                answer_type="boolean",
                signal_key="needs_public_site",
            ),
        )

    if needs_cms is None:
        _append_question_if_missing(
            result.additional_questions,
            existing_ids,
            answered_ids,
            AssistedDiscoveryQuestion(
                id="needs_cms",
                question="Does the project need content management capabilities for managing and editing content easily?",
                answer_type="boolean",
                signal_key="needs_cms",
            ),
        )

    if needs_i18n is None:
        _append_question_if_missing(
            result.additional_questions,
            existing_ids,
            answered_ids,
            AssistedDiscoveryQuestion(
                id="needs_i18n",
                question="Does the application need to support multiple languages or internationalization?",
                answer_type="boolean",
                signal_key="needs_i18n",
            ),
        )

    if needs_scheduled_jobs is None:
        _append_question_if_missing(
            result.additional_questions,
            existing_ids,
            answered_ids,
            AssistedDiscoveryQuestion(
                id="needs_scheduled_jobs",
                question="Will the application require scheduled or background jobs (e.g. notifications, batch processing)?",
                answer_type="boolean",
                signal_key="needs_scheduled_jobs",
            ),
        )

    if (
        app_shape == "internal-work-organizer"
        or primary_audience == "internal_teams"
    ) and not core_work_features:
        _append_question_if_missing(
            result.additional_questions,
            existing_ids,
            answered_ids,
            AssistedDiscoveryQuestion(
                id="core_work_features",
                question=(
                    "What core work organization features are needed? "
                    "Use comma-separated values, for example: deadlines, progress-tracking, task-assignment, reminders."
                ),
                answer_type="list",
                signal_key="core_work_features",
            ),
        )

    return result


def normalize_discovery_result(data: dict[str, Any]) -> AssistedDiscoveryResult:
    return AssistedDiscoveryResult(
        additional_questions=_normalize_questions(data.get("additional_questions")),
        answer_updates=_normalize_answer_updates(data.get("answer_updates")),
        decision_signals=_normalize_decision_signals(data.get("decision_signals")),
        capability_candidates=_normalize_string_list(data.get("capability_candidates")),
        feature_candidates=_normalize_string_list(data.get("feature_candidates")),
        deployment_considerations=_normalize_string_list(
            data.get("deployment_considerations")
        ),
        assumptions=_normalize_string_list(data.get("assumptions")),
        open_questions=_normalize_string_list(data.get("open_questions")),
        conflicts=_normalize_string_list(data.get("conflicts")),
    )


def run_assisted_discovery(
    spec: dict[str, Any],
    *,
    client: AIClient | None = None,
) -> AssistedDiscoveryResult:
    ai_client = client or AIClient(
        AIClientConfig(model="gpt-4.1-mini"),
    )

    payload = build_discovery_payload(spec)
    instructions = build_discovery_instructions()

    response_data = ai_client.generate_json(
        instructions=instructions,
        input_text=json.dumps(payload, indent=2, sort_keys=True),
    )

    result = normalize_discovery_result(response_data)
    result = _augment_questions_from_context(payload, result)
    return result