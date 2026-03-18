"""Tests for the --assist flow (non-interactive, mocked AI and input).

Covers:
- run_optional_assisted_discovery: assist=False passthrough
- run_optional_assisted_discovery: assist=True — single pass (no followup answers)
- run_optional_assisted_discovery: assist=True — two passes (followup answers given)
- _surface_conflicts: printed when conflicts exist, silent when none
- collect_followup_answers: user answers stored correctly in spec
- collect_challenge_decisions: decisions applied to spec; skip works; custom works
- decision_signals and capabilities end up in spec after full assist pass
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock
from typing import Any

import pytest

from initializer.ai.discovery_engine import (
    AssistedDiscoveryResult,
    AssistedDiscoveryQuestion,
)
from initializer.flow.new_project import (
    run_optional_assisted_discovery,
    collect_followup_answers,
    apply_followup_answers_to_spec,
    _surface_conflicts,
)
from initializer.flow.challenges_flow import collect_challenge_decisions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_spec() -> dict[str, Any]:
    return {
        "prompt": "A simple task manager for small teams",
        "archetype": "todo-app",
        "archetype_data": {"id": "todo-app", "name": "Todo App", "features": [], "capabilities": []},
        "answers": {
            "project_name": "TaskFlow",
            "project_slug": "taskflow",
            "summary": "Task manager",
            "surface": "internal_admin_only",
            "deploy_target": "docker",
        },
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "capabilities": [],
        "features": [],
    }


def _make_discovery_result(
    *,
    signals: dict | None = None,
    questions: list[dict] | None = None,
    conflicts: list[str] | None = None,
    capability_candidates: list[str] | None = None,
) -> AssistedDiscoveryResult:
    result = AssistedDiscoveryResult()
    result.decision_signals = signals or {}
    result.conflicts = conflicts or []
    result.capability_candidates = capability_candidates or []
    result.additional_questions = [
        AssistedDiscoveryQuestion(
            id=q["id"],
            question=q["question"],
            answer_type=q.get("answer_type", "text"),
            signal_key=q.get("signal_key"),
        )
        for q in (questions or [])
    ]
    return result


# ---------------------------------------------------------------------------
# run_optional_assisted_discovery — assist=False
# ---------------------------------------------------------------------------

def test_assisted_discovery_passthrough_when_not_assist():
    spec = _base_spec()
    result = run_optional_assisted_discovery(spec, assist=False)
    assert result is spec  # unchanged, same object


# ---------------------------------------------------------------------------
# run_optional_assisted_discovery — assist=True, no followup answers
# ---------------------------------------------------------------------------

def test_assisted_discovery_single_pass_no_followup(capsys):
    spec = _base_spec()
    discovery_result = _make_discovery_result(
        signals={"needs_public_site": False, "app_shape": "internal-work-organizer"},
        questions=[],  # no questions → no followup prompt → single pass
        conflicts=[],
    )

    with patch(
        "initializer.flow.new_project.run_assisted_discovery",
        return_value=discovery_result,
    ) as mock_run, patch(
        "initializer.flow.new_project.merge_assisted_discovery",
        side_effect=lambda s, r: {**s, "discovery": {"decision_signals": r.decision_signals}},
    ) as mock_merge:
        result = run_optional_assisted_discovery(spec, assist=True)

    assert mock_run.call_count == 1
    assert mock_merge.call_count == 1
    assert result["discovery"]["decision_signals"]["app_shape"] == "internal-work-organizer"


# ---------------------------------------------------------------------------
# run_optional_assisted_discovery — assist=True, followup answers trigger second pass
# ---------------------------------------------------------------------------

def test_assisted_discovery_two_passes_when_followup_given(capsys):
    spec = _base_spec()

    first_result = _make_discovery_result(
        signals={"needs_public_site": False},
        questions=[{"id": "q1", "question": "Do you need i18n?", "answer_type": "boolean"}],
    )
    second_result = _make_discovery_result(
        signals={"needs_public_site": False, "needs_i18n": True},
    )

    call_count = {"n": 0}

    def fake_run(s, *, client=None):
        call_count["n"] += 1
        return first_result if call_count["n"] == 1 else second_result

    def fake_merge(s, r):
        merged = {**s}
        existing = merged.get("discovery", {})
        existing["decision_signals"] = r.decision_signals
        merged["discovery"] = existing
        return merged

    # Simulate user typing "yes" for the boolean question
    with patch("initializer.flow.new_project.run_assisted_discovery", side_effect=fake_run), \
         patch("initializer.flow.new_project.merge_assisted_discovery", side_effect=fake_merge), \
         patch("builtins.input", return_value="yes"):
        result = run_optional_assisted_discovery(spec, assist=True)

    assert call_count["n"] == 2, "Should run discovery twice when followup answers are given"
    assert result["discovery"]["decision_signals"].get("needs_i18n") is True


# ---------------------------------------------------------------------------
# _surface_conflicts
# ---------------------------------------------------------------------------

def test_surface_conflicts_prints_when_present(capsys):
    spec = {
        "discovery": {
            "conflicts": [
                "surface says internal_only but needs_public_site=True",
                "deploy_target docker conflicts with k8s signal",
            ]
        }
    }
    _surface_conflicts(spec)
    out = capsys.readouterr().out
    assert "Signal Conflicts Detected" in out
    assert "surface says internal_only" in out
    assert "docker conflicts with k8s signal" in out


def test_surface_conflicts_silent_when_none(capsys):
    spec = {"discovery": {"conflicts": []}}
    _surface_conflicts(spec)
    out = capsys.readouterr().out
    assert out == ""


def test_surface_conflicts_silent_when_no_discovery_key(capsys):
    spec = _base_spec()
    _surface_conflicts(spec)
    out = capsys.readouterr().out
    assert out == ""


# ---------------------------------------------------------------------------
# collect_followup_answers — text, boolean, enum
# ---------------------------------------------------------------------------

def test_collect_followup_answers_text():
    questions = [{"id": "q1", "question": "What is the team size?", "answer_type": "text"}]
    with patch("builtins.input", return_value="10-20 people"):
        result = collect_followup_answers(questions)

    assert "q1" in result
    assert result["q1"]["value"] == "10-20 people"
    assert result["q1"]["answer_type"] == "text"


def test_collect_followup_answers_boolean_yes():
    questions = [{"id": "q2", "question": "Do you need SSO?", "answer_type": "boolean"}]
    with patch("builtins.input", return_value="yes"):
        result = collect_followup_answers(questions)

    assert result["q2"]["value"] is True


def test_collect_followup_answers_boolean_no():
    questions = [{"id": "q3", "question": "Do you need SSO?", "answer_type": "boolean"}]
    with patch("builtins.input", return_value="no"):
        result = collect_followup_answers(questions)

    assert result["q3"]["value"] is False


def test_collect_followup_answers_enum_by_number():
    questions = [
        {
            "id": "q4",
            "question": "What is the deployment region?",
            "answer_type": "enum",
            "choices": ["us-east", "eu-west", "ap-southeast"],
        }
    ]
    with patch("builtins.input", return_value="2"):  # "eu-west"
        result = collect_followup_answers(questions)

    assert result["q4"]["value"] == "eu-west"


def test_collect_followup_answers_skips_empty_input():
    questions = [{"id": "q5", "question": "Any other notes?", "answer_type": "text"}]
    with patch("builtins.input", return_value=""):
        result = collect_followup_answers(questions)

    assert "q5" not in result


def test_collect_followup_answers_deduplicates_by_signal_key():
    questions = [
        {"id": "qa", "question": "Need public site?", "answer_type": "boolean", "signal_key": "needs_public_site"},
        {"id": "qb", "question": "Public site needed?", "answer_type": "boolean", "signal_key": "needs_public_site"},
    ]
    with patch("builtins.input", return_value="yes"):
        result = collect_followup_answers(questions)

    assert len(result) == 1, "Duplicate signal_key questions should be deduplicated"


# ---------------------------------------------------------------------------
# apply_followup_answers_to_spec
# ---------------------------------------------------------------------------

def test_apply_followup_answers_stores_in_discovery():
    spec = _base_spec()
    followup = {
        "q1": {"question": "Team size?", "answer_type": "text", "raw_answer": "5", "value": "5", "signal_key": None}
    }
    result = apply_followup_answers_to_spec(spec, followup, [])
    assert result["discovery"]["followup_answers"]["q1"]["value"] == "5"


def test_apply_followup_answers_merges_with_existing():
    spec = {
        **_base_spec(),
        "discovery": {
            "followup_answers": {
                "old_q": {"question": "Old?", "answer_type": "text", "raw_answer": "x", "value": "x", "signal_key": None}
            }
        },
    }
    new_followup = {
        "new_q": {"question": "New?", "answer_type": "text", "raw_answer": "y", "value": "y", "signal_key": None}
    }
    result = apply_followup_answers_to_spec(spec, new_followup, [])
    assert "old_q" in result["discovery"]["followup_answers"]
    assert "new_q" in result["discovery"]["followup_answers"]


# ---------------------------------------------------------------------------
# collect_challenge_decisions
# ---------------------------------------------------------------------------

def _make_challenge(cid="auth-strategy", default_key="a") -> dict:
    return {
        "id": cid,
        "title": "Authentication Strategy",
        "description": "How should users authenticate?",
        "default": default_key,
        "options": [
            {"key": "a", "label": "JWT stateless", "detail": "Fast, no server state"},
            {"key": "b", "label": "Session-based", "detail": "Easier to revoke"},
        ],
    }


def test_collect_challenge_decisions_option_selected():
    spec = _base_spec()
    challenge = _make_challenge()

    with patch("initializer.flow.challenges_flow.generate_challenges", return_value=[challenge]), \
         patch("initializer.engine.challenges_engine.apply_challenge_decisions", side_effect=lambda s, d: {**s, "challenge_decisions": d}), \
         patch("builtins.input", return_value="b"):
        result = collect_challenge_decisions(spec)

    assert result["challenge_decisions"]["auth-strategy"]["chosen_option"] == "b"
    assert result["challenge_decisions"]["auth-strategy"]["option_label"] == "Session-based"


def test_collect_challenge_decisions_default_on_empty_input():
    spec = _base_spec()
    challenge = _make_challenge(default_key="a")

    with patch("initializer.flow.challenges_flow.generate_challenges", return_value=[challenge]), \
         patch("initializer.engine.challenges_engine.apply_challenge_decisions", side_effect=lambda s, d: {**s, "challenge_decisions": d}), \
         patch("builtins.input", return_value=""):  # empty → default
        result = collect_challenge_decisions(spec)

    assert result["challenge_decisions"]["auth-strategy"]["chosen_option"] == "a"


def test_collect_challenge_decisions_skip():
    spec = _base_spec()
    challenge = _make_challenge()

    with patch("initializer.flow.challenges_flow.generate_challenges", return_value=[challenge]), \
         patch("builtins.input", return_value="s"):
        result = collect_challenge_decisions(spec)

    assert "challenge_decisions" not in result


def test_collect_challenge_decisions_custom():
    spec = _base_spec()
    challenge = _make_challenge()

    with patch("initializer.flow.challenges_flow.generate_challenges", return_value=[challenge]), \
         patch("initializer.engine.challenges_engine.apply_challenge_decisions", side_effect=lambda s, d: {**s, "challenge_decisions": d}), \
         patch("builtins.input", side_effect=["c", "Use OAuth2 with PKCE"]):
        result = collect_challenge_decisions(spec)

    assert result["challenge_decisions"]["auth-strategy"]["chosen_option"] == "custom"
    assert result["challenge_decisions"]["auth-strategy"]["custom_text"] == "Use OAuth2 with PKCE"


def test_collect_challenge_decisions_no_challenges():
    spec = _base_spec()
    with patch("initializer.flow.challenges_flow.generate_challenges", return_value=[]):
        result = collect_challenge_decisions(spec)
    assert result is spec  # unchanged
