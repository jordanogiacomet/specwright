"""
CMS capability
"""


def apply_cms(architecture, stories):

    # garantir estrutura segura

    if "decisions" not in architecture:
        architecture["decisions"] = []

    if "components" not in architecture:
        architecture["components"] = []

    architecture["decisions"].append(
        "CMS content stored in structured collections."
    )

    architecture["decisions"].append(
        "Media assets served via CDN."
    )

    stories.append(
        {
            "id": f"ST-{len(stories)+1:03}",
            "title": "Define CMS content model",
            "description": "Define CMS collections, media handling, and editorial workflows.",
        }
    )

    return architecture, stories
