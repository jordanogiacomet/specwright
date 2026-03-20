from initializer.ai.discovery_engine import AssistedDiscoveryResult
from initializer.ai.discovery_merge import (
    merge_assisted_discovery,
    _merge_decision_signals,
    _apply_capability_signals,
    _summary_conflicts_with_signals,
    _build_summary_from_signals,
    _canonicalize_capability,
    _normalize_feature_candidates,
    _merge_features,
)


def _base_spec(**overrides):
    """Minimal spec for testing merge functions."""
    spec = {
        "archetype": "generic-web-app",
        "archetype_data": {"id": "generic-web-app"},
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": [],
        "capabilities": [],
        "answers": {},
    }
    spec.update(overrides)
    return spec


def _empty_result(**overrides):
    """Minimal AssistedDiscoveryResult for testing."""
    defaults = dict(
        answer_updates={},
        capability_candidates=[],
        feature_candidates=[],
        decision_signals={},
        assumptions=[],
        open_questions=[],
        additional_questions=[],
        conflicts=[],
    )
    defaults.update(overrides)
    return AssistedDiscoveryResult(**defaults)


def test_merge_assisted_discovery_updates_allowed_answers_and_preserves_core_fields():
    original_spec = {
        "prompt": "Editorial CMS with admin panel and public website",
        "archetype": "editorial-cms",
        "archetype_data": {
            "id": "editorial-cms",
            "name": "editorial-cms",
            "features": ["authentication", "preview"],
            "capabilities": ["cms"],
            "stack": {
                "frontend": "nextjs",
                "backend": "payload",
                "database": "postgres",
            },
        },
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication", "preview"],
        "capabilities": ["cms"],
        "answers": {
            "project_name": "Editorial Project",
            "surface": "internal_admin_only",
        },
    }

    result = AssistedDiscoveryResult(
        answer_updates={
            "surface": "admin_plus_public_site",
            "tenant_model": "single_tenant",
            "archetype": "marketplace",  # should be ignored
            "unknown_field": "should_not_be_merged",  # should be ignored
        },
        capability_candidates=[],
        assumptions=["This likely needs a public-facing experience."],
        open_questions=["Does the project require editorial review before publishing?"],
        additional_questions=["Should scheduled publishing be enabled for MVP?"],
    )

    merged = merge_assisted_discovery(original_spec, result)

    assert merged["archetype"] == "editorial-cms"
    assert merged["archetype_data"]["id"] == "editorial-cms"
    assert merged["stack"]["frontend"] == "nextjs"
    assert merged["features"] == ["authentication", "preview"]

    assert merged["answers"]["project_name"] == "Editorial Project"
    assert merged["answers"]["surface"] == "internal_admin_only"
    assert merged["answers"]["tenant_model"] == "single_tenant"
    assert "unknown_field" not in merged["answers"]
    assert "archetype" not in merged["answers"]

    assert merged["discovery"]["assisted"] is True
    assert merged["discovery"]["assumptions"] == [
        "This likely needs a public-facing experience."
    ]
    assert merged["discovery"]["open_questions"] == [
        "Does the project require editorial review before publishing?"
    ]
    assert merged["discovery"]["additional_questions"] == [
        "Should scheduled publishing be enabled for MVP?"
    ]


def test_merge_assisted_discovery_adds_only_valid_capability_candidates():
    original_spec = {
        "archetype": "editorial-cms",
        "archetype_data": {"id": "editorial-cms"},
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication"],
        "capabilities": ["cms"],
        "answers": {},
    }

    result = AssistedDiscoveryResult(
        answer_updates={},
        capability_candidates=[
            "public-site",
            "scheduled-jobs",
            "not-a-real-capability",
            "cms",
            "public-site",
        ],
        assumptions=[],
        open_questions=[],
        additional_questions=[],
    )

    merged = merge_assisted_discovery(original_spec, result)

    assert merged["capabilities"] == ["cms", "public-site", "scheduled-jobs"]
    assert "not-a-real-capability" not in merged["capabilities"]


