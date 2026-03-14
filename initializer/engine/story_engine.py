"""
Story Engine

Generates implementation stories from features and capabilities.
"""


def generate_stories(spec):

    stories = []

    features = spec.get("features", [])
    stack = spec.get("stack", {})

    counter = 1

    def new_story(title, description):
        nonlocal counter

        sid = f"ST-{counter:03d}"

        story = {
            "id": sid,
            "title": title,
            "description": description
        }

        counter += 1

        return story

    # project bootstrap

    stories.append(
        new_story(
            "Initialize project repository",
            "Create project structure using the selected stack."
        )
    )

    # database

    if stack.get("database"):

        stories.append(
            new_story(
                "Setup database",
                f"Configure {stack['database']} database and connection layer."
            )
        )

    # backend

    if stack.get("backend"):

        stories.append(
            new_story(
                "Setup backend service",
                f"Initialize backend using {stack['backend']}."
            )
        )

    # frontend

    if stack.get("frontend"):

        stories.append(
            new_story(
                "Create frontend application",
                f"Implement frontend using {stack['frontend']}."
            )
        )

    # authentication

    if "authentication" in features:

        stories.append(
            new_story(
                "Implement authentication",
                "Add login, logout and session management."
            )
        )

    # roles

    if "roles" in features:

        stories.append(
            new_story(
                "Implement role-based access control",
                "Define roles and permission boundaries."
            )
        )

    # media library

    if "media-library" in features:

        stories.append(
            new_story(
                "Implement media library",
                "Allow uploading and managing media assets."
            )
        )

    # preview

    if "preview" in features:

        stories.append(
            new_story(
                "Implement content preview",
                "Allow previewing unpublished content."
            )
        )

    # scheduled publishing

    if "scheduled-publishing" in features:

        stories.append(
            new_story(
                "Implement scheduled publishing",
                "Create background job to publish content at scheduled time."
            )
        )

    # search

    if "search" in features:

        stories.append(
            new_story(
                "Implement search",
                "Add search functionality across content."
            )
        )

    # payments

    if "payments" in features:

        stories.append(
            new_story(
                "Integrate payment provider",
                "Integrate payment processing for transactions."
            )
        )

    return stories