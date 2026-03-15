"""Regression tests for signal governance.

These tests verify that the key bugs we fixed don't regress:
1. public-site doesn't leak into internal-only projects
2. core_work_features as boolean doesn't overwrite lists
3. engines downstream respect capabilities as source of truth
"""

from initializer.engine.capability_derivation import derive_capabilities
from initializer.engine.architecture_engine import generate_architecture
from initializer.engine.design_system_engine import generate_design_system
from initializer.engine.risk_engine import analyze_risks
from initializer.engine.constraint_engine import generate_constraints


def test_regression_internal_backoffice_no_public_site_leak():
    """Internal backoffice with confirmed needs_public_site=False
    should never have public-site in capabilities or CDN/SSR in architecture."""
    capabilities = derive_capabilities(
        archetype="generic-web-app",
        answers={"surface": "admin_plus_public_site"},
        existing_capabilities=[],
        decision_signals={
            "primary_audience": "internal_teams",
            "needs_public_site": False,
            "needs_cms": False,
            "needs_scheduled_jobs": True,
            "app_shape": "backoffice",
        },
        confirmed_signals={
            "needs_public_site": False,
        },
        has_discovery=True,
    )

    assert "public-site" not in capabilities
    assert "cms" not in capabilities
    assert "scheduled-jobs" in capabilities


def test_regression_internal_teams_inferred_public_site_not_added():
    """When AI infers needs_public_site=True for internal_teams audience,
    public-site should NOT be added without confirmation."""
    capabilities = derive_capabilities(
        archetype="generic-web-app",
        answers={"surface": "admin_plus_public_site"},
        existing_capabilities=[],
        decision_signals={
            "primary_audience": "internal_teams",
            "needs_public_site": True,
            "app_shape": "internal-work-organizer",
        },
        confirmed_signals={},
        has_discovery=True,
    )

    assert "public-site" not in capabilities


def test_regression_external_clients_inferred_public_site_is_added():
    """When AI infers needs_public_site=True for external_clients audience,
    public-site SHOULD be added even without explicit confirmation."""
    capabilities = derive_capabilities(
        archetype="generic-web-app",
        answers={"surface": "admin_plus_public_site"},
        existing_capabilities=[],
        decision_signals={
            "primary_audience": "external_clients",
            "needs_public_site": True,
            "app_shape": "client-portal",
        },
        confirmed_signals={},
        has_discovery=True,
    )

    assert "public-site" in capabilities


def test_regression_architecture_no_cdn_without_public_site():
    """Architecture should NOT have CDN/SSR decisions when public-site
    is not in capabilities."""
    spec = {
        "stack": {"frontend": "nextjs", "backend": "node-api", "database": "postgres"},
        "features": ["authentication"],
        "capabilities": ["scheduled-jobs"],
        "architecture": {"components": [], "decisions": []},
        "discovery": {
            "decision_signals": {
                "primary_audience": "internal_teams",
                "app_shape": "backoffice",
            },
        },
    }

    architecture = generate_architecture(spec)
    decisions_text = " ".join(architecture["decisions"]).lower()

    assert "cdn" not in decisions_text
    assert "ssr" not in decisions_text
    assert "isr" not in decisions_text
    assert "seo" not in decisions_text
    assert "public-facing" not in decisions_text


def test_regression_design_system_no_heroblock_without_public_site():
    """Design system should NOT have HeroBlock/Footer when public-site
    is not in capabilities."""
    spec = {
        "capabilities": ["scheduled-jobs"],
        "features": ["authentication"],
        "discovery": {
            "decision_signals": {
                "primary_audience": "internal_teams",
                "app_shape": "backoffice",
            },
        },
    }

    design_system = generate_design_system(spec)

    assert "HeroBlock" not in design_system["components"]
    assert "Footer" not in design_system["components"]
    assert "DataTable" in design_system["components"]
    assert "StatusBadge" in design_system["components"]


def test_regression_risks_no_traffic_spikes_without_public_site():
    """Risks should NOT include traffic spikes when public-site
    is not in capabilities."""
    spec = {
        "capabilities": ["scheduled-jobs"],
        "features": ["authentication"],
        "discovery": {
            "decision_signals": {
                "primary_audience": "internal_teams",
                "app_shape": "backoffice",
                "needs_scheduled_jobs": True,
            },
        },
    }

    risks = analyze_risks(spec)
    risk_titles = [r["title"] for r in risks]

    assert "Traffic spikes" not in risk_titles
    assert "Background job reliability" in risk_titles
    assert "Workflow sprawl" in risk_titles


def test_regression_constraints_internal_performance_without_public_site():
    """Constraints should use internal performance language when
    public-site is not in capabilities."""
    spec = {
        "capabilities": ["scheduled-jobs"],
        "features": ["authentication"],
        "answers": {"deploy_target": "docker"},
        "discovery": {
            "decision_signals": {
                "primary_audience": "internal_teams",
                "app_shape": "backoffice",
            },
        },
    }

    constraints = generate_constraints(spec)

    performance_text = " ".join(constraints["performance"]).lower()
    assert "authenticated" in performance_text
    assert "public" not in performance_text