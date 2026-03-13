def synthesize_architecture(spec, playbook):

    stack = spec.get("stack", {})
    answers = spec.get("answers", {})

    architecture = {
        "style": "headless-cms",
        "components": [],
        "decisions": [],
    }

    # Core components

    architecture["components"].append(
        {
            "name": "frontend",
            "technology": stack.get("frontend"),
            "role": "public website"
        }
    )

    architecture["components"].append(
        {
            "name": "cms",
            "technology": stack.get("backend"),
            "role": "content management"
        }
    )

    architecture["components"].append(
        {
            "name": "database",
            "technology": stack.get("database"),
            "role": "content storage"
        }
    )

    # Conditional decisions

    if answers.get("public_site"):

        architecture["decisions"].append(
            "Public site consumes content via CMS API"
        )

    if answers.get("scheduled_publishing"):

        architecture["decisions"].append(
            "Background worker required for scheduled publishing"
        )

    if answers.get("localization"):

        architecture["decisions"].append(
            "Content model must support locale fields"
        )

    # Playbook architecture notes

    for note in playbook.get("architecture_notes", []):
        architecture["decisions"].append(note)

    return architecture