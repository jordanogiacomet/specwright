"""Risk Engine.

Generates architectural and product risks from capabilities, features,
and structured discovery signals.
"""


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _append_unique_risk(target, item):
    title = item.get("title")
    for existing in target:
        if existing.get("title") == title:
            return
    target.append(item)


def analyze_risks(spec):
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    signals = _get_decision_signals(spec)

    needs_public_site = signals.get("needs_public_site")
    needs_cms = signals.get("needs_cms")
    needs_i18n = signals.get("needs_i18n")
    needs_scheduled_jobs = signals.get("needs_scheduled_jobs")
    primary_audience = signals.get("primary_audience")
    app_shape = signals.get("app_shape")

    risks: list[dict[str, str]] = []

    if needs_public_site is True or ("public-site" in capabilities and needs_public_site is not False):
        _append_unique_risk(
            risks,
            {
                "title": "Traffic spikes",
                "risk": "Public-facing traffic can fluctuate sharply.",
                "impact": "The application may become unavailable or slow during peak traffic.",
                "mitigation": "Use caching, CDN delivery, and capacity planning for anonymous traffic.",
            },
        )

    if needs_cms is True or "cms" in capabilities:
        _append_unique_risk(
            risks,
            {
                "title": "Content schema evolution",
                "risk": "Content models may evolve after launch.",
                "impact": "Schema changes can create migration and compatibility issues.",
                "mitigation": "Introduce schema versioning and a migration strategy.",
            },
        )
        _append_unique_risk(
            risks,
            {
                "title": "Media storage growth",
                "risk": "Media assets can grow quickly over time.",
                "impact": "Local storage may become insufficient or costly to manage.",
                "mitigation": "Use object storage with lifecycle and retention rules.",
            },
        )

    if needs_scheduled_jobs is True or "scheduled-jobs" in capabilities:
        _append_unique_risk(
            risks,
            {
                "title": "Background job reliability",
                "risk": "Automation depends on reliable job execution.",
                "impact": "Important workflows may not run at the intended time.",
                "mitigation": "Use a durable queue or reliable job persistence strategy.",
            },
        )
        _append_unique_risk(
            risks,
            {
                "title": "Clock drift",
                "risk": "Worker and database clocks may diverge.",
                "impact": "Scheduled tasks may run too early or too late.",
                "mitigation": "Use UTC timestamps and centralized scheduling logic.",
            },
        )

    if needs_i18n is True or "i18n" in capabilities:
        _append_unique_risk(
            risks,
            {
                "title": "Localization consistency",
                "risk": "Translations and locale-specific formatting may drift across the application.",
                "impact": "Users may experience inconsistent language, formatting, or fallback behavior.",
                "mitigation": "Define locale ownership, fallback rules, and validation for translation resources.",
            },
        )

    if app_shape == "internal-work-organizer" or primary_audience == "internal_teams":
        _append_unique_risk(
            risks,
            {
                "title": "Workflow sprawl",
                "risk": "Internal workflow requirements may expand rapidly after first adoption.",
                "impact": "The product can become hard to maintain and difficult for teams to use consistently.",
                "mitigation": "Keep the MVP focused and validate each workflow expansion with real usage.",
            },
        )
        _append_unique_risk(
            risks,
            {
                "title": "Status model complexity",
                "risk": "Work-item states and transitions may become inconsistent over time.",
                "impact": "Progress tracking and operational reporting become unreliable.",
                "mitigation": "Define a clear status model and transition rules early.",
            },
        )

    if "notifications" in features:
        _append_unique_risk(
            risks,
            {
                "title": "Notification fatigue",
                "risk": "Poorly tuned notifications can overwhelm users.",
                "impact": "Important alerts may be ignored and trust in the system may drop.",
                "mitigation": "Introduce notification preferences, priorities, and delivery rules.",
            },
        )

    return risks