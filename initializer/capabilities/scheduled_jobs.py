"""
Scheduled jobs capability handler.

Adds worker component, job-related decisions, and setup/implementation stories
with acceptance criteria, scope boundaries, and validation.
"""


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


def _story_exists(stories, title):
    return any(story.get("title") == title for story in stories)


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

        if not _story_exists(stories, "Setup job worker"):
            stories.append({
                "id": f"ST-{len(stories)+1:03}",
                "title": "Setup job worker",
                "description": "Create worker process responsible for scheduled publishing.",
                "acceptance_criteria": [
                    "Worker process starts and connects to the database",
                    "Worker runs on a configurable interval",
                    "Worker logs execution start and completion",
                    "Worker does not block the main application server",
                ],
                "scope_boundaries": [
                    "Do NOT implement specific job logic — only the worker infrastructure",
                    "Do NOT implement job management UI",
                ],
                "expected_files": [
                    "src/jobs/index.ts",
                    "src/lib/scheduler.ts",
                ],
                "depends_on": ["bootstrap.backend"],
                "validation": {
                    "commands": ["npm run build"],
                    "manual_check": "Worker process starts and logs heartbeat",
                },
            })

        if not _story_exists(stories, "Implement publishing scheduler"):
            stories.append({
                "id": f"ST-{len(stories)+1:03}",
                "title": "Implement publishing scheduler",
                "description": "Create scheduled publishing mechanism.",
                "acceptance_criteria": [
                    "Content with a scheduled publish date is published automatically",
                    "Scheduler checks for due content on each run",
                    "Published content is visible on the appropriate surface",
                    "Failed publish attempts are logged",
                ],
                "scope_boundaries": [
                    "Do NOT implement scheduled unpublishing",
                    "Do NOT implement complex retry logic — simple retry on next run is sufficient",
                ],
                "expected_files": [
                    "src/jobs/publish-scheduled.ts",
                ],
                "depends_on": ["feature.draft-publish"],
                "validation": {
                    "commands": ["npm run build", "npm test"],
                    "manual_check": "Set publishAt to near future, verify content publishes automatically",
                },
            })

        return architecture, stories

    # Non-CMS scheduled jobs
    _add_unique_decision(
        architecture,
        "Automation workflows require a background worker and durable job execution strategy.",
    )

    if not _story_exists(stories, "Setup job worker"):
        stories.append({
            "id": f"ST-{len(stories)+1:03}",
            "title": "Setup job worker",
            "description": "Create worker process responsible for automation jobs and scheduled workflows.",
            "acceptance_criteria": [
                "Worker process starts and connects to the database",
                "Worker runs on a configurable interval",
                "Worker logs execution start and completion",
                "Worker does not block the main application server",
            ],
            "scope_boundaries": [
                "Do NOT implement specific job logic — only the worker infrastructure",
                "Do NOT implement job management UI",
            ],
            "expected_files": [
                "src/jobs/index.ts",
                "src/lib/scheduler.ts",
            ],
            "depends_on": ["bootstrap.backend"],
            "validation": {
                "commands": ["npm run build"],
                "manual_check": "Worker process starts and logs heartbeat",
            },
        })

    if not _story_exists(stories, "Implement scheduled automation"):
        stories.append({
            "id": f"ST-{len(stories)+1:03}",
            "title": "Implement scheduled automation",
            "description": "Implement scheduled jobs and automated workflows required by the application.",
            "acceptance_criteria": [
                "At least one automation job is implemented and runs on schedule",
                "Job execution results are logged",
                "Failed jobs are flagged for retry or manual intervention",
            ],
            "scope_boundaries": [
                "Do NOT implement a distributed job queue — a simple scheduler is sufficient for MVP",
            ],
            "expected_files": [
                "src/jobs/automation.ts",
            ],
            "depends_on": ["bootstrap.backend"],
            "validation": {
                "commands": ["npm run build", "npm test"],
                "manual_check": "Automation job runs and logs output on interval",
            },
        })

    return architecture, stories