"""Design System Engine.

Generates design-system guidance from product shape and structured discovery signals.
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


def generate_design_system(spec):
    capabilities = spec.get("capabilities", [])
    features = spec.get("features", [])
    signals = _get_decision_signals(spec)

    needs_public_site = signals.get("needs_public_site")
    needs_cms = signals.get("needs_cms")
    primary_audience = signals.get("primary_audience")
    app_shape = signals.get("app_shape")

    philosophy: list[str] = []
    components: list[str] = []
    patterns: list[str] = []
    recommendations: list[str] = []

    tokens = {
        "spacing_scale": "4px base grid",
        "border_radius": "6px default",
        "font_primary": "Inter",
        "font_secondary": "System UI",
    }

    if app_shape == "internal-work-organizer" or primary_audience == "internal_teams":
        _append_unique(philosophy, "Favor workflow clarity and fast task-oriented navigation.")
        _append_unique(philosophy, "Optimize for dense, readable operational interfaces.")
        _append_unique(philosophy, "Reduce cognitive load for recurring internal workflows.")

        for component in [
            "AppShell",
            "SidebarNav",
            "TopBar",
            "Button",
            "Input",
            "Textarea",
            "Select",
            "Modal",
            "Toast",
            "Dropdown",
            "DataTable",
            "FilterBar",
            "StatusBadge",
            "WorkItemCard",
            "DetailDrawer",
            "DatePicker",
            "AssigneeSelect",
        ]:
            _append_unique(components, component)

        _append_unique(patterns, "Use clear status states and visible progress markers.")
        _append_unique(patterns, "Keep common actions close to work-item context.")
        _append_unique(patterns, "Use optimistic UI carefully for low-risk edits.")
        _append_unique(patterns, "Support keyboard-friendly workflows where practical.")
    else:
        _append_unique(philosophy, "Favor clarity and content-first layout.")
        _append_unique(philosophy, "Use consistent spacing scale and typography hierarchy.")
        _append_unique(philosophy, "Minimize cognitive load across the application experience.")

        for component in [
            "Button",
            "Input",
            "Textarea",
            "Select",
            "Modal",
            "Toast",
            "Dropdown",
            "NavigationBar",
            "ContentCard",
        ]:
            _append_unique(components, component)

        _append_unique(patterns, "Provide clear status indicators for important workflow states.")
        _append_unique(patterns, "Use progressive disclosure for advanced options.")

    if needs_cms is True:
        for component in [
            "RichTextEditor",
            "MediaPicker",
            "ContentList",
            "ContentStatusBadge",
            "PublishControls",
        ]:
            _append_unique(components, component)

        _append_unique(patterns, "Preview mode should match rendered output closely.")
        _append_unique(patterns, "Use explicit draft and publish states for editorial workflows.")

    if needs_public_site is True or ("public-site" in capabilities and needs_public_site is not False):
        for component in ["NavigationBar", "HeroBlock", "Footer"]:
            _append_unique(components, component)

    if "i18n" in capabilities or signals.get("needs_i18n") is True:
        _append_unique(patterns, "Design text containers to handle locale expansion gracefully.")
        _append_unique(patterns, "Ensure locale switching is easy to find and clearly reflected in the UI.")

    if "notifications" in features:
        _append_unique(components, "NotificationCenter")
        _append_unique(patterns, "Use notifications for meaningful events, not routine noise.")

    _append_unique(recommendations, "Use Tailwind CSS or CSS variables for the token system.")
    _append_unique(recommendations, "Maintain a shared component library where possible.")
    _append_unique(recommendations, "Document component usage and accessibility expectations.")

    return {
        "philosophy": philosophy,
        "tokens": tokens,
        "components": components,
        "patterns": patterns,
        "recommendations": recommendations,
    }