"""Constraint Engine.

Generates system constraints from capabilities, features, and structured discovery signals.

Key change: uses capabilities list as single source of truth for public-site,
instead of the old pattern that checked both capabilities and signals separately.
"""


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _append_unique(target, value):
    if value not in target:
        target.append(value)


def _has_public_site(capabilities):
    """Check if public-site is in the reconciled capabilities list."""
    return "public-site" in capabilities


def generate_constraints(spec):
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    signals = _get_decision_signals(spec)

    needs_i18n = signals.get("needs_i18n")
    needs_scheduled_jobs = signals.get("needs_scheduled_jobs")
    primary_audience = signals.get("primary_audience")
    app_shape = signals.get("app_shape")

    has_public = _has_public_site(capabilities)

    performance: list[str] = []
    scalability: list[str] = []
    security: list[str] = []
    operational: list[str] = []

    if has_public:
        _append_unique(performance, "Public pages should render quickly under normal load.")
        _append_unique(performance, "API responses should target low median latency for public traffic.")
        _append_unique(performance, "Public assets should be cacheable and efficiently delivered.")
    else:
        _append_unique(performance, "Authenticated application screens should respond quickly for common team workflows.")
        _append_unique(performance, "API responses should target low median latency for interactive application usage.")

    _append_unique(scalability, "System should support horizontal scaling of application servers.")
    _append_unique(scalability, "Database must support concurrent authenticated users.")

    if needs_scheduled_jobs is True or "scheduled-jobs" in capabilities:
        _append_unique(scalability, "Background job workers must scale independently from interactive application traffic.")

    _append_unique(security, "All authentication flows must enforce secure password hashing.")
    _append_unique(security, "All external APIs must require authentication or signed requests.")

    if "roles" in features:
        _append_unique(security, "Role and permission boundaries must be enforced consistently.")

    if primary_audience == "internal_teams" or app_shape == "internal-work-organizer":
        _append_unique(security, "Internal operational data must be isolated to authorized users and teams.")

    if needs_i18n is True or "i18n" in capabilities:
        _append_unique(operational, "Localization resources and locale handling must remain consistent across frontend and backend.")

    _append_unique(operational, "Application must support environment-based configuration.")
    _append_unique(operational, "Structured logging should be used for all backend services.")

    deploy_target = spec.get("answers", {}).get("deploy_target")
    if deploy_target == "docker" or deploy_target == "docker_and_k8s_later":
        _append_unique(operational, "Application must run in containerized environments.")

    return {
        "performance": performance,
        "scalability": scalability,
        "security": security,
        "operational": operational,
    }