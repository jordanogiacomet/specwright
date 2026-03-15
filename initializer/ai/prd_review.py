"""
PRD Review Agent

Reviews a PRD document and provides suggestions.
"""

from initializer.ai.client import AIClient, AIClientConfig


def review_prd(prd_text, *, client=None):
    """Review a PRD and return suggestions.

    Uses the AI client when available, falls back to a stub otherwise.
    """

    prompt = f"""
Review this product requirements document.

Identify:

- missing requirements
- scalability concerns
- unclear specifications
- architectural risks

PRD:

{prd_text}
"""

    if client is None:
        try:
            client = AIClient(AIClientConfig())
        except RuntimeError:
            # No API key — return stub response
            return _stub_review(prd_text)

    return client.generate_text(
        instructions="You are a senior product manager reviewing a PRD. Be concise and actionable.",
        input_text=prompt,
    )


def _stub_review(prd_text):
    """Fallback when no AI client is available."""
    suggestions = [
        "Consider adding explicit success metrics.",
        "Clarify the scope boundaries between MVP and future phases.",
        "Ensure all architectural decisions have documented rationale.",
    ]
    return "\n".join(f"- {s}" for s in suggestions)