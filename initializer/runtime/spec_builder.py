def build_semantic_spec(raw_prompt, archetype, playbook, answers):

    spec = {
        "prompt": raw_prompt,
        "archetype": archetype,
        "stack": playbook.get("default_stack", {}),
        "features": playbook.get("common_features", []),
        "answers": answers,
        "architecture": {},
        "stories": [],
        "capabilities": [],
    }

    return spec