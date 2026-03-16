"""Tests for the challenges engine."""

from initializer.engine.challenges_engine import (
    generate_challenges,
    apply_challenge_decisions,
)


def _make_spec(archetype="generic-web-app", features=None, capabilities=None, signals=None):
    spec = {
        "archetype": archetype,
        "features": ["authentication"] if features is None else features,
        "capabilities": [] if capabilities is None else capabilities,
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "answers": {"surface": "internal_admin_only", "deploy_target": "docker"},
        "architecture": {"components": [], "decisions": []},
    }
    if signals:
        spec["discovery"] = {"decision_signals": signals}
    return spec


# -------------------------------------------------------------------
# Challenge generation by archetype
# -------------------------------------------------------------------

class TestEditorialChallenges:
    def test_editorial_with_public_site_has_cache_invalidation(self):
        challenges = generate_challenges(_make_spec(
            "editorial-cms",
            features=["authentication", "media-library", "draft-publish"],
            capabilities=["cms", "public-site"],
        ))
        ids = [c["id"] for c in challenges]
        assert "cache-invalidation" in ids
        assert "preview-vs-production" in ids
        assert "seo-vs-auth-routes" in ids

    def test_editorial_without_public_site_no_cache_challenge(self):
        challenges = generate_challenges(_make_spec(
            "editorial-cms",
            features=["authentication"],
            capabilities=["cms"],
        ))
        ids = [c["id"] for c in challenges]
        assert "cache-invalidation" not in ids
        assert "seo-vs-auth-routes" not in ids

    def test_editorial_with_media_has_storage_challenge(self):
        challenges = generate_challenges(_make_spec(
            "editorial-cms",
            features=["authentication", "media-library"],
            capabilities=["cms"],
        ))
        ids = [c["id"] for c in challenges]
        assert "media-storage-strategy" in ids

    def test_editorial_with_draft_publish_has_versioning_challenge(self):
        challenges = generate_challenges(_make_spec(
            "editorial-cms",
            features=["authentication", "draft-publish"],
            capabilities=["cms"],
        ))
        ids = [c["id"] for c in challenges]
        assert "content-versioning" in ids

    def test_content_platform_shape_triggers_editorial_challenges(self):
        challenges = generate_challenges(_make_spec(
            "generic-web-app",
            features=["authentication", "media-library"],
            capabilities=["cms", "public-site"],
            signals={"app_shape": "content-platform"},
        ))
        ids = [c["id"] for c in challenges]
        assert "cache-invalidation" in ids


class TestBackofficeChallenges:
    def test_backoffice_has_status_model_challenge(self):
        challenges = generate_challenges(_make_spec(
            "backoffice",
            signals={"app_shape": "backoffice"},
        ))
        ids = [c["id"] for c in challenges]
        assert "status-model-design" in ids

    def test_backoffice_with_deadlines_has_overdue_challenge(self):
        challenges = generate_challenges(_make_spec(
            "backoffice",
            signals={
                "app_shape": "backoffice",
                "core_work_features": ["deadlines"],
            },
        ))
        ids = [c["id"] for c in challenges]
        assert "overdue-handling" in ids

    def test_backoffice_with_approvals_has_approval_challenge(self):
        challenges = generate_challenges(_make_spec(
            "backoffice",
            signals={
                "app_shape": "backoffice",
                "core_work_features": ["approvals"],
            },
        ))
        ids = [c["id"] for c in challenges]
        assert "approval-model" in ids

    def test_backoffice_with_reports_has_data_strategy_challenge(self):
        challenges = generate_challenges(_make_spec(
            "backoffice",
            signals={
                "app_shape": "backoffice",
                "core_work_features": ["report-generation"],
            },
        ))
        ids = [c["id"] for c in challenges]
        assert "report-data-strategy" in ids


class TestWorkOrganizerChallenges:
    def test_work_organizer_inherits_backoffice_challenges(self):
        challenges = generate_challenges(_make_spec(
            "work-organizer",
            signals={"app_shape": "internal-work-organizer"},
        ))
        ids = [c["id"] for c in challenges]
        assert "status-model-design" in ids

    def test_work_organizer_with_assignment_has_assignment_challenge(self):
        challenges = generate_challenges(_make_spec(
            "work-organizer",
            signals={
                "app_shape": "internal-work-organizer",
                "core_work_features": ["task-assignment"],
            },
        ))
        ids = [c["id"] for c in challenges]
        assert "assignment-model" in ids


