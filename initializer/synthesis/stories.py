def generate_stories(spec, architecture):

    stories = []

    story_id = 1

    def new_story(title, description):

        nonlocal story_id

        story = {
            "id": f"ST-{story_id:03}",
            "title": title,
            "description": description
        }

        story_id += 1

        stories.append(story)

    # Base setup

    new_story(
        "Initialize project structure",
        "Create base project using selected stack."
    )

    new_story(
        "Setup database",
        "Configure PostgreSQL database and connection layer."
    )

    new_story(
        "Setup CMS",
        "Install and configure Payload CMS."
    )

    # Public site

    if spec["answers"].get("public_site"):

        new_story(
            "Create public website",
            "Implement Next.js public site consuming CMS content."
        )

    # Scheduling

    if spec["answers"].get("scheduled_publishing"):

        new_story(
            "Implement scheduled publishing",
            "Create background job for scheduled publishing."
        )

    # Localization

    if spec["answers"].get("localization"):

        new_story(
            "Add localization support",
            "Implement multilingual content fields."
        )

    return stories