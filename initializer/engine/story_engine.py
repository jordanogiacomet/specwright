"""
Story Engine

Generates implementation stories from features and capabilities.
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


def generate_stories(spec):

    stories = [dict(story) for story in spec.get("stories", [])]

    features = spec.get("features", [])
    stack = spec.get("stack", {})

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

    # project bootstrap

    upsert_story(
        "bootstrap.repository",
        "Initialize project repository",
        "Create project structure using the selected stack.",
    )

    # database

    if stack.get("database"):

        upsert_story(
            "bootstrap.database",
            "Setup database",
            f"Configure {stack['database']} database and connection layer.",
        )

    # backend

    if stack.get("backend"):

        upsert_story(
            "bootstrap.backend",
            "Setup backend service",
            f"Initialize backend using {stack['backend']}.",
        )

    # frontend

    if stack.get("frontend"):

        upsert_story(
            "bootstrap.frontend",
            "Create frontend application",
            f"Implement frontend using {stack['frontend']}.",
        )

    # authentication

    if "authentication" in features:

        upsert_story(
            "feature.authentication",
            "Implement authentication",
            "Add login, logout and session management.",
        )

    # roles

    if "roles" in features:

        upsert_story(
            "feature.roles",
            "Implement role-based access control",
            "Define roles and permission boundaries.",
        )

    # media library

    if "media-library" in features:

        upsert_story(
            "feature.media-library",
            "Implement media library",
            "Allow uploading and managing media assets.",
        )

    # preview

    if "preview" in features:

        upsert_story(
            "feature.preview",
            "Implement content preview",
            "Allow previewing unpublished content.",
        )

    # scheduled publishing

    if "scheduled-publishing" in features:

        upsert_story(
            "feature.scheduled-publishing",
            "Implement scheduled publishing",
            "Create background job to publish content at scheduled time.",
        )

    # search

    if "search" in features:

        upsert_story(
            "feature.search",
            "Implement search",
            "Add search functionality across content.",
        )

    # payments

    if "payments" in features:

        upsert_story(
            "feature.payments",
            "Integrate payment provider",
            "Integrate payment processing for transactions.",
        )

    return stories
