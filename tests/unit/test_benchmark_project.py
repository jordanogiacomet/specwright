import json
import subprocess
from pathlib import Path

from initializer.flow.benchmark_project import analyze_project, run_benchmark_project


def _write_project(
    root: Path,
    stories: list[dict],
    progress: str,
    *,
    parallel: bool = False,
) -> Path:
    project_dir = root / "project"
    project_dir.mkdir(parents=True, exist_ok=True)

    spec = {
        "answers": {
            "project_name": "Benchmark Project",
            "project_slug": "benchmark-project",
        },
        "stories": stories,
    }
    (project_dir / "spec.json").write_text(
        json.dumps(spec, indent=2) + "\n",
        encoding="utf-8",
    )
    (project_dir / "progress.txt").write_text(progress, encoding="utf-8")

    openclaw = project_dir / ".openclaw"
    openclaw.mkdir(parents=True, exist_ok=True)
    (openclaw / "execution-plan.json").write_text(
        json.dumps({"total_stories": len(stories), "stories": stories}, indent=2) + "\n",
        encoding="utf-8",
    )

    if parallel:
        for track, total in (
            ("shared", 1),
            ("frontend", 1),
            ("backend", 2),
            ("integration", 1),
        ):
            (openclaw / f"{track}-plan.json").write_text(
                json.dumps({"track": track, "total_stories": total, "stories": []}, indent=2) + "\n",
                encoding="utf-8",
            )

    return project_dir


def test_analyze_project_summarizes_serial_progress_and_buckets(tmp_path):
    stories = [
        {
            "id": "ST-001",
            "story_key": "bootstrap.repository",
            "title": "Initialize repository",
            "expected_files": ["package.json"],
        },
        {
            "id": "ST-005",
            "story_key": "bootstrap.backend",
            "title": "Setup backend service",
            "expected_files": ["src/server.ts", "src/api/health.ts"],
        },
        {
            "id": "ST-007",
            "story_key": "feature.authentication",
            "title": "Implement authentication",
            "expected_files": ["src/app/(auth)/login/page.tsx", "src/api/auth.ts"],
            "acceptance_criteria": ["POST /api/auth/login returns 200 on success"],
        },
    ]

    progress = """\
[2026-03-20T12:00:00Z] ST-001 — START — Initialize repository
[2026-03-20T12:02:00Z] ST-001 — DONE — Initialize repository
[2026-03-20T12:02:00Z] ST-005 — START — Setup backend service
[2026-03-20T12:03:00Z] ST-005 — RETRY — Attempt 2: Build failure
[2026-03-20T12:07:00Z] ST-005 — DONE — Setup backend service
[2026-03-20T12:07:00Z] ST-007 — START — Implement authentication
"""

    project_dir = _write_project(tmp_path, stories, progress)
    analysis = analyze_project(project_dir)

    assert analysis["execution_mode"] == "serial"
    assert analysis["metrics"]["current_state"] == "in_progress"
    assert analysis["metrics"]["completed_units"] == 2
    assert analysis["metrics"]["expected_units"] == 3
    assert analysis["metrics"]["retries_total"] == 1
    assert analysis["metrics"]["stories_with_retry"] == 1
    assert analysis["metrics"]["build_failures"] == 1
    assert len(analysis["buckets"]["shared"]) == 1
    assert len(analysis["buckets"]["backend"]) == 2
    assert len(analysis["buckets"]["frontend"]) == 1
    assert len(analysis["buckets"]["integration"]) == 1
    assert analysis["mixed_stories"][0]["id"] == "ST-007"


