# Architecture

**Style:** service-oriented

## Components

### cdn
- **Technology:** cdn
- **Role:** public asset delivery

### worker
- **Technology:** node-api
- **Role:** process scheduled jobs

### frontend
- **Technology:** nextjs
- **Role:** user interface

### api
- **Technology:** node-api
- **Role:** application logic

### database
- **Technology:** postgres
- **Role:** persistent storage

## Communication

### frontend → api
- **Protocol:** http
- **Pattern:** REST API
- **Auth:** JWT bearer token or session cookie

### api → database
- **Protocol:** tcp
- **Pattern:** ORM or query builder over postgres connection pool

### worker → database
- **Protocol:** tcp
- **Pattern:** Direct postgres connection for job execution

### worker → api
- **Protocol:** http
- **Pattern:** Internal HTTP call for notification delivery or webhook triggers

### cdn → frontend
- **Protocol:** http
- **Pattern:** Edge cache proxying static assets and SSR/ISR responses

## Responsibility Boundaries

### Frontend
- Rendering pages and UI components
- Client-side routing and navigation
- Form validation (client-side)
- Client-side state management
- Public page rendering (SSR/ISR) for SEO
- CDN-compatible caching headers
- Locale-aware rendering and text formatting

### Backend
- Business logic and domain rules
- Authentication and session management
- Authorization and permission enforcement
- Data persistence and queries
- Input validation (server-side, authoritative)
- Background job scheduling and execution
- Locale-aware data storage and API responses

### Shared
- Shared types or API contract between frontend and backend

## Typical Request Flow

### Authenticated action (e.g., create or update a record)

1. User interacts with the frontend (nextjs)
2. Frontend sends HTTP request to the API (node-api) with auth token/session
3. API middleware validates authentication and authorization
4. API executes business logic and validates input
5. API persists data to postgres via ORM/query layer
6. API returns response to frontend
7. Frontend updates UI based on response

### Background job execution

1. Scheduler triggers job at configured interval
2. Worker queries postgres for pending work
3. Worker processes each item (publish, notify, remind, etc.)
4. Worker updates postgres with results
5. Worker logs outcome for observability

## Architectural Decisions

- Public assets should be delivered through a CDN.
- Use SSR or ISR for SEO-sensitive public pages when applicable.
- CMS content stored in structured collections.
- Media assets served via CDN.
- Scheduled publishing requires a background worker.
- Content models must support locale-aware fields and fallback rules.
- [todo-data-model] Standard: title, description, completed, dueDate, priority, createdAt.
- [todo-filtering] Basic: Filter by completed/pending + sort by date or priority.
- [todo-auth-scope] Email + password only: Register, login, logout. No password reset, no OAuth.
- [i18n-strategy] Full i18n (content + UI + routing): Content, UI labels, and URL structure are all locale-aware. Complete solution but more work upfront.
- [job-infrastructure] Separate worker process: Dedicated worker process with its own lifecycle. More reliable. Can scale independently. Needs docker-compose entry.
- [auth-strategy] Email + password (built-in): Classic email/password auth. Use the framework's built-in auth if available (e.g., Payload auth). Simple, no external dependencies.
- Use SSR or ISR for SEO-sensitive pages.
- Serve static assets through CDN.
- Implement structured logging.
- Add health check endpoints.
- Use connection pooling.
- Add automated database backups.
- Background worker processes scheduled jobs.
- Authentication handled via secure session or JWT.
- Public-facing pages should use caching and delivery strategies appropriate for anonymous traffic.
- SEO-sensitive public pages should use rendering strategies such as SSR or ISR when beneficial.
- Automation workflows require a background worker and durable job execution strategy.
- Work items should support due dates, deadline validation, and overdue detection.
- Work items should support explicit status progression and progress visibility.
- Ownership and assignment must be modeled for teams and individual users.
- Reminder workflows should be driven by scheduled jobs and configurable trigger rules.
- Operational reporting should be generated from durable domain data and background jobs when needed.
- Introduce caching for frequently accessed public content.
- CDN recommended for public assets.
- Add monitoring and logging stack.
