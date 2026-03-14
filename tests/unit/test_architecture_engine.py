from initializer.engine.architecture_engine import generate_architecture


def test_generate_architecture_preserves_existing_keys_and_decisions():
    spec = {
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": ["authentication", "media-library"],
        "architecture": {
            "notes": ["preserve me"],
            "style": "modular-monolith",
            "components": [
                {
                    "name": "cdn",
                    "technology": "edge-cache",
                    "role": "static delivery",
                }
            ],
            "decisions": [
                "Existing architectural decision.",
            ],
        },
    }

    architecture = generate_architecture(spec)

    assert architecture["notes"] == ["preserve me"]
    assert architecture["style"] == "modular-monolith"

    component_names = [c["name"] for c in architecture["components"]]
    assert "cdn" in component_names
    assert "frontend" in component_names
    assert "api" in component_names
    assert "database" in component_names
    assert "object-storage" in component_names

    assert "Existing architectural decision." in architecture["decisions"]
    assert "Media assets stored in object storage." in architecture["decisions"]
    assert "Authentication handled via secure session or JWT." in architecture["decisions"]


def test_generate_architecture_merges_worker_by_name_without_duplication():
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