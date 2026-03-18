"""Tests for StoryGraph and StoryScheduler."""

import json
import pytest
from pathlib import Path

from initializer.graph.story_graph import StoryGraph
from initializer.runtime.story_scheduler import StoryScheduler, load_completed_from_progress


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

def _make_plan(stories):
    return {"stories": stories}


def _write_plan(tmp_path, stories):
    plan = _make_plan(stories)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    return path


SIMPLE_STORIES = [
    {
        "id": "ST-001",
        "title": "Init repo",
        "story_key": "bootstrap.repository",
        "depends_on": [],
    },
    {
        "id": "ST-002",
        "title": "Setup DB",
        "story_key": "bootstrap.database",
        "depends_on": ["bootstrap.repository"],
    },
    {
        "id": "ST-003",
        "title": "Setup backend",
        "story_key": "bootstrap.backend",
        "depends_on": ["bootstrap.database"],
    },
]


# -------------------------------------------------------------------
# StoryGraph.load — key translation
# -------------------------------------------------------------------

def test_load_translates_depends_on_from_story_key_to_id(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    # depends_on should now contain ids, not story_keys
    assert graph.dependencies("ST-002") == ["ST-001"]
    assert graph.dependencies("ST-003") == ["ST-002"]


def test_load_preserves_empty_depends_on(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    assert graph.dependencies("ST-001") == []


def test_load_handles_stories_without_story_key(tmp_path):
    stories = [
        {"id": "ST-001", "title": "Init", "depends_on": []},
        {"id": "ST-900", "title": "Monitoring", "depends_on": []},
    ]
    path = _write_plan(tmp_path, stories)
    graph = StoryGraph.load(path)

    assert set(graph.all_stories()) == {"ST-001", "ST-900"}


# -------------------------------------------------------------------
# StoryGraph.available
# -------------------------------------------------------------------

def test_available_returns_root_stories_first(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    available = graph.available(set())
    assert available == ["ST-001"]


def test_available_unlocks_dependents_when_deps_completed(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    available = graph.available({"ST-001"})
    assert "ST-002" in available
    assert "ST-001" not in available


def test_available_returns_empty_when_all_completed(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    available = graph.available({"ST-001", "ST-002", "ST-003"})
    assert available == []


# -------------------------------------------------------------------
# StoryGraph.topological_order
# -------------------------------------------------------------------

def test_topological_order_respects_dependencies(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    order = graph.topological_order()
    assert order.index("ST-001") < order.index("ST-002")
    assert order.index("ST-002") < order.index("ST-003")


# -------------------------------------------------------------------
# StoryGraph.detect_cycles
# -------------------------------------------------------------------

def test_detect_cycles_raises_on_circular_dependency(tmp_path):
    stories = [
        {"id": "ST-001", "story_key": "a", "title": "A", "depends_on": ["b"]},
        {"id": "ST-002", "story_key": "b", "title": "B", "depends_on": ["a"]},
    ]
    path = _write_plan(tmp_path, stories)

    with pytest.raises(RuntimeError, match="Cycle detected"):
        StoryGraph.load(path)


# -------------------------------------------------------------------
# load_completed_from_progress
# -------------------------------------------------------------------

PROGRESS_CONTENT = """\
# progress.txt
[2026-03-17T12:03:17Z] ST-001 — START — Initialize project repository
[2026-03-17T12:14:20Z] ST-001 — DONE — Initialize project repository
[2026-03-17T12:14:20Z] ST-002 — START — Setup database
[2026-03-17T12:28:02Z] ST-002 — DONE — Setup database
[2026-03-17T12:28:02Z] ST-003 — START — Setup backend service
[2026-03-17T12:40:55Z] ST-003 — RETRY — Attempt 2: Build failure
[2026-03-17T12:45:00Z] ST-003 — DONE — Setup backend service (succeeded on attempt 2)
"""


def test_load_completed_extracts_story_ids(tmp_path):
    path = tmp_path / "progress.txt"
    path.write_text(PROGRESS_CONTENT)

    completed = load_completed_from_progress(path)
    assert completed == {"ST-001", "ST-002", "ST-003"}


def test_load_completed_ignores_non_done_lines(tmp_path):
    content = """\
[2026-03-17T12:03:17Z] ST-001 — START — Initialize
[2026-03-17T12:28:02Z] ST-002 — BLOCKED — Failed
"""
    path = tmp_path / "progress.txt"
    path.write_text(content)

    completed = load_completed_from_progress(path)
    assert completed == set()


def test_load_completed_does_not_return_done_as_story_id(tmp_path):
    """Regression: BUG-002 — parser must not extract 'DONE' as a story ID."""
    path = tmp_path / "progress.txt"
    path.write_text(PROGRESS_CONTENT)

    completed = load_completed_from_progress(path)
    assert "DONE" not in completed


# -------------------------------------------------------------------
# StoryScheduler
# -------------------------------------------------------------------

def test_scheduler_returns_next_available_story(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    scheduler = StoryScheduler(graph, completed=set())
    assert scheduler.next_story() == "ST-001"


def test_scheduler_skips_completed_stories(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    scheduler = StoryScheduler(graph, completed={"ST-001"})
    assert scheduler.next_story() == "ST-002"


def test_scheduler_returns_none_when_all_done(tmp_path):
    path = _write_plan(tmp_path, SIMPLE_STORIES)
    graph = StoryGraph.load(path)

    scheduler = StoryScheduler(graph, completed={"ST-001", "ST-002", "ST-003"})
    assert scheduler.next_story() is None
