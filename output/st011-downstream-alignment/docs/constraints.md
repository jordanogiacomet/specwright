# System Constraints

## Performance

- Public pages should render in under 500ms under normal load.
- API responses should target <200ms median latency.
- Public assets must be cacheable via CDN.

## Scalability

- System should support horizontal scaling of application servers.
- Database must support concurrent editorial users.

## Security

- All authentication flows must enforce secure password hashing.
- All external APIs must require authentication or signed requests.
- Editorial roles must enforce permission boundaries.

## Operational

- Application must support environment-based configuration.
- Structured logging should be used for all backend services.
- Application must run in containerized environments.