"""
AI Refine Engine

Improves generated spec using heuristics now
and AI later.

Key change: CDN recommendation is only added when
public-site is in the reconciled capabilities list.

ST-900 and ST-901 now include acceptance criteria,
scope boundaries, expected files, and validation
derived from the project stack and capabilities.

ST-902 (rate limiting) and ST-903 (password policy)
are security-hardening stories added when
authentication is present.

Complex stories (>7 ACs or >8 expected files) are
automatically split into smaller parts to keep
AI execution time manageable.
"""

import math

from initializer.engine.story_engine import derive_execution_metadata


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
        "story_key": "operations.monitoring",
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
        "story_key": "operations.backups",
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


def _build_rate_limiting_story(spec):
    """Build enriched ST-902 rate limiting story."""
    stack = _get_stack(spec)
    backend = stack["backend"]
    frontend = stack["frontend"]

    is_payload = backend in ("payload", "payload-cms")
    is_nextjs = frontend in ("nextjs", "next.js", "next")

    acceptance_criteria = [
        "Auth endpoints return 429 Too Many Requests after exceeding the request threshold",
        "Rate limiter uses a sliding window or token bucket algorithm with configurable limits",
        "Responses include rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, and Retry-After",
    ]

    expected_files = [
        "src/lib/rate-limit.ts",
    ]

    if is_payload:
        acceptance_criteria.append(
            "Rate limiting applies to Payload endpoints /api/users/login and /api/users/create"
        )

    if is_nextjs:
        acceptance_criteria.append(
            "Rate limiting is implemented as Next.js middleware or API route wrapper"
        )
        expected_files.append("src/middleware.ts")

    scope_boundaries = [
        "Do NOT implement IP-based blocking or ban lists",
        "Do NOT implement CAPTCHA or challenge-response mechanisms",
        "Do NOT implement distributed rate limiting — in-memory is sufficient for MVP",
    ]

    return {
        "id": "ST-902",
        "title": "Add rate limiting to auth endpoints",
        "story_key": "security.rate-limiting",
        "description": "Protect authentication endpoints against brute-force attacks with configurable rate limiting.",
        "acceptance_criteria": acceptance_criteria,
        "scope_boundaries": scope_boundaries,
        "expected_files": expected_files,
        "depends_on": ["feature.authentication"],
        "validation": {
            "commands": ["npm run build"],
            "manual_check": "Rapidly hitting /api/auth/login returns 429 after threshold is exceeded",
        },
    }


def _build_password_policy_story(spec):
    """Build enriched ST-903 password policy story."""

    acceptance_criteria = [
        "Registration endpoint rejects passwords shorter than 8 characters with a 400 response and descriptive error message",
        "Login form validates minimum password length of 8 characters on the client before submission",
        "Password validation logic is centralized in a shared utility importable by both client and server",
    ]

    expected_files = [
        "src/lib/validation.ts",
    ]

    scope_boundaries = [
        "Do NOT implement password complexity rules (uppercase, special characters) beyond minimum length",
        "Do NOT implement a password strength meter",
        "Do NOT implement password history or reuse prevention",
    ]

    return {
        "id": "ST-903",
        "title": "Enforce password policy",
        "story_key": "security.password-policy",
        "description": "Enforce minimum password length of 8 characters on both client and server.",
        "acceptance_criteria": acceptance_criteria,
        "scope_boundaries": scope_boundaries,
        "expected_files": expected_files,
        "depends_on": ["feature.authentication"],
        "validation": {
            "commands": ["npm run build", "npm test"],
            "manual_check": "Registering with a 3-character password returns 400; 8+ character password succeeds",
        },
    }


# -------------------------------------------------------
# Story-splitting heuristic
# -------------------------------------------------------

MAX_AC_COUNT = 9
MAX_EXPECTED_FILES = 8
MIN_AC_PER_PART = 4

_SUFFIX_LETTERS = "bcdefghijklmnopqrstuvwxyz"


