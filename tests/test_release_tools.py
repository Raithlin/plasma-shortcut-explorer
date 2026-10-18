"""Release gates must reject regressions, not just produce a passing percentage."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_release_manifest_uses_public_asset_filenames(tmp_path):
    """GitHub renames leading-dot assets; normalize before calculating checksums."""
    from hashlib import sha256
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    for name in ("source.tar.gz", "app.whl", "app.deb", "app.rpm", "app.pkg.tar.zst", ".SRCINFO"):
        (artifacts / name).write_text(name)
    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    step = workflow.split("- name: Generate checksums\n", 1)[1]
    script = textwrap.dedent(step.split("python3 - <<'PY'\n", 1)[1].split("\n          PY", 1)[0])
    process = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    assert not (artifacts / ".SRCINFO").exists()
    assert (artifacts / "plasma-shortcut-explorer.SRCINFO").exists()
    for line in (artifacts / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert not name.startswith(".")
        assert sha256((artifacts / name).read_bytes()).hexdigest() == digest


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


@pytest.mark.parametrize("state,upload_failure,expected,status", [
    ("missing", False, ["view", "create", "upload", "edit"], 0),
    ("draft", False, ["view", "upload", "edit"], 0),
    ("published", False, ["view"], 1),
    ("missing", True, ["view", "create", "upload"], 17),
])
def test_publication_order_and_recovery(tmp_path, state, upload_failure, expected, status):
    """Exercise real shell control flow with a fake provider, never publish to GitHub."""
    stub = tmp_path / "gh"
    log = tmp_path / "calls.jsonl"
    stub.write_text(f"#!{sys.executable}\n" + '''
import json, os, sys
from pathlib import Path
with open(os.environ['FAKE_GH_LOG'], 'a') as stream:
    stream.write(json.dumps(sys.argv[1:]) + '\\n')
operation = sys.argv[2]
if operation == 'view':
    state = os.environ['FAKE_GH_STATE']
    if state == 'missing':
        sys.exit(1)
    print('true' if state == 'draft' else 'false')
if operation == 'upload' and os.environ['FAKE_GH_FAIL'] == '1':
    sys.exit(17)
''')
    stub.chmod(0o755)
    artifacts = tmp_path / "artifacts with spaces"
    artifacts.mkdir()
    (artifacts / "release.whl").write_bytes(b"test asset")
    env = dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"],
               FAKE_GH_LOG=str(log), FAKE_GH_STATE=state, FAKE_GH_FAIL=str(int(upload_failure)))
    process = subprocess.run(["bash", str(ROOT / "scripts/publish_release.sh"), "v0.1.0", str(artifacts)],
                             env=env, capture_output=True, text=True)
    assert process.returncode == status, process.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert [call[1] for call in calls] == expected
    if "create" in expected:
        assert "--draft" in calls[1] and "--verify-tag" in calls[1]
    if "edit" in expected:
        assert "--draft=false" in calls[-1] and "--latest" in calls[-1]
