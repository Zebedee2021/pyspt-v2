"""Parity tests for the waveforms module against MATLAB golden fixtures.

These tests load .npz files written by ``scripts/gen_fixtures.py`` and assert
that pyspt's Python implementation matches MATLAB's output to within the
tolerance recorded in each fixture's metadata (default 1e-9).

Design notes
------------

* **Fixture-driven, not function-driven.** We discover fixtures on disk and
  parametrise tests across whichever ones exist. This means the test file
  doesn't need to be edited every time a new fixture is added — just rerun
  ``gen_fixtures.py`` and pytest picks them up.

* **Skip when the Python side isn't implemented yet.** pyspt is a phased
  rollout; some functions referenced in fixtures may not yet have a Python
  counterpart. Missing imports are reported as ``pytest.skip`` rather than
  collection errors, so the suite remains green during incremental work.

* **Per-case Python invocation lives in CASE_RUNNERS.** The MATLAB code in a
  fixture is the source of truth for the *inputs*; here we declare how to
  reproduce that call in Python. This indirection is deliberate — keeps the
  Python invocation explicit and reviewable instead of trying to evaluate
  arbitrary MATLAB strings.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "waveforms"

# Number of timed runs per fixture (after warmup) on the pyspt side.
# Mirrors gen_fixtures.py defaults so MATLAB and pyspt timing samples are
# directly comparable in their statistical structure.
N_TIMING_RUNS = 10
N_WARMUP = 2


# --------------------------------------------------------------------------
# Fixture discovery
# --------------------------------------------------------------------------

def discover_fixtures() -> list[Path]:
    """Return all .npz fixtures under tests/fixtures/waveforms/, sorted."""
    if not FIXTURE_DIR.exists():
        return []
    return sorted(FIXTURE_DIR.glob("*__*.npz"))


def load_fixture(path: Path) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Open a fixture and split data arrays from the JSON metadata blob.

    The ``_meta`` entry is a 0-d object array wrapping a JSON string (see
    ``write_fixture`` in scripts/gen_fixtures.py). We use ``.item()`` to pull
    the underlying Python string out cleanly — ``str(0d_array)`` happens to
    work for plain string contents on most NumPy versions but is fragile
    across versions and dtypes, so don't rely on it.
    """
    raw = np.load(path, allow_pickle=True)
    meta = json.loads(raw["_meta"].item())
    data = {k: raw[k] for k in raw.files if k != "_meta"}
    return data, meta


def fixture_id(path: Path) -> str:
    """Use the filename stem as the pytest test id, e.g. 'square__default'."""
    return path.stem


# --------------------------------------------------------------------------
# Per-case Python "rerun" registry
#
# Each entry maps a fixture stem ("<func>__<case>") to a callable that takes
# the fixture's input arrays and returns the array we want to compare against
# the MATLAB-saved output. Keep these small and obvious — if a "rerun" needs
# more than ~5 lines, the test isn't telling you anything; refactor first.
# --------------------------------------------------------------------------

def _square_default(data):
    from pyspt.waveforms import square
    return square(2 * np.pi * 5 * data["t"])

def _square_duty25(data):
    from pyspt.waveforms import square
    return square(2 * np.pi * 5 * data["t"], duty=25)

def _sawtooth_default(data):
    from pyspt.waveforms import sawtooth
    return sawtooth(2 * np.pi * 5 * data["t"])

def _sawtooth_triangle_via_width(data):
    from pyspt.waveforms import sawtooth
    return sawtooth(2 * np.pi * 5 * data["t"], width=0.5)

def _chirp_linear(data):
    from pyspt.waveforms import chirp
    return chirp(data["t"], 50, 1, 200)

def _chirp_quadratic(data):
    from pyspt.waveforms import chirp
    return chirp(data["t"], 50, 1, 200, method="quadratic")

def _diric_n4_default(data):
    from pyspt.waveforms import diric
    return diric(data["x"], 4)

def _diric_n7_with_limit_points(data):
    from pyspt.waveforms import diric
    return diric(data["x"], 7)

def _gauspuls_default(data):
    from pyspt.waveforms import gauspuls
    return gauspuls(data["t"], 1e3, 0.5)

def _gauspuls_bwr_minus20(data):
    from pyspt.waveforms import gauspuls
    return gauspuls(data["t"], 1e3, 0.5, -20)

def _rectpuls_width_default(data):
    from pyspt.waveforms import rectpuls
    return rectpuls(data["t"])

def _rectpuls_width_05_with_edges(data):
    from pyspt.waveforms import rectpuls
    return rectpuls(data["t"], 0.5)

def _gmonopuls_fc1k(data):
    from pyspt.waveforms import gmonopuls
    return gmonopuls(data["t"], 1000)

def _gmonopuls_fc2g_high_freq(data):
    from pyspt.waveforms import gmonopuls
    return gmonopuls(data["t"], 2e9)

def _tripuls_default_symmetric(data):
    from pyspt.waveforms import tripuls
    return tripuls(data["t"])

def _tripuls_width05_skew_left(data):
    from pyspt.waveforms import tripuls
    return tripuls(data["t"], width=0.5, skew=-0.5)

def _pulstran_rectpuls_train_default(data):
    from pyspt.waveforms import pulstran
    return pulstran(data["t"], data["d"], "rectpuls")

