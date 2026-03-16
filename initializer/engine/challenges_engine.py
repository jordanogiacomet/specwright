"""Challenges Engine.

Identifies known architectural and product challenges based on
archetype, capabilities, features, and discovery signals.

Each challenge includes:
- id: unique identifier
- title: short name
- description: what the problem is and why it matters
- options: list of resolution strategies (a, b, c, ...)
- default: which option is recommended
- affects: which spec sections this decision influences

The engine is deterministic — it maps archetype+capabilities to
known challenges. The AI layer (in the --assist flow) can refine
descriptions and add project-specific challenges.

User decisions are stored in spec["challenge_decisions"] and
influence architecture decisions, story acceptance criteria,
and agent instructions.
"""

from __future__ import annotations

from typing import Any


# -------------------------------------------------------------------
# Challenge definition helper
# -------------------------------------------------------------------

def _challenge(
    id: str,
    title: str,
    description: str,
    options: list[dict[str, str]],
    default: str = "a",
    affects: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": id,
        "title": title,
        "description": description,
        "options": options,
        "default": default,
        "affects": affects or ["architecture"],
    }


def _option(key: str, label: str, detail: str) -> dict[str, str]:
    return {"key": key, "label": label, "detail": detail}


# -------------------------------------------------------------------
# Challenges by archetype + capabilities
# -------------------------------------------------------------------