def test_merge_assisted_discovery_merges_discovery_metadata_without_duplication():
    original_spec = {
        "archetype": "editorial-cms",
        "archetype_data": {"id": "editorial-cms"},
        "stack": {"frontend": "nextjs", "backend": "payload", "database": "postgres"},
        "features": ["authentication"],
        "capabilities": ["cms"],
        "answers": {},
        "discovery": {
            "assisted": True,
            "assumptions": ["Existing assumption"],
            "open_questions": ["Existing question"],
            "additional_questions": ["Existing additional question"],
            "capability_candidates": ["public-site"],
        },
    }

    result = AssistedDiscoveryResult(
        answer_updates={},
        capability_candidates=["public-site", "i18n"],
        assumptions=["Existing assumption", "New assumption"],
        open_questions=["Existing question", "New question"],
        additional_questions=[
            "Existing additional question",
            "New additional question",
        ],
    )

    merged = merge_assisted_discovery(original_spec, result)

    assert merged["discovery"]["assisted"] is True
    assert merged["discovery"]["assumptions"] == [
        "Existing assumption",
        "New assumption",
    ]
    assert merged["discovery"]["open_questions"] == [
        "Existing question",
        "New question",
    ]
    assert merged["discovery"]["additional_questions"] == [
        "Existing additional question",
        "New additional question",
    ]
    assert merged["discovery"]["capability_candidates"] == [
        "public-site",
        "i18n",
    ]


# -------------------------------------------------------
# Empty / null discovery inputs
# -------------------------------------------------------


def test_merge_with_empty_discovery_result():
    spec = _base_spec(capabilities=["cms"], features=["authentication"])
    result = _empty_result()
    merged = merge_assisted_discovery(spec, result)

    assert merged["capabilities"] == ["cms"]
    assert merged["features"] == ["authentication"]
    assert merged["discovery"]["assisted"] is True


def test_merge_with_no_prior_discovery():
    """Spec has no discovery key at all."""
    spec = _base_spec()
    assert "discovery" not in spec

    result = _empty_result(
        decision_signals={"needs_cms": True},
        capability_candidates=["cms"],
    )
    merged = merge_assisted_discovery(spec, result)
    assert "discovery" in merged
    assert merged["discovery"]["assisted"] is True


# -------------------------------------------------------
# Decision signal merging
# -------------------------------------------------------


def test_merge_decision_signals_incoming_applied():
    spec = _base_spec()
    effective, inferred, confirmed = _merge_decision_signals(
        spec, {"app_shape": "backoffice", "needs_cms": False}
    )
    assert effective["app_shape"] == "backoffice"
    assert effective["needs_cms"] is False
    assert inferred["app_shape"] == "backoffice"
    assert len(confirmed) == 0


def test_merge_decision_signals_confirmed_wins_over_incoming():
    """User followup answers take precedence over AI inference."""
    spec = _base_spec()
    spec["discovery"] = {
        "followup_answers": {
            "q1": {
                "signal_key": "needs_public_site",
                "value": True,
            },
        }
    }
    effective, inferred, confirmed = _merge_decision_signals(
        spec, {"needs_public_site": False}
    )
    # Confirmed (True from user) should win over AI inference (False)
    assert effective["needs_public_site"] is True


# -------------------------------------------------------
# Capability signal application
# -------------------------------------------------------


def test_apply_capability_signals_adds_cms_when_true():
    caps, added, removed = _apply_capability_signals(
        [], {"needs_cms": True}, {}
    )
    assert "cms" in caps
    assert "cms" in added


def test_apply_capability_signals_removes_cms_when_false():
    caps, added, removed = _apply_capability_signals(
        ["cms"], {"needs_cms": False}, {}
    )
    assert "cms" not in caps
    assert "cms" in removed


def test_apply_capability_signals_internal_audience_removes_public_site():
    caps, added, removed = _apply_capability_signals(
        ["public-site"],
        {"primary_audience": "internal_teams", "needs_public_site": None},
        {},
    )
    assert "public-site" not in caps


def test_apply_capability_signals_confirmed_public_site_kept():
    caps, added, removed = _apply_capability_signals(
        [],
        {"needs_public_site": True, "primary_audience": "internal_teams"},
        {"needs_public_site": True},  # user confirmed
    )
    assert "public-site" in caps


def test_apply_capability_signals_i18n():
    caps, _, _ = _apply_capability_signals([], {"needs_i18n": True}, {})
    assert "i18n" in caps

    caps2, _, _ = _apply_capability_signals(["i18n"], {"needs_i18n": False}, {})
    assert "i18n" not in caps2


