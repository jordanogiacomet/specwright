"""Domain Model Engine.

Derives the domain model for the generated project based on archetype,
features, capabilities, and structured discovery signals.

The domain model gives the execution agent concrete knowledge about:
- What entities exist and their fields
- What states each entity can be in and valid transitions
- What roles exist and what each role can do
- How authentication works
- Core business rules that govern the system

This is stack-agnostic — it describes the domain, not the implementation.
The agent uses this to make consistent decisions across stories.
"""

from __future__ import annotations

from typing import Any


def _get_decision_signals(spec: dict[str, Any]) -> dict[str, Any]:
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip().lower() for item in value if isinstance(item, str) and item.strip()]


# -------------------------------------------------------------------
# Entity definitions by archetype / app_shape
# -------------------------------------------------------------------

def _entity(
    name: str,
    description: str,
    fields: list[str] | None = None,
    states: list[str] | None = None,
    transitions: list[dict[str, str]] | None = None,
    relationships: list[str] | None = None,
) -> dict[str, Any]:
    entity: dict[str, Any] = {
        "name": name,
        "description": description,
    }
    if fields:
        entity["fields"] = fields
    if states:
        entity["states"] = states
    if transitions:
        entity["transitions"] = transitions
    if relationships:
        entity["relationships"] = relationships
    return entity


def _user_entity() -> dict[str, Any]:
    return _entity(
        "User",
        "System user with authentication credentials and role assignment.",
        fields=["id", "email", "name", "password_hash", "role", "created_at", "updated_at"],
        states=["active", "disabled"],
        transitions=[
            {"from": "active", "to": "disabled", "actor": "admin"},
            {"from": "disabled", "to": "active", "actor": "admin"},
        ],
    )


# --- Editorial CMS / Content Platform ---

def _editorial_entities(features: list[str], has_public: bool) -> list[dict[str, Any]]:
    entities = [_user_entity()]

    article_states = ["draft", "in_review", "published", "archived"]
    article_transitions = [
        {"from": "draft", "to": "in_review", "actor": "editor"},
        {"from": "in_review", "to": "published", "actor": "reviewer"},
        {"from": "in_review", "to": "draft", "actor": "reviewer", "label": "request changes"},
        {"from": "published", "to": "archived", "actor": "admin"},
    ]

    if "scheduled-publishing" in features:
        article_states.insert(3, "scheduled")
        article_transitions.append(
            {"from": "in_review", "to": "scheduled", "actor": "reviewer", "label": "schedule for publishing"}
        )
        article_transitions.append(
            {"from": "scheduled", "to": "published", "actor": "system", "label": "auto-publish at scheduled time"}
        )

    entities.append(_entity(
        "Article",
        "Editorial content item managed through a draft-to-publish workflow.",
        fields=["id", "title", "slug", "body", "excerpt", "status", "author_id", "published_at", "scheduled_at", "created_at", "updated_at"],
        states=article_states,
        transitions=article_transitions,
        relationships=["belongs_to User (as author)", "has_many MediaAsset", "has_many Category"],
    ))

    entities.append(_entity(
        "Category",
        "Taxonomy for organizing and filtering content.",
        fields=["id", "name", "slug", "description"],
        relationships=["has_many Article"],
    ))

    if "media-library" in features:
        entities.append(_entity(
            "MediaAsset",
            "Uploaded image, document, or file managed in the media library.",
            fields=["id", "filename", "mime_type", "size_bytes", "url", "alt_text", "uploaded_by", "created_at"],
            relationships=["belongs_to User (as uploader)"],
        ))

    return entities


# --- Backoffice ---

def _backoffice_entities(core_work_features: list[str]) -> list[dict[str, Any]]:
    entities = [_user_entity()]

    record_states = ["open", "in_progress", "completed", "cancelled"]
    record_transitions = [
        {"from": "open", "to": "in_progress", "actor": "operator"},
        {"from": "in_progress", "to": "completed", "actor": "operator"},
        {"from": "open", "to": "cancelled", "actor": "manager"},
        {"from": "in_progress", "to": "cancelled", "actor": "manager"},
    ]

    if "approvals" in core_work_features:
        record_states.insert(2, "pending_approval")
        record_transitions.append(
            {"from": "in_progress", "to": "pending_approval", "actor": "operator"}
        )
        record_transitions.append(
            {"from": "pending_approval", "to": "completed", "actor": "manager", "label": "approve"}
        )
        record_transitions.append(
            {"from": "pending_approval", "to": "in_progress", "actor": "manager", "label": "reject"}
        )

    record_fields = ["id", "title", "description", "status", "priority", "assigned_to", "created_by", "created_at", "updated_at"]

    if "deadlines" in core_work_features:
        record_fields.append("due_date")

    entities.append(_entity(
        "Record",
        "Core operational work item tracked through the backoffice.",
        fields=record_fields,
        states=record_states,
        transitions=record_transitions,
        relationships=["belongs_to User (as assignee)", "belongs_to User (as creator)"],
    ))

    if "report-generation" in core_work_features or "report generation" in core_work_features:
        entities.append(_entity(
            "Report",
            "Generated operational report for visibility and tracking.",
            fields=["id", "title", "type", "date_range_start", "date_range_end", "generated_by", "created_at"],
            relationships=["belongs_to User (as generator)"],
        ))

    return entities


