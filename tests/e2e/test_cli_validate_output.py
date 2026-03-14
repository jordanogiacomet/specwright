import subprocess
import sys
from pathlib import Path


def test_cli_validate_passes_for_generated_editorial_output():
    slug = "editorial-e2e-test"
    out_dir = Path("output") / slug

    assert out_dir.exists(), (
        f"Expected generated output at {out_dir}. "
        "Run the CLI new E2E test first."
    )
    assert (out_dir / "spec.json").exists()

    result = subprocess.run(
        [sys.executable, "-m", "initializer", "validate", str(out_dir)],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Checking spec.json" in result.stdout
    assert "✓ spec.json valid" in result.stdout
    assert "Validation OK" in result.stdout