from initializer.engine.prd_intelligence_engine import generate_prd_intelligence


def test_prd_intelligence_backoffice_shape():
    spec = {
        "archetype": "generic-web-app",
        "capabilities": ["scheduled-jobs"],
        "features": ["authentication", "api"],
        "answers": {"surface": "internal_admin_only"},
        "discovery": {
            "decision_signals": {
                "app_shape": "backoffice",
                "primary_audience": "internal_teams",
                "core_work_features": ["deadlines", "report-generation"],
                "needs_scheduled_jobs": True,
            },
        },
    }

    intelligence = generate_prd_intelligence(spec)

    assert "operations" in intelligence["problem_statement"].lower()
    assert len(intelligence["personas"]) == 3

    persona_names = [p["name"] for p in intelligence["personas"]]
    assert "Operations Staff" in persona_names
    assert "Operations Manager" in persona_names

    assert any("deadlines" in item.lower() or "overdue" in item.lower() for item in intelligence["success_metrics"])
    assert any("report" in item.lower() for item in intelligence["success_metrics"])

    assert any("internal" in item.lower() or "staff" in item.lower() for item in intelligence["assumptions"])
    assert any("background" in item.lower() or "scheduled" in item.lower() for item in intelligence["assumptions"])


def test_prd_intelligence_client_portal_shape():
    spec = {
        "archetype": "generic-web-app",
        "capabilities": ["public-site", "scheduled-jobs"],
        "features": ["authentication", "api", "notifications"],
        "answers": {"surface": "admin_plus_public_site"},
        "discovery": {
            "decision_signals": {
                "app_shape": "client-portal",
                "primary_audience": "mixed",
            },
        },
    }

    intelligence = generate_prd_intelligence(spec)

    assert "client" in intelligence["problem_statement"].lower()

    persona_names = [p["name"] for p in intelligence["personas"]]
    assert "Client User" in persona_names
    assert "Internal Reviewer" in persona_names

    assert any("public" in item.lower() or "performance" in item.lower() for item in intelligence["success_metrics"])


def test_prd_intelligence_editorial_cms():
    spec = {
        "archetype": "editorial-cms",
        "capabilities": ["cms", "public-site"],
        "features": ["authentication", "roles", "media-library"],
        "answers": {"surface": "admin_plus_public_site"},
        "discovery": {
            "decision_signals": {
                "app_shape": "content-platform",
                "primary_audience": "external_clients",
            },
        },
    }

    intelligence = generate_prd_intelligence(spec)

    assert "editorial" in intelligence["problem_statement"].lower() or "content" in intelligence["problem_statement"].lower()

    persona_names = [p["name"] for p in intelligence["personas"]]
    assert "Content Editor" in persona_names
    assert "Site Visitor" in persona_names

    assert any("publishing" in item.lower() for item in intelligence["success_metrics"])


def test_prd_intelligence_internal_work_organizer():
    spec = {
        "archetype": "generic-web-app",
        "capabilities": ["scheduled-jobs", "i18n"],
        "features": ["authentication", "api"],
        "answers": {"surface": "internal_admin_only"},
        "discovery": {
            "decision_signals": {
                "app_shape": "internal-work-organizer",
                "primary_audience": "internal_teams",
                "core_work_features": ["deadlines", "progress-tracking"],
                "needs_i18n": True,
                "needs_scheduled_jobs": True,
            },
        },
    }

    intelligence = generate_prd_intelligence(spec)

    assert "work" in intelligence["problem_statement"].lower() or "team" in intelligence["problem_statement"].lower()

    persona_names = [p["name"] for p in intelligence["personas"]]
    assert "Team Member" in persona_names
    assert "Team Lead" in persona_names

    assert "Multi-language support." in intelligence["scope"]["in_scope"]
    assert any("public" in item.lower() for item in intelligence["scope"]["out_of_scope"])


def test_prd_intelligence_no_public_site_in_scope():
    """Without public-site capability, no public performance metrics."""
    spec = {
        "archetype": "generic-web-app",
        "capabilities": [],
        "features": ["authentication"],
        "answers": {"surface": "internal_admin_only"},
        "discovery": {
            "decision_signals": {
                "primary_audience": "internal_teams",
            },
        },
    }

    intelligence = generate_prd_intelligence(spec)

    assert not any("public pages" in item.lower() for item in intelligence["success_metrics"])