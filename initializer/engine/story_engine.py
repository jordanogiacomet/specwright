"""Story Engine.

Generates implementation stories from features, capabilities,
stack, and structured discovery signals.
"""


def _merge_story(existing_story, generated_story):
    merged = dict(existing_story)

    if not merged.get("story_key"):
        merged["story_key"] = generated_story["story_key"]

    if not merged.get("title"):
        merged["title"] = generated_story["title"]
    elif merged["title"] != generated_story["title"]:
        titles = list(merged.get("title_alternatives", []))
        if generated_story["title"] not in titles:
            titles.append(generated_story["title"])
        merged["title_alternatives"] = titles

    if not merged.get("description"):
        merged["description"] = generated_story["description"]
    elif merged["description"] != generated_story["description"]:
        descriptions = list(merged.get("description_alternatives", []))
        if generated_story["description"] not in descriptions:
            descriptions.append(generated_story["description"])
        merged["description_alternatives"] = descriptions

    return merged


def _find_story_index(stories, story_key, title):
    for index, story in enumerate(stories):
        if story.get("story_key") == story_key:
            return index

    for index, story in enumerate(stories):
        if story.get("title") == title:
            return index

    return None


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _normalize_core_work_features(value):
    if not isinstance(value, list):
        return []

    normalized = []
    for item in value:
        if isinstance(item, str):
            text = item.strip().lower()
            if text and text not in normalized:
                normalized.append(text)

    return normalized


def generate_stories(spec):
    stories = [dict(story) for story in spec.get("stories", [])]
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    stack = spec.get("stack", {})
    signals = _get_decision_signals(spec)

    primary_audience = signals.get("primary_audience")
    app_shape = signals.get("app_shape")
    core_work_features = _normalize_core_work_features(
        signals.get("core_work_features", [])
    )

    counter = 1
    for story in stories:
        story_id = story.get("id", "")
        if not story_id.startswith("ST-"):
            continue

        suffix = story_id[3:]
        if suffix.isdigit():
            counter = max(counter, int(suffix) + 1)

    def upsert_story(story_key, title, description):
        nonlocal counter

        generated_story = {
            "story_key": story_key,
            "title": title,
            "description": description,
        }

        existing_index = _find_story_index(stories, story_key, title)
        if existing_index is not None:
            stories[existing_index] = _merge_story(
                stories[existing_index],
                generated_story,
            )
            return stories[existing_index]

        sid = f"ST-{counter:03d}"
        story = {
            "id": sid,
            **generated_story,
        }
        counter += 1
        stories.append(story)
        return story

    upsert_story(
        "bootstrap.repository",
        "Initialize project repository",
        "Create project structure using the selected stack.",
    )

    if stack.get("database"):
        upsert_story(
            "bootstrap.database",
            "Setup database",
            f"Configure {stack['database']} database and connection layer.",
        )

    if stack.get("backend"):
        upsert_story(
            "bootstrap.backend",
            "Setup backend service",
            f"Initialize backend using {stack['backend']}.",
        )

    if stack.get("frontend"):
        upsert_story(
            "bootstrap.frontend",
            "Create frontend application",
            f"Implement frontend using {stack['frontend']}.",
        )

    if "authentication" in features:
        upsert_story(
            "feature.authentication",
            "Implement authentication",
            "Add login, logout and session management.",
        )

    if "roles" in features:
        upsert_story(
            "feature.roles",
            "Implement role-based access control",
            "Define roles and permission boundaries.",
        )

    if "media-library" in features:
        upsert_story(
            "feature.media-library",
            "Implement media library",
            "Allow uploading and managing media assets.",
        )

    if "preview" in features:
        upsert_story(
            "feature.preview",
            "Implement content preview",
            "Allow previewing unpublished content.",
        )

    if "scheduled-publishing" in features:
        upsert_story(
            "feature.scheduled-publishing",
            "Implement scheduled publishing",
            "Create background job to publish content at scheduled time.",
        )

    if "search" in features:
        upsert_story(
            "feature.search",
            "Implement search",
            "Add search functionality across the application.",
        )

    if "payments" in features:
        upsert_story(
            "feature.payments",
            "Integrate payment provider",
            "Integrate payment processing for transactions.",
        )

    if app_shape == "internal-work-organizer" or primary_audience == "internal_teams":
        upsert_story(
            "product.internal-dashboard",
            "Build internal dashboard shell",
            "Create the main internal application shell and navigation for team workflows.",
        )

    if "deadlines" in core_work_features:
        upsert_story(
            "product.deadlines",
            "Model deadlines and due dates",
            "Implement domain support for deadlines, due dates, and related validations.",
        )

    if "progress-tracking" in core_work_features or "progress tracking" in core_work_features:
        upsert_story(
            "product.progress-tracking",
            "Implement progress tracking",
            "Add progress tracking and status transitions for core work items.",
        )

    if "task-assignment" in core_work_features or "task assignment" in core_work_features:
        upsert_story(
            "product.task-assignment",
            "Implement task assignment",
            "Allow work items to be assigned to owners and teams.",
        )

    if "reminders" in core_work_features:
        upsert_story(
            "product.reminders",
            "Implement reminders",
            "Add reminder workflows for approaching deadlines and pending work.",
        )

    if "report-generation" in core_work_features or "report generation" in core_work_features:
        upsert_story(
            "product.report-generation",
            "Implement report generation",
            "Generate summary reports for work progress and operational visibility.",
        )

    if "scheduled-jobs" in capabilities and app_shape == "internal-work-organizer":
        upsert_story(
            "product.automation-jobs",
            "Implement workflow automation jobs",
            "Implement scheduled jobs for reminders, progress automation, or recurring operational tasks.",
        )

    return stories