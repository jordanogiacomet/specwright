"""CMS capability handler."""

from initializer.engine.validation_contract import migration_commands


def _story_exists(stories, story_key, title):
    for story in stories:
        if story.get("story_key") == story_key or story.get("title") == title:
            return True
    return False


def _add_unique_decision(architecture, decision):
    decisions = architecture.setdefault("decisions", [])
    if decision not in decisions:
        decisions.append(decision)


def _guided_answers(spec):
    answers = spec.get("answers", {})
    ga = answers.get("guided_answers", {})
    return ga if isinstance(ga, dict) else {}


def _get_content_model(spec):
    return _guided_answers(spec).get("content_model", {})


def _get_storage_backend(spec):
    storage = _guided_answers(spec).get("storage_requirements", {})
    if not isinstance(storage, dict):
        return ""
    backend = storage.get("upload_backend", "")
    return backend.lower().strip() if isinstance(backend, str) else ""


def _is_enabled(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    return bool(value)


def _supports_public_route(name):
    return name not in {"authors", "media", "users", "categories", "tags"}


def _pascal_case(value):
    return "".join(part.capitalize() for part in value.replace("_", "-").split("-") if part)


def _format_fields(fields):
    return ", ".join(f"`{field}`" for field in fields if field)


def _collection_fields(name, has_media):
    mapping = {
        "pages": ["title", "slug", "hero", "body_or_blocks", "seo_title", "seo_description"],
        "posts": ["title", "slug", "excerpt", "body", "author", "featured_image", "published_at"],
        "authors": ["name", "slug", "bio", "avatar"],
        "media": ["alt_text", "caption", "file", "mime_type", "size"],
    }
    fields = list(mapping.get(name, ["title", "slug", "summary", "body"]))

    if name == "posts" and not has_media:
        fields = [field for field in fields if field != "featured_image"]
    if name == "authors" and not has_media:
        fields = [field for field in fields if field != "avatar"]
    return fields


def _global_fields(name):
    mapping = {
        "site-settings": ["site_name", "navigation", "footer", "default_seo"],
        "homepage": ["hero", "featured_posts", "featured_pages", "seo"],
    }
    return mapping.get(name, ["title", "content"])


def _collection_relationship_notes(name, collection_names):
    if name == "posts":
        notes = []
        if "authors" in collection_names:
            notes.append("`author` relation to `authors`")
        if "media" in collection_names:
            notes.append("optional `featured_image` relation to `media`")
        if notes:
            return f"`posts` includes {', '.join(notes)}."

    if name == "authors" and "media" in collection_names:
        return "`authors` can reference `media` for avatar/headshot assets."

    if name == "pages" and "media" in collection_names:
        return "`pages` can reference `media` for hero or inline assets."

    return None


def _collection_criteria(spec, collections, is_payload):
    features = spec.get("features", [])
    capabilities = spec.get("capabilities", [])
    collection_names = {
        col.get("name", "").strip().lower()
        for col in collections
        if isinstance(col, dict)
    }
    has_media = "media" in collection_names
    criteria = []

    for col in collections:
        if not isinstance(col, dict):
            continue

        name = col.get("name", "").strip().lower()
        if not name:
            continue

        purpose = col.get("purpose", "").strip()
        fields = _collection_fields(name, has_media)
        noun = "Payload collection" if is_payload else "Collection schema"
        criteria.append(
            f"{noun} `{name}` exists with fields { _format_fields(fields) }"
            f"{' — ' + purpose if purpose else ''}"
        )

        if _supports_public_route(name) and "public-site" in capabilities:
            criteria.append(
                f"`{name}` includes a unique `slug` used by the later public route `/{name}/[slug]` and preview lookup."
            )

        relation_note = _collection_relationship_notes(name, collection_names)
        if relation_note:
            criteria.append(relation_note)

        if "draft-publish" in features and _supports_public_route(name):
            criteria.append(
                f"`{name}` is modeled so the later draft/publish story can add editorial status handling without redefining the schema."
            )

    return criteria


def _global_criteria(globals_list, is_payload):
    criteria = []
    noun = "Payload global" if is_payload else "Global config"
    for item in globals_list:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "").strip().lower()
        if not name:
            continue
        purpose = item.get("purpose", "").strip()
        criteria.append(
            f"{noun} `{name}` exists with fields { _format_fields(_global_fields(name)) }"
            f"{' — ' + purpose if purpose else ''}"
        )
    return criteria


