import argparse


_REFERENCE_HELP = (
    "Path to a directory of design reference images (png, jpg, webp). "
    "The AI will analyze them and extract colors, layout, typography, and "
    "components into the design system."
)


def main():
    parser = argparse.ArgumentParser(prog="initializer")
    subparsers = parser.add_subparsers(dest="command")

    new_parser = subparsers.add_parser("new")
    new_parser.add_argument("--spec")
    new_parser.add_argument(
        "--assist",
        action="store_true",
        help="Enable AI-assisted discovery before final spec generation.",
    )
    new_parser.add_argument("--reference", help=_REFERENCE_HELP)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--spec", help="Path to existing spec.json to skip interactive input.")
    run_parser.add_argument(
        "--assist",
        action="store_true",
        help="Enable AI-assisted discovery.",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run everything except actual Codex execution.",
    )
    run_parser.add_argument(
        "--no-execute",
        action="store_true",
        help="Stop after prepare, don't run ralph loop.",
    )
    run_parser.add_argument("--reference", help=_REFERENCE_HELP)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--spec")

    enrich_parser = subparsers.add_parser("enrich")
    enrich_parser.add_argument("path", help="Path to generated project directory.")
    enrich_parser.add_argument(
        "--review",
        action="store_true",
        help="Also run AI architecture review (requires OPENAI_API_KEY).",
    )

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("path", help="Path to generated project directory.")

    refine_parser = subparsers.add_parser("refine")
    refine_parser.add_argument("path")

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("path", nargs="?", default=".")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("path", nargs="?", default=".")

    benchmark_parser = subparsers.add_parser("benchmark")
    benchmark_parser.add_argument("path", help="Path to the baseline generated project directory.")
    benchmark_parser.add_argument(
        "--candidate",
        help="Optional path to the parallel/candidate generated project directory.",
    )
    benchmark_parser.add_argument(
        "--output",
        help="Optional path to write the Markdown benchmark report.",
    )
    benchmark_parser.add_argument(
        "--json",
        dest="json_output",
        help="Optional path to write the JSON benchmark payload.",
    )
    benchmark_parser.add_argument(
        "--snapshot-dir",
        help="Optional directory where progress, git-status, and summary snapshots will be written.",
    )

    architect_parser = subparsers.add_parser(
        "architect",
        help="Interactively edit project architecture (components, communication, boundaries).",
    )
    architect_parser.add_argument("path", help="Path to generated project directory.")

    design_parser = subparsers.add_parser(
        "design",
        help="Interactively edit project design system (colors, typography, spacing, components).",
    )
    design_parser.add_argument("path", help="Path to generated project directory.")
    design_parser.add_argument("--reference", help=_REFERENCE_HELP)

    args = parser.parse_args()

    if args.command == "new":
        from initializer.flow.new_project import run_new_project

        return run_new_project(
            args.spec,
            assist=args.assist,
            reference=args.reference,
        ) or 0

    elif args.command == "run":
        from initializer.flow.run_project import run_full_pipeline

        return run_full_pipeline(
            spec_path=args.spec,
            assist=args.assist,
            dry_run=args.dry_run,
            skip_ralph=args.no_execute,
            reference=args.reference,
        )

    elif args.command == "plan":
        from initializer.flow.plan_project import run_plan_project

        return run_plan_project(args.spec) or 0

    elif args.command == "enrich":
        from initializer.flow.enrich_project import run_enrich_project

        return run_enrich_project(args.path, review=args.review)

    elif args.command == "prepare":
        from initializer.flow.prepare_project import run_prepare_project

        return run_prepare_project(args.path)

    elif args.command == "refine":
        from initializer.flow.refine_project import run_refine_project

        return run_refine_project(args.path) or 0

    elif args.command == "doctor":
        from initializer.flow.doctor_project import run_doctor_project

        return run_doctor_project(args.path) or 0

    elif args.command == "validate":
        from initializer.flow.validate_project import run_validate_project

        return run_validate_project(args.path)

    elif args.command == "benchmark":
        from initializer.flow.benchmark_project import run_benchmark_project

        return run_benchmark_project(
            args.path,
            candidate=args.candidate,
            output=args.output,
            json_output=args.json_output,
            snapshot_dir=args.snapshot_dir,
        )

    elif args.command == "architect":
        from initializer.flow.architect_flow import run_architect

        return run_architect(args.path)

    elif args.command == "design":
        from initializer.flow.design_flow import run_design

        return run_design(args.path, reference=getattr(args, "reference", None))

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
