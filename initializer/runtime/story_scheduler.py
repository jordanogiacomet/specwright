from pathlib import Path
from initializer.graph.story_graph import StoryGraph


class StoryScheduler:

    def __init__(self, graph: StoryGraph, completed: set[str]):
        self.graph = graph
        self.completed = completed

    def next_story(self):

        available = self.graph.available(self.completed)

        if not available:
            return None

        return available[0]


def load_completed_from_progress(progress_path: Path) -> set[str]:

    completed = set()

    for line in progress_path.read_text().splitlines():

        if "DONE" in line:

            parts = line.split("—")

            if len(parts) > 1 and "DONE" in parts[1]:
                # Story ID is the last token before the first —
                # Format: [timestamp] ST-001 — DONE — description
                story = parts[0].strip().split()[-1]
                completed.add(story)

    return completed