def _pulstran_gauspuls_train_default(data):
    from pyspt.waveforms import pulstran
    return pulstran(data["t"], data["d"], "gauspuls")

def _sinc_default_grid(data):
    from pyspt.waveforms import sinc
    return sinc(data["x"])

def _sinc_exact_zeros_and_origin(data):
    from pyspt.waveforms import sinc
    return sinc(data["x"])


# Map from fixture stem to (runner, name-of-output-key-in-fixture).
# The output-key is whichever variable in the fixture holds the MATLAB result
# you want to compare against (typically "y").
CASE_RUNNERS: dict[str, tuple[Callable[[dict[str, np.ndarray]], np.ndarray], str]] = {
    "square__default":              (_square_default,              "y"),
    "square__duty25":               (_square_duty25,               "y"),
    "sawtooth__default":            (_sawtooth_default,            "y"),
    "sawtooth__triangle_via_width": (_sawtooth_triangle_via_width, "y"),
    "chirp__linear":                (_chirp_linear,                "y"),
    "chirp__quadratic":             (_chirp_quadratic,             "y"),
    "diric__n4_default":            (_diric_n4_default,            "y"),
    "diric__n7_with_limit_points":  (_diric_n7_with_limit_points,  "y"),
    "gauspuls__default":            (_gauspuls_default,            "y"),
    "gauspuls__bwr_minus20":        (_gauspuls_bwr_minus20,        "y"),
    "rectpuls__width_default":      (_rectpuls_width_default,      "y"),
    "rectpuls__width_05_with_edges":(_rectpuls_width_05_with_edges,"y"),
    "gmonopuls__fc1k":              (_gmonopuls_fc1k,              "y"),
    "gmonopuls__fc2g_high_freq":    (_gmonopuls_fc2g_high_freq,    "y"),
    "tripuls__default_symmetric":   (_tripuls_default_symmetric,   "y"),
    "tripuls__width05_skew_left":   (_tripuls_width05_skew_left,   "y"),
    "pulstran__rectpuls_train_default":  (_pulstran_rectpuls_train_default,  "y"),
    "pulstran__gauspuls_train_default":  (_pulstran_gauspuls_train_default,  "y"),
    "sinc__default_grid":           (_sinc_default_grid,           "y"),
    "sinc__exact_zeros_and_origin": (_sinc_exact_zeros_and_origin, "y"),
}


# --------------------------------------------------------------------------
# The actual test
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "fixture_path",
    discover_fixtures(),
    ids=fixture_id,
)
def test_waveform_matches_matlab(fixture_path):
    data, meta = load_fixture(fixture_path)
    stem = fixture_path.stem

    if stem not in CASE_RUNNERS:
        pytest.skip(
            f"No Python runner registered for fixture {stem!r}. "
            f"Add an entry to CASE_RUNNERS in {Path(__file__).name}."
        )

    runner, output_key = CASE_RUNNERS[stem]
    expected = np.asarray(data[output_key]).squeeze()

    try:
        actual = np.asarray(runner(data)).squeeze()
    except ImportError as e:
        pytest.skip(
            f"pyspt does not yet expose the function needed for {stem!r}: {e}"
        )

    assert actual.shape == expected.shape, (
        f"Shape mismatch for {stem}: pyspt={actual.shape} vs MATLAB={expected.shape}"
    )

    tol = float(meta.get("tolerance", 1e-9))
    max_err = float(np.max(np.abs(actual - expected)))
    assert max_err < tol, (
        f"{stem}: max abs error {max_err:.3e} exceeds tolerance {tol:.3e}.\n"
        f"  Generated by MATLAB code:\n    {meta.get('matlab_code', '?')!r}"
    )

    # ----------------------------------------------------------------
    # Timing report (informational, not asserted).
    #
    # If the fixture's _meta carries a MATLAB median time (recorded by
    # gen_fixtures.py at fixture-creation time), measure pyspt's runtime
    # under the same statistical regime (N_WARMUP discarded, then median
    # over N_TIMING_RUNS) and print a one-line "matlab vs pyspt" comparison.
    #
    # We deliberately don't assert on speed: GitHub Actions runners can
    # vary by 2-3× run-to-run, which would make any threshold-based
    # assertion flaky. The report is for humans (or downstream tooling)
    # to consume; performance regressions get caught by trend analysis,
    # not by per-test assertions.
    # ----------------------------------------------------------------
    matlab_us = meta.get("matlab_time_median_us")
    if matlab_us is not None:
        py_samples: list[float] = []
        for i in range(N_WARMUP + N_TIMING_RUNS):
            t0 = time.perf_counter()
            runner(data)
            elapsed = time.perf_counter() - t0
            if i >= N_WARMUP:
                py_samples.append(elapsed)
        py_us = float(np.median(py_samples)) * 1e6
        ratio = py_us / matlab_us
        verdict = "pyspt faster" if ratio < 0.95 else (
            "pyspt slower" if ratio > 1.05 else "≈ same"
        )
        # ``-s`` (or ``--capture=no``) needed on pytest CLI to see this print.
        print(
            f"\n  timing  matlab: {matlab_us:7.1f} us  "
            f"pyspt: {py_us:7.1f} us  ratio: {ratio:5.2f}x  ({verdict})"
        )
