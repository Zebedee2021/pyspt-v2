"""Negative tests for :func:`pyspt._validate.validate_registry`.

These tests synthesise broken parity claims in-memory and confirm
that each breakage produces a clear, actionable error message.
Real fixtures and real test files are NEVER touched — every test
passes ``items`` (and optionally ``repo_root``) into the validator.

Why monkeypatch ``collect_registry``
------------------------------------
The real :func:`validate_registry` calls :func:`collect_registry`
when ``items`` is ``None``, which would import every ``pyspt``
submodule and surface *real* failures. For these tests we want
isolated, predictable inputs, so we always pass ``items`` explicitly.

Why use a tempdir for ``repo_root``
-----------------------------------
The validator reads the on-disk fixtures and parses test files
under ``repo_root``. Using a tempdir means each test owns its own
mini-repo and cannot accidentally pick up stray files.
"""

from __future__ import annotations

from pathlib import Path

from pyspt._meta import ParityInfo
from pyspt._validate import ValidationError, validate_registry

# Reference to a real test module that exists in this repo. We will
# copy it into a tempdir so the validator can parse CASE_RUNNERS out
# of it without depending on test ordering.
REAL_TEST_MODULE = Path(
    "tests/waveforms/test_waveforms_parity.py"
)


def _make_temp_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Build a minimal repo layout under ``tmp_path``.

    Returns ``(repo_root, fixtures_root)`` so tests can drop .npz
    files into ``fixtures_root/waveforms/`` and reference them
    via ``repo_root / <test_path>``.
    """
    fixtures_root = tmp_path / "tests" / "fixtures"
    fixtures_root.mkdir(parents=True)
    return tmp_path, fixtures_root


def _copy_real_test_module(repo_root: Path, target_rel: str) -> Path:
    """Copy the real waveforms parity test module into the temp repo.

    This gives the validator a real ``CASE_RUNNERS`` dict to read
    without having to construct one from scratch.
    """
    target = repo_root / target_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    # Resolve REAL_TEST_MODULE against this test file's directory
    # so the copy works regardless of cwd.
    here = Path(__file__).resolve().parent
    src = (here / ".." / REAL_TEST_MODULE).resolve()
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def _drop_fixture(repo_root: Path, module: str, name: str) -> Path:
    """Create an empty ``.npz`` file at the canonical fixture path."""
    path = repo_root / "tests" / "fixtures" / module / f"{name}.npz"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")  # size/contents irrelevant for existence checks
    return path


# --------------------------------------------------------------------------
# Each of the following tests builds a registry that violates exactly
# one invariant and asserts the validator reports the right error.
# --------------------------------------------------------------------------


def test_empty_fixtures_is_reported(tmp_path: Path) -> None:
    """An empty fixtures list is the most common lie; it must fail."""
    _make_temp_repo(tmp_path)
    items = [
        (
            "pyspt.waveforms.dummy",
            ParityInfo(
                reference="MATLAB R2025b — dummy",
                fixtures=(),  # empty!
                test_path="tests/waveforms/test_waveforms_parity.py",
            ),
        ),
    ]
    errors = validate_registry(items=items, repo_root=tmp_path)
    assert len(errors) == 1
    assert "empty fixtures" in errors[0].message
    assert errors[0].qualname == "pyspt.waveforms.dummy"


def test_invalid_test_path_is_reported(tmp_path: Path) -> None:
    """A test_path that doesn't exist on disk must be flagged."""
    _make_temp_repo(tmp_path)
    items = [
        (
            "pyspt.waveforms.dummy",
            ParityInfo(
                reference="r",
                fixtures=("chirp__linear",),
                test_path="tests/waveforms/no_such_file.py",
            ),
        ),
    ]
    errors = validate_registry(items=items, repo_root=tmp_path)
    assert len(errors) == 1
    assert "does not exist" in errors[0].message
    assert "no_such_file.py" in errors[0].message


def test_none_test_path_is_reported(tmp_path: Path) -> None:
    """Omitting ``test_path`` entirely is just as broken as a bad path."""
    _make_temp_repo(tmp_path)
    items = [
        (
            "pyspt.waveforms.dummy",
            ParityInfo(reference="r", fixtures=("chirp__linear",), test_path=None),
        ),
    ]
    errors = validate_registry(items=items, repo_root=tmp_path)
    assert len(errors) == 1
    assert "test_path is None" in errors[0].message


