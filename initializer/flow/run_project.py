"""Run Project Flow.

Single command that orchestrates the full Specwright pipeline:
    new → enrich → prepare → ralph loop

Usage:
    initializer run --assist           # full interactive flow
    initializer run --assist --dry-run # everything except actual Codex execution
    initializer run --spec path.json   # from existing spec, skip interactive
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from initializer.flow.new_project import run_new_project
from initializer.flow.enrich_project import run_enrich_project
from initializer.flow.prepare_project import run_prepare_project


def _find_latest_output() -> Path | None:
    """Find the most recently modified output directory."""
    output_root = Path("output")
    if not output_root.exists():
        return None

    candidates = [
        d for d in output_root.iterdir()
        if d.is_dir() and (d / "spec.json").exists()
    ]

    if not candidates:
        return None

    return max(candidates, key=lambda d: (d / "spec.json").stat().st_mtime).resolve()


def _run_ralph(project_dir: Path, dry_run: bool = False) -> int:
    """Execute ralph.sh in the project directory."""
    ralph_path = project_dir / "ralph.sh"

    if not ralph_path.exists():
        print(f"\nError: ralph.sh not found in {project_dir}")
        print("Run 'initializer prepare' first.")
        return 1

    cmd = [str(ralph_path)]
    if dry_run:
        cmd.append("--dry-run")

    print()
    print("=" * 60)
    print("Starting Ralph Loop")
    print("=" * 60)
    print()

    result = subprocess.run(
        cmd,
        cwd=str(project_dir),
    )

    return result.returncode


def run_full_pipeline(
    spec_path: str | None = None,
    assist: bool = False,
    dry_run: bool = False,
    skip_ralph: bool = False,
) -> int:
    """Run the full Specwright pipeline."""

    print()
    print("=" * 60)
    print("Specwright — Full Pipeline")
    print("=" * 60)
    print()

    # -------------------------------------------------------
    # Step 1: Generate
    # -------------------------------------------------------

    print("Step 1/4: Generate project")
    print("-" * 40)

    exit_code = run_new_project(spec_path, assist=assist)
    if exit_code and exit_code != 0:
        print("\nPipeline stopped: project generation failed.")
        return exit_code

    # Find the output directory
    project_dir = _find_latest_output()
    if not project_dir:
        print("\nError: Could not find generated output directory.")
        return 1

    print(f"\nGenerated: {project_dir}")

    # -------------------------------------------------------
    # Step 2: Enrich
    # -------------------------------------------------------

    print()
    print("Step 2/4: Enrich with PRD intelligence")
    print("-" * 40)

    exit_code = run_enrich_project(str(project_dir))
    if exit_code != 0:
        print("\nWarning: enrichment failed, continuing without intelligence.")
        # Don't stop — enrich is optional

    # -------------------------------------------------------
    # Step 3: Prepare
    # -------------------------------------------------------

    print()
    print("Step 3/4: Prepare for execution")
    print("-" * 40)

    exit_code = run_prepare_project(str(project_dir))
    if exit_code != 0:
        print("\nPipeline stopped: preparation failed.")
        return exit_code

    # -------------------------------------------------------
    # Step 4: Execute
    # -------------------------------------------------------

    if skip_ralph:
        print()
        print("Step 4/4: Skipped (--no-execute)")
        print()
        print("=" * 60)
        print("Pipeline complete (without execution)")
        print("=" * 60)
        print()
        print(f"Project ready at: {project_dir}")
        print()
        print("To execute manually:")
        print(f"  cd {project_dir}")
        print("  ./ralph.sh --dry-run    # preview")
        print("  ./ralph.sh              # execute")
        return 0

    print()
    print("Step 4/4: Execute via Ralph Loop")
    print("-" * 40)

    exit_code = _run_ralph(project_dir, dry_run=dry_run)

    print()
    print("=" * 60)
    if exit_code == 0:
        print("Pipeline complete")
    else:
        print(f"Pipeline finished with ralph exit code {exit_code}")
    print("=" * 60)
    print()
    print(f"Project at: {project_dir}")
    print(f"Progress:   {project_dir / 'progress.txt'}")
    print()

    return exit_code