import argparse


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

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--spec")

    enrich_parser = subparsers.add_parser("enrich")
    enrich_parser.add_argument("path", help="Path to generated project directory.")
    enrich_parser.add_argument(
        "--review",
        action="store_true",
        help="Also run AI architecture review (requires OPENAI_API_KEY).",
    )

    refine_parser = subparsers.add_parser("refine")
    refine_parser.add_argument("path")

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("path", nargs="?", default=".")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("path", nargs="?", default=".")

    args = parser.parse_args()

    if args.command == "new":
        from initializer.flow.new_project import run_new_project

        return run_new_project(args.spec, assist=args.assist) or 0

    elif args.command == "plan":
        from initializer.flow.plan_project import run_plan_project

        return run_plan_project(args.spec) or 0

    elif args.command == "enrich":
        from initializer.flow.enrich_project import run_enrich_project

        return run_enrich_project(args.path, review=args.review)

    elif args.command == "refine":
        from initializer.flow.refine_project import run_refine_project

        return run_refine_project(args.path) or 0

    elif args.command == "doctor":
        from initializer.flow.doctor_project import run_doctor_project

        return run_doctor_project(args.path) or 0

    elif args.command == "validate":
        from initializer.flow.validate_project import run_validate_project

        return run_validate_project(args.path)

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())