def test_missing_fixture_file_is_reported(tmp_path: Path) -> None:
    """A fixture that has been deleted from disk must be flagged."""
    _make_temp_repo(tmp_path)
    _copy_real_test_module(tmp_path, "tests/waveforms/test_waveforms_parity.py")
    _drop_fixture(tmp_path, "waveforms", "chirp__linear")  # ok

    items = [
        (
            "pyspt.waveforms.dummy",
            ParityInfo(
                reference="r",
                fixtures=("chirp__linear", "chirp__NOT_HERE"),
                test_path="tests/waveforms/test_waveforms_parity.py",
            ),
        ),
    ]
    errors = validate_registry(items=items, repo_root=tmp_path)
    # We expect two errors: missing fixture + missing runner entry.
    messages = [e.message for e in errors]
    assert any("chirp__NOT_HERE" in m and "not found" in m for m in messages), (
        f"Expected missing-fixture error, got: {errors}"
    )


def test_missing_runner_entry_is_reported(tmp_path: Path) -> None:
    """A fixture that exists but has no CASE_RUNNERS key must be flagged."""
    _make_temp_repo(tmp_path)
    _copy_real_test_module(tmp_path, "tests/waveforms/test_waveforms_parity.py")
    _drop_fixture(tmp_path, "waveforms", "ghost__case")  # fixture on disk
    # But no runner in CASE_RUNNERS for ghost__case.

    items = [
        (
            "pyspt.waveforms.dummy",
            ParityInfo(
                reference="r",
                fixtures=("ghost__case",),
                test_path="tests/waveforms/test_waveforms_parity.py",
            ),
        ),
    ]
    errors = validate_registry(items=items, repo_root=tmp_path)
    assert len(errors) == 1
    assert "CASE_RUNNERS" in errors[0].message
    assert "ghost__case" in errors[0].message


def test_test_module_without_case_runners_is_reported(tmp_path: Path) -> None:
    """If the test file doesn't even define CASE_RUNNERS, fail loudly."""
    _make_temp_repo(tmp_path)
    # Drop a fake test file that has no CASE_RUNNERS.
    fake = tmp_path / "tests" / "waveforms" / "empty_test.py"
    fake.parent.mkdir(parents=True, exist_ok=True)
    fake.write_text("def test_nothing():\n    assert True\n", encoding="utf-8")
    _drop_fixture(tmp_path, "waveforms", "any__case")

    items = [
        (
            "pyspt.waveforms.dummy",
            ParityInfo(
                reference="r",
                fixtures=("any__case",),
                test_path="tests/waveforms/empty_test.py",
            ),
        ),
    ]
    errors = validate_registry(items=items, repo_root=tmp_path)
    assert len(errors) == 1
    assert "no top-level CASE_RUNNERS" in errors[0].message


def test_unknown_module_prefix_is_reported(tmp_path: Path) -> None:
    """A qualname that isn't ``pyspt.<module>.<func>`` cannot be resolved."""
    _make_temp_repo(tmp_path)
    items = [
        (
            "weird.key",  # not pyspt.* format
            ParityInfo(
                reference="r",
                fixtures=("any__case",),
                test_path="tests/waveforms/test_waveforms_parity.py",
            ),
        ),
    ]
    errors = validate_registry(items=items, repo_root=tmp_path)
    assert len(errors) == 1
    assert "does not start with 'pyspt.<module>.'" in errors[0].message


def test_valid_claim_passes(tmp_path: Path) -> None:
    """Sanity: a fully-wired claim in a synthetic repo produces 0 errors."""
    _make_temp_repo(tmp_path)
    _copy_real_test_module(tmp_path, "tests/waveforms/test_waveforms_parity.py")
    _drop_fixture(tmp_path, "waveforms", "chirp__linear")
    _drop_fixture(tmp_path, "waveforms", "chirp__quadratic")

    items = [
        (
            "pyspt.waveforms.dummy",
            ParityInfo(
                reference="r",
                fixtures=("chirp__linear", "chirp__quadratic"),
                test_path="tests/waveforms/test_waveforms_parity.py",
            ),
        ),
    ]
    errors = validate_registry(items=items, repo_root=tmp_path)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_validation_error_str_format() -> None:
    """``ValidationError.__str__`` includes qualname + message."""
    e = ValidationError("pyspt.waveforms.chirp", "fixture missing")
    assert str(e) == "pyspt.waveforms.chirp: fixture missing"
    e2 = ValidationError("", "global problem")
    assert str(e2) == "global problem"
