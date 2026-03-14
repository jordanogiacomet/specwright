"""
Architecture Engine

Generates system architecture based on stack and features.
"""


def generate_architecture(spec):

    stack = spec.get("stack", {})
    features = spec.get("features", [])

    frontend = stack.get("frontend")
    backend = stack.get("backend")
    database = stack.get("database")

    components = []
    decisions = []

    # frontend

    if frontend:
        components.append(
            {
                "name": "frontend",
                "technology": frontend,
                "role": "user interface",
            }
        )

    # backend / api

    if backend:
        components.append(
            {
                "name": "api",
                "technology": backend,
                "role": "application logic",
            }
        )

    # database

    if database:
        components.append(
            {
                "name": "database",
                "technology": database,
                "role": "persistent storage",
            }
        )

    # media storage

    if "media-library" in features:

        components.append(
            {
                "name": "object-storage",
                "technology": "s3-compatible",
                "role": "media storage",
            }
        )

        decisions.append(
            "Media assets stored in object storage."
        )

    # background worker

    if "scheduled-publishing" in features:

        components.append(
            {
                "name": "worker",
                "technology": backend,
                "role": "background processing",
            }
        )

        decisions.append(
            "Background worker processes scheduled jobs."
        )

    # authentication

    if "authentication" in features:

        decisions.append(
            "Authentication handled via secure session or JWT."
        )

    # caching recommendation

    decisions.append(
        "Introduce caching layer for frequently accessed content."
    )

    architecture = {
        "style": "service-oriented",
        "components": components,
        "decisions": decisions,
    }

    return architecture