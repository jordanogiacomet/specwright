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

            if len(parts) > 1:
                story = parts[1].strip().split()[0]
                completed.add(story)

    return completed