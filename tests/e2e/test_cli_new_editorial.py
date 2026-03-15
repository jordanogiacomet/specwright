import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_cli_new_generates_editorial_output():
    slug = "editorial-e2e-test"
    out_dir = Path("output") / slug

    if out_dir.exists():
        shutil.rmtree(out_dir)

    user_input = "\n".join(
        [
            "Editorial CMS with admin panel, public website, media library, preview, and scheduled publishing for articles",
            "Editorial E2E Test",
            slug,
            "Editorial validation run",
            "",  # default surface => admin_plus_public_site
            "",  # default deploy => docker
        ]
    ) + "\n"

    result = subprocess.run(
        [sys.executable, "-m", "initializer", "new"],
        input=user_input,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Project generated successfully." in result.stdout

    assert out_dir.exists()
    assert (out_dir / "spec.json").exists()
    assert (out_dir / "PRD.md").exists()
    assert (out_dir / "architecture.md").exists()
    assert (out_dir / "decisions.md").exists()
    assert (out_dir / "progress.txt").exists()
    assert (out_dir / "docs" / "stories").exists()
    assert (out_dir / "docs" / "constraints.md").exists()
    assert (out_dir / "docs" / "design-system.md").exists()
    assert (out_dir / "docs" / "risks.md").exists()
    assert (out_dir / "docs" / "architecture" / "diagram.mmd").exists()
    assert (out_dir / ".openclaw" / "AGENTS.md").exists()
    assert (out_dir / ".openclaw" / "manifest.json").exists()
    assert (out_dir / ".openclaw" / "execution-plan.json").exists()
    assert (out_dir / ".codex" / "AGENTS.md").exists()
    assert (out_dir / "ralph.sh").exists()

    spec = json.loads((out_dir / "spec.json").read_text())

    assert spec["archetype"] == "editorial-cms"
    assert spec["archetype_data"]["id"] == "editorial-cms"

    assert spec["answers"]["project_name"] == "Editorial E2E Test"
    assert spec["answers"]["project_slug"] == slug
    assert spec["answers"]["summary"] == "Editorial validation run"
    assert spec["answers"]["surface"] == "admin_plus_public_site"
    assert spec["answers"]["deploy_target"] == "docker"

    assert "cms" in spec["capabilities"]
    assert "public-site" in spec["capabilities"]

    component_names = [component["name"] for component in spec["architecture"]["components"]]
    assert "frontend" in component_names
    assert "api" in component_names
    assert "database" in component_names
    assert "object-storage" in component_names
    assert "cdn" in component_names
    assert "worker" in component_names