# --- Internal Work Organizer ---

def _work_organizer_entities(core_work_features: list[str]) -> list[dict[str, Any]]:
    entities = [_user_entity()]

    entities.append(_entity(
        "Team",
        "Group of users working together on shared tasks.",
        fields=["id", "name", "description", "created_at"],
        relationships=["has_many User (as members)", "has_many WorkItem"],
    ))

    item_states = ["todo", "in_progress", "done", "blocked"]
    item_transitions = [
        {"from": "todo", "to": "in_progress", "actor": "assignee"},
        {"from": "in_progress", "to": "done", "actor": "assignee"},
        {"from": "in_progress", "to": "blocked", "actor": "assignee"},
        {"from": "blocked", "to": "in_progress", "actor": "assignee"},
        {"from": "todo", "to": "blocked", "actor": "assignee"},
    ]

    item_fields = ["id", "title", "description", "status", "priority", "assigned_to", "team_id", "created_by", "created_at", "updated_at"]

    if "deadlines" in core_work_features:
        item_fields.append("due_date")

    if "approvals" in core_work_features:
        item_states.insert(3, "pending_approval")
        item_transitions.append(
            {"from": "in_progress", "to": "pending_approval", "actor": "assignee"}
        )
        item_transitions.append(
            {"from": "pending_approval", "to": "done", "actor": "team_lead", "label": "approve"}
        )

    entities.append(_entity(
        "WorkItem",
        "Unit of work tracked by the team.",
        fields=item_fields,
        states=item_states,
        transitions=item_transitions,
        relationships=["belongs_to User (as assignee)", "belongs_to Team"],
    ))

    if "report-generation" in core_work_features or "report generation" in core_work_features:
        entities.append(_entity(
            "Report",
            "Generated progress or workload report.",
            fields=["id", "title", "type", "date_range_start", "date_range_end", "team_id", "generated_by", "created_at"],
            relationships=["belongs_to Team", "belongs_to User (as generator)"],
        ))

    return entities


# --- Client Portal ---

def _client_portal_entities(core_work_features: list[str]) -> list[dict[str, Any]]:
    entities = [_user_entity()]

    request_states = ["submitted", "under_review", "approved", "rejected", "completed"]
    request_transitions = [
        {"from": "submitted", "to": "under_review", "actor": "reviewer"},
        {"from": "under_review", "to": "approved", "actor": "reviewer"},
        {"from": "under_review", "to": "rejected", "actor": "reviewer"},
        {"from": "approved", "to": "completed", "actor": "system_or_reviewer"},
        {"from": "rejected", "to": "submitted", "actor": "client", "label": "resubmit"},
    ]

    entities.append(_entity(
        "Request",
        "Client-submitted request tracked through review and resolution.",
        fields=["id", "title", "description", "status", "submitted_by", "assigned_to", "created_at", "updated_at"],
        states=request_states,
        transitions=request_transitions,
        relationships=["belongs_to User (as submitter)", "belongs_to User (as reviewer)"],
    ))

    return entities


# --- Marketplace ---

