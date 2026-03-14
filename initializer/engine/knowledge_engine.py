"""
Knowledge Engine

Adds domain knowledge and architectural best practices
based on detected stack, features and archetype.

Key change: SSR/ISR and CDN decisions are only added when
public-site is in the reconciled capabilities list.  For
internal-only apps using Next.js, these are not relevant.
"""


def _has_public_site(spec):
    """Check if public-site is in the reconciled capabilities list."""
    capabilities = spec.get("capabilities", [])
    return "public-site" in capabilities


def apply_knowledge(spec):

    architecture = spec.get("architecture", {})

    decisions = architecture.get("decisions", [])

    stack = spec.get("stack", {})
    features = spec.get("features", [])

    frontend = stack.get("frontend")
    backend = stack.get("backend")
    database = stack.get("database")

    has_public = _has_public_site(spec)

    # Frontend knowledge
    if frontend == "nextjs":

        # SSR/ISR and CDN are only relevant for public-facing sites.
        # Internal apps using Next.js don't need SEO or public CDN.
        if has_public:
            if "Use SSR or ISR for SEO-sensitive pages." not in decisions:
                decisions.append(
                    "Use SSR or ISR for SEO-sensitive pages."
                )

            if "Serve static assets through CDN." not in decisions:
                decisions.append(
                    "Serve static assets through CDN."
                )

    # Backend knowledge
    if backend in ["node-api", "payload"]:

        if "Implement structured logging." not in decisions:
            decisions.append(
                "Implement structured logging."
            )

        if "Add health check endpoints." not in decisions:
            decisions.append(
                "Add health check endpoints."
            )

    # Database knowledge
    if database == "postgres":

        if "Use connection pooling." not in decisions:
            decisions.append(
                "Use connection pooling."
            )

        if "Add automated database backups." not in decisions:
            decisions.append(
                "Add automated database backups."
            )

    # Feature-specific knowledge

    if "scheduled-publishing" in features:

        if "Introduce background worker for scheduled tasks." not in decisions:
            decisions.append(
                "Introduce background worker for scheduled tasks."
            )

    if "media-library" in features:

        if "Store media in S3-compatible object storage." not in decisions:
            decisions.append(
                "Store media in S3-compatible object storage."
            )

    architecture["decisions"] = decisions

    spec["architecture"] = architecture

    return spec