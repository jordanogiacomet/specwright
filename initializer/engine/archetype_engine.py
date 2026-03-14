"""
Archetype Engine

Detects the project archetype from the initial prompt
and provides default stack and features.
"""

from copy import deepcopy


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


ARCHETYPE_DEFINITIONS = {
    "editorial-cms": {
        "id": "editorial-cms",
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
        "capabilities": [
            "cms",
        ],
    },
    "marketplace": {
        "id": "marketplace",
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
        "capabilities": [],
    },
    "saas-app": {
        "id": "saas-app",
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
        "capabilities": [],
    },
    "generic-web-app": {
        "id": "generic-web-app",
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
        "capabilities": [],
    },
}


ARCHETYPE_ALIASES = {
    "api-service": "generic-web-app",
}


def canonical_archetype_id(archetype):

    if isinstance(archetype, dict):
        archetype_id = archetype.get("id") or archetype.get("name")
    else:
        archetype_id = archetype

    if not isinstance(archetype_id, str) or not archetype_id:
        raise ValueError("Archetype must resolve to a non-empty canonical identifier")

    return ARCHETYPE_ALIASES.get(archetype_id, archetype_id)


def detect_archetype(prompt):

    p = prompt.lower()

    if any(k in p for k in EDITORIAL_KEYWORDS):
        return deepcopy(ARCHETYPE_DEFINITIONS["editorial-cms"])

    if any(k in p for k in MARKETPLACE_KEYWORDS):
        return deepcopy(ARCHETYPE_DEFINITIONS["marketplace"])

    if any(k in p for k in SAAS_KEYWORDS):
        return deepcopy(ARCHETYPE_DEFINITIONS["saas-app"])

    # fallback archetype

    return deepcopy(ARCHETYPE_DEFINITIONS["generic-web-app"])
