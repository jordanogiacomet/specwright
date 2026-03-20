import json
import re
from pathlib import Path
from initializer.graph.story_graph import StoryGraph

_SERIAL_PROGRESS_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+"
    r"(?P<story_id>\S+)\s+—\s+"
    r"(?P<status>[^—]+?)\s+—\s+"
    r"(?P<description>.*)$"
)

_PARALLEL_PROGRESS_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+\[(?P<track>[^\]]+)\]\s+"
    r"(?P<unit_id>\S+)\s+\((?P<source_story_id>[^)]+)\)\s+—\s+"
    r"(?P<status>[^—]+?)\s+—\s+"
    r"(?P<description>.*)$"
)


class StoryScheduler:

    def __init__(self, graph: StoryGraph, completed: set[str]):
        self.graph = graph
        self.completed = completed

    def next_story(self):

        available = self.graph.available(self.completed)

        if not available:
            return None

        return available[0]


def _load_parallel_requirements(progress_path: Path) -> dict[str, set[str]]:

    openclaw_dir = progress_path.parent / ".openclaw"
    requirements: dict[str, set[str]] = {}

    for track in ("shared", "frontend", "backend", "integration"):
        path = openclaw_dir / f"{track}-plan.json"
        if not path.exists():
            continue

        try:
            plan = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        for story in plan.get("stories", []):
            if not isinstance(story, dict):
                continue

            source_story_id = story.get("source_story_id")
            unit_id = story.get("id")
            if isinstance(source_story_id, str) and isinstance(unit_id, str) and source_story_id and unit_id:
                requirements.setdefault(source_story_id, set()).add(unit_id)

    return requirements


def load_completed_from_progress(progress_path: Path) -> set[str]:

    completed = set()
    done_units = set()
    done_sources_without_plan = set()
    required_units_by_story = _load_parallel_requirements(progress_path)

    for line in progress_path.read_text(encoding="utf-8").splitlines():
        parallel_match = _PARALLEL_PROGRESS_RE.match(line)
        if parallel_match:
            groups = parallel_match.groupdict()
            if groups["status"].strip() == "DONE":
                unit_id = groups["unit_id"].strip()
                source_story_id = groups["source_story_id"].strip()
                if unit_id:
                    done_units.add(unit_id)
                if source_story_id and not required_units_by_story:
                    done_sources_without_plan.add(source_story_id)
            continue

        serial_match = _SERIAL_PROGRESS_RE.match(line)
        if serial_match:
            groups = serial_match.groupdict()
            if groups["status"].strip() == "DONE":
                story_id = groups["story_id"].strip()
                if story_id:
                    completed.add(story_id)

    for source_story_id, required_units in required_units_by_story.items():
        if required_units and required_units.issubset(done_units):
            completed.add(source_story_id)

    completed.update(done_sources_without_plan)

    return completed