class TestClientPortalChallenges:
    def test_client_portal_has_isolation_challenge(self):
        challenges = generate_challenges(_make_spec(
            "client-portal",
            signals={"app_shape": "client-portal"},
        ))
        ids = [c["id"] for c in challenges]
        assert "client-data-isolation" in ids
        assert "request-communication" in ids


class TestMarketplaceChallenges:
    def test_marketplace_with_payments_has_payment_flow(self):
        challenges = generate_challenges(_make_spec(
            "marketplace",
            features=["authentication", "payments"],
        ))
        ids = [c["id"] for c in challenges]
        assert "payment-flow" in ids
        assert "trust-and-safety" in ids

    def test_marketplace_without_payments_no_payment_flow(self):
        challenges = generate_challenges(_make_spec(
            "marketplace",
            features=["authentication"],
        ))
        ids = [c["id"] for c in challenges]
        assert "payment-flow" not in ids


class TestSaasChallenges:
    def test_saas_has_tenant_isolation(self):
        challenges = generate_challenges(_make_spec("saas-app"))
        ids = [c["id"] for c in challenges]
        assert "tenant-isolation" in ids

    def test_saas_with_billing_has_billing_model(self):
        challenges = generate_challenges(_make_spec(
            "saas-app",
            features=["authentication", "billing"],
        ))
        ids = [c["id"] for c in challenges]
        assert "billing-model" in ids


# -------------------------------------------------------------------
# Common challenges
# -------------------------------------------------------------------

class TestCommonChallenges:
    def test_i18n_capability_adds_i18n_strategy(self):
        challenges = generate_challenges(_make_spec(
            capabilities=["i18n"],
        ))
        ids = [c["id"] for c in challenges]
        assert "i18n-strategy" in ids

    def test_scheduled_jobs_adds_job_infrastructure(self):
        challenges = generate_challenges(_make_spec(
            capabilities=["scheduled-jobs"],
        ))
        ids = [c["id"] for c in challenges]
        assert "job-infrastructure" in ids

    def test_auth_feature_adds_auth_strategy(self):
        challenges = generate_challenges(_make_spec(
            features=["authentication"],
        ))
        ids = [c["id"] for c in challenges]
        assert "auth-strategy" in ids

    def test_no_auth_no_auth_challenge(self):
        challenges = generate_challenges(_make_spec(
            features=["api"],
        ))
        ids = [c["id"] for c in challenges]
        assert "auth-strategy" not in ids

    def test_i18n_default_is_b_when_cms(self):
        challenges = generate_challenges(_make_spec(
            capabilities=["i18n", "cms"],
        ))
        i18n = next(c for c in challenges if c["id"] == "i18n-strategy")
        assert i18n["default"] == "b"

    def test_i18n_default_is_c_without_cms(self):
        challenges = generate_challenges(_make_spec(
            capabilities=["i18n"],
        ))
        i18n = next(c for c in challenges if c["id"] == "i18n-strategy")
        assert i18n["default"] == "c"


# -------------------------------------------------------------------
# Challenge structure
# -------------------------------------------------------------------

class TestChallengeStructure:
    def test_every_challenge_has_required_fields(self):
        challenges = generate_challenges(_make_spec(
            "editorial-cms",
            features=["authentication", "media-library", "draft-publish"],
            capabilities=["cms", "public-site", "i18n", "scheduled-jobs"],
        ))

        for challenge in challenges:
            assert "id" in challenge, f"Missing id"
            assert "title" in challenge, f"Missing title in {challenge.get('id')}"
            assert "description" in challenge, f"Missing description in {challenge['id']}"
            assert "options" in challenge, f"Missing options in {challenge['id']}"
            assert "default" in challenge, f"Missing default in {challenge['id']}"
            assert "affects" in challenge, f"Missing affects in {challenge['id']}"
            assert len(challenge["options"]) >= 2, f"Need at least 2 options in {challenge['id']}"

    def test_every_option_has_key_label_detail(self):
        challenges = generate_challenges(_make_spec(
            "editorial-cms",
            features=["authentication", "media-library", "draft-publish"],
            capabilities=["cms", "public-site"],
        ))

        for challenge in challenges:
            for option in challenge["options"]:
                assert "key" in option, f"Missing key in {challenge['id']}"
                assert "label" in option, f"Missing label in {challenge['id']}"
                assert "detail" in option, f"Missing detail in {challenge['id']}"

    def test_default_is_valid_option_key(self):
        challenges = generate_challenges(_make_spec(
            "editorial-cms",
            features=["authentication", "media-library", "draft-publish"],
            capabilities=["cms", "public-site"],
        ))

        for challenge in challenges:
            option_keys = {o["key"] for o in challenge["options"]}
            assert challenge["default"] in option_keys, (
                f"Default '{challenge['default']}' not in options {option_keys} for {challenge['id']}"
            )

    def test_no_duplicate_ids(self):
        challenges = generate_challenges(_make_spec(
            "editorial-cms",
            features=["authentication", "media-library", "draft-publish"],
            capabilities=["cms", "public-site", "i18n", "scheduled-jobs"],
        ))
        ids = [c["id"] for c in challenges]
        assert len(ids) == len(set(ids))


