"""Challenges CLI Flow.

Presents known architectural challenges to the user during the
--assist flow, collects their decisions, and applies them to the spec.

This is called after discovery and capability derivation, but before
architecture generation — so that challenge decisions influence
the generated architecture.

Integration point: called from run_new_project() in new_project.py
"""

from __future__ import annotations

from typing import Any

from initializer.engine.challenges_engine import (
    generate_challenges,
    apply_challenge_decisions,
)


def _present_challenge(index: int, total: int, challenge: dict[str, Any]) -> dict[str, Any] | None:
    """Present a single challenge and collect the user's decision.

    Returns a decision dict or None if skipped.
    """
    print(f"\n{'─' * 60}")
    print(f"  Challenge {index}/{total}: {challenge['title']}")
    print(f"{'─' * 60}")
    print()
    print(f"  {challenge['description']}")
    print()

    options = challenge.get("options", [])
    default = challenge.get("default", "a")

    for opt in options:
        key = opt["key"]
        label = opt["label"]
        detail = opt["detail"]
        default_marker = " (recommended)" if key == default else ""

        print(f"  {key}) {label}{default_marker}")
        print(f"     {detail}")
        print()

    print(f"  s) Skip — decide later")
    print(f"  c) Custom — write your own solution")
    print()

    valid_keys = {opt["key"] for opt in options} | {"s", "skip", "c", "custom", ""}

    while True:
        raw = input(f"  Your choice [{default}]: ").strip().lower()

        if raw == "" :
            raw = default

        if raw in ("s", "skip"):
            print("  → Skipped")
            return None

        if raw in ("c", "custom"):
            custom_text = input("  Describe your approach: ").strip()
            if not custom_text:
                print("  → Skipped (empty input)")
                return None

            print(f"  → Custom: {custom_text}")
            return {
                "chosen_option": "custom",
                "custom_text": custom_text,
                "option_label": "Custom solution",
                "option_detail": custom_text,
            }

        if raw in valid_keys:
            chosen_opt = next((o for o in options if o["key"] == raw), None)
            if chosen_opt:
                print(f"  → {chosen_opt['label']}")
                return {
                    "chosen_option": raw,
                    "custom_text": "",
                    "option_label": chosen_opt["label"],
                    "option_detail": chosen_opt["detail"],
                }

        print(f"  Please enter one of: {', '.join(sorted(valid_keys))}")


def collect_challenge_decisions(spec: dict[str, Any]) -> dict[str, Any]:
    """Present all challenges and collect user decisions.

    Args:
        spec: The project spec (after discovery and capability derivation)

    Returns:
        Updated spec with challenge_decisions applied
    """
    challenges = generate_challenges(spec)

    if not challenges:
        return spec

    print("\n" + "=" * 60)
    print("  🔍 Known Challenges for Your Project")
    print("=" * 60)
    print()
    print(f"  Found {len(challenges)} known challenge(s) for this project type.")
    print("  For each one, choose a resolution strategy or skip.")
    print("  Your decisions will be built into the architecture and stories.")

    decisions: dict[str, dict[str, Any]] = {}
    total = len(challenges)

    for i, challenge in enumerate(challenges, start=1):
        result = _present_challenge(i, total, challenge)
        if result is not None:
            decisions[challenge["id"]] = result

    if decisions:
        spec = apply_challenge_decisions(spec, decisions)
        print(f"\n  ✅ {len(decisions)} decision(s) added to architecture.\n")
    else:
        print("\n  No decisions made — challenges can be addressed later.\n")

    return spec