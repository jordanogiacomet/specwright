"""
Capability Engine

Applies capability handlers that modify architecture and stories.
"""

from initializer.engine.capability_derivation import normalize_capabilities
from initializer.engine.capability_registry import CAPABILITY_REGISTRY


def apply_capabilities(spec):
    architecture = dict(spec.get("architecture") or {})
    stories = list(spec.get("stories") or [])

    if "decisions" not in architecture:
        architecture["decisions"] = []

    if "components" not in architecture:
        architecture["components"] = []

    capabilities = normalize_capabilities(spec.get("capabilities", []))
    spec["capabilities"] = capabilities

    for capability in capabilities:
        handler = CAPABILITY_REGISTRY.get(capability)

        if handler:
            architecture, stories = handler(architecture, stories)

    spec["architecture"] = architecture
    spec["stories"] = stories

    return spec