def test_apply_capability_signals_scheduled_jobs():
    caps, _, _ = _apply_capability_signals([], {"needs_scheduled_jobs": True}, {})
    assert "scheduled-jobs" in caps


# -------------------------------------------------------
# Summary conflict detection
# -------------------------------------------------------


def test_summary_conflicts_with_external_clients_and_internal_audience():
    assert _summary_conflicts_with_signals(
        "A public-facing dashboard for external clients",
        {"primary_audience": "internal_teams"},
    )


def test_summary_no_conflict_when_audience_matches():
    assert not _summary_conflicts_with_signals(
        "Internal team dashboard",
        {"primary_audience": "internal_teams"},
    )


def test_summary_conflicts_cms_mention_when_no_cms():
    assert _summary_conflicts_with_signals(
        "A content management system for blog posts",
        {"needs_cms": False},
    )


def test_summary_no_conflict_with_empty_summary():
    assert not _summary_conflicts_with_signals(
        "",
        {"primary_audience": "internal_teams"},
    )


# -------------------------------------------------------
# Summary building from signals
# -------------------------------------------------------


def test_build_summary_from_signals_internal_work_organizer():
    summary = _build_summary_from_signals(
        None, None, {"app_shape": "internal-work-organizer"}
    )
    assert "Internal work organization tool" in summary


def test_build_summary_includes_core_features():
    summary = _build_summary_from_signals(
        None, None,
        {"app_shape": "backoffice", "core_work_features": ["invoicing", "reporting"]},
    )
    assert "invoicing" in summary
    assert "reporting" in summary


def test_build_summary_includes_i18n_and_scheduled():
    summary = _build_summary_from_signals(
        None, None,
        {"app_shape": "backoffice", "needs_i18n": True, "needs_scheduled_jobs": True},
    )
    assert "multilingual" in summary
    assert "scheduled" in summary


# -------------------------------------------------------
# Capability canonicalization
# -------------------------------------------------------


def test_canonicalize_known_capability():
    assert _canonicalize_capability("cms") == "cms"
    assert _canonicalize_capability("public-site") == "public-site"
    assert _canonicalize_capability("i18n") == "i18n"


def test_canonicalize_unknown_capability():
    assert _canonicalize_capability("not-a-capability") is None


# -------------------------------------------------------
# Feature merging
# -------------------------------------------------------


def test_merge_features_deduplicates():
    merged, applied = _merge_features(
        ["authentication", "roles"],
        ["authentication", "media-library"],
    )
    assert merged.count("authentication") == 1
    assert "media-library" in merged
    assert "roles" in merged
    assert "media-library" in applied
    assert "authentication" not in applied


def test_merge_features_empty_inputs():
    merged, applied = _merge_features([], [])
    assert merged == []
    assert applied == []


# -------------------------------------------------------
# Full merge with decision signals
# -------------------------------------------------------


def test_merge_decision_signals_add_and_remove_capabilities():
    spec = _base_spec(capabilities=["cms", "i18n"])
    result = _empty_result(
        decision_signals={"needs_i18n": False, "needs_scheduled_jobs": True},
    )
    merged = merge_assisted_discovery(spec, result)
    assert "i18n" not in merged["capabilities"]
    assert "scheduled-jobs" in merged["capabilities"]


def test_merge_preserves_immutable_answers():
    """project_name and surface should not be overwritten by AI."""
    spec = _base_spec(answers={
        "project_name": "My Project",
        "surface": "internal_admin_only",
    })
    result = _empty_result(
        answer_updates={
            "project_name": "AI Renamed Project",
            "surface": "admin_plus_public_site",
            "workflow": "kanban",
        },
    )
    merged = merge_assisted_discovery(spec, result)
    assert merged["answers"]["project_name"] == "My Project"
    assert merged["answers"]["surface"] == "internal_admin_only"
    assert merged["answers"]["workflow"] == "kanban"


def test_merge_feature_candidates_added():
    spec = _base_spec(
        features=["authentication"],
        archetype_data={
            "id": "generic-web-app",
            "features": ["authentication", "roles", "media-library"],
        },
    )
    result = _empty_result(feature_candidates=["roles", "media-library"])
    merged = merge_assisted_discovery(spec, result)
    assert "roles" in merged["features"]
    assert "media-library" in merged["features"]