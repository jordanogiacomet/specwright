# Editorial E2E Test

## Problem Statement

Editorial validation run

## Summary

Editorial validation run

## Personas

- **Admin**: Can manage_users, manage_config, publish
- **Editor**: Can create_article, edit_own_article, submit_for_review
- **Reviewer**: Can approve_article, reject_article, edit_any_article

## Scope

### In Scope

- User registration, login, logout, and session management
- Role-based access control with permission enforcement
- Media upload, storage, and management
- Content draft and publish workflow
- Content preview for unpublished items
- Scheduled content publishing via background jobs

### Out of Scope

- Multi-language / internationalization
- Background jobs or scheduled tasks

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

## Stories

- **ST-001**: Define CMS content model
- **ST-002**: Configure static asset delivery
- **ST-003**: Initialize project repository (part 1 of 2)
- **ST-003b**: Initialize project repository (part 2 of 2)
- **ST-004**: Setup database
- **ST-005**: Setup backend service
- **ST-006**: Create frontend application
- **ST-007**: Implement authentication
- **ST-008**: Implement role-based access control
- **ST-009**: Implement media library
- **ST-010**: Implement draft and publish workflow
- **ST-011**: Implement content preview
- **ST-012**: Implement scheduled publishing (part 1 of 2)
- **ST-012b**: Implement scheduled publishing (part 2 of 2)
- **ST-013**: Implement public site pages
- **ST-900**: Setup monitoring and logging
- **ST-901**: Implement backups
- **ST-902**: Add rate limiting to auth endpoints
- **ST-903**: Enforce password policy

Total: 19 stories. See `docs/stories/` for full details.