def _editorial_cms_challenges(capabilities: list[str], features: list[str]) -> list[dict[str, Any]]:
    challenges = []

    if "public-site" in capabilities:
        challenges.append(_challenge(
            "cache-invalidation",
            "Cache Invalidation",
            "When content is published or updated, cached public pages may show stale content. "
            "This is especially impactful for editorial sites where timeliness matters.",
            options=[
                _option("a", "On-demand ISR revalidation",
                        "Trigger Next.js revalidation via webhook after each publish event. "
                        "Pages update within seconds. Requires a revalidation API route."),
                _option("b", "Short TTL caching",
                        "Set a short cache TTL (30-60s) on all public pages. "
                        "Simple but introduces a small delay for content freshness."),
                _option("c", "Full static regeneration",
                        "Rebuild all static pages on each publish. "
                        "Guarantees freshness but slow for large sites."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

        challenges.append(_challenge(
            "preview-vs-production",
            "Preview vs Production",
            "Draft content must be previewable by editors without leaking to public visitors or search engines.",
            options=[
                _option("a", "Payload draft mode + Next.js preview",
                        "Use Payload's built-in draft mode with Next.js preview cookies. "
                        "Editors see drafts in-context; public visitors see only published content."),
                _option("b", "Separate preview URL",
                        "Deploy a separate preview instance or route that requires authentication. "
                        "Stronger isolation but more infrastructure."),
                _option("c", "Skip for MVP",
                        "Implement preview in a later iteration. "
                        "Editors verify content in the admin panel only."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

        challenges.append(_challenge(
            "seo-vs-auth-routes",
            "SEO vs Authenticated Routes",
            "The same Next.js app serves both public (SEO-optimized) pages and authenticated admin routes. "
            "Misconfiguration can expose admin routes to crawlers or block public pages behind auth.",
            options=[
                _option("a", "Route groups with middleware",
                        "Use Next.js route groups: (public) for SEO pages, (app) for admin, (payload) for CMS. "
                        "Middleware enforces auth only on non-public groups."),
                _option("b", "Separate subdomains",
                        "Serve admin on admin.example.com and public on www.example.com. "
                        "Cleaner separation but requires DNS and deployment config."),
                _option("c", "robots.txt + noindex",
                        "Keep everything on one domain. Use robots.txt and noindex meta tags to hide admin routes. "
                        "Simplest but relies on crawler compliance."),
            ],
            default="a",
            affects=["architecture"],
        ))

    if "media-library" in features:
        challenges.append(_challenge(
            "media-storage-strategy",
            "Media Storage Strategy",
            "Media assets (images, documents) need a storage backend. "
            "The choice affects cost, performance, and complexity.",
            options=[
                _option("a", "Local filesystem (dev) + S3 (production)",
                        "Use local disk in development for simplicity. "
                        "Switch to S3-compatible storage in production via environment variable."),
                _option("b", "S3-compatible from the start",
                        "Use MinIO locally and S3 in production. "
                        "Consistent behavior across environments but requires MinIO in docker-compose."),
                _option("c", "Local filesystem only",
                        "Store media on disk. Simple but doesn't scale and isn't suitable for multi-instance deployment."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

    if "draft-publish" in features:
        challenges.append(_challenge(
            "content-versioning",
            "Content Versioning",
            "When editors update published content, should the system keep history? "
            "Without versioning, published content is overwritten directly.",
            options=[
                _option("a", "Payload built-in versions",
                        "Enable Payload's versions feature on content collections. "
                        "Editors can see history and restore previous versions."),
                _option("b", "No versioning for MVP",
                        "Skip versioning initially. Editors edit content directly. "
                        "Simpler but no rollback capability."),
                _option("c", "Manual snapshots",
                        "Create a snapshot before each publish that can be restored manually. "
                        "Middle ground between full versioning and none."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

    return challenges


def _backoffice_challenges(capabilities: list[str], features: list[str], core_work_features: list[str]) -> list[dict[str, Any]]:
    challenges = []

    challenges.append(_challenge(
        "status-model-design",
        "Work Item Status Model",
        "The status model defines how work items flow through states. "
        "Getting this wrong early creates data migration headaches later.",
        options=[
            _option("a", "Predefined states with strict transitions",
                    "Define states (open, in_progress, done, cancelled) with explicit transition rules. "
                    "Prevents invalid state changes but requires upfront planning."),
            _option("b", "Flexible status field",
                    "Use a free-form status string that operators can set to anything. "
                    "Maximum flexibility but no enforcement or reporting consistency."),
            _option("c", "Configurable state machine",
                    "Build a state machine that admins can configure. "
                    "Most powerful but significantly more complex to implement."),
        ],
        default="a",
        affects=["architecture", "domain_model", "stories"],
    ))

    if "deadlines" in core_work_features:
        challenges.append(_challenge(
            "overdue-handling",
            "Overdue Item Handling",
            "When a work item passes its due date, the system needs a strategy for surfacing and handling it.",
            options=[
                _option("a", "Computed field + dashboard filter",
                        "Calculate overdue status on read. Show overdue items prominently in dashboards. "
                        "No background job needed."),
                _option("b", "Background job + notifications",
                        "A scheduled job checks for overdue items and sends notifications. "
                        "More proactive but requires job infrastructure."),
                _option("c", "Manual tracking only",
                        "Operators check due dates manually. "
                        "Simplest but easy to miss deadlines."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

    if "approvals" in core_work_features:
        challenges.append(_challenge(
            "approval-model",
            "Approval Workflow Model",
            "Approvals add a review step before work items can be completed. "
            "The complexity depends on how many approval steps are needed.",
            options=[
                _option("a", "Single-step approval",
                        "One approver signs off. Item goes from pending_approval → done or back to in_progress. "
                        "Simple and sufficient for most small teams."),
                _option("b", "Multi-step approval chain",
                        "Multiple approvers in sequence. "
                        "More control but significantly more complex to implement and maintain."),
                _option("c", "Skip for MVP",
                        "Implement approvals in a later iteration. "
                        "Items go directly to done without review."),
            ],
            default="a",
            affects=["domain_model", "stories"],
        ))

    if "report-generation" in core_work_features:
        challenges.append(_challenge(
            "report-data-strategy",
            "Report Data Strategy",
            "Reports need data. The question is whether to query live data or pre-aggregate it.",
            options=[
                _option("a", "Live queries",
                        "Reports query the database directly each time. "
                        "Always fresh but can be slow on large datasets."),
                _option("b", "Pre-aggregated materialized views",
                        "Background job pre-computes report data into summary tables. "
                        "Fast reads but introduces staleness and complexity."),
                _option("c", "Client-side aggregation",
                        "Fetch raw data and compute summaries in the browser. "
                        "Simplest backend but limited to small datasets."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

    return challenges


def _work_organizer_challenges(capabilities: list[str], features: list[str], core_work_features: list[str]) -> list[dict[str, Any]]:
    # Work organizer shares many challenges with backoffice
    challenges = _backoffice_challenges(capabilities, features, core_work_features)

    if "task-assignment" in core_work_features:
        challenges.append(_challenge(
            "assignment-model",
            "Task Assignment Model",
            "How are tasks assigned to people? This affects the data model and UI significantly.",
            options=[
                _option("a", "Single assignee per task",
                        "Each task has one owner. Simple and clear accountability."),
                _option("b", "Multiple assignees",
                        "Tasks can have multiple assignees. More flexible but complicates progress tracking."),
                _option("c", "Team assignment",
                        "Tasks are assigned to teams, not individuals. "
                        "Team members self-select from the team queue."),
            ],
            default="a",
            affects=["domain_model", "stories"],
        ))

    return challenges


def _client_portal_challenges(capabilities: list[str], features: list[str]) -> list[dict[str, Any]]:
    challenges = []

    challenges.append(_challenge(
        "client-data-isolation",
        "Client Data Isolation",
        "Clients should only see their own data. The isolation strategy affects security and architecture.",
        options=[
            _option("a", "Row-level filtering",
                    "All clients share one database. Queries filter by client_id. "
                    "Simple but a bug can leak data between clients."),
            _option("b", "Schema-per-client",
                    "Each client gets a separate database schema. "
                    "Stronger isolation but harder to manage migrations."),
            _option("c", "Shared with strict middleware",
                    "Shared database with mandatory middleware that enforces client scope on every query. "
                    "Balance between simplicity and safety."),
        ],
        default="a",
        affects=["architecture", "domain_model"],
    ))

    challenges.append(_challenge(
        "request-communication",
        "Client-Internal Communication",
        "How do clients and internal reviewers communicate about requests?",
        options=[
            _option("a", "Comments on requests",
                    "Threaded comments attached to each request. "
                    "Simple and keeps context together."),
            _option("b", "Status updates only",
                    "No direct messaging. Clients see status changes and can add notes when resubmitting. "
                    "Minimal but may frustrate users."),
            _option("c", "Integrated messaging",
                    "Full messaging system between client and reviewer. "
                    "Best UX but significant implementation effort."),
        ],
        default="a",
        affects=["domain_model", "stories"],
    ))

    return challenges


def _marketplace_challenges(capabilities: list[str], features: list[str]) -> list[dict[str, Any]]:
    challenges = []

    if "payments" in features:
        challenges.append(_challenge(
            "payment-flow",
            "Payment Flow",
            "How does money move between buyers and sellers?",
            options=[
                _option("a", "Platform holds funds (escrow)",
                        "Payment goes to platform. Released to seller after delivery confirmation. "
                        "Safest for buyers but requires escrow capability from payment provider."),
                _option("b", "Direct to seller with platform fee",
                        "Payment goes directly to seller minus platform fee via Stripe Connect or equivalent. "
                        "Less control but simpler compliance."),
                _option("c", "Manual settlement",
                        "Platform collects all payments and settles with sellers manually. "
                        "Simplest to implement but doesn't scale."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

    challenges.append(_challenge(
        "trust-and-safety",
        "Trust and Safety",
        "How does the platform handle disputes, fraud, and content moderation?",
        options=[
            _option("a", "Admin review queue",
                    "Flagged content and disputes go to an admin review queue. "
                    "Simple and sufficient for low-volume marketplaces."),
            _option("b", "Automated rules + admin escalation",
                    "Basic rules auto-flag content. Admins handle escalated cases. "
                    "Better coverage but requires rule definition."),
            _option("c", "Skip for MVP",
                    "Launch without moderation tooling. Handle issues manually via support. "
                    "Fastest to market but risky."),
        ],
        default="a",
        affects=["stories"],
    ))

    return challenges


def _saas_challenges(capabilities: list[str], features: list[str]) -> list[dict[str, Any]]:
    challenges = []

    challenges.append(_challenge(
        "tenant-isolation",
        "Tenant Isolation",
        "Multi-tenant SaaS needs data isolation between organizations.",
        options=[
            _option("a", "Shared database with org_id filter",
                    "All tenants share one database. Every query filters by organization. "
                    "Simplest but requires discipline to prevent data leaks."),
            _option("b", "Schema-per-tenant",
                    "Each organization gets its own database schema. "
                    "Stronger isolation. Migration management is more complex."),
            _option("c", "Database-per-tenant",
                    "Each organization gets a separate database. "
                    "Maximum isolation but highest operational complexity."),
        ],
        default="a",
        affects=["architecture", "domain_model"],
    ))

    if "billing" in features:
        challenges.append(_challenge(
            "billing-model",
            "Billing Model",
            "How are customers billed?",
            options=[
                _option("a", "Fixed plans (free, pro, enterprise)",
                        "Predefined plans with fixed pricing. "
                        "Simple to implement and communicate."),
                _option("b", "Usage-based billing",
                        "Charge based on actual usage (API calls, storage, etc.). "
                        "Fair but requires metering infrastructure."),
                _option("c", "Hybrid (base plan + overages)",
                        "Fixed base plan with usage-based overages. "
                        "Common model but more complex to implement."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

    return challenges


# -------------------------------------------------------------------
# Common challenges (apply to multiple archetypes)
# -------------------------------------------------------------------

def _common_challenges(capabilities: list[str], features: list[str]) -> list[dict[str, Any]]:
    challenges = []

    if "i18n" in capabilities:
        challenges.append(_challenge(
            "i18n-strategy",
            "Internationalization Strategy",
            "Multi-language support touches content, UI, URLs, and formatting. "
            "The strategy affects how deep i18n goes in the first version.",
            options=[
                _option("a", "Content-level i18n only",
                        "Content collections support multiple locales. "
                        "UI stays in one language. Simplest if the admin is internal-only."),
                _option("b", "Full i18n (content + UI + routing)",
                        "Content, UI labels, and URL structure are all locale-aware. "
                        "Complete solution but more work upfront."),
                _option("c", "UI i18n only",
                        "UI labels are translatable. Content stays single-language. "
                        "Good for apps where content is user-generated, not editorial."),
            ],
            default="b" if "cms" in capabilities else "c",
            affects=["architecture", "stories"],
        ))

    if "scheduled-jobs" in capabilities:
        challenges.append(_challenge(
            "job-infrastructure",
            "Job Infrastructure",
            "Background jobs need reliable execution. The infrastructure choice affects reliability and complexity.",
            options=[
                _option("a", "In-process cron (node-cron or similar)",
                        "Jobs run inside the main Node.js process on a schedule. "
                        "Simplest. No extra infrastructure. But jobs die if the process restarts."),
                _option("b", "Separate worker process",
                        "Dedicated worker process with its own lifecycle. "
                        "More reliable. Can scale independently. Needs docker-compose entry."),
                _option("c", "External job queue (BullMQ + Redis)",
                        "Full job queue with Redis. Retries, priorities, concurrency control. "
                        "Most robust but adds Redis dependency."),
            ],
            default="b",
            affects=["architecture", "stories"],
        ))

    if "authentication" in features:
        challenges.append(_challenge(
            "auth-strategy",
            "Authentication Strategy",
            "How users authenticate affects security, UX, and implementation complexity.",
            options=[
                _option("a", "Email + password (built-in)",
                        "Classic email/password auth. Use the framework's built-in auth if available (e.g., Payload auth). "
                        "Simple, no external dependencies."),
                _option("b", "OAuth / social login",
                        "Login via Google, GitHub, etc. Better UX for consumer apps. "
                        "Requires OAuth provider setup and callback handling."),
                _option("c", "Magic link (passwordless)",
                        "Users receive a login link via email. No passwords to manage. "
                        "Great UX but requires email delivery infrastructure."),
            ],
            default="a",
            affects=["architecture", "stories"],
        ))

    return challenges


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

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


def generate_challenges(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate known challenges for the project based on archetype, capabilities, and features.

    Returns a list of challenge dicts, each with:
    - id, title, description
    - options: list of {key, label, detail}
    - default: recommended option key
    - affects: list of spec sections influenced
    """
    archetype = spec.get("archetype", "")
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    signals = _get_decision_signals(spec)
    app_shape = signals.get("app_shape")
    core_work_features = _normalize_list(signals.get("core_work_features", []))

    challenges: list[dict[str, Any]] = []

    # Archetype-specific challenges
    if archetype == "editorial-cms" or app_shape == "content-platform":
        challenges.extend(_editorial_cms_challenges(capabilities, features))

    elif archetype == "backoffice" or app_shape == "backoffice":
        challenges.extend(_backoffice_challenges(capabilities, features, core_work_features))

    elif archetype == "work-organizer" or app_shape == "internal-work-organizer":
        challenges.extend(_work_organizer_challenges(capabilities, features, core_work_features))

    elif archetype == "client-portal" or app_shape == "client-portal":
        challenges.extend(_client_portal_challenges(capabilities, features))

    elif archetype == "marketplace":
        challenges.extend(_marketplace_challenges(capabilities, features))

    elif archetype == "saas-app":
        challenges.extend(_saas_challenges(capabilities, features))

    # Common challenges (cross-archetype)
    challenges.extend(_common_challenges(capabilities, features))

    # Deduplicate by id
    seen = set()
    unique = []
    for challenge in challenges:
        if challenge["id"] not in seen:
            seen.add(challenge["id"])
            unique.append(challenge)

    return unique


def apply_challenge_decisions(
    spec: dict[str, Any],
    decisions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Apply user challenge decisions to the spec.

    Args:
        spec: The project spec dict
        decisions: dict mapping challenge_id to {
            "chosen_option": "a"|"b"|"c"|"custom",
            "custom_text": "..." (if chosen_option == "custom"),
            "option_label": "..." (label of chosen option),
            "option_detail": "..." (detail of chosen option),
        }

    Updates:
        - spec["challenge_decisions"] — stores all decisions
        - spec["architecture"]["decisions"] — adds architectural decisions
    """
    spec["challenge_decisions"] = decisions

    # Add each decision to architecture decisions
    architecture = spec.get("architecture", {})
    arch_decisions = architecture.get("decisions", [])

    for challenge_id, decision in decisions.items():
        chosen = decision.get("chosen_option", "")
        label = decision.get("option_label", "")
        detail = decision.get("option_detail", "")
        custom_text = decision.get("custom_text", "")

        if chosen == "custom" and custom_text:
            decision_text = f"[{challenge_id}] {custom_text}"
        elif label and detail:
            decision_text = f"[{challenge_id}] {label}: {detail}"
        elif label:
            decision_text = f"[{challenge_id}] {label}"
        else:
            continue

        if decision_text not in arch_decisions:
            arch_decisions.append(decision_text)

    architecture["decisions"] = arch_decisions
    spec["architecture"] = architecture

    return spec