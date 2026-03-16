# decisions.md

## Purpose

This file records stable project decisions for this generated project.

Use it to reduce drift during agent execution.

---

## Status labels

- `accepted`
- `superseded`
- `provisional`

---

## Decisions

### DEC-001
- **Date:** generated
- **Status:** accepted
- **Decision:** `spec.json` is the primary structured source of truth for this generated project.
- **Reason:** This project folder was generated from the initializer and should be implemented from the generated spec.
- **Consequences:** Execution agents should consult `spec.json` before changing architecture or scope.

### DEC-002
- **Date:** generated
- **Status:** accepted
- **Decision:** `docs/stories/` defines the preferred unit of implementation work.
- **Reason:** Story-by-story execution reduces drift and improves validation.
- **Consequences:** Agents should implement one story at a time and record progress after each meaningful iteration.

### DEC-003
- **Date:** generated
- **Status:** accepted
- **Decision:** Generated architecture should remain stable unless a story explicitly changes it.
- **Reason:** The initializer already derived the architecture from the project spec.
- **Consequences:** Agents should not silently redesign the system during routine implementation work.

### DEC-004
- **Date:** generated
- **Status:** accepted
- **Decision:** Use surface `admin_plus_public_site` with deploy target `docker`.
- **Reason:** These values are explicit project inputs.
- **Consequences:** Implementation should respect product shape and deployment assumptions derived from them.

### DEC-005
- **Date:** generated
- **Status:** accepted
- **Decision:** Use stack frontend=`nextjs`, backend=`payload`, database=`postgres`.
- **Reason:** Stack was derived as part of the generated project contract.
- **Consequences:** Code generation and implementation decisions should remain aligned with this stack.

### DEC-006
- **Date:** generated
- **Status:** accepted
- **Decision:** Capabilities for this generated project are `cms, public-site, i18n, scheduled-jobs`.
- **Reason:** Capabilities shape downstream behavior and implementation scope.
- **Consequences:** Agents should not add behaviors that conflict with the generated capability set.


### DEC-007
- **Date:** generated
- **Status:** accepted
- **Decision:** CMS content stored in structured collections.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-008
- **Date:** generated
- **Status:** accepted
- **Decision:** Media assets served via CDN.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-009
- **Date:** generated
- **Status:** accepted
- **Decision:** Public assets should be delivered through a CDN.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-010
- **Date:** generated
- **Status:** accepted
- **Decision:** Use SSR or ISR for SEO-sensitive public pages when applicable.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-011
- **Date:** generated
- **Status:** accepted
- **Decision:** Content models must support locale-aware fields and fallback rules.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-012
- **Date:** generated
- **Status:** accepted
- **Decision:** Scheduled publishing requires a background worker.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-013
- **Date:** generated
- **Status:** accepted
- **Decision:** [cache-invalidation] On-demand ISR revalidation: Trigger Next.js revalidation via webhook after each publish event. Pages update within seconds. Requires a revalidation API route.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-014
- **Date:** generated
- **Status:** accepted
- **Decision:** [preview-vs-production] Payload draft mode + Next.js preview: Use Payload's built-in draft mode with Next.js preview cookies. Editors see drafts in-context; public visitors see only published content.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-015
- **Date:** generated
- **Status:** accepted
- **Decision:** [seo-vs-auth-routes] Route groups with middleware: Use Next.js route groups: (public) for SEO pages, (app) for admin, (payload) for CMS. Middleware enforces auth only on non-public groups.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-016
- **Date:** generated
- **Status:** accepted
- **Decision:** [media-storage-strategy] local filesystem
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-017
- **Date:** generated
- **Status:** accepted
- **Decision:** [content-versioning] No versioning for MVP: Skip versioning initially. Editors edit content directly. Simpler but no rollback capability.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-018
- **Date:** generated
- **Status:** accepted
- **Decision:** [i18n-strategy] Full i18n (content + UI + routing): Content, UI labels, and URL structure are all locale-aware. Complete solution but more work upfront.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-019
- **Date:** generated
- **Status:** accepted
- **Decision:** [job-infrastructure] Separate worker process: Dedicated worker process with its own lifecycle. More reliable. Can scale independently. Needs docker-compose entry.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-020
- **Date:** generated
- **Status:** accepted
- **Decision:** [auth-strategy] Email + password (built-in): Classic email/password auth. Use the framework's built-in auth if available (e.g., Payload auth). Simple, no external dependencies.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-021
- **Date:** generated
- **Status:** accepted
- **Decision:** Use SSR or ISR for SEO-sensitive pages.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-022
- **Date:** generated
- **Status:** accepted
- **Decision:** Serve static assets through CDN.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-023
- **Date:** generated
- **Status:** accepted
- **Decision:** Implement structured logging.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-024
- **Date:** generated
- **Status:** accepted
- **Decision:** Add health check endpoints.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-025
- **Date:** generated
- **Status:** accepted
- **Decision:** Use connection pooling.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-026
- **Date:** generated
- **Status:** accepted
- **Decision:** Add automated database backups.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-027
- **Date:** generated
- **Status:** accepted
- **Decision:** Introduce background worker for scheduled tasks.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-028
- **Date:** generated
- **Status:** accepted
- **Decision:** Store media in S3-compatible object storage.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-029
- **Date:** generated
- **Status:** accepted
- **Decision:** Media assets stored in object storage.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-030
- **Date:** generated
- **Status:** accepted
- **Decision:** Background worker processes scheduled jobs.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-031
- **Date:** generated
- **Status:** accepted
- **Decision:** Authentication handled via secure session or JWT.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-032
- **Date:** generated
- **Status:** accepted
- **Decision:** Authorization must enforce role and permission boundaries.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-033
- **Date:** generated
- **Status:** accepted
- **Decision:** Public-facing pages should use caching and delivery strategies appropriate for anonymous traffic.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-034
- **Date:** generated
- **Status:** accepted
- **Decision:** SEO-sensitive public pages should use rendering strategies such as SSR or ISR when beneficial.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-035
- **Date:** generated
- **Status:** accepted
- **Decision:** Automation workflows require a background worker and durable job execution strategy.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-036
- **Date:** generated
- **Status:** accepted
- **Decision:** Introduce caching for frequently accessed public content.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-037
- **Date:** generated
- **Status:** accepted
- **Decision:** CDN recommended for public assets.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.


### DEC-038
- **Date:** generated
- **Status:** accepted
- **Decision:** Add monitoring and logging stack.
- **Reason:** This decision was derived in the generated architecture.
- **Consequences:** Implementation should respect this architectural constraint.
