
# cms site baseline

## Summary

cms site for my clients

## Stack

Frontend: nextjs
Backend: payload
Database: postgres

## Features
- authentication
- roles
- media-library
- draft-publish
- preview
- scheduled-publishing

## Architecture Decisions
- CMS content stored in structured collections.
- Media assets served via CDN.
- Public assets should be delivered through a CDN
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
- Introduce caching layer for frequently accessed content.
- CDN recommended for public assets.
- Add monitoring and logging stack.
