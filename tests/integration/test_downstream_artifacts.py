from initializer.flow.new_project import derive_downstream_artifacts


def test_derive_downstream_artifacts_populates_all_expected_sections():
    spec = {
        "prompt": "Editorial CMS with admin panel and public website",
        "archetype": "editorial-cms",
        "archetype_data": {
            "id": "editorial-cms",
            "name": "editorial-cms",
            "stack": {
                "frontend": "nextjs",
                "backend": "payload",
                "database": "postgres",
            },
            "features": [
                "authentication",
                "roles",
                "media-library",
                "preview",
                "scheduled-publishing",
            ],
            "capabilities": ["cms"],
        },
        "stack": {
            "frontend": "nextjs",
            "backend": "payload",
            "database": "postgres",
        },
        "features": [
            "authentication",
            "roles",
            "media-library",
            "preview",
            "scheduled-publishing",
        ],
        "capabilities": ["cms", "public-site"],
        "architecture": {
            "components": [
                {"name": "cdn", "technology": "edge-cache", "role": "static delivery"},
                {"name": "frontend", "technology": "nextjs", "role": "web ui"},
                {"name": "api", "technology": "payload", "role": "application backend"},
                {"name": "database", "technology": "postgres", "role": "data storage"},
                {
                    "name": "object-storage",
                    "technology": "s3",
                    "role": "media storage",
                },
                {"name": "worker", "technology": "payload", "role": "background jobs"},
            ],
            "decisions": [
                "Authentication handled via secure session or JWT.",
                "Media assets stored in object storage.",
                "Background worker processes scheduled jobs.",
            ],
        },
        "stories": [
            {
                "id": "ST-001",
                "title": "Implement CMS content management",
                "description": "Implement cms content management workflows.",
            },
            {
                "id": "ST-002",
                "title": "Implement public website",
                "description": "Implement public-site content delivery flows.",
            },
        ],
        "answers": {
            "project_name": "Downstream Test",
            "project_slug": "downstream-test",
            "summary": "Downstream artifact integration test",
            "surface": "admin_plus_public_site",
            "deploy_target": "docker",
        },
    }

    result = derive_downstream_artifacts(spec)

    assert "constraints" in result
    assert "design_system" in result
    assert "risks" in result
    assert "diagram" in result

    assert result["constraints"]
    assert result["design_system"]
    assert result["risks"]
    assert result["diagram"]

    assert "nodes" in result["diagram"]
    assert "edges" in result["diagram"]
    assert ("frontend", "api") in result["diagram"]["edges"]
    assert ("api", "database") in result["diagram"]["edges"]
    assert ("api", "object_storage") in result["diagram"]["edges"]
    assert ("worker", "database") in result["diagram"]["edges"]
    assert ("cdn", "frontend") in result["diagram"]["edges"]