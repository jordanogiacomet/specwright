"""
Capability Engine

Responsible for enriching architecture and stories based on detected
system capabilities.

Capabilities are derived from answers in the semantic spec.
"""

from copy import deepcopy


def detect_capabilities(spec):
    """
    Determine system capabilities based on spec answers.
    """

    answers = spec.get("answers", {})

    capabilities = []

    # public site
    if answers.get("public_site"):
        capabilities.append("public-site")

    # background jobs
    if answers.get("scheduled_publishing"):
        capabilities.append("scheduled-jobs")

    # localization
    if answers.get("localization"):
        capabilities.append("i18n")

    # cms always exists for this archetype
    capabilities.append("cms")

    return capabilities


def apply_capabilities(spec):
    """
    Apply capability patches to architecture and stories.
    """

    capabilities = detect_capabilities(spec)

    architecture = deepcopy(spec["architecture"])
    stories = deepcopy(spec["stories"])

    story_index = len(stories) + 1

    def new_story(title, description):

        nonlocal story_index

        story = {
            "id": f"ST-{story_index:03}",
            "title": title,
            "description": description,
        }

        story_index += 1

        stories.append(story)

    for capability in capabilities:

        # PUBLIC SITE
        if capability == "public-site":

            architecture["components"].append(
                {
                    "name": "cdn",
                    "technology": "cdn",
                    "role": "public asset delivery",
                }
            )

            architecture["decisions"].append(
                "Public assets should be delivered through a CDN"
            )

            new_story(
                "Configure CDN",
                "Configure CDN for public asset delivery."
            )

        # SCHEDULED JOBS
        elif capability == "scheduled-jobs":

            architecture["components"].append(
                {
                    "name": "worker",
                    "technology": "background-worker",
                    "role": "process scheduled jobs",
                }
            )

            architecture["decisions"].append(
                "Scheduled publishing requires a background worker"
            )

            new_story(
                "Setup job worker",
                "Create worker process responsible for scheduled publishing."
            )

            new_story(
                "Implement publishing scheduler",
                "Create scheduled publishing mechanism."
            )

        # LOCALIZATION
        elif capability == "i18n":

            architecture["decisions"].append(
                "Content model must support locale-aware fields"
            )

            new_story(
                "Add locale support",
                "Add locale fields to content models."
            )

            new_story(
                "Implement locale routing",
                "Add locale-aware routing in frontend."
            )

        # CMS
        elif capability == "cms":

            architecture["decisions"].append(
                "Payload CMS will manage editorial content."
            )

    return architecture, stories, capabilities