def _marketplace_entities(features: list[str]) -> list[dict[str, Any]]:
    entities = [_user_entity()]

    entities.append(_entity(
        "Listing",
        "Product or service offered for sale on the marketplace.",
        fields=["id", "title", "description", "price", "seller_id", "status", "created_at", "updated_at"],
        states=["draft", "active", "sold", "archived"],
        transitions=[
            {"from": "draft", "to": "active", "actor": "seller"},
            {"from": "active", "to": "sold", "actor": "system"},
            {"from": "active", "to": "archived", "actor": "seller"},
        ],
        relationships=["belongs_to User (as seller)", "has_many Review"],
    ))

    entities.append(_entity(
        "Order",
        "Purchase transaction between buyer and seller.",
        fields=["id", "listing_id", "buyer_id", "seller_id", "amount", "status", "created_at"],
        states=["pending", "paid", "shipped", "completed", "cancelled", "refunded"],
        transitions=[
            {"from": "pending", "to": "paid", "actor": "system"},
            {"from": "paid", "to": "shipped", "actor": "seller"},
            {"from": "shipped", "to": "completed", "actor": "buyer"},
            {"from": "pending", "to": "cancelled", "actor": "buyer"},
            {"from": "paid", "to": "refunded", "actor": "admin"},
        ],
        relationships=["belongs_to Listing", "belongs_to User (as buyer)", "belongs_to User (as seller)"],
    ))

    if "reviews" in features:
        entities.append(_entity(
            "Review",
            "Buyer review of a listing or seller.",
            fields=["id", "listing_id", "reviewer_id", "rating", "comment", "created_at"],
            relationships=["belongs_to Listing", "belongs_to User (as reviewer)"],
        ))

    return entities


# --- SaaS App ---

def _saas_entities(features: list[str]) -> list[dict[str, Any]]:
    entities = [_user_entity()]

    entities.append(_entity(
        "Organization",
        "Tenant or account that groups users and resources.",
        fields=["id", "name", "slug", "plan", "created_at", "updated_at"],
        states=["active", "suspended", "cancelled"],
        transitions=[
            {"from": "active", "to": "suspended", "actor": "admin"},
            {"from": "suspended", "to": "active", "actor": "admin"},
            {"from": "active", "to": "cancelled", "actor": "account_admin"},
        ],
        relationships=["has_many User", "has_one Subscription"],
    ))

    if "billing" in features:
        entities.append(_entity(
            "Subscription",
            "Billing subscription tied to an organization.",
            fields=["id", "organization_id", "plan", "status", "current_period_start", "current_period_end", "created_at"],
            states=["trialing", "active", "past_due", "cancelled"],
            transitions=[
                {"from": "trialing", "to": "active", "actor": "system"},
                {"from": "active", "to": "past_due", "actor": "system"},
                {"from": "past_due", "to": "active", "actor": "system", "label": "payment received"},
                {"from": "active", "to": "cancelled", "actor": "account_admin"},
            ],
            relationships=["belongs_to Organization"],
        ))

    return entities


# --- Knowledge Base ---

def _knowledge_base_entities(features: list[str]) -> list[dict[str, Any]]:
    entities = [_user_entity()]

    entities.append(_entity(
        "Article",
        "Knowledge base article or documentation page.",
        fields=["id", "title", "slug", "body", "status", "author_id", "created_at", "updated_at"],
        states=["draft", "published", "archived"],
        transitions=[
            {"from": "draft", "to": "published", "actor": "author"},
            {"from": "published", "to": "archived", "actor": "admin"},
            {"from": "archived", "to": "draft", "actor": "admin"},
        ],
        relationships=["belongs_to User (as author)", "has_many Tag"],
    ))

    entities.append(_entity(
        "Tag",
        "Label for categorizing and filtering articles.",
        fields=["id", "name", "slug"],
        relationships=["has_many Article"],
    ))

    return entities


# --- Generic fallback ---

def _generic_entities() -> list[dict[str, Any]]:
    return [_user_entity()]


# -------------------------------------------------------------------
# Role definitions
# -------------------------------------------------------------------

def _editorial_roles() -> list[dict[str, str | list[str]]]:
    return [
        {"name": "admin", "can": [
            "manage_users", "manage_config", "publish", "archive",
            "delete_content", "manage_categories", "manage_media",
        ]},
        {"name": "editor", "can": [
            "create_article", "edit_own_article", "submit_for_review",
            "upload_media", "manage_own_media",
        ]},
        {"name": "reviewer", "can": [
            "approve_article", "reject_article", "edit_any_article",
            "publish", "view_all_articles",
        ]},
    ]


def _backoffice_roles() -> list[dict[str, str | list[str]]]:
    return [
        {"name": "admin", "can": [
            "manage_users", "manage_config", "view_all_records",
            "cancel_any_record", "generate_reports",
        ]},
        {"name": "manager", "can": [
            "view_team_records", "approve_records", "cancel_records",
            "assign_records", "generate_reports",
        ]},
        {"name": "operator", "can": [
            "create_record", "edit_own_records", "update_status",
            "view_own_records",
        ]},
    ]


