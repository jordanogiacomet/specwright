"""
AI Refine Engine

Improves generated spec using heuristics now
and AI later.

Key change: CDN recommendation is only added when
public-site is in the reconciled capabilities list.

ST-900 and ST-901 now include acceptance criteria,
scope boundaries, expected files, and validation
derived from the project stack and capabilities.
"""


def _has_public_site(spec):
    """Check if public-site is in the reconciled capabilities list."""
    capabilities = spec.get("capabilities", [])
    return "public-site" in capabilities


def _get_stack(spec):
    stack = spec.get("stack", {})
    return {
        "backend": (stack.get("backend") or "node-api").lower().strip(),
        "database": (stack.get("database") or "postgres").lower().strip(),
        "frontend": (stack.get("frontend") or "nextjs").lower().strip(),
    }


def refine_prd(spec):

    architecture = spec.get("architecture", {})
    decisions = architecture.get("decisions", [])

    improvements = []

    # CDN is only relevant for public-facing sites
    if _has_public_site(spec):
        if "CDN recommended for public assets." not in decisions:
            improvements.append("CDN recommended for public assets.")

    if "Add monitoring and logging stack." not in decisions:
        improvements.append("Add monitoring and logging stack.")

    if "Add automated database backups." not in decisions:
        improvements.append("Add automated database backups.")

    decisions.extend(improvements)

    spec["architecture"]["decisions"] = decisions

    return spec


def _build_monitoring_story(spec):
    """Build enriched ST-900 monitoring story."""
    stack = _get_stack(spec)
    capabilities = spec.get("capabilities", [])
    backend = stack["backend"]
    database = stack["database"]

    is_payload = backend in ("payload", "payload-cms")

    acceptance_criteria = [
        "Structured JSON logging is configured for all backend services",
        "Log levels (debug, info, warn, error) are used consistently",
        "Health check endpoint exists and returns service status",
        "Unhandled errors are caught and logged with stack traces",
    ]

    expected_files = [
        "src/lib/logger.ts",
        "src/app/api/health/route.ts",
    ]

    if database == "postgres":
        acceptance_criteria.append(
            "Database connection health is included in the health check response"
        )

    if "scheduled-jobs" in capabilities:
        acceptance_criteria.append(
            "Background job execution is logged with start time, duration, and outcome"
        )

    if _has_public_site(spec):
        acceptance_criteria.append(
            "Request logging includes response time for public-facing routes"
        )

    scope_boundaries = [
        "Do NOT integrate external monitoring services (Datadog, Sentry, etc.) — use structured logs only",
        "Do NOT implement custom dashboards — logs should be queryable via standard tools",
        "Do NOT add performance profiling — focus on operational visibility",
    ]

    return {
        "id": "ST-900",
        "title": "Setup monitoring and logging",
        "description": "Integrate structured logging, health checks, and error tracking across the application.",
        "acceptance_criteria": acceptance_criteria,
        "scope_boundaries": scope_boundaries,
        "expected_files": expected_files,
        "depends_on": ["bootstrap.backend"],
        "validation": {
            "commands": ["npm run build"],
            "manual_check": "Health check endpoint returns 200 with service status; logs appear in structured JSON format",
        },
    }


def _build_backups_story(spec):
    """Build enriched ST-901 backups story."""
    stack = _get_stack(spec)
    database = stack["database"]
    deploy_target = spec.get("answers", {}).get("deploy_target", "docker")

    acceptance_criteria = [
        f"Automated {database} backup script exists and runs successfully",
        "Backup files are stored in a configurable location",
        "Backup retention policy is documented (e.g., keep last 7 daily backups)",
        "Restore procedure is documented and has been tested manually",
    ]

    expected_files = [
        "scripts/backup.sh",
        "scripts/restore.sh",
    ]

    if database == "postgres":
        acceptance_criteria.append(
            "Backup uses pg_dump with custom format for efficient storage and selective restore"
        )
        expected_files.append("docs/backup-restore.md")
    elif database in ("mysql", "mariadb"):
        acceptance_criteria.append(
            "Backup uses mysqldump with single-transaction for consistency"
        )
        expected_files.append("docs/backup-restore.md")
    elif database == "mongodb":
        acceptance_criteria.append(
            "Backup uses mongodump with oplog for point-in-time recovery capability"
        )
        expected_files.append("docs/backup-restore.md")

    if deploy_target in ("docker", "docker_and_k8s_later"):
        acceptance_criteria.append(
            "Backup script can run inside or outside the Docker environment"
        )

    scope_boundaries = [
        "Do NOT implement cloud-specific backup solutions (RDS snapshots, etc.) — use portable scripts",
        "Do NOT implement real-time replication — periodic backups are sufficient for MVP",
        "Do NOT implement backup monitoring or alerting — that can be added later",
    ]

    return {
        "id": "ST-901",
        "title": "Implement backups",
        "description": f"Automate {database} database backups with retention policies and documented restore procedure.",
        "acceptance_criteria": acceptance_criteria,
        "scope_boundaries": scope_boundaries,
        "expected_files": expected_files,
        "depends_on": ["bootstrap.database"],
        "validation": {
            "commands": ["bash scripts/backup.sh"],
            "manual_check": f"Backup file is created; restore script successfully restores a test {database} dump",
        },
    }


def refine_stories(spec):

    stories = spec.get("stories", [])

    ids = [s["id"] for s in stories]

    if "ST-900" not in ids:
        stories.append(_build_monitoring_story(spec))

    if "ST-901" not in ids:
        stories.append(_build_backups_story(spec))

    spec["stories"] = stories

    return spec


def refine_spec(spec):

    spec = refine_prd(spec)
    spec = refine_stories(spec)

    return spec