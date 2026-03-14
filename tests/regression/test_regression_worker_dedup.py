from initializer.engine.architecture_engine import generate_architecture


def test_regression_scheduled_publishing_does_not_duplicate_worker():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["scheduled-publishing"],
        "architecture": {
            "components": [
                {
                    "name": "worker",
                    "technology": "background-worker",
                    "role": "process scheduled jobs",
                }
            ],
            "decisions": [
                "Scheduled publishing requires a background worker",
            ],
        },
    }

    architecture = generate_architecture(spec)

    workers = [c for c in architecture["components"] if c["name"] == "worker"]
    assert len(workers) == 1

    worker = workers[0]

    assert worker["technology"] == "payload"
    assert "background-worker" in worker["technology_alternatives"]

    assert worker["role"] == "process scheduled jobs"
    assert "background processing" in worker["role_alternatives"]

    assert "Background worker processes scheduled jobs." in architecture["decisions"]


def test_regression_generated_architecture_keeps_unique_component_names():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["media-library", "scheduled-publishing"],
        "architecture": {
            "components": [
                {
                    "name": "worker",
                    "technology": "background-worker",
                    "role": "process scheduled jobs",
                },
                {
                    "name": "cdn",
                    "technology": "edge-cache",
                    "role": "static delivery",
                },
            ],
            "decisions": [],
        },
    }

    architecture = generate_architecture(spec)

    component_names = [component["name"] for component in architecture["components"]]
    assert len(component_names) == len(set(component_names))

    assert "worker" in component_names
    assert "cdn" in component_names
    assert "frontend" in component_names
    assert "api" in component_names
    assert "database" in component_names
    assert "object-storage" in component_names