def _split_complex_stories(spec):
    """Split stories that exceed complexity thresholds into smaller parts."""
    stories = spec.get("stories", [])
    new_stories = []

    for story in stories:
        acs = story.get("acceptance_criteria", [])
        files = story.get("expected_files", [])

        exceeds_threshold = len(acs) > MAX_AC_COUNT or len(files) > MAX_EXPECTED_FILES
        # Don't split if each part would have fewer than MIN_AC_PER_PART ACs
        worth_splitting = len(acs) >= MIN_AC_PER_PART * 2

        if not exceeds_threshold or not worth_splitting:
            new_stories.append(story)
            continue

        parts = _split_story(story)
        new_stories.extend(parts)

    spec["stories"] = new_stories
    return spec


def _split_story(story):
    """Split a single story into balanced parts."""
    acs = story.get("acceptance_criteria", [])
    files = story.get("expected_files", [])
    num_parts = max(
        math.ceil(len(acs) / MAX_AC_COUNT),
        math.ceil(len(files) / MAX_EXPECTED_FILES) if files else 1,
    )
    num_parts = max(num_parts, 2)  # at least 2 parts if we're splitting

    # Balanced AC chunks
    ac_chunk_size = math.ceil(len(acs) / num_parts)
    ac_chunks = [acs[i:i + ac_chunk_size] for i in range(0, len(acs), ac_chunk_size)]

    # Balanced file chunks
    if files:
        file_chunk_size = math.ceil(len(files) / num_parts)
        file_chunks = [files[i:i + file_chunk_size] for i in range(0, len(files), file_chunk_size)]
    else:
        file_chunks = [[] for _ in range(num_parts)]

    # Pad chunks to same length
    while len(ac_chunks) < num_parts:
        ac_chunks.append([])
    while len(file_chunks) < num_parts:
        file_chunks.append([])

    original_id = story["id"]
    original_key = story["story_key"]
    original_title = story["title"]
    original_depends = story.get("depends_on", [])

    parts = []
    for i in range(num_parts):
        part_num = i + 1
        if i == 0:
            part_id = original_id
            part_key = original_key
            part_depends = list(original_depends)
        else:
            suffix = _SUFFIX_LETTERS[i - 1] if i - 1 < len(_SUFFIX_LETTERS) else str(i + 1)
            part_id = f"{original_id}{suffix}"
            part_key = f"{original_key}-part-{part_num}"
            # Chain: each subsequent part depends on the previous part's key
            prev_key = original_key if i == 1 else f"{original_key}-part-{i}"
            part_depends = [prev_key]

        part = {
            "id": part_id,
            "title": f"{original_title} (part {part_num} of {num_parts})",
            "story_key": part_key,
            "description": story.get("description", ""),
            "acceptance_criteria": ac_chunks[i],
            "scope_boundaries": list(story.get("scope_boundaries", [])),
            "expected_files": file_chunks[i],
            "depends_on": part_depends,
            "validation": dict(story.get("validation", {})),
        }
        parts.append(part)

    return parts


def refine_stories(spec):

    stories = spec.get("stories", [])
    features = spec.get("features", [])

    ids = [s["id"] for s in stories]

    if "ST-900" not in ids:
        stories.append(_build_monitoring_story(spec))

    if "ST-901" not in ids:
        stories.append(_build_backups_story(spec))

    if "ST-902" not in ids:
        if "authentication" in features:
            stories.append(_build_rate_limiting_story(spec))

    if "ST-903" not in ids:
        if "authentication" in features:
            stories.append(_build_password_policy_story(spec))

    spec["stories"] = stories

    return spec


def refine_spec(spec):

    spec = refine_prd(spec)
    spec = refine_stories(spec)
    spec = _split_complex_stories(spec)

    for story in spec.get("stories", []):
        if isinstance(story, dict):
            story["execution"] = derive_execution_metadata(story)

    return spec
