import argparse


def main():
    parser = argparse.ArgumentParser(prog="initializer")
    subparsers = parser.add_subparsers(dest="command")

    new_parser = subparsers.add_parser("new")
    new_parser.add_argument("--spec")

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--spec")

    refine_parser = subparsers.add_parser("refine")
    refine_parser.add_argument("path")

    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("path", nargs="?", default=".")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("path", nargs="?", default=".")

    args = parser.parse_args()

    if args.command == "new":
        from initializer.flow.new_project import run_new_project
        return run_new_project(args.spec) or 0

    elif args.command == "plan":
        from initializer.flow.plan_project import run_plan_project
        return run_plan_project(args.spec) or 0

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