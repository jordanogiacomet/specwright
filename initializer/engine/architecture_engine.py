"""
Architecture Engine

Generates system architecture based on stack and features.
"""


GENERIC_COMPONENT_TECHNOLOGIES = {
    "background-worker",
}


def _unique(values):
    items = []

    for value in values:
        if value not in items:
            items.append(value)

    return items


def _clone_architecture(existing_architecture):
    architecture = dict(existing_architecture)
    architecture["components"] = [
        dict(component)
        for component in existing_architecture.get("components", [])
    ]
    architecture["decisions"] = list(existing_architecture.get("decisions", []))

    return architecture


def _merge_component(existing_component, incoming_component):
    merged = dict(existing_component)

    for key, value in incoming_component.items():
        if key == "name" or value in (None, "", []):
            continue

        existing_value = merged.get(key)

        if not existing_value:
            merged[key] = value
            continue

        if existing_value == value:
            continue

        chosen_value = existing_value
        alternate_value = value

        if (
            key == "technology"
            and existing_value in GENERIC_COMPONENT_TECHNOLOGIES
        ):
            chosen_value = value
            alternate_value = existing_value

        merged[key] = chosen_value

        alternatives_key = f"{key}_alternatives"
        alternatives = _unique(
            list(merged.get(alternatives_key, [])) + [alternate_value]
        )
        merged[alternatives_key] = alternatives

    return merged


def generate_architecture(spec):

    stack = spec.get("stack", {})
    features = spec.get("features", [])
    existing_architecture = spec.get("architecture") or {}

    frontend = stack.get("frontend")
    backend = stack.get("backend")
    database = stack.get("database")

    architecture = _clone_architecture(existing_architecture)
    components = architecture["components"]
    decisions = architecture["decisions"]

    def add_component(component):
        name = component.get("name")

        if name:
            for index, existing_component in enumerate(components):
                if existing_component.get("name") == name:
                    components[index] = _merge_component(
                        existing_component,
                        component,
                    )
                    return

        if component not in components:
            components.append(dict(component))

    def add_decision(decision):
        if decision not in decisions:
            decisions.append(decision)

    # frontend

    if frontend:
        add_component(
            {
                "name": "frontend",
                "technology": frontend,
                "role": "user interface",
            }
        )

    # backend / api

    if backend:
        add_component(
            {
                "name": "api",
                "technology": backend,
                "role": "application logic",
            }
        )

    # database

    if database:
        add_component(
            {
                "name": "database",
                "technology": database,
                "role": "persistent storage",
            }
        )

    # media storage

    if "media-library" in features:

        add_component(
            {
                "name": "object-storage",
                "technology": "s3-compatible",
                "role": "media storage",
            }
        )

        add_decision(
            "Media assets stored in object storage."
        )

    # background worker

    if "scheduled-publishing" in features:

        add_component(
            {
                "name": "worker",
                "technology": backend,
                "role": "background processing",
            }
        )

        add_decision(
            "Background worker processes scheduled jobs."
        )

    # authentication

    if "authentication" in features:

        add_decision(
            "Authentication handled via secure session or JWT."
        )

    # caching recommendation

    add_decision(
        "Introduce caching layer for frequently accessed content."
    )

    architecture["style"] = existing_architecture.get(
        "style",
        "service-oriented",
    )
    architecture["components"] = components
    architecture["decisions"] = decisions

    return architecture
