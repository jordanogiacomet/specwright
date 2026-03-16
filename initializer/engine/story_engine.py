"""Story Engine.

Generates implementation stories from features, capabilities,
stack, and structured discovery signals.

Key improvements in this version:
- Acceptance criteria for every story
- Scope boundaries (what NOT to do) for every story
- Expected files derived from stack
- Explicit depends_on for execution ordering
- Validation commands per story
- More core_work_features generate stories (approvals, team-visibility)
- Product shape stories for client-portal, backoffice, content-platform
- Less restrictive condition for automation-jobs story
- Notifications story when feature is present
- Draft-publish story when feature is present
"""


def _merge_story(existing_story, generated_story):
    merged = dict(existing_story)

    if not merged.get("story_key"):
        merged["story_key"] = generated_story["story_key"]

    if not merged.get("title"):
        merged["title"] = generated_story["title"]
    elif merged["title"] != generated_story["title"]:
        titles = list(merged.get("title_alternatives", []))
        if generated_story["title"] not in titles:
            titles.append(generated_story["title"])
        merged["title_alternatives"] = titles

    if not merged.get("description"):
        merged["description"] = generated_story["description"]
    elif merged["description"] != generated_story["description"]:
        descriptions = list(merged.get("description_alternatives", []))
        if generated_story["description"] not in descriptions:
            descriptions.append(generated_story["description"])
        merged["description_alternatives"] = descriptions

    # Merge new enrichment fields only if not already present
    for key in (
        "acceptance_criteria",
        "scope_boundaries",
        "expected_files",
        "depends_on",
        "validation",
    ):
        if key in generated_story and not merged.get(key):
            merged[key] = generated_story[key]

    return merged


def _find_story_index(stories, story_key, title):
    for index, story in enumerate(stories):
        if story.get("story_key") == story_key:
            return index

    for index, story in enumerate(stories):
        if story.get("title") == title:
            return index

    return None


def _get_decision_signals(spec):
    discovery = spec.get("discovery", {})
    if not isinstance(discovery, dict):
        return {}
    signals = discovery.get("decision_signals", {})
    if not isinstance(signals, dict):
        return {}
    return signals


def _normalize_core_work_features(value):
    if not isinstance(value, list):
        return []

    normalized = []
    for item in value:
        if isinstance(item, str):
            text = item.strip().lower()
            if text and text not in normalized:
                normalized.append(text)

    return normalized


# ---------------------------------------------------------------------------
# Stack-aware path helpers
# ---------------------------------------------------------------------------

def _frontend_page_path(stack, route):
    """Return expected page file path based on frontend stack."""
    frontend = stack.get("frontend", "nextjs")
    if frontend in ("nextjs", "next.js", "next"):
        return f"src/app/{route}/page.tsx"
    return f"src/pages/{route}.tsx"


def _backend_path(stack, name):
    """Return expected backend file path based on backend stack."""
    backend = stack.get("backend", "node-api")
    if backend in ("payload", "payload-cms"):
        return f"src/collections/{name}.ts"
    return f"src/api/{name}.ts"


def _lib_path(name):
    return f"src/lib/{name}.ts"


def _component_path(name):
    return f"src/components/{name}.tsx"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_DEFAULT_VALIDATION = {
    "commands": ["npm run build", "npm run lint"],
    "manual_check": None,
}

_MIGRATION_CRITERIA = "Database migration is generated and executed for all schema changes (run migrate:create then migrate)"


def _validation(commands=None, manual_check=None):
    return {
        "commands": commands or ["npm run build", "npm run lint"],
        "manual_check": manual_check,
    }


