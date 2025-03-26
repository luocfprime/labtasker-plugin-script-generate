import difflib
import shutil
from pathlib import Path
from typing import Tuple

import pytest
from labtasker_plugin_script_generate.main import app
from typer.testing import CliRunner

runner = CliRunner()


def compare_files(file1: Path, file2: Path) -> Tuple[bool, str]:
    """Compare two files with detailed diff output."""
    with open(file1) as f1, open(file2) as f2:
        lines1 = [line.rstrip() + "\n" for line in f1.readlines()]
        lines2 = [line.rstrip() + "\n" for line in f2.readlines()]

    if lines1 == lines2:
        return True, ""

    diff = difflib.unified_diff(
        lines1, lines2, fromfile=str(file1), tofile=str(file2), lineterm=""
    )
    return False, "\n".join(diff)


@pytest.fixture
def test_dir(tmp_path):
    scripts_dir = Path(__file__).parent / "scripts"
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    # Copy test script to temp directory
    shutil.copy(scripts_dir / "original.sh", test_dir / "original.sh")

    return test_dir


def test_script_generation(test_dir):
    input_script = test_dir / "original.sh"
    expected_submit = Path(__file__).parent / "scripts" / "original_submit.sh"
    expected_run = Path(__file__).parent / "scripts" / "original_run.sh"

    result = runner.invoke(app, ["generate", str(input_script)])
    assert result.exit_code == 0, f"Command failed with output:\n{result.output}"

    # Check if output files were created
    submit_output = test_dir / "original_submit.sh"
    run_output = test_dir / "original_run.sh"
    assert submit_output.exists(), "Submit script was not created"
    assert run_output.exists(), "Run script was not created"

    # Compare submit script
    submit_match, submit_diff = compare_files(submit_output, expected_submit)
    assert submit_match, f"Submit script differs:\n{submit_diff}"

    # Compare run script
    run_match, run_diff = compare_files(run_output, expected_run)
    assert run_match, f"Run script differs:\n{run_diff}"
