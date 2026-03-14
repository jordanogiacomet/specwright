def _add_unique_decision(architecture, decision):
    decisions = architecture.setdefault("decisions", [])
    if decision not in decisions:
        decisions.append(decision)


def _add_unique_story(stories, title, description):
    for story in stories:
        if story.get("title") == title:
            return

    stories.append(
        {
            "id": f"ST-{len(stories)+1:03}",
            "title": title,
            "description": description,
        }
    )


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def apply_i18n(spec, architecture, stories):
    signals = _get_decision_signals(spec)

    needs_i18n = signals.get("needs_i18n")
    needs_cms = signals.get("needs_cms")
    primary_audience = signals.get("primary_audience")

    if needs_i18n is False:
        return architecture, stories

    if needs_cms is True:
        _add_unique_decision(
            architecture,
            "Content models must support locale-aware fields and fallback rules.",
        )
        _add_unique_story(
            stories,
            "Add locale support",
            "Add locale fields and fallback rules to content models.",
        )
        _add_unique_story(
            stories,
            "Implement locale routing",
            "Add locale-aware routing in the frontend experience.",
        )
        return architecture, stories

    _add_unique_decision(
        architecture,
        "Application UI and APIs must support locale-aware text, formatting, and translation resources.",
    )

    if primary_audience == "internal_teams":
        _add_unique_story(
            stories,
            "Add application locale support",
            "Add translation resources and locale-aware formatting to the internal application UI.",
        )
    else:
        _add_unique_story(
            stories,
            "Add application locale support",
            "Add translation resources and locale-aware formatting across the application experience.",
        )

    _add_unique_story(
        stories,
        "Implement locale selection",
        "Allow users to choose locale and ensure locale-aware rendering and formatting.",
    )

    return architecture, stories