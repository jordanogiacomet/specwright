def apply_public_site(architecture, stories):

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

    stories.append(
        {
            "id": f"ST-{len(stories)+1:03}",
            "title": "Configure CDN",
            "description": "Configure CDN for public site asset delivery.",
        }
    )

    return architecture, stories