def _work_organizer_roles() -> list[dict[str, str | list[str]]]:
    return [
        {"name": "admin", "can": [
            "manage_users", "manage_teams", "manage_config",
            "view_all_work_items",
        ]},
        {"name": "team_lead", "can": [
            "view_team_work_items", "assign_work_items",
            "approve_work_items", "generate_reports",
        ]},
        {"name": "member", "can": [
            "create_work_item", "edit_own_work_items",
            "update_own_status", "view_team_work_items",
        ]},
    ]


def _client_portal_roles() -> list[dict[str, str | list[str]]]:
    return [
        {"name": "admin", "can": [
            "manage_users", "manage_config", "view_all_requests",
        ]},
        {"name": "reviewer", "can": [
            "view_assigned_requests", "approve_request",
            "reject_request", "reassign_request",
        ]},
        {"name": "client", "can": [
            "submit_request", "view_own_requests",
            "resubmit_rejected_request",
        ]},
    ]


def _marketplace_roles() -> list[dict[str, str | list[str]]]:
    return [
        {"name": "admin", "can": [
            "manage_users", "manage_platform", "resolve_disputes",
            "manage_listings",
        ]},
        {"name": "seller", "can": [
            "create_listing", "edit_own_listing", "ship_order",
            "view_own_orders",
        ]},
        {"name": "buyer", "can": [
            "browse_listings", "place_order", "leave_review",
            "view_own_orders",
        ]},
    ]


def _saas_roles() -> list[dict[str, str | list[str]]]:
    return [
        {"name": "platform_admin", "can": [
            "manage_all_organizations", "manage_platform_config",
            "view_system_analytics",
        ]},
        {"name": "account_admin", "can": [
            "manage_org_members", "manage_billing",
            "manage_org_settings",
        ]},
        {"name": "member", "can": [
            "use_application", "view_own_data",
            "update_own_profile",
        ]},
    ]


def _generic_roles() -> list[dict[str, str | list[str]]]:
    return [
        {"name": "admin", "can": [
            "manage_users", "manage_config",
        ]},
        {"name": "user", "can": [
            "use_application", "view_own_data",
        ]},
    ]


# -------------------------------------------------------------------
# Auth model
# -------------------------------------------------------------------

def _derive_auth_model(spec: dict[str, Any]) -> dict[str, Any]:
    """Derive auth configuration from the spec."""
    backend = (spec.get("stack", {}).get("backend") or "").lower().strip()

    auth_model: dict[str, Any] = {
        "strategy": "email_password",
        "session": "jwt",
        "mfa": False,
    }

    if backend in ("payload", "payload-cms"):
        auth_model["provider"] = "payload-auth"
        auth_model["session"] = "jwt (Payload built-in)"
    elif backend == "django":
        auth_model["provider"] = "django-auth"
        auth_model["session"] = "session-cookie (Django built-in)"
    else:
        auth_model["provider"] = "custom"

    return auth_model


# -------------------------------------------------------------------
# Business rules
# -------------------------------------------------------------------

def _editorial_rules(features: list[str]) -> list[str]:
    rules = [
        "Only users with reviewer or admin role can approve content for publication.",
        "Published content cannot be edited directly — create a new draft version instead.",
        "Deleting published content requires admin role.",
    ]
    if "scheduled-publishing" in features:
        rules.append("Scheduled publishing requires content to be in approved/in_review state.")
        rules.append("The scheduler checks for due content on a configurable interval and publishes automatically.")
    if "media-library" in features:
        rules.append("Media assets must pass file type and size validation before storage.")
    return rules


def _backoffice_rules(core_work_features: list[str]) -> list[str]:
    rules = [
        "Operators can only edit records assigned to them or created by them.",
        "Managers can view all records within their team scope.",
        "Cancellation of in-progress records requires manager approval.",
    ]
    if "approvals" in core_work_features:
        rules.append("Records in pending_approval state can only be approved or rejected by a manager.")
    if "deadlines" in core_work_features:
        rules.append("Overdue records are flagged automatically and visible in dashboards.")
    if "report-generation" in core_work_features or "report generation" in core_work_features:
        rules.append("Reports are generated from live data — they are not cached snapshots.")
    return rules


def _work_organizer_rules(core_work_features: list[str]) -> list[str]:
    rules = [
        "Work items can only be moved to 'done' by their assignee or a team lead.",
        "Blocked items must include a reason for blocking.",
        "Team leads can reassign work items within their team.",
    ]
    if "approvals" in core_work_features:
        rules.append("Work items requiring approval must go through pending_approval before done.")
    if "deadlines" in core_work_features:
        rules.append("Overdue work items are surfaced in the team dashboard.")
    return rules


