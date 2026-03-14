"""Architecture Engine.

Generates system architecture based on stack, features, capabilities,
and structured discovery signals.

Key change: public-site related decisions (CDN, SSR/ISR, public traffic
caching) are only generated when public-site is actually in capabilities.
The old pattern `"public-site" in capabilities and needs_public_site is not False`
allowed leakage when public-site survived without confirmation.  Now the
capabilities list is the single source of truth — if capability_derivation
and discovery_merge did their job, public-site won't be in capabilities
unless it was justified.
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
        dict(component) for component in existing_architecture.get("components", [])
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

        if key == "technology" and existing_value in GENERIC_COMPONENT_TECHNOLOGIES:
            chosen_value = value
            alternate_value = existing_value

        merged[key] = chosen_value
        alternatives_key = f"{key}_alternatives"
        alternatives = _unique(list(merged.get(alternatives_key, [])) + [alternate_value])
        merged[alternatives_key] = alternatives

    return merged


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _core_features(signals):
    value = signals.get("core_work_features", [])
    if not isinstance(value, list):
        return []

    items = []
    for item in value:
        if isinstance(item, str):
            text = item.strip().lower()
            if text and text not in items:
                items.append(text)
    return items


def _has_public_site(capabilities):
    """Check if public-site is in the reconciled capabilities list.
    This is the single source of truth — it means capability_derivation
    and discovery_merge have already validated whether public-site
    should be present."""
    return "public-site" in capabilities


def generate_architecture(spec):
    stack = spec.get("stack", {})
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    existing_architecture = spec.get("architecture") or {}
    signals = _get_decision_signals(spec)

    frontend = stack.get("frontend")
    backend = stack.get("backend")
    database = stack.get("database")

    needs_cms = signals.get("needs_cms")
    needs_i18n = signals.get("needs_i18n")
    needs_scheduled_jobs = signals.get("needs_scheduled_jobs")
    primary_audience = signals.get("primary_audience")
    app_shape = signals.get("app_shape")
    core_work_features = _core_features(signals)

    has_public = _has_public_site(capabilities)

    architecture = _clone_architecture(existing_architecture)
    components = architecture["components"]
    decisions = architecture["decisions"]

    def add_component(component):
        name = component.get("name")
        if name:
            for index, existing_component in enumerate(components):
                if existing_component.get("name") == name:
                    components[index] = _merge_component(existing_component, component)
                    return

        if component not in components:
            components.append(dict(component))

    def add_decision(decision):
        if decision not in decisions:
            decisions.append(decision)

    if frontend:
        add_component(
            {
                "name": "frontend",
                "technology": frontend,
                "role": "user interface",
            }
        )

    if backend:
        add_component(
            {
                "name": "api",
                "technology": backend,
                "role": "application logic",
            }
        )

    if database:
        add_component(
            {
                "name": "database",
                "technology": database,
                "role": "persistent storage",
            }
        )

    if "media-library" in features:
        add_component(
            {
                "name": "object-storage",
                "technology": "s3-compatible",
                "role": "media storage",
            }
        )
        add_decision("Media assets stored in object storage.")

    if "scheduled-publishing" in features or "scheduled-jobs" in capabilities or needs_scheduled_jobs is True:
        add_component(
            {
                "name": "worker",
                "technology": backend or "background-worker",
                "role": "background processing",
            }
        )
        add_decision("Background worker processes scheduled jobs.")

    if "authentication" in features:
        add_decision("Authentication handled via secure session or JWT.")

    if "roles" in features:
        add_decision("Authorization must enforce role and permission boundaries.")

    # Public-site decisions ONLY when public-site is in reconciled capabilities
    if has_public:
        add_decision("Public-facing pages should use caching and delivery strategies appropriate for anonymous traffic.")
        add_decision("SEO-sensitive public pages should use rendering strategies such as SSR or ISR when beneficial.")

    if needs_i18n is True:
        if needs_cms is True:
            add_decision("Content models must support locale-aware fields and fallback rules.")
        else:
            add_decision("Application UI and APIs must support locale-aware text, formatting, and translation resources.")

    if needs_scheduled_jobs is True:
        add_decision("Automation workflows require a background worker and durable job execution strategy.")

    if app_shape == "internal-work-organizer":
        add_decision("Model work items, deadlines, ownership, and progress explicitly in the application domain.")
        add_decision("Prioritize internal workflow clarity and fast task-oriented interactions.")

    if primary_audience == "internal_teams" and not has_public:
        add_decision("Prioritize internal dashboard and workflow ergonomics over public-site delivery concerns.")

    if "deadlines" in core_work_features:
        add_decision("Work items should support due dates, deadline validation, and overdue detection.")

    if "progress-tracking" in core_work_features:
        add_decision("Work items should support explicit status progression and progress visibility.")

    if "task-assignment" in core_work_features:
        add_decision("Ownership and assignment must be modeled for teams and individual users.")

    if "reminders" in core_work_features:
        add_decision("Reminder workflows should be driven by scheduled jobs and configurable trigger rules.")

    if "report-generation" in core_work_features:
        add_decision("Operational reporting should be generated from durable domain data and background jobs when needed.")

    add_decision("Implement structured logging.")
    add_decision("Add health check endpoints.")
    add_decision("Use connection pooling.")
    add_decision("Add automated database backups.")

    if has_public:
        add_decision("Introduce caching for frequently accessed public content.")
    else:
        add_decision("Introduce caching for frequently accessed application data where beneficial.")

    architecture["style"] = existing_architecture.get("style", "service-oriented")
    architecture["components"] = components
    architecture["decisions"] = decisions

    return architecture