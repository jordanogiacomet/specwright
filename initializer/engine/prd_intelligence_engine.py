"""
PRD Intelligence Engine

Enriches PRD with product thinking elements derived from
archetype, app_shape, primary_audience, and decision signals.
"""


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _normalize_list(value):
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def generate_prd_intelligence(spec):

    archetype = spec.get("archetype")
    answers = spec.get("answers", {})
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    signals = _get_decision_signals(spec)

    app_shape = signals.get("app_shape")
    primary_audience = signals.get("primary_audience")
    core_work_features = _normalize_list(signals.get("core_work_features", []))

    intelligence = {
        "problem_statement": "",
        "personas": [],
        "success_metrics": [],
        "scope": {
            "in_scope": [],
            "out_of_scope": [],
        },
        "assumptions": [],
    }

    # --------------------------------------------------
    # PROBLEM STATEMENT
    # --------------------------------------------------

    if archetype == "editorial-cms" or app_shape == "content-platform":
        intelligence["problem_statement"] = (
            "Organizations often need to manage structured editorial content "
            "and publish it across digital surfaces without tightly coupling "
            "content management to frontend presentation."
        )
    elif app_shape == "internal-work-organizer":
        intelligence["problem_statement"] = (
            "Teams need a structured way to organize work, track progress, "
            "and coordinate across team members without relying on ad-hoc "
            "tools that fragment visibility and accountability."
        )
    elif app_shape == "backoffice":
        intelligence["problem_statement"] = (
            "Operations teams need a centralized system to manage day-to-day "
            "workflows, process operational data, and maintain visibility "
            "across team activities and responsibilities."
        )
    elif app_shape == "client-portal":
        intelligence["problem_statement"] = (
            "Clients need a structured way to submit requests, track their "
            "status, and interact with the internal team without relying on "
            "email or unstructured communication channels."
        )
    elif app_shape == "worker-pipeline":
        intelligence["problem_statement"] = (
            "The system needs to process recurring or triggered workflows "
            "reliably, with visibility into job status and failure handling."
        )
    elif archetype == "marketplace":
        intelligence["problem_statement"] = (
            "Buyers and sellers need a trusted platform to discover, transact, "
            "and manage exchanges with transparent pricing and reviews."
        )
    elif archetype == "saas-app":
        intelligence["problem_statement"] = (
            "Users need a managed application that provides ongoing value "
            "through a subscription model with reliable access and clear "
            "account management."
        )
    else:
        intelligence["problem_statement"] = (
            "The system aims to solve a defined operational workflow by "
            "providing a structured backend and scalable architecture."
        )

    # --------------------------------------------------
    # PERSONAS
    # --------------------------------------------------

    if archetype == "editorial-cms" or app_shape == "content-platform":
        intelligence["personas"] = [
            {"name": "Content Editor", "goal": "Create and publish editorial content quickly."},
            {"name": "Administrator", "goal": "Manage users, roles, and system configuration."},
        ]
        if "public-site" in capabilities:
            intelligence["personas"].append(
                {"name": "Site Visitor", "goal": "Consume published content through the public website."}
            )

    elif app_shape == "internal-work-organizer" or (primary_audience == "internal_teams" and app_shape in (None, "unknown")):
        intelligence["personas"] = [
            {"name": "Team Member", "goal": "Track assigned work and update progress efficiently."},
            {"name": "Team Lead", "goal": "Monitor team workload, deadlines, and overall progress."},
            {"name": "Administrator", "goal": "Manage users, teams, and system configuration."},
        ]

    elif app_shape == "backoffice":
        intelligence["personas"] = [
            {"name": "Operations Staff", "goal": "Process daily operational tasks and manage records."},
            {"name": "Operations Manager", "goal": "Monitor team output, generate reports, and manage workload."},
            {"name": "Administrator", "goal": "Manage users, roles, and system configuration."},
        ]

    elif app_shape == "client-portal":
        intelligence["personas"] = [
            {"name": "Client User", "goal": "Submit requests and track their status."},
            {"name": "Internal Reviewer", "goal": "Review, approve, or respond to client requests."},
            {"name": "Administrator", "goal": "Manage users, access control, and system configuration."},
        ]

    elif archetype == "marketplace":
        intelligence["personas"] = [
            {"name": "Buyer", "goal": "Find and purchase products or services."},
            {"name": "Seller", "goal": "List offerings and manage orders."},
            {"name": "Administrator", "goal": "Manage the platform, users, and disputes."},
        ]

    elif archetype == "saas-app":
        intelligence["personas"] = [
            {"name": "End User", "goal": "Use the application to accomplish their primary workflow."},
            {"name": "Account Admin", "goal": "Manage team members, billing, and account settings."},
            {"name": "Platform Admin", "goal": "Monitor system health and manage tenants."},
        ]

    else:
        intelligence["personas"] = [
            {"name": "Primary User", "goal": "Accomplish core workflows provided by the application."},
            {"name": "Administrator", "goal": "Manage users and system configuration."},
        ]

    # --------------------------------------------------
    # SUCCESS METRICS
    # --------------------------------------------------

    metrics = []

    if archetype == "editorial-cms" or app_shape == "content-platform":
        metrics.append("Content publishing time reduced compared to manual workflows.")
        metrics.append("Editorial users can publish content without developer intervention.")

    if app_shape == "internal-work-organizer" or app_shape == "backoffice":
        metrics.append("Team members can track and update work status without external tools.")
        metrics.append("Operational visibility improves across team activities.")

    if app_shape == "client-portal":
        metrics.append("Clients can submit and track requests without email or phone.")
        metrics.append("Internal response time to client requests improves measurably.")

    if "deadlines" in core_work_features:
        metrics.append("Overdue work items are surfaced and addressed proactively.")

    if "report-generation" in core_work_features:
        metrics.append("Operational reports are generated automatically without manual data gathering.")

    metrics.append("System availability above 99.5%.")

    if "public-site" in capabilities:
        metrics.append("Public pages load under acceptable performance thresholds.")

    intelligence["success_metrics"] = metrics

    # --------------------------------------------------
    # SCOPE
    # --------------------------------------------------

    in_scope = []
    out_of_scope = []

    if archetype == "editorial-cms" or app_shape == "content-platform":
        in_scope.append("Core content management workflows.")
        in_scope.append("Authentication and role-based access control.")
        if "public-site" in capabilities:
            in_scope.append("Public content delivery via frontend.")
        out_of_scope.append("Advanced marketing automation.")

    elif app_shape in ("internal-work-organizer", "backoffice"):
        in_scope.append("Core work management workflows.")
        in_scope.append("Authentication and role-based access control.")
        if core_work_features:
            in_scope.append(f"Core features: {', '.join(core_work_features)}.")
        out_of_scope.append("Public-facing marketing or content pages.")
        out_of_scope.append("Advanced analytics dashboards beyond operational reporting.")

    elif app_shape == "client-portal":
        in_scope.append("Client request submission and tracking.")
        in_scope.append("Internal review and approval workflows.")
        in_scope.append("Authentication and role-based access control.")
        out_of_scope.append("Full CRM or customer relationship management.")

    else:
        in_scope.append("Core application workflows.")
        in_scope.append("Authentication and access control.")

    if "scheduled-jobs" in capabilities:
        in_scope.append("Background job processing and automation.")

    if "i18n" in capabilities:
        in_scope.append("Multi-language support.")

    out_of_scope.append("Complex analytics dashboards not defined in the initial spec.")
    out_of_scope.append("External integrations not required for core workflow.")

    intelligence["scope"]["in_scope"] = in_scope
    intelligence["scope"]["out_of_scope"] = _dedupe(out_of_scope)

    # --------------------------------------------------
    # ASSUMPTIONS
    # --------------------------------------------------

    assumptions = []

    if primary_audience == "internal_teams":
        assumptions.append("Primary users are internal staff with appropriate training.")
    elif primary_audience == "external_clients":
        assumptions.append("External clients will access the system through authenticated sessions.")
    elif primary_audience == "mixed":
        assumptions.append("Both internal teams and external clients will use the system with appropriate access controls.")

    assumptions.append("Initial traffic will be moderate.")
    assumptions.append("System will evolve after MVP validation.")

    if "scheduled-jobs" in capabilities:
        assumptions.append("Background job infrastructure will be available in the deployment environment.")

    intelligence["assumptions"] = assumptions

    return intelligence


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result