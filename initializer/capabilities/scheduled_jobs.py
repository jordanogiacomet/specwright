def _add_unique_component(architecture, component):
    components = architecture.setdefault("components", [])
    name = component.get("name")

    if name:
        for existing in components:
            if existing.get("name") == name:
                return

    components.append(dict(component))


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


def apply_scheduled_jobs(spec, architecture, stories):
    signals = _get_decision_signals(spec)
    features = spec.get("features", [])

    needs_scheduled_jobs = signals.get("needs_scheduled_jobs")
    needs_cms = signals.get("needs_cms")

    if needs_scheduled_jobs is False:
        return architecture, stories

    _add_unique_component(
        architecture,
        {
            "name": "worker",
            "technology": "background-worker",
            "role": "process scheduled jobs",
        },
    )

    if needs_cms is True or "scheduled-publishing" in features:
        _add_unique_decision(
            architecture,
            "Scheduled publishing requires a background worker.",
        )
        _add_unique_story(
            stories,
            "Setup job worker",
            "Create worker process responsible for scheduled publishing.",
        )
        _add_unique_story(
            stories,
            "Implement publishing scheduler",
            "Create scheduled publishing mechanism.",
        )
        return architecture, stories

    _add_unique_decision(
        architecture,
        "Automation workflows require a background worker and durable job execution strategy.",
    )

    _add_unique_story(
        stories,
        "Setup job worker",
        "Create worker process responsible for automation jobs and scheduled workflows.",
    )
    _add_unique_story(
        stories,
        "Implement scheduled automation",
        "Implement scheduled jobs and automated workflows required by the application.",
    )

    return architecture, stories