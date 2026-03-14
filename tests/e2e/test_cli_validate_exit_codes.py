import subprocess
import sys
from pathlib import Path


def test_cli_validate_returns_zero_on_success():
    out_dir = Path("output") / "editorial-e2e-test"
    assert out_dir.exists(), "Run the editorial CLI new E2E test first."

    result = subprocess.run(
        [sys.executable, "-m", "initializer", "validate", str(out_dir)],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Validation OK" in result.stdout


def test_cli_validate_returns_nonzero_on_failure(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "initializer", "validate", str(tmp_path)],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "No known spec artifact found" in result.stdout