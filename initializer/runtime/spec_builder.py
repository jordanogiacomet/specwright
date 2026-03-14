from initializer.engine.archetype_engine import canonical_archetype_id
from initializer.engine.capability_derivation import derive_capabilities


def build_semantic_spec(raw_prompt, archetype, playbook, answers):
    canonical_archetype = canonical_archetype_id(archetype)

    spec = {
        "prompt": raw_prompt,
        "archetype": canonical_archetype,
        "stack": playbook.get("default_stack", {}),
        "features": playbook.get("common_features", []),
        "answers": answers,
        "architecture": {},
        "stories": [],
        "capabilities": derive_capabilities(
            archetype=canonical_archetype,
            answers=answers,
            existing_capabilities=playbook.get("capabilities", []),
        ),
    }

    return spec
