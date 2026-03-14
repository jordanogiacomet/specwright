"""
Archetype Engine

Detects the project archetype from the initial prompt
and provides default stack and features.
"""


EDITORIAL_KEYWORDS = [
    "cms",
    "editorial",
    "blog",
    "content",
    "media",
]


SAAS_KEYWORDS = [
    "saas",
    "dashboard",
    "analytics",
    "admin",
]


MARKETPLACE_KEYWORDS = [
    "marketplace",
    "courses",
    "store",
    "ecommerce",
]


def detect_archetype(prompt):

    p = prompt.lower()

    if any(k in p for k in EDITORIAL_KEYWORDS):

        return {
            "name": "editorial-cms",
            "stack": {
                "frontend": "nextjs",
                "backend": "payload",
                "database": "postgres",
            },
            "features": [
                "authentication",
                "roles",
                "media-library",
                "draft-publish",
                "preview",
                "scheduled-publishing",
            ],
        }

    if any(k in p for k in MARKETPLACE_KEYWORDS):

        return {
            "name": "marketplace",
            "stack": {
                "frontend": "nextjs",
                "backend": "node-api",
                "database": "postgres",
            },
            "features": [
                "authentication",
                "payments",
                "search",
                "reviews",
                "notifications",
            ],
        }

    if any(k in p for k in SAAS_KEYWORDS):

        return {
            "name": "saas-app",
            "stack": {
                "frontend": "nextjs",
                "backend": "node-api",
                "database": "postgres",
            },
            "features": [
                "authentication",
                "roles",
                "billing",
                "analytics",
                "notifications",
            ],
        }

    # fallback archetype

    return {
        "name": "generic-web-app",
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": [
            "authentication",
            "api",
        ],
    }