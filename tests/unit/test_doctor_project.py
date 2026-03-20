from initializer.flow.doctor_project import run_doctor_project


def _write_healthy_project(root):
    (root / "docs" / "stories").mkdir(parents=True)
    (root / ".codex").mkdir(parents=True)
    (root / ".openclaw").mkdir(parents=True)

    for filename in ("spec.json", "PRD.md", "decisions.md", "progress.txt", "README.md"):
        (root / filename).write_text("{}\n" if filename == "spec.json" else "ok\n", encoding="utf-8")

    (root / ".codex" / "AGENTS.md").write_text("ok\n", encoding="utf-8")
    (root / ".openclaw" / "AGENTS.md").write_text("ok\n", encoding="utf-8")
    (root / ".openclaw" / "execution-plan.json").write_text("{}\n", encoding="utf-8")
    (root / ".openclaw" / "commands.json").write_text("{}\n", encoding="utf-8")


def test_doctor_accepts_current_generated_project_layout(tmp_path, capsys):
    _write_healthy_project(tmp_path)

    exit_code = run_doctor_project(str(tmp_path))
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Doctor result: OK" in output


def test_doctor_reports_missing_bundle_files(tmp_path, capsys):
    _write_healthy_project(tmp_path)
    (tmp_path / ".codex" / "AGENTS.md").unlink()
    (tmp_path / ".openclaw" / "commands.json").unlink()

    exit_code = run_doctor_project(str(tmp_path))
    output = capsys.readouterr().out

    assert exit_code == 1
    assert ".codex/AGENTS.md" in output
    assert ".openclaw/commands.json" in output
    assert "Doctor result: FAIL" in output
