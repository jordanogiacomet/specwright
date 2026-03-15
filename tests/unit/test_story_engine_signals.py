from initializer.engine.story_engine import generate_stories


def test_generate_stories_creates_product_shape_stories_for_backoffice():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": ["authentication", "api"],
        "capabilities": ["scheduled-jobs"],
        "stories": [],
        "discovery": {
            "decision_signals": {
                "app_shape": "backoffice",
                "primary_audience": "internal_teams",
                "core_work_features": [
                    "deadlines",
                    "report-generation",
                    "task-assignment",
                    "team-visibility",
                ],
                "needs_scheduled_jobs": True,
            },
        },
    }

    stories = generate_stories(spec)
    titles = [story["title"] for story in stories]

    assert "Build internal dashboard shell" in titles
    assert "Build backoffice application shell" in titles
    assert "Model deadlines and due dates" in titles
    assert "Implement task assignment" in titles
    assert "Implement report generation" in titles
    assert "Implement team visibility" in titles
    assert "Implement workflow automation jobs" in titles


def test_generate_stories_creates_client_portal_stories():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": ["authentication", "api", "notifications"],
        "capabilities": ["scheduled-jobs"],
        "stories": [],
        "discovery": {
            "decision_signals": {
                "app_shape": "client-portal",
                "primary_audience": "mixed",
                "core_work_features": ["approvals", "progress-tracking"],
                "needs_scheduled_jobs": True,
            },
        },
    }

    stories = generate_stories(spec)
    titles = [story["title"] for story in stories]

    assert "Build client portal shell" in titles
    assert "Implement approval workflows" in titles
    assert "Implement progress tracking" in titles
    assert "Implement notification system" in titles


def test_generate_stories_handles_project_tracking_variant():
    """project-tracking should trigger progress-tracking story."""
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": ["authentication"],
        "capabilities": [],
        "stories": [],
        "discovery": {
            "decision_signals": {
                "app_shape": "backoffice",
                "primary_audience": "internal_teams",
                "core_work_features": ["project-tracking"],
            },
        },
    }

    stories = generate_stories(spec)
    titles = [story["title"] for story in stories]

    assert "Implement progress tracking" in titles


def test_generate_stories_no_domain_stories_without_signals():
    """Without decision signals, no domain or product shape stories."""
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": ["authentication"],
        "capabilities": [],
        "stories": [],
    }

    stories = generate_stories(spec)
    titles = [story["title"] for story in stories]

    assert "Build internal dashboard shell" not in titles
    assert "Build backoffice application shell" not in titles
    assert "Model deadlines and due dates" not in titles
    assert "Implement workflow automation jobs" not in titles


def test_generate_stories_boolean_core_work_features_ignored():
    """core_work_features as boolean should not generate domain stories."""
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": ["authentication"],
        "capabilities": [],
        "stories": [],
        "discovery": {
            "decision_signals": {
                "core_work_features": True,
            },
        },
    }

    stories = generate_stories(spec)
    titles = [story["title"] for story in stories]

    assert "Model deadlines and due dates" not in titles
    assert "Implement task assignment" not in titles
    assert "Implement report generation" not in titles