def test_analyze_project_aggregates_parallel_progress_by_source_story(tmp_path):
    stories = [
        {
            "id": "ST-005",
            "story_key": "bootstrap.backend",
            "title": "Setup backend service",
            "expected_files": ["src/server.ts", "src/api/health.ts"],
        },
        {
            "id": "ST-007",
            "story_key": "feature.authentication",
            "title": "Implement authentication",
            "expected_files": ["src/app/(auth)/login/page.tsx", "src/api/auth.ts"],
            "acceptance_criteria": ["POST /api/auth/login returns 200 on success"],
        },
    ]

    progress = """\
[2026-03-20T12:00:00Z] [frontend] FE-ST-007 (ST-007) — START — Frontend slice — Implement authentication
[2026-03-20T12:01:00Z] [backend] BE-ST-007 (ST-007) — START — Backend slice — Implement authentication
[2026-03-20T12:02:00Z] [frontend] FE-ST-007 (ST-007) — DONE — Frontend slice — Implement authentication
[2026-03-20T12:03:00Z] [backend] BE-ST-007 (ST-007) — RETRY — Attempt 2: Test failure
[2026-03-20T12:05:00Z] [backend] BE-ST-007 (ST-007) — DONE — Backend slice — Implement authentication
[2026-03-20T12:05:00Z] [integration] IN-ST-007 (ST-007) — START — Integration slice — Implement authentication
[2026-03-20T12:08:00Z] [integration] IN-ST-007 (ST-007) — DONE — Integration slice — Implement authentication
"""

    project_dir = _write_project(tmp_path, stories, progress, parallel=True)
    analysis = analyze_project(project_dir)

    assert analysis["execution_mode"] == "parallel"
    assert analysis["metrics"]["unit_label"] == "slices"
    assert analysis["metrics"]["retries_total"] == 1

    auth_row = next(row for row in analysis["critical_story_rows"] if row["label"] == "auth")
    assert auth_row["story_id"] == "ST-007"
    assert auth_row["retries"] == 1
    assert auth_row["duration"] == "8m 0s"


def test_analyze_project_collects_git_changes(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "bench@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Bench"], cwd=repo, check=True)

    stories = [
        {
            "id": "ST-005",
            "story_key": "bootstrap.backend",
            "title": "Setup backend service",
            "expected_files": ["src/server.ts"],
        }
    ]
    project_dir = _write_project(repo, stories, "")

    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "server.ts").write_text("console.log('v1')\n", encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

    (src_dir / "server.ts").write_text("console.log('v2')\nconsole.log('v3')\n", encoding="utf-8")
    (src_dir / "new.ts").write_text("export const value = 1;\n", encoding="utf-8")

    analysis = analyze_project(project_dir)

    changed_paths = {item["path"] for item in analysis["changed_files"]}
    assert "src/server.ts" in changed_paths
    assert "src/new.ts" in changed_paths
    assert analysis["top_changed_files"][0]["path"] == "src/server.ts"


def test_run_benchmark_project_writes_report_json_and_snapshots(tmp_path, capsys):
    baseline = _write_project(
        tmp_path / "baseline",
        [
            {
                "id": "ST-005",
                "story_key": "bootstrap.backend",
                "title": "Setup backend service",
                "expected_files": ["src/server.ts"],
            }
        ],
        "[2026-03-20T12:00:00Z] ST-005 — START — Setup backend service\n",
    )
    candidate = _write_project(
        tmp_path / "candidate",
        [
            {
                "id": "ST-005",
                "story_key": "bootstrap.backend",
                "title": "Setup backend service",
                "expected_files": ["src/server.ts"],
            }
        ],
        "[2026-03-20T12:00:00Z] ST-005 — DONE — Setup backend service\n",
    )

    report_path = tmp_path / "reports" / "benchmark.md"
    json_path = tmp_path / "reports" / "benchmark.json"
    snapshot_dir = tmp_path / "reports" / "snapshots"

    exit_code = run_benchmark_project(
        str(baseline),
        candidate=str(candidate),
        output=str(report_path),
        json_output=str(json_path),
        snapshot_dir=str(snapshot_dir),
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "## Data Collection" in captured.out
    assert report_path.exists()
    assert json_path.exists()
    assert (snapshot_dir / "serial-summary.json").exists()
    assert (snapshot_dir / "parallel-summary.json").exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["baseline"]["project_name"] == "Benchmark Project"
    assert payload["candidate"]["project_name"] == "Benchmark Project"