def _schema_validation(commands=None, manual_check=None):
    """Validation for stories that modify database schema."""
    base_commands = commands or ["npm run build", "npm run lint"]
    return {
        "commands": base_commands,
        "manual_check": manual_check,
    }


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_stories(spec):
    stories = [dict(story) for story in spec.get("stories", [])]
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    stack = spec.get("stack", {})
    signals = _get_decision_signals(spec)

    primary_audience = signals.get("primary_audience")
    app_shape = signals.get("app_shape")
    needs_scheduled_jobs = signals.get("needs_scheduled_jobs")
    core_work_features = _normalize_core_work_features(
        signals.get("core_work_features", [])
    )

    backend = stack.get("backend", "node-api")
    frontend = stack.get("frontend", "nextjs")
    database = stack.get("database", "postgres")

    counter = 1
    for story in stories:
        story_id = story.get("id", "")
        if not story_id.startswith("ST-"):
            continue

        suffix = story_id[3:]
        if suffix.isdigit():
            counter = max(counter, int(suffix) + 1)

    def upsert_story(
        story_key,
        title,
        description,
        acceptance_criteria=None,
        scope_boundaries=None,
        expected_files=None,
        depends_on=None,
        validation=None,
    ):
        nonlocal counter

        generated_story = {
            "story_key": story_key,
            "title": title,
            "description": description,
            "acceptance_criteria": acceptance_criteria or [],
            "scope_boundaries": scope_boundaries or [],
            "expected_files": expected_files or [],
            "depends_on": depends_on or [],
            "validation": validation or dict(_DEFAULT_VALIDATION),
        }

        existing_index = _find_story_index(stories, story_key, title)
        if existing_index is not None:
            stories[existing_index] = _merge_story(
                stories[existing_index],
                generated_story,
            )
            return stories[existing_index]

        sid = f"ST-{counter:03d}"
        story = {
            "id": sid,
            **generated_story,
        }
        counter += 1
        stories.append(story)
        return story

    # ===================================================================
    # BOOTSTRAP STORIES
    # ===================================================================

    upsert_story(
        "bootstrap.repository",
        "Initialize project repository",
        f"Create project structure using {frontend} + {backend} + {database}.",
        acceptance_criteria=[
            "package.json exists with scripts: dev, build, lint, test",
            ".env.example exists with all required environment variables",
            "TypeScript is configured with tsconfig.json",
            "ESLint and Prettier are configured",
            "npm install completes without errors",
            "npm run build passes",
        ],
        scope_boundaries=[
            "Do NOT implement any features yet — this is project scaffolding only",
            "Do NOT add authentication, roles, or any business logic",
            "Do NOT create database tables — that is a separate story",
        ],
        expected_files=[
            "package.json",
            "tsconfig.json",
            ".eslintrc.js or eslint.config.js",
            ".env.example",
            ".gitignore",
            "README.md",
        ],
        depends_on=[],
        validation=_validation(
            commands=["npm install", "npm run build", "npm run lint"],
            manual_check="Project directory exists with expected structure",
        ),
    )

    if stack.get("database"):
        upsert_story(
            "bootstrap.database",
            "Setup database",
            f"Configure {database} database with connection pool and migrations.",
            acceptance_criteria=[
                f"{database} connection is configured via environment variable",
                "Database client or ORM is installed and configured",
                "Initial migration or schema setup runs without errors",
                "Connection can be verified programmatically",
                "docker-compose.yml includes database service" if database == "postgres" else f"{database} setup is documented",
                _MIGRATION_CRITERIA,
            ],
            scope_boundaries=[
                "Do NOT create application tables yet — only the connection layer",
                "Do NOT add seed data",
                "Do NOT implement any API endpoints",
            ],
            expected_files=[
                "docker-compose.yml" if database == "postgres" else f"docs/database-setup.md",
                _lib_path("db"),
                ".env.example (updated with DB connection string)",
            ],
            depends_on=["bootstrap.repository"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Database container starts and connection succeeds",
            ),
        )

    if stack.get("backend"):
        backend_ac = [
            f"Backend is initialized using {backend}",
            "Server starts and responds to health check",
            "API is accessible at the configured port",
        ]
        backend_files = []

        if backend in ("payload", "payload-cms"):
            backend_ac.append("Payload config file exists with database adapter configured")
            backend_ac.append("Payload admin panel is accessible at /admin")
            backend_files = [
                "src/payload.config.ts",
                "src/server.ts or src/app/(payload)/layout.tsx",
            ]
        else:
            backend_ac.append("Express or Fastify server starts with basic health endpoint")
            backend_files = [
                "src/server.ts",
                "src/api/health.ts",
            ]

        upsert_story(
            "bootstrap.backend",
            "Setup backend service",
            f"Initialize backend using {backend} with database connection.",
            acceptance_criteria=backend_ac,
            scope_boundaries=[
                "Do NOT implement authentication yet",
                "Do NOT create domain collections or models yet",
                "Do NOT add business logic — only the backend skeleton",
            ],
            expected_files=backend_files,
            depends_on=["bootstrap.database"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Backend starts and /api/health or /admin responds",
            ),
        )

    if stack.get("frontend"):
        frontend_ac = [
            f"Frontend application renders using {frontend}",
            "Root page loads without errors",
            "Basic layout component exists (shell, navigation placeholder)",
        ]
        frontend_files = [
            _frontend_page_path(stack, "(app)"),
            _component_path("Layout"),
        ]

        if frontend in ("nextjs", "next.js", "next"):
            frontend_ac.append("Next.js app router is configured with route groups")
            frontend_files.append("src/app/layout.tsx")

        upsert_story(
            "bootstrap.frontend",
            "Create frontend application",
            f"Implement frontend application shell using {frontend}.",
            acceptance_criteria=frontend_ac,
            scope_boundaries=[
                "Do NOT implement pages beyond the root layout and a placeholder home page",
                "Do NOT add authentication UI — that is a separate story",
                "Do NOT style extensively — basic layout only",
            ],
            expected_files=frontend_files,
            depends_on=["bootstrap.backend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Frontend loads in browser without errors",
            ),
        )

    # ===================================================================
    # FEATURE STORIES
    # ===================================================================

    if "authentication" in features:
        auth_ac = [
            "Users can register with email and password",
            "Users can log in and receive a valid session",
            "Users can log out and have their session invalidated",
            "Protected routes return 401 for unauthenticated requests",
            "Passwords are hashed before storage",
        ]
        auth_files = [_lib_path("auth")]

        if backend in ("payload", "payload-cms"):
            auth_ac.append("Payload Users collection has auth enabled")
            auth_files.append(_backend_path(stack, "Users"))
        else:
            auth_files.append("src/api/auth.ts")

        auth_ac.append(_MIGRATION_CRITERIA)
        auth_files.append(_frontend_page_path(stack, "(auth)/login"))

        upsert_story(
            "feature.authentication",
            "Implement authentication",
            "Add registration, login, logout and session management.",
            acceptance_criteria=auth_ac,
            scope_boundaries=[
                "Do NOT implement OAuth or social login in this story",
                "Do NOT implement password reset or email verification",
                "Do NOT implement MFA",
            ],
            expected_files=auth_files,
            depends_on=["bootstrap.backend", "bootstrap.frontend"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can register, log in, and access protected route",
            ),
        )

    if "roles" in features:
        roles_ac = [
            "Role model is defined with at least admin and default user roles",
            "Permissions are enforced on protected endpoints",
            "Admin users can manage other users' roles",
            "Unauthorized role access returns 403",
            _MIGRATION_CRITERIA,
        ]
        roles_files = [_lib_path("permissions")]

        if backend in ("payload", "payload-cms"):
            roles_ac.append("Payload access control functions use role checks")
            roles_files.append(f"{_backend_path(stack, 'Users')} (updated with roles field)")
        else:
            roles_files.append("src/middleware/authorize.ts")

        upsert_story(
            "feature.roles",
            "Implement role-based access control",
            "Define roles, permissions, and enforce authorization boundaries.",
            acceptance_criteria=roles_ac,
            scope_boundaries=[
                "Do NOT implement granular per-field permissions unless required by spec",
                "Do NOT implement a permissions admin UI — enforce in backend only",
            ],
            expected_files=roles_files,
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Admin can access admin routes; regular user gets 403",
            ),
        )

    if "media-library" in features:
        media_ac = [
            "Users can upload images and files",
            "Uploaded media is stored and retrievable via URL",
            "Media list view shows uploaded assets with thumbnails",
            "File size and type validation is enforced on upload",
            _MIGRATION_CRITERIA,
        ]
        media_files = []

        if backend in ("payload", "payload-cms"):
            media_ac.append("Payload Media collection is configured with upload settings")
            media_files.append(_backend_path(stack, "Media"))
        else:
            media_files.append("src/api/media.ts")
            media_files.append(_lib_path("storage"))

        upsert_story(
            "feature.media-library",
            "Implement media library",
            "Allow uploading, listing, and managing media assets.",
            acceptance_criteria=media_ac,
            scope_boundaries=[
                "Do NOT implement image optimization or CDN delivery in this story",
                "Do NOT implement media usage tracking across content",
            ],
            expected_files=media_files,
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can upload an image and see it in the media list",
            ),
        )

    if "draft-publish" in features:
        dp_ac = [
            "Content items have a status field with at least draft and published states",
            "Only authorized roles can transition content to published state",
            "Published content is visible through the appropriate surface",
            "Draft content is only visible to editors and admins",
            _MIGRATION_CRITERIA,
        ]

        if "roles" in features:
            dp_ac.append("Publishing requires reviewer or admin role")

        upsert_story(
            "feature.draft-publish",
            "Implement draft and publish workflow",
            "Add draft, review, and publish states with role-based transitions.",
            acceptance_criteria=dp_ac,
            scope_boundaries=[
                "Do NOT implement versioning or revision history",
                "Do NOT implement scheduled publishing — that is a separate story",
                "Do NOT implement approval notifications",
            ],
            expected_files=[
                _lib_path("content-status"),
            ],
            depends_on=["feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can create draft, publish it, verify it appears on the appropriate surface",
            ),
        )

    if "preview" in features:
        upsert_story(
            "feature.preview",
            "Implement content preview",
            "Allow previewing unpublished content in the frontend.",
            acceptance_criteria=[
                "Draft content can be previewed through a unique preview URL or mode",
                "Preview renders content as it would appear when published",
                "Preview is only accessible to authenticated users with appropriate roles",
                "Preview does not leak draft content to public or search engines",
            ],
            scope_boundaries=[
                "Do NOT implement live editing or inline editing",
                "Do NOT implement preview for multiple content types — start with the primary type",
            ],
            expected_files=[
                _frontend_page_path(stack, "preview/[slug]"),
                _lib_path("preview"),
            ],
            depends_on=["feature.draft-publish"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Can preview draft content via preview URL while logged in",
            ),
        )

    if "scheduled-publishing" in features:
        upsert_story(
            "feature.scheduled-publishing",
            "Implement scheduled publishing",
            "Create background job to publish content at a scheduled time.",
            acceptance_criteria=[
                "Content items can have a publishAt date/time field",
                "A background job checks for content due for publishing and publishes it",
                "Published content appears on the appropriate surface after the scheduled time",
                "Job runs reliably on a configurable interval",
                "Failed publish attempts are logged and retried",
                _MIGRATION_CRITERIA,
            ],
            scope_boundaries=[
                "Do NOT implement a full job queue system — a simple cron-style check is sufficient",
                "Do NOT implement scheduled unpublishing in this story",
            ],
            expected_files=[
                _lib_path("scheduler"),
                "src/jobs/publish-scheduled.ts",
            ],
            depends_on=["feature.draft-publish"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Set publishAt to near future, verify content publishes automatically",
            ),
        )

    if "search" in features:
        upsert_story(
            "feature.search",
            "Implement search",
            "Add search functionality across the application.",
            acceptance_criteria=[
                "Users can search for content or records via a search input",
                "Search results are relevant and ordered by relevance or date",
                "Search handles empty queries and no-results gracefully",
                "Search responds within acceptable latency for typical dataset sizes",
            ],
            scope_boundaries=[
                "Do NOT implement full-text search engine integration (Elasticsearch, etc.) — use database search",
                "Do NOT implement faceted search or advanced filters in this story",
            ],
            expected_files=[
                _component_path("SearchInput"),
                _frontend_page_path(stack, "search"),
            ],
            depends_on=["bootstrap.frontend", "bootstrap.backend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Can search and see relevant results",
            ),
        )

    if "payments" in features:
        upsert_story(
            "feature.payments",
            "Integrate payment provider",
            "Integrate payment processing for transactions.",
            acceptance_criteria=[
                "Payment provider SDK is installed and configured",
                "Users can initiate a payment flow",
                "Successful payments are recorded in the database",
                "Failed payments are handled gracefully with user feedback",
                "Payment webhooks are handled for async confirmation",
            ],
            scope_boundaries=[
                "Do NOT implement subscription billing — that is a separate story if needed",
                "Do NOT implement refunds in this story",
                "Do NOT store raw card data — use the provider's tokenization",
            ],
            expected_files=[
                _lib_path("payments"),
                "src/api/webhooks/payment.ts",
            ],
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can complete a test payment flow in sandbox/test mode",
            ),
        )

    if "notifications" in features:
        upsert_story(
            "feature.notifications",
            "Implement notification system",
            "Add notification delivery for important events.",
            acceptance_criteria=[
                "Notifications can be created programmatically for events",
                "Users can see their notifications in the UI",
                "Notifications have read/unread state",
                "Notification preferences or rules can be configured per user",
            ],
            scope_boundaries=[
                "Do NOT implement email or push notification delivery in this story",
                "Do NOT implement real-time WebSocket delivery — polling or page-load is sufficient",
            ],
            expected_files=[
                _backend_path(stack, "Notifications") if backend in ("payload", "payload-cms") else "src/api/notifications.ts",
                _component_path("NotificationCenter"),
                _lib_path("notifications"),
            ],
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Can trigger a notification and see it in the UI",
            ),
        )

    if "analytics" in features:
        upsert_story(
            "feature.analytics",
            "Implement analytics tracking",
            "Add analytics instrumentation for usage tracking.",
            acceptance_criteria=[
                "Analytics events are tracked for key user actions",
                "Event data is sent to the configured analytics backend",
                "Analytics does not block UI rendering or degrade performance",
                "Page views are tracked automatically",
            ],
            scope_boundaries=[
                "Do NOT implement a custom analytics dashboard",
                "Do NOT implement server-side analytics in this story",
            ],
            expected_files=[
                _lib_path("analytics"),
                _component_path("AnalyticsProvider"),
            ],
            depends_on=["bootstrap.frontend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Analytics events appear in the configured provider",
            ),
        )

    if "billing" in features:
        upsert_story(
            "feature.billing",
            "Implement billing and subscription management",
            "Add billing flows, subscription management, and payment lifecycle.",
            acceptance_criteria=[
                "Users can subscribe to a plan",
                "Subscription status is tracked in the database",
                "Billing portal or management UI exists for users",
                "Subscription webhooks are handled for lifecycle events",
                "Trial periods are supported if configured",
            ],
            scope_boundaries=[
                "Do NOT implement custom invoicing",
                "Do NOT implement multiple payment methods — start with card via provider",
            ],
            expected_files=[
                _lib_path("billing"),
                "src/api/webhooks/billing.ts",
                _frontend_page_path(stack, "(app)/billing"),
            ],
            depends_on=["feature.authentication", "feature.payments"] if "payments" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can subscribe to a plan in sandbox/test mode",
            ),
        )

    # ===================================================================
    # PRODUCT SHAPE STORIES
    # ===================================================================

    if app_shape == "internal-work-organizer" or primary_audience == "internal_teams":
        upsert_story(
            "product.internal-dashboard",
            "Build internal dashboard shell",
            "Create the main internal application shell and navigation for team workflows.",
            acceptance_criteria=[
                "Application shell renders with sidebar navigation",
                "Navigation includes links to main work sections",
                "Dashboard home shows a summary or placeholder content",
                "Shell is responsive and works on common screen sizes",
            ],
            scope_boundaries=[
                "Do NOT implement data tables or work item views — those are separate stories",
                "Do NOT add real data — use placeholder content for the shell",
            ],
            expected_files=[
                _component_path("AppShell"),
                _component_path("SidebarNav"),
                _frontend_page_path(stack, "(app)/dashboard"),
            ],
            depends_on=["feature.authentication", "feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Dashboard shell renders with navigation after login",
            ),
        )

    if app_shape == "client-portal":
        upsert_story(
            "product.client-portal-shell",
            "Build client portal shell",
            "Create the client-facing application shell, navigation, and access control.",
            acceptance_criteria=[
                "Client-facing shell renders with appropriate navigation",
                "Access is restricted to authenticated client users",
                "Navigation includes links to requests, status tracking, and account",
                "Shell distinguishes between client and internal views",
            ],
            scope_boundaries=[
                "Do NOT implement request submission forms — that is a separate story",
                "Do NOT implement internal reviewer views in this story",
            ],
            expected_files=[
                _component_path("PortalShell"),
                _frontend_page_path(stack, "(portal)/dashboard"),
            ],
            depends_on=["feature.authentication", "feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Client portal shell renders after login with client role",
            ),
        )

    if app_shape == "backoffice":
        upsert_story(
            "product.backoffice-shell",
            "Build backoffice application shell",
            "Create the internal backoffice shell with navigation, filtering, and operational views.",
            acceptance_criteria=[
                "Backoffice shell renders with sidebar navigation and top bar",
                "Navigation includes links to operational sections (orders, tasks, reports, etc.)",
                "Filtering and search placeholders are present in the shell",
                "Shell supports compact, data-dense layout suitable for operations",
            ],
            scope_boundaries=[
                "Do NOT implement actual data views or CRUD — only the shell and navigation",
                "Do NOT implement reports or charts in this story",
            ],
            expected_files=[
                _component_path("BackofficeShell"),
                _component_path("SidebarNav"),
                _component_path("TopBar"),
                _frontend_page_path(stack, "(admin)/dashboard"),
            ],
            depends_on=["feature.authentication", "feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Backoffice shell renders with navigation after admin login",
            ),
        )

    if app_shape == "content-platform":
        upsert_story(
            "product.content-platform-shell",
            "Build content platform shell",
            "Create the content management and delivery shell with editorial navigation.",
            acceptance_criteria=[
                "Admin shell renders with editorial navigation (content, media, settings)",
                "Shell supports both admin and public route groups if public-site capability exists",
                "Content list and detail views have placeholder layouts",
            ],
            scope_boundaries=[
                "Do NOT implement actual content CRUD — only the navigation shell",
                "Do NOT implement the public site layout in this story if public-site capability exists",
            ],
            expected_files=[
                _frontend_page_path(stack, "(admin)/content"),
                _component_path("AdminShell"),
            ],
            depends_on=["feature.authentication"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Admin content shell renders with editorial navigation",
            ),
        )

    # ===================================================================
    # CORE WORK FEATURE STORIES
    # ===================================================================

    if "deadlines" in core_work_features:
        upsert_story(
            "product.deadlines",
            "Model deadlines and due dates",
            "Implement domain support for deadlines, due dates, and related validations.",
            acceptance_criteria=[
                "Work items have a dueDate field",
                "Overdue items are identifiable via query or computed field",
                "UI displays due date and overdue status clearly",
                "Due date can be set and updated by authorized roles",
            ],
            scope_boundaries=[
                "Do NOT implement reminder notifications — that is a separate story",
                "Do NOT implement recurring deadlines",
            ],
            expected_files=[
                _lib_path("deadlines"),
            ],
            depends_on=["product.internal-dashboard"] if app_shape == "internal-work-organizer" else ["bootstrap.backend"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can set a due date and see overdue status",
            ),
        )

    if "progress-tracking" in core_work_features or "progress tracking" in core_work_features or "project-tracking" in core_work_features or "project tracking" in core_work_features:
        upsert_story(
            "product.progress-tracking",
            "Implement progress tracking",
            "Add progress tracking and status transitions for core work items.",
            acceptance_criteria=[
                "Work items have a status field with defined states and valid transitions",
                "Status transitions are enforced — invalid transitions return an error",
                "UI reflects current status with visual indicators",
                "Status history is tracked or at least the last transition is logged",
            ],
            scope_boundaries=[
                "Do NOT implement Kanban or drag-and-drop UI",
                "Do NOT implement automated status transitions",
            ],
            expected_files=[
                _lib_path("status-machine"),
            ],
            depends_on=["product.internal-dashboard"] if app_shape == "internal-work-organizer" else ["bootstrap.backend"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can transition a work item through valid states",
            ),
        )

    if "task-assignment" in core_work_features or "task assignment" in core_work_features:
        upsert_story(
            "product.task-assignment",
            "Implement task assignment",
            "Allow work items to be assigned to owners and teams.",
            acceptance_criteria=[
                "Work items have an assignee field referencing a user",
                "Authorized roles can assign and reassign work items",
                "Assigned user can see their assignments in a filtered view",
                "Unassigned items are identifiable",
            ],
            scope_boundaries=[
                "Do NOT implement workload balancing or auto-assignment",
                "Do NOT implement team-based assignment — start with individual assignment",
            ],
            expected_files=[
                _component_path("AssigneeSelect"),
            ],
            depends_on=["feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can assign a work item and see it in the assignee's view",
            ),
        )

    if "reminders" in core_work_features:
        upsert_story(
            "product.reminders",
            "Implement reminders",
            "Add reminder workflows for approaching deadlines and pending work.",
            acceptance_criteria=[
                "Reminders are generated for work items approaching their due date",
                "Reminders appear in the notification center or a dedicated view",
                "Reminder timing is configurable (e.g., 1 day before, same day)",
                "Completed items do not generate reminders",
            ],
            scope_boundaries=[
                "Do NOT implement email or push delivery for reminders",
                "Do NOT implement custom reminder rules per user",
            ],
            expected_files=[
                "src/jobs/generate-reminders.ts",
                _lib_path("reminders"),
            ],
            depends_on=["product.deadlines"] if "deadlines" in core_work_features else ["bootstrap.backend"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Reminder appears for a work item near its due date",
            ),
        )

    if "report-generation" in core_work_features or "report generation" in core_work_features:
        upsert_story(
            "product.report-generation",
            "Implement report generation",
            "Generate summary reports for work progress and operational visibility.",
            acceptance_criteria=[
                "At least one report type is available (e.g., weekly summary, status distribution)",
                "Report data is queried from the database, not hardcoded",
                "Report is viewable in the UI with appropriate formatting",
                "Report can be filtered by date range or team",
            ],
            scope_boundaries=[
                "Do NOT implement PDF export in this story",
                "Do NOT implement scheduled report delivery",
                "Do NOT implement custom report builder",
            ],
            expected_files=[
                _frontend_page_path(stack, "(app)/reports"),
                "src/api/reports.ts" if backend not in ("payload", "payload-cms") else _lib_path("reports"),
            ],
            depends_on=["product.internal-dashboard"] if app_shape == "internal-work-organizer" else ["bootstrap.backend", "bootstrap.frontend"],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Report page shows data from the database with date filtering",
            ),
        )

    if "approvals" in core_work_features:
        upsert_story(
            "product.approvals",
            "Implement approval workflows",
            "Add approval steps and sign-off flows for work items that require review.",
            acceptance_criteria=[
                "Work items can be submitted for approval",
                "Designated approvers can approve or reject submissions",
                "Approval status is tracked and visible in the UI",
                "Rejected items can be revised and resubmitted",
            ],
            scope_boundaries=[
                "Do NOT implement multi-step approval chains",
                "Do NOT implement approval delegation or escalation",
            ],
            expected_files=[
                _lib_path("approvals"),
            ],
            depends_on=["feature.roles"] if "roles" in features else ["feature.authentication"],
            validation=_validation(
                commands=["npm run build", "npm test"],
                manual_check="Can submit for approval, approve, and see status change",
            ),
        )

    if "team-visibility" in core_work_features or "team visibility" in core_work_features:
        upsert_story(
            "product.team-visibility",
            "Implement team visibility",
            "Add team-level views showing workload distribution, progress, and capacity.",
            acceptance_criteria=[
                "Team view shows all team members and their assigned work items",
                "Workload distribution is visible (items per person or similar metric)",
                "Team view supports filtering by status or date",
                "Only team leads or admins can see the team view",
            ],
            scope_boundaries=[
                "Do NOT implement capacity planning or forecasting",
                "Do NOT implement cross-team comparisons",
            ],
            expected_files=[
                _frontend_page_path(stack, "(app)/team"),
                _component_path("TeamWorkloadView"),
            ],
            depends_on=[
                "product.task-assignment" if "task-assignment" in core_work_features else "feature.roles",
            ],
            validation=_validation(
                commands=["npm run build"],
                manual_check="Team view shows members and their workload after login as team lead",
            ),
        )

    # ===================================================================
    # AUTOMATION STORIES
    # ===================================================================

    if "scheduled-jobs" in capabilities:
        if app_shape in {"internal-work-organizer", "backoffice", "worker-pipeline"}:
            upsert_story(
                "product.automation-jobs",
                "Implement workflow automation jobs",
                "Implement scheduled jobs for reminders, progress automation, or recurring operational tasks.",
                acceptance_criteria=[
                    "At least one scheduled job runs on a configurable interval",
                    "Job execution is logged with timestamps and outcomes",
                    "Failed jobs are retried or flagged for manual intervention",
                    "Jobs do not block the main application process",
                ],
                scope_boundaries=[
                    "Do NOT implement a full job queue system — a simple scheduler is sufficient for MVP",
                    "Do NOT implement job management UI",
                ],
                expected_files=[
                    "src/jobs/index.ts",
                    _lib_path("scheduler"),
                ],
                depends_on=["bootstrap.backend"],
                validation=_validation(
                    commands=["npm run build", "npm test"],
                    manual_check="Scheduled job runs and logs output on interval",
                ),
            )
        elif needs_scheduled_jobs is True and app_shape not in {"content-platform"}:
            upsert_story(
                "product.automation-jobs",
                "Implement background automation jobs",
                "Implement scheduled and background jobs for application automation workflows.",
                acceptance_criteria=[
                    "At least one background job runs on a configurable interval",
                    "Job execution is logged with timestamps and outcomes",
                    "Failed jobs are retried or flagged",
                    "Jobs run independently of the main application process",
                ],
                scope_boundaries=[
                    "Do NOT implement a distributed job queue",
                    "Do NOT implement job management UI",
                ],
                expected_files=[
                    "src/jobs/index.ts",
                    _lib_path("scheduler"),
                ],
                depends_on=["bootstrap.backend"],
                validation=_validation(
                    commands=["npm run build", "npm test"],
                    manual_check="Background job runs and logs output",
                ),
            )

    return stories