# -------------------------------------------------------------------
# Apply decisions
# -------------------------------------------------------------------

class TestApplyDecisions:
    def test_applies_decision_to_architecture(self):
        spec = _make_spec()
        decisions = {
            "auth-strategy": {
                "chosen_option": "a",
                "custom_text": "",
                "option_label": "Email + password (built-in)",
                "option_detail": "Classic email/password auth.",
            },
        }

        result = apply_challenge_decisions(spec, decisions)

        assert "challenge_decisions" in result
        assert "auth-strategy" in result["challenge_decisions"]
        assert any(
            "auth-strategy" in d
            for d in result["architecture"]["decisions"]
        )

    def test_applies_custom_decision(self):
        spec = _make_spec()
        decisions = {
            "auth-strategy": {
                "chosen_option": "custom",
                "custom_text": "Use Clerk for auth with webhook sync to local DB",
                "option_label": "Custom solution",
                "option_detail": "Use Clerk for auth with webhook sync to local DB",
            },
        }

        result = apply_challenge_decisions(spec, decisions)

        assert any(
            "Clerk" in d
            for d in result["architecture"]["decisions"]
        )

    def test_does_not_duplicate_decisions(self):
        spec = _make_spec()
        spec["architecture"]["decisions"] = [
            "[auth-strategy] Email + password (built-in): Classic email/password auth."
        ]

        decisions = {
            "auth-strategy": {
                "chosen_option": "a",
                "custom_text": "",
                "option_label": "Email + password (built-in)",
                "option_detail": "Classic email/password auth.",
            },
        }

        result = apply_challenge_decisions(spec, decisions)

        auth_decisions = [
            d for d in result["architecture"]["decisions"]
            if "auth-strategy" in d
        ]
        assert len(auth_decisions) == 1

    def test_preserves_existing_architecture_decisions(self):
        spec = _make_spec()
        spec["architecture"]["decisions"] = ["Existing decision."]

        decisions = {
            "auth-strategy": {
                "chosen_option": "a",
                "custom_text": "",
                "option_label": "Email + password",
                "option_detail": "Classic auth.",
            },
        }

        result = apply_challenge_decisions(spec, decisions)

        assert "Existing decision." in result["architecture"]["decisions"]
        assert len(result["architecture"]["decisions"]) == 2


# -------------------------------------------------------------------
# Empty / edge cases
# -------------------------------------------------------------------

class TestEdgeCases:
    def test_generic_archetype_only_common_challenges(self):
        challenges = generate_challenges(_make_spec(
            "generic-web-app",
            features=["authentication"],
            capabilities=[],
        ))
        ids = [c["id"] for c in challenges]
        assert "auth-strategy" in ids
        assert "cache-invalidation" not in ids
        assert "status-model-design" not in ids

    def test_no_features_no_capabilities_returns_empty(self):
        challenges = generate_challenges(_make_spec(
            "generic-web-app",
            features=[],
            capabilities=[],
        ))
        assert challenges == []

    def test_apply_empty_decisions_is_noop(self):
        spec = _make_spec()
        original_decisions = list(spec["architecture"]["decisions"])
        result = apply_challenge_decisions(spec, {})
        assert result["architecture"]["decisions"] == original_decisions
        assert result["challenge_decisions"] == {}