from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from initializer.engine.story_engine import derive_execution_metadata

_SERIAL_PROGRESS_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+"
    r"(?P<story_id>\S+)\s+—\s+"
    r"(?P<status>[^—]+?)\s+—\s+"
    r"(?P<description>.*)$"
)

_PARALLEL_PROGRESS_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<track>[^\]]+)\]\s+"
    r"(?P<story_id>\S+)\s+\((?P<source_story_id>[^)]+)\)\s+—\s+"
    r"(?P<status>[^—]+?)\s+—\s+"
    r"(?P<description>.*)$"
)

_HTTP_CONTRACT_RE = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_./:[\]-]+)"
)

_FAILURE_STATUSES = {"RETRY", "BLOCKED", "VALIDATION"}
_FINAL_FAILURE_STATUSES = {"BLOCKED", "VALIDATION"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format_duration(seconds: int | None) -> str:
    if seconds is None:
        return ""

    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _expand_expected_file_candidates(expected_files: list[Any]) -> list[str]:
    candidates: list[str] = []

    for item in expected_files:
        if not isinstance(item, str):
            continue

        text = item.strip().strip("`")
        if not text:
            continue

        text = text.split(" (", 1)[0].strip()
        for part in text.split(" or "):
            part = part.strip()
            if part:
                candidates.append(part)

    return candidates


def _parse_progress(progress_path: Path) -> list[dict[str, Any]]:
    if not progress_path.exists():
        return []

    events: list[dict[str, Any]] = []

    for line in progress_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue

        match = _PARALLEL_PROGRESS_RE.match(line) or _SERIAL_PROGRESS_RE.match(line)
        if not match:
            continue

        groups = match.groupdict()
        events.append(
            {
                "timestamp": groups["timestamp"],
                "timestamp_dt": _parse_timestamp(groups["timestamp"]),
                "track": groups.get("track"),
                "story_id": groups["story_id"],
                "source_story_id": groups.get("source_story_id"),
                "status": groups["status"].strip(),
                "description": groups["description"].strip(),
                "raw": line,
            }
        )

    return events


def _summarize_events(
    events: list[dict[str, Any]],
    expected_total: int | None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    unit_summaries: dict[str, dict[str, Any]] = {}
    source_summaries: dict[str, dict[str, Any]] = {}

    first_failure: dict[str, Any] | None = None
    build_failures = 0
    type_failures = 0
    test_failures = 0
    migration_warnings = 0

    for event in events:
        description = event["description"].lower()
        if "build" in description:
            build_failures += 1
        if "typecheck" in description or "type error" in description or "typescript" in description:
            type_failures += 1
        if "test" in description:
            test_failures += 1
        if "migration" in description and ("warn" in description or "failed" in description or "skip" in description):
            migration_warnings += 1

        if first_failure is None and event["status"] in _FAILURE_STATUSES:
            first_failure = event

        unit_id = event["story_id"]
        source_id = event.get("source_story_id") or unit_id

        for key, summary_map in ((unit_id, unit_summaries), (source_id, source_summaries)):
            summary = summary_map.setdefault(
                key,
                {
                    "id": key,
                    "start": None,
                    "end": None,
                    "retries": 0,
                    "statuses": [],
                    "description": event["description"],
                    "tracks": set(),
                    "unit_ids": set(),
                },
            )

            summary["end"] = event["timestamp_dt"]
            summary["description"] = event["description"]
            summary["statuses"].append(event["status"])
            if event.get("track"):
                summary["tracks"].add(event["track"])
            summary["unit_ids"].add(unit_id)

            if summary["start"] is None and event["status"] == "START":
                summary["start"] = event["timestamp_dt"]
            elif summary["start"] is None:
                summary["start"] = event["timestamp_dt"]

            if event["status"] == "RETRY":
                summary["retries"] += 1

    completed_units = sum(1 for event in events if event["status"] == "DONE")
    retries_total = sum(1 for event in events if event["status"] == "RETRY")
    stories_with_retry = len({event["story_id"] for event in events if event["status"] == "RETRY"})

    final_failures = 0
    exact_blocker = ""
    for summary in unit_summaries.values():
        final_status = summary["statuses"][-1] if summary["statuses"] else ""
        if final_status in _FINAL_FAILURE_STATUSES:
            final_failures += 1
            if not exact_blocker:
                exact_blocker = f"{summary['id']} — {summary['description']}"

    start = events[0]["timestamp_dt"] if events else None
    end = events[-1]["timestamp_dt"] if events else None
    duration_seconds = int((end - start).total_seconds()) if start and end else None

    if not events:
        current_state = "not_started"
    elif final_failures > 0:
        current_state = "blocked"
    elif expected_total and completed_units >= expected_total:
        current_state = "complete"
    else:
        current_state = "in_progress"

    first_failure_seconds = None
    if start and first_failure is not None:
        first_failure_seconds = int((first_failure["timestamp_dt"] - start).total_seconds())

    metrics = {
        "start": start.isoformat().replace("+00:00", "Z") if start else "",
        "end": end.isoformat().replace("+00:00", "Z") if end else "",
        "duration_seconds": duration_seconds,
        "duration": _format_duration(duration_seconds),
        "completed_units": completed_units,
        "expected_units": expected_total or 0,
        "retries_total": retries_total,
        "stories_with_retry": stories_with_retry,
        "final_failures": final_failures,
        "first_failure": first_failure["raw"] if first_failure else "",
        "time_to_first_failure_seconds": first_failure_seconds,
        "time_to_first_failure": _format_duration(first_failure_seconds),
        "build_failures": build_failures,
        "type_failures": type_failures,
        "test_failures": test_failures,
        "migration_warnings": migration_warnings,
        "exact_blocker": exact_blocker,
        "current_state": current_state,
    }

    for summary in (unit_summaries, source_summaries):
        for item in summary.values():
            start_dt = item["start"]
            end_dt = item["end"]
            item["duration_seconds"] = (
                int((end_dt - start_dt).total_seconds())
                if start_dt and end_dt
                else None
            )
            item["duration"] = _format_duration(item["duration_seconds"])
            item["start"] = start_dt.isoformat().replace("+00:00", "Z") if start_dt else ""
            item["end"] = end_dt.isoformat().replace("+00:00", "Z") if end_dt else ""
            item["tracks"] = sorted(item["tracks"])
            item["unit_ids"] = sorted(item["unit_ids"])

    return metrics, unit_summaries, source_summaries


def _find_git_root(project_dir: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(project_dir), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return None

    return Path(result.stdout.strip()).resolve()


def _project_pathspec(project_dir: Path, git_root: Path | None) -> str:
    if git_root is None:
        return str(project_dir)

    try:
        return str(project_dir.resolve().relative_to(git_root.resolve()))
    except ValueError:
        return str(project_dir)


def _git_status(project_dir: Path) -> list[dict[str, str]]:
    git_root = _find_git_root(project_dir)
    if git_root is None:
        return []

    pathspec = _project_pathspec(project_dir, git_root)
    result = subprocess.run(
        ["git", "-C", str(git_root), "status", "--short", "--", pathspec],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return []

    entries: list[dict[str, str]] = []
    prefix = f"{pathspec}/"

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        status = line[:2].strip()
        raw_path = line[3:].strip()
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1].strip()
        if raw_path.startswith(prefix):
            raw_path = raw_path[len(prefix):]

        entries.append({"status": status, "path": raw_path})

    return entries


def _git_diff_numstat(project_dir: Path) -> list[dict[str, Any]]:
    git_root = _find_git_root(project_dir)
    if git_root is None:
        return []

    pathspec = _project_pathspec(project_dir, git_root)
    result = subprocess.run(
        ["git", "-C", str(git_root), "diff", "--numstat", "--", pathspec],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return []

    stats: list[dict[str, Any]] = []
    prefix = f"{pathspec}/"

    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue

        added_text, removed_text, raw_path = parts
        if raw_path.startswith(prefix):
            raw_path = raw_path[len(prefix):]

        added = int(added_text) if added_text.isdigit() else 0
        removed = int(removed_text) if removed_text.isdigit() else 0
        stats.append(
            {
                "path": raw_path,
                "added": added,
                "removed": removed,
                "total": added + removed,
            }
        )

    stats.sort(key=lambda item: (-item["total"], item["path"]))
    return stats


def _story_http_contracts(story: dict[str, Any]) -> bool:
    for item in story.get("acceptance_criteria", []):
        if isinstance(item, str) and _HTTP_CONTRACT_RE.search(item):
            return True
    return False


def _classify_stories(stories: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, str]]], list[dict[str, Any]], list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    mixed_stories: list[dict[str, Any]] = []
    classified: list[dict[str, Any]] = []

    for story in stories:
        if not isinstance(story, dict):
            continue

        execution = story.get("execution")
        if not isinstance(execution, dict) or not execution.get("tracks"):
            execution = derive_execution_metadata(story)

        story_info = {
            "id": story.get("id", ""),
            "story_key": story.get("story_key", ""),
            "title": story.get("title", ""),
            "tracks": execution.get("tracks", []),
            "execution": execution,
            "expected_files": _expand_expected_file_candidates(story.get("expected_files", [])),
            "acceptance_criteria": story.get("acceptance_criteria", []),
        }
        classified.append(story_info)

        for track in execution.get("tracks", []):
            buckets[track].append(
                {
                    "id": story_info["id"],
                    "story_key": story_info["story_key"],
                    "title": story_info["title"],
                }
            )

        reasons: list[str] = []
        if execution.get("frontend_files") and execution.get("backend_files"):
            reasons.append("touches frontend and backend files")
        if "integration" in execution.get("tracks", []):
            reasons.append("requires frontend/backend wiring")
        if execution.get("frontend_files") and _story_http_contracts(story):
            reasons.append("combines UI work with HTTP contract surface")

        if reasons:
            mixed_stories.append(
                {
                    "id": story_info["id"],
                    "story_key": story_info["story_key"],
                    "title": story_info["title"],
                    "tracks": execution.get("tracks", []),
                    "reasons": reasons,
                }
            )

    for track in ("shared", "frontend", "backend", "integration"):
        buckets.setdefault(track, [])
        buckets[track].sort(key=lambda item: item["id"])

    mixed_stories.sort(key=lambda item: item["id"])
    classified.sort(key=lambda item: item["id"])

    return buckets, mixed_stories, classified


def _risk_level(value: int, medium_threshold: int, high_threshold: int) -> str:
    if value >= high_threshold:
        return "high"
    if value >= medium_threshold:
        return "medium"
    return "low"


def _build_risks(classified_stories: list[dict[str, Any]], mixed_stories: list[dict[str, Any]]) -> list[dict[str, str]]:
    migration_stories = 0
    integration_stories = 0

    for story in classified_stories:
        execution = story["execution"]
        if "integration" in execution.get("tracks", []):
            integration_stories += 1
        if any(
            isinstance(item, str) and "migration" in item.lower()
            for item in story.get("acceptance_criteria", [])
        ):
            if any(track in execution.get("tracks", []) for track in ("backend", "integration")):
                migration_stories += 1

    return [
        {
            "name": "collision",
            "level": _risk_level(len(mixed_stories), 2, 5),
            "summary": (
                f"{len(mixed_stories)} stories are mixed across frontend/backend surfaces "
                "and are the main candidates for workspace/file collisions."
            ),
        },
        {
            "name": "validation",
            "level": _risk_level(integration_stories, 2, 5),
            "summary": (
                f"{integration_stories} stories likely need partial validation before final integration "
                "to avoid build/typecheck failures from incomplete wiring."
            ),
        },
        {
            "name": "migrations",
            "level": _risk_level(migration_stories, 1, 3),
            "summary": (
                f"{migration_stories} stories include schema/migration work and need serialized migration execution "
                "in any parallel benchmark."
            ),
        },
    ]


def _select_story(stories: list[dict[str, Any]], predicate) -> dict[str, Any] | None:
    for story in stories:
        if predicate(story):
            return story
    return None


def _critical_story_specs() -> list[tuple[str, Any]]:
    return [
        ("ST-005 backend", lambda story: story["id"] == "ST-005" or story["story_key"] == "bootstrap.backend"),
        ("auth", lambda story: "authentication" in story["story_key"] or "auth" in story["title"].lower()),
        ("roles", lambda story: "roles" in story["story_key"] or "role" in story["title"].lower()),
        ("media", lambda story: "media" in story["story_key"] or "media" in story["title"].lower()),
        ("public site", lambda story: "public-site-rendering" in story["story_key"] or "public site" in story["title"].lower()),
    ]


def _top_changed_files_for_story(
    story: dict[str, Any],
    top_changed_files: list[dict[str, Any]],
    changed_files: list[dict[str, str]],
) -> list[str]:
    expected = set(story.get("expected_files", []))
    if not expected:
        return []

    ranked = [item["path"] for item in top_changed_files if item["path"] in expected]
    if ranked:
        return ranked[:5]

    changed = [item["path"] for item in changed_files if item["path"] in expected]
    return changed[:5]


def _build_critical_story_rows(
    stories: list[dict[str, Any]],
    source_summaries: dict[str, dict[str, Any]],
    top_changed_files: list[dict[str, Any]],
    changed_files: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for label, predicate in _critical_story_specs():
        story = _select_story(stories, predicate)
        if story is None:
            rows.append(
                {
                    "label": label,
                    "story_id": "",
                    "duration": "",
                    "duration_seconds": None,
                    "retries": 0,
                    "observation": "not present in this project",
                    "changed_files": [],
                }
            )
            continue

        summary = source_summaries.get(story["id"], {})
        changed = _top_changed_files_for_story(story, top_changed_files, changed_files)
        rows.append(
            {
                "label": label,
                "story_id": story["id"],
                "duration": summary.get("duration", ""),
                "duration_seconds": summary.get("duration_seconds"),
                "retries": summary.get("retries", 0),
                "observation": ", ".join(changed) if changed else "",
                "changed_files": changed,
            }
        )

    return rows


def _build_table(headers: list[str], rows: list[list[str]]) -> str:
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(row) + " |" for row in rows)
    if body:
        return "\n".join([header_line, separator, body])
    return "\n".join([header_line, separator])


def analyze_project(project_dir: Path) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    spec_path = project_dir / "spec.json"
    if not spec_path.exists():
        raise ValueError(f"spec.json not found in {project_dir}")

    spec = _load_json(spec_path)
    stories = spec.get("stories", [])
    buckets, mixed_stories, classified_stories = _classify_stories(stories)

    execution_plan_path = project_dir / ".openclaw" / "execution-plan.json"
    execution_plan = _load_json(execution_plan_path) if execution_plan_path.exists() else {}

    parallel_plan_total = 0
    parallel_plan_exists = False
    for track in ("shared", "frontend", "backend", "integration"):
        path = project_dir / ".openclaw" / f"{track}-plan.json"
        if path.exists():
            parallel_plan_exists = True
            parallel_plan_total += _load_json(path).get("total_stories", 0)

    if parallel_plan_exists:
        expected_units = parallel_plan_total
        unit_label = "slices"
        execution_mode = "parallel"
    else:
        expected_units = execution_plan.get("total_stories", len(stories))
        unit_label = "stories"
        execution_mode = "serial"

    progress_path = project_dir / "progress.txt"
    events = _parse_progress(progress_path)
    metrics, unit_summaries, source_summaries = _summarize_events(events, expected_units)
    metrics["unit_label"] = unit_label

    changed_files = _git_status(project_dir)
    top_changed_files = _git_diff_numstat(project_dir)[:5]

    risks = _build_risks(classified_stories, mixed_stories)
    critical_rows = _build_critical_story_rows(
        classified_stories,
        source_summaries,
        top_changed_files,
        changed_files,
    )

    top_slow_stories = sorted(
        (
            {
                "story_id": story_id,
                "duration": summary.get("duration", ""),
                "duration_seconds": summary.get("duration_seconds"),
                "retries": summary.get("retries", 0),
                "description": summary.get("description", ""),
            }
            for story_id, summary in source_summaries.items()
        ),
        key=lambda item: (item["duration_seconds"] or -1),
        reverse=True,
    )[:5]

    return {
        "project_dir": str(project_dir),
        "project_name": spec.get("answers", {}).get("project_name", project_dir.name),
        "project_slug": spec.get("answers", {}).get("project_slug", project_dir.name),
        "execution_mode": execution_mode,
        "metrics": metrics,
        "buckets": buckets,
        "mixed_stories": mixed_stories,
        "risks": risks,
        "success_criteria": [
            "at least 25% lower total duration, or",
            "same duration with fewer retries/failures, or",
            "clear wall-clock improvement on mixed frontend/backend stories",
        ],
        "immediate_after_run": [
            "record final serial end time",
            "extract per-story durations and retries from progress.txt",
            "capture git status snapshot for the project path",
            "list the five most changed files for the slow/problem stories",
            "build the story -> shared/frontend/backend/integration map for the parallel candidate",
            "run the parallel benchmark only after the serial baseline artifacts are frozen",
        ],
        "changed_files": changed_files,
        "top_changed_files": top_changed_files,
        "critical_story_rows": critical_rows,
        "top_slow_stories": top_slow_stories,
        "events": [
            {
                "timestamp": event["timestamp"],
                "track": event.get("track") or "",
                "story_id": event["story_id"],
                "source_story_id": event.get("source_story_id") or "",
                "status": event["status"],
                "description": event["description"],
            }
            for event in events
        ],
    }


def _comparison_rows(baseline: dict[str, Any], candidate: dict[str, Any]) -> list[list[str]]:
    fields = [
        ("Início", "start"),
        ("Fim", "end"),
        ("Duração total", "duration"),
        ("Stories/slices concluídas", None),
        ("Retries totais", "retries_total"),
        ("Stories com retry", "stories_with_retry"),
        ("Falhas finais", "final_failures"),
        ("Primeira falha", "first_failure"),
        ("Tempo até primeira falha", "time_to_first_failure"),
        ("Build failures", "build_failures"),
        ("Type failures", "type_failures"),
        ("Test failures", "test_failures"),
        ("Migrações com warning", "migration_warnings"),
    ]

    rows: list[list[str]] = []
    for label, key in fields:
        if key is None:
            baseline_value = (
                f"{baseline['metrics']['completed_units']}/{baseline['metrics']['expected_units']} "
                f"{baseline['metrics']['unit_label']}"
            )
            candidate_value = (
                f"{candidate['metrics']['completed_units']}/{candidate['metrics']['expected_units']} "
                f"{candidate['metrics']['unit_label']}"
            )
        else:
            baseline_value = str(baseline["metrics"].get(key, ""))
            candidate_value = str(candidate["metrics"].get(key, ""))
        rows.append([label, baseline_value, candidate_value])

    return rows


def _merge_critical_rows(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> list[list[str]]:
    baseline_map = {row["label"]: row for row in baseline["critical_story_rows"]}
    candidate_map = {row["label"]: row for row in candidate["critical_story_rows"]}
    labels = ["ST-005 backend", "auth", "roles", "media", "public site"]

    rows: list[list[str]] = []
    for label in labels:
        base = baseline_map.get(label, {})
        cand = candidate_map.get(label, {})
        observation = cand.get("observation") or base.get("observation") or ""
        rows.append(
            [
                label,
                base.get("duration", ""),
                cand.get("duration", ""),
                str(base.get("retries", 0)),
                str(cand.get("retries", 0)),
                observation,
            ]
        )

    return rows


def _build_verdict(baseline: dict[str, Any], candidate: dict[str, Any]) -> str:
    baseline_duration = baseline["metrics"].get("duration_seconds")
    candidate_duration = candidate["metrics"].get("duration_seconds")

    if candidate["metrics"]["current_state"] != "complete":
        return "pending: candidate run is not complete yet"

    if (
        baseline_duration
        and candidate_duration
        and candidate_duration <= baseline_duration * 0.75
    ):
        return "pass: total duration improved by at least 25%"

    if (
        candidate["metrics"]["retries_total"] < baseline["metrics"]["retries_total"]
        and candidate["metrics"]["final_failures"] <= baseline["metrics"]["final_failures"]
    ):
        return "pass: retries/failures improved even without a 25% wall-clock gain"

    improved_critical = 0
    baseline_map = {row["label"]: row for row in baseline["critical_story_rows"]}
    candidate_map = {row["label"]: row for row in candidate["critical_story_rows"]}
    for label in ("ST-005 backend", "auth", "roles", "media", "public site"):
        base = baseline_map.get(label, {})
        cand = candidate_map.get(label, {})
        base_seconds = base.get("duration_seconds")
        cand_seconds = cand.get("duration_seconds")
        if (
            isinstance(base_seconds, int)
            and isinstance(cand_seconds, int)
            and cand_seconds < base_seconds
        ):
            improved_critical += 1

    if improved_critical >= 2:
        return "pass: critical mixed stories improved materially"

    return "fail: candidate did not yet beat the baseline on time, retries, or critical stories"


def build_benchmark_report(
    baseline: dict[str, Any],
    candidate: dict[str, Any] | None = None,
) -> str:
    lines = [
        f"# Benchmark Report — {baseline['project_name']}",
        "",
        f"- Baseline path: `{baseline['project_dir']}`",
        f"- Baseline mode: `{baseline['execution_mode']}`",
        f"- Current state: `{baseline['metrics']['current_state']}`",
    ]

    if candidate:
        lines.append(f"- Candidate path: `{candidate['project_dir']}`")
        lines.append(f"- Candidate mode: `{candidate['execution_mode']}`")
        lines.append(f"- Candidate state: `{candidate['metrics']['current_state']}`")

    lines.extend(["", "## Data Collection", ""])

    if candidate:
        lines.append(_build_table(["Campo", "Serial", "Paralelo"], _comparison_rows(baseline, candidate)))
    else:
        single_rows = [
            ["Início", baseline["metrics"]["start"]],
            ["Fim", baseline["metrics"]["end"]],
            ["Duração total", baseline["metrics"]["duration"]],
            [
                "Stories/slices concluídas",
                f"{baseline['metrics']['completed_units']}/{baseline['metrics']['expected_units']} {baseline['metrics']['unit_label']}",
            ],
            ["Retries totais", str(baseline["metrics"]["retries_total"])],
            ["Stories com retry", str(baseline["metrics"]["stories_with_retry"])],
            ["Falhas finais", str(baseline["metrics"]["final_failures"])],
            ["Primeira falha", baseline["metrics"]["first_failure"]],
            ["Tempo até primeira falha", baseline["metrics"]["time_to_first_failure"]],
            ["Build failures", str(baseline["metrics"]["build_failures"])],
            ["Type failures", str(baseline["metrics"]["type_failures"])],
            ["Test failures", str(baseline["metrics"]["test_failures"])],
            ["Migrações com warning", str(baseline["metrics"]["migration_warnings"])],
        ]
        lines.append(_build_table(["Campo", "Valor"], single_rows))

    lines.extend(["", "## Buckets", ""])
    bucket_rows = []
    for track in ("shared", "frontend", "backend", "integration"):
        items = baseline["buckets"].get(track, [])
        example = ", ".join(item["id"] for item in items[:5])
        bucket_rows.append([track, str(len(items)), example])
    lines.append(_build_table(["Bucket", "Count", "Examples"], bucket_rows))

    lines.extend(["", "## Mixed Stories", ""])
    if baseline["mixed_stories"]:
        mixed_rows = [
            [
                item["id"],
                item["story_key"],
                ", ".join(item["tracks"]),
                "; ".join(item["reasons"]),
            ]
            for item in baseline["mixed_stories"]
        ]
        lines.append(_build_table(["Story", "Key", "Tracks", "Reasons"], mixed_rows))
    else:
        lines.append("No mixed stories detected.")

    lines.extend(["", "## Risks", ""])
    risk_rows = [
        [risk["name"], risk["level"], risk["summary"]]
        for risk in baseline["risks"]
    ]
    lines.append(_build_table(["Risk", "Level", "Summary"], risk_rows))

    lines.extend(["", "## Critical Stories", ""])
    if candidate:
        lines.append(
            _build_table(
                ["Story", "Serial duração", "Paralelo duração", "Retries serial", "Retries paralelo", "Observação"],
                _merge_critical_rows(baseline, candidate),
            )
        )
    else:
        current_rows = [
            [
                row["label"],
                row["story_id"],
                row["duration"],
                str(row["retries"]),
                row["observation"],
            ]
            for row in baseline["critical_story_rows"]
        ]
        lines.append(
            _build_table(
                ["Story", "ID", "Duração atual", "Retries", "Changed files / note"],
                current_rows,
            )
        )

    lines.extend(["", "## Blockers", ""])
    if candidate:
        lines.append(f"- Serial blocker: {baseline['metrics']['exact_blocker'] or 'none'}")
        lines.append(f"- Parallel blocker: {candidate['metrics']['exact_blocker'] or 'none'}")
    else:
        lines.append(f"- Current blocker: {baseline['metrics']['exact_blocker'] or 'none'}")

    lines.extend(["", "## Top Slow Stories", ""])
    if baseline["top_slow_stories"]:
        slow_rows = [
            [
                row["story_id"],
                row["duration"],
                str(row["retries"]),
                row["description"],
            ]
            for row in baseline["top_slow_stories"]
        ]
        lines.append(_build_table(["Story", "Duration", "Retries", "Last description"], slow_rows))
    else:
        lines.append("No progress events yet.")

    lines.extend(["", "## Top Changed Files", ""])
    if baseline["top_changed_files"]:
        changed_rows = [
            [row["path"], str(row["added"]), str(row["removed"]), str(row["total"])]
            for row in baseline["top_changed_files"]
        ]
        lines.append(_build_table(["File", "Added", "Removed", "Total"], changed_rows))
    else:
        lines.append("No tracked diff detected for the project path.")

    lines.extend(["", "## Success Criteria", ""])
    for item in baseline["success_criteria"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Immediate After Current Run", ""])
    for item in baseline["immediate_after_run"]:
        lines.append(f"- {item}")

    if candidate:
        lines.extend(["", "## Verdict", "", f"- {_build_verdict(baseline, candidate)}"])

    return "\n".join(lines).rstrip() + "\n"


def _write_snapshot(snapshot_dir: Path, label: str, analysis: dict[str, Any]) -> None:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    project_dir = Path(analysis["project_dir"])

    (snapshot_dir / f"{label}-summary.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    progress_path = project_dir / "progress.txt"
    if progress_path.exists():
        shutil.copy2(progress_path, snapshot_dir / f"{label}-progress.txt")

    (snapshot_dir / f"{label}-git-status.txt").write_text(
        "\n".join(f"{item['status']:>2} {item['path']}" for item in analysis["changed_files"]) + "\n",
        encoding="utf-8",
    )
    (snapshot_dir / f"{label}-top-changed-files.txt").write_text(
        "\n".join(
            f"{item['total']:>6}  +{item['added']:<4} -{item['removed']:<4} {item['path']}"
            for item in analysis["top_changed_files"]
        ) + "\n",
        encoding="utf-8",
    )


def run_benchmark_project(
    path: str,
    candidate: str | None = None,
    output: str | None = None,
    json_output: str | None = None,
    snapshot_dir: str | None = None,
) -> int:
    try:
        baseline = analyze_project(Path(path))
        candidate_analysis = analyze_project(Path(candidate)) if candidate else None
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    report = build_benchmark_report(baseline, candidate_analysis)
    print(report, end="")

    if output:
        output_path = Path(output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")

    if json_output:
        json_path = Path(json_output).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(
                {
                    "baseline": baseline,
                    "candidate": candidate_analysis,
                },
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

    if snapshot_dir:
        directory = Path(snapshot_dir).resolve()
        _write_snapshot(directory, "serial", baseline)
        if candidate_analysis:
            _write_snapshot(directory, "parallel", candidate_analysis)

    return 0