def _client_portal_rules() -> list[str]:
    return [
        "Clients can only see their own requests.",
        "Rejected requests can be resubmitted by the client with changes.",
        "Reviewers can only see requests assigned to them unless they are admin.",
        "Completed requests are read-only for all parties.",
    ]


def _marketplace_rules() -> list[str]:
    return [
        "Sellers can only edit their own listings.",
        "Orders can only be cancelled by the buyer before shipment.",
        "Reviews can only be left after order completion.",
        "Refunds require admin approval.",
    ]


def _saas_rules() -> list[str]:
    return [
        "Users belong to exactly one organization.",
        "Account admins can only manage their own organization.",
        "Suspended organizations cannot access application features.",
        "Billing changes take effect at the next billing period.",
    ]


def _generic_rules() -> list[str]:
    return [
        "Admin role is required for user management and system configuration.",
        "Regular users can only access their own data.",
    ]


# -------------------------------------------------------------------
# Todo-app
# -------------------------------------------------------------------

def _todo_app_entities() -> list[dict[str, Any]]:
    return [
        _entity(
            "Todo",
            "A task or action item owned by a user",
            fields=["title", "description", "completed", "dueDate", "priority", "createdAt", "updatedAt"],
            states=["pending", "completed"],
            transitions=[
                {"from": "pending", "to": "completed", "actor": "owner"},
                {"from": "completed", "to": "pending", "actor": "owner"},
            ],
            relationships=["belongs_to User"],
        ),
        _entity(
            "User",
            "An application user who owns todos",
            fields=["email", "name", "passwordHash", "createdAt"],
            relationships=["has_many Todo"],
        ),
    ]


def _todo_app_roles() -> list[dict[str, str | list[str]]]:
    return [
        {"name": "user", "can": [
            "create_todo", "read_own_todos", "update_own_todo",
            "delete_own_todo", "toggle_todo_complete",
        ]},
    ]


def _todo_app_rules() -> list[str]:
    return [
        "Users can only see and modify their own todos.",
        "Toggling a todo marks it as completed or pending.",
        "Deleting a todo is permanent (no soft-delete).",
        "Todos are ordered by createdAt descending by default.",
        "No roles or admin panel — single user type.",
    ]


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

def generate_domain_model(spec: dict[str, Any]) -> dict[str, Any]:
    """Generate the domain model for the project.

    Returns a dict with:
    - entities: list of entity definitions with fields, states, transitions
    - roles: list of role definitions with permissions
    - auth_model: authentication configuration
    - business_rules: list of business rule strings
    """
    archetype = spec.get("archetype", "")
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    signals = _get_decision_signals(spec)

    app_shape = signals.get("app_shape")
    core_work_features = _normalize_list(signals.get("core_work_features", []))
    has_public = "public-site" in capabilities

    # --- Entities ---
    if archetype == "todo-app":
        entities = _todo_app_entities()
        roles = _todo_app_roles()
        business_rules = _todo_app_rules()

    elif archetype == "editorial-cms" or app_shape == "content-platform":
        entities = _editorial_entities(features, has_public)
        roles = _editorial_roles()
        business_rules = _editorial_rules(features)

    elif app_shape == "backoffice" or archetype == "backoffice":
        entities = _backoffice_entities(core_work_features)
        roles = _backoffice_roles()
        business_rules = _backoffice_rules(core_work_features)

    elif app_shape == "internal-work-organizer" or archetype == "work-organizer":
        entities = _work_organizer_entities(core_work_features)
        roles = _work_organizer_roles()
        business_rules = _work_organizer_rules(core_work_features)

    elif app_shape == "client-portal" or archetype == "client-portal":
        entities = _client_portal_entities(core_work_features)
        roles = _client_portal_roles()
        business_rules = _client_portal_rules()

    elif archetype == "marketplace":
        entities = _marketplace_entities(features)
        roles = _marketplace_roles()
        business_rules = _marketplace_rules()

    elif archetype == "saas-app":
        entities = _saas_entities(features)
        roles = _saas_roles()
        business_rules = _saas_rules()

    elif archetype == "knowledge-base":
        entities = _knowledge_base_entities(features)
        roles = _generic_roles()
        business_rules = _generic_rules()

    else:
        entities = _generic_entities()
        roles = _generic_roles()
        business_rules = _generic_rules()

    # --- Auth ---
    auth_model = _derive_auth_model(spec)

    return {
        "entities": entities,
        "roles": roles,
        "auth_model": auth_model,
        "business_rules": business_rules,
    }