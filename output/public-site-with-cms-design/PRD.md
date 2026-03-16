# public site with cms design

## Problem Statement

Organizations often need to manage structured editorial content and publish it across digital surfaces without tightly coupling content management to frontend presentation.

## Summary

A public-facing content platform with an integrated CMS supporting content creation, editing, versioning, user management, publishing workflows, multi-language support, and scheduled/background jobs.

## Personas

- **Content Editor**: Create and publish editorial content quickly.
- **Administrator**: Manage users, roles, and system configuration.
- **Site Visitor**: Consume published content through the public website.

## Success Metrics

- Content publishing time reduced compared to manual workflows.
- Editorial users can publish content without developer intervention.
- System availability above 99.5%.
- Public pages load under acceptable performance thresholds.

## Scope

### In Scope

- Core content management workflows.
- Authentication and role-based access control.
- Public content delivery via frontend.
- Background job processing and automation.
- Multi-language support.

### Out of Scope

- Advanced marketing automation.
- Complex analytics dashboards not defined in the initial spec.
- External integrations not required for core workflow.

## Assumptions

- Both internal teams and external clients will use the system with appropriate access controls.
- Initial traffic will be moderate.
- System will evolve after MVP validation.
- Background job infrastructure will be available in the deployment environment.

## Stack

- Frontend: nextjs
- Backend: payload
- Database: postgres

## Features

- authentication
- roles
- media-library
- draft-publish
- preview
- scheduled-publishing

## Capabilities

- cms
- public-site
- i18n
- scheduled-jobs

## Architecture Decisions

- CMS content stored in structured collections.
- Media assets served via CDN.
- Public assets should be delivered through a CDN.
- Use SSR or ISR for SEO-sensitive public pages when applicable.
- Content models must support locale-aware fields and fallback rules.
- Scheduled publishing requires a background worker.
- [cache-invalidation] On-demand ISR revalidation: Trigger Next.js revalidation via webhook after each publish event. Pages update within seconds. Requires a revalidation API route.
- [preview-vs-production] Payload draft mode + Next.js preview: Use Payload's built-in draft mode with Next.js preview cookies. Editors see drafts in-context; public visitors see only published content.
- [seo-vs-auth-routes] Route groups with middleware: Use Next.js route groups: (public) for SEO pages, (app) for admin, (payload) for CMS. Middleware enforces auth only on non-public groups.
- [media-storage-strategy] local filesystem
- [content-versioning] No versioning for MVP: Skip versioning initially. Editors edit content directly. Simpler but no rollback capability.
- [i18n-strategy] Full i18n (content + UI + routing): Content, UI labels, and URL structure are all locale-aware. Complete solution but more work upfront.
- [job-infrastructure] Separate worker process: Dedicated worker process with its own lifecycle. More reliable. Can scale independently. Needs docker-compose entry.
- [auth-strategy] Email + password (built-in): Classic email/password auth. Use the framework's built-in auth if available (e.g., Payload auth). Simple, no external dependencies.
- Use SSR or ISR for SEO-sensitive pages.
- Serve static assets through CDN.
- Implement structured logging.
- Add health check endpoints.
- Use connection pooling.
- Add automated database backups.
- Introduce background worker for scheduled tasks.
- Store media in S3-compatible object storage.
- Media assets stored in object storage.
- Background worker processes scheduled jobs.
- Authentication handled via secure session or JWT.
- Authorization must enforce role and permission boundaries.
- Public-facing pages should use caching and delivery strategies appropriate for anonymous traffic.
- SEO-sensitive public pages should use rendering strategies such as SSR or ISR when beneficial.
- Automation workflows require a background worker and durable job execution strategy.
- Introduce caching for frequently accessed public content.
- CDN recommended for public assets.
- Add monitoring and logging stack.

## Stories

- **ST-001**: Define CMS content model
- **ST-002**: Configure CDN
- **ST-003**: Add locale support
- **ST-004**: Implement locale routing
- **ST-005**: Setup job worker
- **ST-006**: Implement publishing scheduler
- **ST-007**: Initialize project repository (bootstrap)
- **ST-008**: Setup database (bootstrap)
- **ST-009**: Setup backend service (bootstrap)
- **ST-010**: Create frontend application (bootstrap)
- **ST-011**: Implement authentication (feature)
- **ST-012**: Implement role-based access control (feature)
- **ST-013**: Implement media library (feature)
- **ST-014**: Implement draft and publish workflow (feature)
- **ST-015**: Implement content preview (feature)
- **ST-016**: Implement scheduled publishing (feature)
- **ST-017**: Build content platform shell (product)
- **ST-900**: Setup monitoring and logging
- **ST-901**: Implement backups

## Discovery Signals

- **needs_public_site**: True
- **needs_cms**: True
- **app_shape**: content-platform
- **core_work_features**: ['content-creation', 'editing', 'versioning', 'user-management']
- **needs_i18n**: True
- **primary_audience**: mixed
- **needs_scheduled_jobs**: True

