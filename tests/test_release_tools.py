"""Release gates must reject regressions, not just produce a passing percentage."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("lines,branches,status", [(95, 95, 0), (100, 94, 1), (94, 100, 1)])
def test_coverage_thresholds_are_independent(tmp_path, lines, branches, status):
    report = tmp_path / "coverage.json"
    report.write_text(json.dumps({"totals": {"covered_lines": lines, "num_statements": 100,
        "covered_branches": branches, "num_branches": 100}}))
    process = subprocess.run([sys.executable, str(ROOT / "scripts/check_coverage.py"), str(report)],
                             capture_output=True, text=True)
    assert process.returncode == status, process.stderr


def test_release_tag_must_match_project_version():
    process = subprocess.run([sys.executable, str(ROOT / "scripts/validate_release.py"),
                              "--tag", "v999.0.0"], capture_output=True, text=True)
    assert process.returncode != 0
    assert "Tag must be" in process.stderr
