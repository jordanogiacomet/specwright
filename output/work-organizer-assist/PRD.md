
# work organizer

## Summary

Internal work organization tool, focused on deadlines, progress-tracking, with multilingual support and scheduled automation.

## Stack

Frontend: nextjs
Backend: node-api
Database: postgres

## Features
- authentication
- api

## Architecture Decisions
- Public assets should be delivered through a CDN.
- Use SSR or ISR for SEO-sensitive public pages when applicable.
- Application UI and APIs must support locale-aware text, formatting, and translation resources.
- Automation workflows require a background worker and durable job execution strategy.
- Use SSR or ISR for SEO-sensitive pages.
- Serve static assets through CDN.
- Implement structured logging.
- Add health check endpoints.
- Use connection pooling.
- Add automated database backups.
- Authentication is handled through secure sessions or JWT-based flows.
- Public-facing pages should use caching and delivery strategies appropriate for anonymous traffic.
- SEO-sensitive public pages should use rendering strategies such as SSR or ISR when beneficial.
- Work items should support due dates, deadline validation, and overdue detection.
- Work items should support explicit status progression and progress visibility.
- Introduce caching for frequently accessed public content.
- CDN recommended for public assets.
- Add monitoring and logging stack.