def apply_cms(spec, architecture, stories):
    _add_unique_decision(
        architecture,
        "CMS content is modeled in explicit collections/globals with stable slugs and typed relationships.",
    )

    storage_backend = _get_storage_backend(spec)
    if storage_backend in {"s3", "s3_compatible", "object_storage"}:
        _add_unique_decision(
            architecture,
            "Media storage uses an S3-compatible object storage boundary.",
        )
    else:
        _add_unique_decision(
            architecture,
            "Media storage starts on local filesystem with a clear adapter boundary for a later object-storage swap.",
        )

    if _story_exists(stories, "product.cms-content-model", "Define CMS content model"):
        return architecture, stories

    stack = spec.get("stack", {})
    backend = (stack.get("backend") or "").lower().strip()
    is_payload = backend in ("payload", "payload-cms")
    migration_cmds = migration_commands(spec)

    content_model = _get_content_model(spec)
    collections = content_model.get("collections", [])
    globals_list = content_model.get("globals", [])
    media_items = content_model.get("media", [])

    if not isinstance(collections, list):
        collections = []
    if not isinstance(globals_list, list):
        globals_list = []
    if not isinstance(media_items, list):
        media_items = []

    acceptance_criteria = []

    if collections:
        acceptance_criteria.extend(_collection_criteria(spec, collections, is_payload))
    else:
        acceptance_criteria.append(
            "The CMS schema explicitly defines at least one primary content collection with slug-based lookup and one supporting media collection."
        )

    if globals_list:
        acceptance_criteria.extend(_global_criteria(globals_list, is_payload))

    if media_items:
        media_kinds = [
            item.get("kind", "").strip().lower()
            for item in media_items
            if isinstance(item, dict) and item.get("kind")
        ]
        if media_kinds:
            acceptance_criteria.append(
                f"Media requirements are explicit: support {', '.join(media_kinds)} uploads in the `media` collection."
            )

    acceptance_criteria.append(
        "Only the collections/globals listed in this story are created; no extra editorial schema is invented outside the spec."
    )
    acceptance_criteria.append(
        "Content editors can create and edit entries for each modeled collection/global through the admin surface."
    )
    acceptance_criteria.append(
        "Database migration is generated and executed for all schema changes "
        f"(run `{migration_cmds['create']}` then `{migration_cmds['run']}`)"
    )

    expected_files = []

    if is_payload:
        acceptance_criteria.append(
            "All collections and globals are registered in `src/payload.config.ts` using dedicated definition files."
        )
        expected_files.append("src/payload.config.ts (updated with collections and globals)")
        for col in collections:
            name = col.get("name", "") if isinstance(col, dict) else ""
            expected_files.append(f"src/collections/{_pascal_case(name or 'articles')}.ts")
        for item in globals_list:
            name = item.get("name", "") if isinstance(item, dict) else ""
            expected_files.append(f"src/globals/{_pascal_case(name or 'site-settings')}.ts")
        if not collections:
            expected_files.append("src/collections/Posts.ts or equivalent")
        if not globals_list:
            expected_files.append("src/globals/SiteSettings.ts or equivalent")
    else:
        acceptance_criteria.append(
            "The backend exposes content schema/models that match the collections/globals listed in this story."
        )
        expected_files.append("src/api/content.ts or equivalent")
        for col in collections:
            name = col.get("name", "") if isinstance(col, dict) else ""
            expected_files.append(f"src/models/{_pascal_case(name or 'article')}.ts")
        if not collections:
            expected_files.append("src/models/Post.ts or equivalent")

    col_names = [c.get("name", "") for c in collections if isinstance(c, dict) and c.get("name")]
    glob_names = [g.get("name", "") for g in globals_list if isinstance(g, dict) and g.get("name")]
    parts = []
    if col_names:
        parts.append(f"collections: {', '.join(col_names)}")
    if glob_names:
        parts.append(f"globals: {', '.join(glob_names)}")
    description = (
        f"Define CMS content model — {'; '.join(parts)}."
        if parts
        else "Define the CMS content schema, globals, and editorial relationships."
    )

    stories.append(
        {
            "id": f"ST-{len(stories)+1:03}",
            "story_key": "product.cms-content-model",
            "title": "Define CMS content model",
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "scope_boundaries": [
                "Do NOT implement draft/publish transitions, preview mode, or scheduled publishing in this story.",
                "Do NOT build media library UI or public page routes here — only define the schema and registration points.",
                "Do NOT add collections/globals beyond the ones named in this story unless `spec.json` is updated first.",
            ],
            "expected_files": expected_files,
            "depends_on": ["bootstrap.backend"],
            "validation": {
                "commands": ["npm run build"],
                "manual_check": "Admin can create sample page/post entries, assign author/media relations, and edit globals without missing fields.",
            },
        }
    )

    return architecture, stories
