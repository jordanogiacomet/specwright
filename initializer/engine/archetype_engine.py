"""
Archetype Engine

Detects the project archetype from the initial prompt
and provides default stack and features.

Archetypes:
- editorial-cms: content management and publishing
- marketplace: buying/selling platform
- saas-app: subscription-based application
- backoffice: internal operations management
- client-portal: client-facing request/tracking system
- work-organizer: internal work/task management
- knowledge-base: documentation/wiki system
- todo-app: simple task/todo list application (fast validation archetype)
- generic-web-app: fallback for unrecognized prompts
"""

from copy import deepcopy


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
    "backoffice": {
        "id": "backoffice",
        "name": "backoffice",
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": [
            "authentication",
            "roles",
            "api",
        ],
        "capabilities": [],
    },
    "client-portal": {
        "id": "client-portal",
        "name": "client-portal",
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": [
            "authentication",
            "roles",
            "notifications",
            "api",
        ],
        "capabilities": [],
    },
    "work-organizer": {
        "id": "work-organizer",
        "name": "work-organizer",
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": [
            "authentication",
            "roles",
            "api",
        ],
        "capabilities": [],
    },
    "knowledge-base": {
        "id": "knowledge-base",
        "name": "knowledge-base",
        "stack": {
            "frontend": "nextjs",
            "backend": "node-api",
            "database": "postgres",
        },
        "features": [
            "authentication",
            "search",
            "api",
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
    "todo-app": {
        "id": "todo-app",
        "name": "todo-app",
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


# Keywords grouped by archetype, with weights.
# Higher weight = stronger signal.
# A keyword can appear in multiple archetypes with different weights.
ARCHETYPE_KEYWORDS = {
    "editorial-cms": [
        ("cms", 3),
        ("editorial", 3),
        ("blog", 2),
        ("content management", 3),
        ("media library", 2),
        ("publishing", 2),
        ("articles", 2),
        ("posts", 1),
        ("editor", 1),
        ("draft", 2),
        ("publish", 2),
    ],
    "marketplace": [
        ("marketplace", 3),
        ("ecommerce", 3),
        ("e-commerce", 3),
        ("store", 2),
        ("shop", 2),
        ("courses", 2),
        ("buy and sell", 3),
        ("buyers and sellers", 3),
        ("listings", 2),
        ("catalog", 1),
        ("cart", 2),
        ("checkout", 2),
    ],
    "saas-app": [
        ("saas", 3),
        ("subscription", 2),
        ("multi-tenant", 3),
        ("multitenant", 3),
        ("tenant", 2),
        ("billing", 2),
        ("analytics dashboard", 2),
        ("usage tracking", 2),
        ("plans and pricing", 2),
    ],
    "backoffice": [
        ("backoffice", 3),
        ("back office", 3),
        ("back-office", 3),
        ("operations team", 3),
        ("operations management", 3),
        ("manage orders", 2),
        ("order management", 2),
        ("internal operations", 3),
        ("admin panel for operations", 3),
        ("operational", 1),
        ("generate reports", 2),
        ("report generation", 2),
    ],
    "client-portal": [
        ("client portal", 3),
        ("customer portal", 3),
        ("clients can submit", 3),
        ("client requests", 3),
        ("customer requests", 3),
        ("request tracking", 2),
        ("submit requests", 2),
        ("track requests", 2),
        ("approvals from", 2),
        ("approval workflow", 2),
        ("client access", 2),
        ("portal for clients", 3),
        ("portal for customers", 3),
    ],
    "work-organizer": [
        ("work organizer", 3),
        ("organize work", 3),
        ("organizar trabalho", 3),
        ("organizarem trabalho", 3),
        ("organizar o trabalho", 3),
        ("organizarem melhor o trabalho", 3),
        ("task management", 3),
        ("project management", 2),
        ("team workload", 2),
        ("track work", 2),
        ("work management", 3),
        ("task tracking", 2),
        ("task assignment", 2),
        ("assign tasks", 2),
        ("deadlines and progress", 2),
        ("kanban", 2),
        ("sprint", 1),
        ("to-do", 1),
        ("todo", 1),
    ],
    "knowledge-base": [
        ("knowledge base", 3),
        ("knowledgebase", 3),
        ("wiki", 3),
        ("documentation platform", 3),
        ("docs platform", 2),
        ("internal docs", 2),
        ("help center", 2),
        ("faq system", 2),
        ("support articles", 2),
    ],
    "todo-app": [
        ("todo app", 5),
        ("todo-app", 5),
        ("todo list", 4),
        ("task list", 3),
        ("simple task", 3),
        ("simple todo", 4),
        ("minimal todo", 4),
        ("basic todo", 4),
        ("checklist app", 3),
        ("to-do app", 4),
        ("to do app", 4),
        ("lista de tarefas", 3),
    ],
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


def _score_archetype(prompt_lower: str, archetype_id: str) -> int:
    """Score how well a prompt matches an archetype based on keyword weights."""
    keywords = ARCHETYPE_KEYWORDS.get(archetype_id, [])
    score = 0

    for keyword, weight in keywords:
        if keyword in prompt_lower:
            score += weight

    return score


def detect_archetype(prompt):
    """Detect the best-matching archetype from the prompt.

    Uses weighted keyword scoring. The archetype with the highest
    score wins. If no archetype scores above 0, falls back to
    generic-web-app.
    """
    p = prompt.lower()

    scores = {}
    for archetype_id in ARCHETYPE_KEYWORDS:
        score = _score_archetype(p, archetype_id)
        if score > 0:
            scores[archetype_id] = score

    if not scores:
        return deepcopy(ARCHETYPE_DEFINITIONS["generic-web-app"])

    # Pick the highest scoring archetype
    best_id = max(scores, key=scores.get)

    # Ensure the archetype exists in definitions
    if best_id not in ARCHETYPE_DEFINITIONS:
        return deepcopy(ARCHETYPE_DEFINITIONS["generic-web-app"])

    return deepcopy(ARCHETYPE_DEFINITIONS[best_id])