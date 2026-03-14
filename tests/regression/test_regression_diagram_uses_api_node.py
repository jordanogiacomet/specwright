from initializer.engine.architeture_diagram_engine import generate_architecture_diagram


def test_regression_diagram_uses_api_as_application_node_when_present():
    spec = {
        "architecture": {
            "components": [
                {"name": "cdn", "technology": "edge-cache", "role": "static delivery"},
                {"name": "frontend", "technology": "nextjs", "role": "web ui"},
                {"name": "api", "technology": "payload", "role": "application backend"},
                {"name": "database", "technology": "postgres", "role": "data storage"},
                {
                    "name": "object-storage",
                    "technology": "s3",
                    "role": "media storage",
                },
                {"name": "worker", "technology": "payload", "role": "background jobs"},
            ]
        }
    }

    diagram = generate_architecture_diagram(spec)

    assert ("frontend", "api") in diagram["edges"]
    assert ("api", "database") in diagram["edges"]
    assert ("api", "object_storage") in diagram["edges"]
    assert ("worker", "database") in diagram["edges"]
    assert ("cdn", "frontend") in diagram["edges"]

    assert ("frontend", "cms") not in diagram["edges"]
    assert ("cms", "database") not in diagram["edges"]
    assert ("cms", "object_storage") not in diagram["edges"]


def test_regression_diagram_falls_back_to_cms_when_api_is_missing():
    spec = {
        "architecture": {
            "components": [
                {"name": "frontend", "technology": "nextjs", "role": "web ui"},
                {"name": "cms", "technology": "payload", "role": "application backend"},
                {"name": "database", "technology": "postgres", "role": "data storage"},
                {
                    "name": "object-storage",
                    "technology": "s3",
                    "role": "media storage",
                },
            ]
        }
    }

    diagram = generate_architecture_diagram(spec)

    assert ("frontend", "cms") in diagram["edges"]
    assert ("cms", "database") in diagram["edges"]
    assert ("cms", "object_storage") in diagram["edges"]
    assert ("frontend", "api") not in diagram["edges"]