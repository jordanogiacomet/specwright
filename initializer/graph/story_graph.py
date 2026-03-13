from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set


class StoryGraph:
    """
    Represents a Directed Acyclic Graph (DAG) of stories.

    Used to determine execution order for story-based agents.
    """

    def __init__(self, stories: Dict[str, dict]):
        self.stories = stories

    # -----------------------------------------------------------
    # Load graph
    # -----------------------------------------------------------

    @classmethod
    def load(cls, path: Path) -> "StoryGraph":
        if not path.exists():
            raise FileNotFoundError(f"Story graph not found: {path}")

        data = json.loads(path.read_text())

        stories = {story["id"]: story for story in data["stories"]}

        graph = cls(stories)

        graph.detect_cycles()

        return graph

    # -----------------------------------------------------------
    # Accessors
    # -----------------------------------------------------------

    def all_stories(self) -> List[str]:
        return list(self.stories.keys())

    def dependencies(self, story_id: str) -> List[str]:
        story = self.stories.get(story_id)

        if not story:
            raise KeyError(f"Unknown story: {story_id}")

        return story.get("depends_on", [])

    # -----------------------------------------------------------
    # Execution logic
    # -----------------------------------------------------------

    def available(self, completed: Set[str]) -> List[str]:
        """
        Return stories that can be executed now.
        """

        available: List[str] = []

        for story_id, story in self.stories.items():

            if story_id in completed:
                continue

            deps = story.get("depends_on", [])

            if all(dep in completed for dep in deps):
                available.append(story_id)

        return available

    # -----------------------------------------------------------
    # Cycle detection
    # -----------------------------------------------------------

    def detect_cycles(self) -> None:
        visited: Set[str] = set()
        stack: Set[str] = set()

        def visit(node: str):

            if node in stack:
                raise RuntimeError(f"Cycle detected in story graph at {node}")

            if node in visited:
                return

            stack.add(node)

            for dep in self.dependencies(node):
                visit(dep)

            stack.remove(node)
            visited.add(node)

        for story_id in self.stories:
            visit(story_id)

    # -----------------------------------------------------------
    # Topological order
    # -----------------------------------------------------------

    def topological_order(self) -> List[str]:
        """
        Return stories in valid execution order.
        """

        completed: Set[str] = set()
        order: List[str] = []

        while len(completed) < len(self.stories):

            available = self.available(completed)

            if not available:
                raise RuntimeError("No executable stories found. Graph may be invalid.")

            for story in available:
                if story not in completed:
                    completed.add(story)
                    order.append(story)

        return order