"""scripts/gen_fixtures.py

Generate MATLAB-derived "golden output" fixtures for pyspt-v2 parity tests.

For each (function, input case) pair declared in FIXTURE_SPEC, this script:

  1. Calls MATLAB to execute the reference function on canonical input(s).
  2. Captures the named output variables back into NumPy arrays.
  3. Saves them to ``tests/fixtures/<module>/<func>__<case>.npz`` along with
     a JSON ``_meta`` blob recording the exact MATLAB code that produced them.

The fixtures are then loaded by ``tests/test_*_parity.py`` (one example test
file is shown in the docstring at the bottom of this file) which assert that
pyspt's Python implementation matches MATLAB to within ``FIXTURE_TOL``.

This is the operational backbone of pyspt-v2's "MATLAB-aligned" promise:
every claim of behavioural parity becomes a checked-in artifact that CI
can re-verify on demand, instead of a README assertion no one has tested.

----------------------------------------------------------------------------
Usage
----------------------------------------------------------------------------

    # Regenerate all fixtures (using whichever backend is available)
    python scripts/gen_fixtures.py

    # Regenerate just one or two functions
    python scripts/gen_fixtures.py --funcs square sawtooth

    # Force regeneration even if the .npz already exists
    python scripts/gen_fixtures.py --force

    # Pick the MATLAB driver explicitly:
    python scripts/gen_fixtures.py --backend engine   # matlab.engine, fastest
    python scripts/gen_fixtures.py --backend batch    # `matlab -batch`, no extra deps

----------------------------------------------------------------------------
Backends
----------------------------------------------------------------------------

* ``engine``  Uses the official ``matlab`` Python package (``pip install matlabengine``).
              One persistent MATLAB session is started; subsequent calls are fast.
              Recommended for local development and CI when MATLAB is installed.

* ``batch``   Uses ``matlab -batch`` as a subprocess. No extra Python deps; works
              anywhere ``matlab`` is on PATH. Slower (one MATLAB launch per case)
              but useful as a fallback or in restricted environments.

* ``mcp``     Stub. Designed to be invoked **by Claude** (Claude Code with the
              matlab-agentic-toolkit MCP). When Claude runs this module it can
              swap in a backend that calls ``evaluate_matlab_code``. As a plain
              Python script you'd hit a NotImplementedError; pick engine or batch.

----------------------------------------------------------------------------
Adding a new fixture
----------------------------------------------------------------------------

Append a ``FunctionSpec`` to ``FIXTURE_SPEC`` below. Each ``FixtureCase`` is a
self-contained MATLAB snippet that produces one or more named workspace
variables; list those names in ``capture`` and they become the keys of the
saved .npz.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures"

# Default tolerance recorded in the fixture metadata. Individual parity tests
# may tighten or relax this, but most pyspt parity tests should default to
# 1e-9 — anything looser usually masks a real bug rather than a numerical one.
FIXTURE_TOL = 1e-9

DEFAULT_BACKEND = "engine"

# Timing collection: how many runs per fixture to time, and how many to
# discard up front as JIT / cache warmup. The recorded median + stddev let
# parity tests print a "matlab vs pyspt" speed comparison without re-running
# MATLAB on CI (where MATLAB usually isn't installed).
N_TIMING_RUNS = 10
N_WARMUP = 2


# --------------------------------------------------------------------------
# Spec types
# --------------------------------------------------------------------------

@dataclass
class FixtureCase:
    """One canonical input grid for a MATLAB function.

    Attributes:
        name:         Short identifier appended to the fixture filename.
                      Use lowercase + underscores: "default", "duty25", "edge_n0".
        matlab_code:  MATLAB snippet that, when executed, leaves the variables
                      listed in ``capture`` in the workspace. Make it
                      deterministic — no rng() unless seeded explicitly.
        capture:      Names of MATLAB workspace variables to save into the
                      .npz. They become the keys of np.load(...).
    """
    name: str
    matlab_code: str
    capture: list[str]


@dataclass
class FunctionSpec:
    """Set of fixture cases for one MATLAB SPT function."""
    func: str                    # MATLAB function name (e.g. "square")
    module: str                  # pyspt sub-module (e.g. "waveforms")
    cases: list[FixtureCase]
    notes: str = ""              # optional human-readable behaviour notes


# --------------------------------------------------------------------------
# Fixture spec registry — the heart of this script.
# Add to this list as you progress through Phase 2..8.
# --------------------------------------------------------------------------

FIXTURE_SPEC: list[FunctionSpec] = [

    # ----- Phase 1: waveforms (already implemented in pyspt) -----
    FunctionSpec(
        func="square",
        module="waveforms",
        notes="MATLAB square uses duty in percent (default 50).",
        cases=[
            FixtureCase(
                name="default",
                matlab_code=(
                    "t = linspace(0, 1, 1000);\n"
                    "y = square(2*pi*5*t);\n"
                ),
                capture=["t", "y"],
            ),
            FixtureCase(
                name="duty25",
                matlab_code=(
                    "t = linspace(0, 1, 1000);\n"
                    "y = square(2*pi*5*t, 25);\n"
                ),
                capture=["t", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="sawtooth",
        module="waveforms",
        notes="Width=1 is sawtooth, width=0.5 is triangle.",
        cases=[
            FixtureCase(
                name="default",
                matlab_code=(
                    "t = linspace(0, 1, 1000);\n"
                    "y = sawtooth(2*pi*5*t);\n"
                ),
                capture=["t", "y"],
            ),
            FixtureCase(
                name="triangle_via_width",
                matlab_code=(
                    "t = linspace(0, 1, 1000);\n"
                    "y = sawtooth(2*pi*5*t, 0.5);\n"
                ),
                capture=["t", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="chirp",
        module="waveforms",
        notes="Method options: 'linear' (default), 'quadratic', 'logarithmic'.",
        cases=[
            FixtureCase(
                name="linear",
                matlab_code=(
                    "t = 0:1/1000:2;\n"
                    "y = chirp(t, 50, 1, 200);\n"  # 50 Hz at t=0, 200 Hz at t=1
                ),
                capture=["t", "y"],
            ),
            FixtureCase(
                name="quadratic",
                matlab_code=(
                    "t = 0:1/1000:2;\n"
                    "y = chirp(t, 50, 1, 200, 'quadratic');\n"
                ),
                capture=["t", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="diric",
        module="waveforms",
        notes=(
            "Dirichlet (periodic sinc) function. diric(x, n) is well-defined for "
            "integer n >= 1. Edge cases: x at multiples of 2*pi where the formula "
            "would divide by zero — both MATLAB and a correct port must hit the "
            "limit, so include those points in the grid."
        ),
        cases=[
            FixtureCase(
                name="n4_default",
                matlab_code=(
                    "x = linspace(-2*pi, 2*pi, 1001);\n"
                    "y = diric(x, 4);\n"
                ),
                capture=["x", "y"],
            ),
            FixtureCase(
                name="n7_with_limit_points",
                # Include the singular points x = 0, ±2π so the limit branch is exercised.
                matlab_code=(
                    "x = unique([linspace(-2*pi, 2*pi, 1000), -2*pi, 0, 2*pi]);\n"
                    "y = diric(x, 7);\n"
                ),
                capture=["x", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="gauspuls",
        module="waveforms",
        notes=(
            "Gaussian-modulated sinusoidal pulse. Defaults: fc=1000 Hz, bw=0.5, "
            "bwr=-6 dB. Both 1- and 2-output forms exist in MATLAB; we test the "
            "1-output (yi) form here — extend if pyspt also exposes (yi, yq)."
        ),
        cases=[
            FixtureCase(
                name="default",
                matlab_code=(
                    "t = -1e-3 : 1e-6 : 1e-3;\n"  # 1 µs step, 1 ms span
                    "y = gauspuls(t, 1e3, 0.5);\n"
                ),
                capture=["t", "y"],
            ),
            FixtureCase(
                name="bwr_minus20",
                matlab_code=(
                    "t = -1e-3 : 1e-6 : 1e-3;\n"
                    "y = gauspuls(t, 1e3, 0.5, -20);\n"
                ),
                capture=["t", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="rectpuls",
        module="waveforms",
        notes=(
            "Rectangular pulse rectpuls(t, w): 1 for |t|<w/2, 0 elsewhere. "
            "Edge handling at |t| = w/2 differs across implementations; include "
            "exact-edge points in the grid so any disagreement surfaces."
        ),
        cases=[
            FixtureCase(
                name="width_default",
                matlab_code=(
                    "t = -1 : 0.001 : 1;\n"
                    "y = rectpuls(t);\n"  # default width = 1
                ),
                capture=["t", "y"],
            ),
            FixtureCase(
                name="width_05_with_edges",
                matlab_code=(
                    "t = unique([-1:0.001:1, -0.25, 0.25]);\n"
                    "y = rectpuls(t, 0.5);\n"
                ),
                capture=["t", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="gmonopuls",
        module="waveforms",
        notes=(
            "Gaussian monopulse with center frequency fc. MATLAB has no default "
            "for fc — pyspt defaults to 1000 Hz. We test with explicit fc on both "
            "sides so signature mismatch doesn't hide a numerics bug."
        ),
        cases=[
            FixtureCase(
                name="fc1k",
                matlab_code=(
                    "t = -5e-3 : 1e-6 : 5e-3;\n"
                    "y = gmonopuls(t, 1000);\n"
                ),
                capture=["t", "y"],
            ),
            FixtureCase(
                name="fc2g_high_freq",
                matlab_code=(
                    "t = -1e-9 : 1e-12 : 1e-9;\n"
                    "y = gmonopuls(t, 2e9);\n"
                ),
                capture=["t", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="tripuls",
        module="waveforms",
        notes=(
            "Triangular pulse. pyspt sig: tripuls(t, width=1.0, skew=0.0). "
            "MATLAB: tripuls(t, w, s) where s ∈ [-1, 1] (default 0 = symmetric). "
            "Cover symmetric and skewed cases; include exact apex/edge points."
        ),
        cases=[
            FixtureCase(
                name="default_symmetric",
                matlab_code=(
                    "t = -1 : 0.001 : 1;\n"
                    "y = tripuls(t);\n"
                ),
                capture=["t", "y"],
            ),
            FixtureCase(
                name="width05_skew_left",
                matlab_code=(
                    "t = unique([-1:0.001:1, -0.25, 0, 0.25]);\n"
                    "y = tripuls(t, 0.5, -0.5);\n"
                ),
                capture=["t", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="pulstran",
        module="waveforms",
        notes=(
            "Pulse train: superposes a chosen pulse function at delays d. "
            "NOTE: pyspt's current signature is pulstran(t, d, func, fs=None) "
            "and does NOT forward extra args to the prototype function. MATLAB's "
            "pulstran(t, d, 'rectpuls', W) IS supported there. To keep parity "
            "achievable today, fixtures use only the *default-args* form of the "
            "prototype function. When pyspt grows **kwargs forwarding, add "
            "fixtures like 'rectpuls_width_005_train' that exercise it."
        ),
        cases=[
            FixtureCase(
                name="rectpuls_train_default",
                matlab_code=(
                    "t = -2 : 0.001 : 2;\n"
                    "d = [-1, 0, 1];\n"
                    "y = pulstran(t, d, 'rectpuls');\n"  # default width = 1
                ),
                capture=["t", "d", "y"],
            ),
            FixtureCase(
                name="gauspuls_train_default",
                matlab_code=(
                    "t = -1 : 0.001 : 1;\n"
                    "d = [-0.5, 0, 0.5];\n"
                    "y = pulstran(t, d, 'gauspuls');\n"  # default fc=1000, bw=0.5
                ),
                capture=["t", "d", "y"],
            ),
        ],
    ),

    FunctionSpec(
        func="sinc",
        module="waveforms",
        notes=(
            "Normalized sinc: sin(pi*x)/(pi*x), with limit value 1 at x=0. "
            "Both MATLAB and NumPy use the normalized form, so this is largely "
            "a smoke test for the x=0 limit and the integer-zero structure."
        ),
        cases=[
            FixtureCase(
                name="default_grid",
                matlab_code=(
                    "x = -5 : 0.01 : 5;\n"
                    "y = sinc(x);\n"
                ),
                capture=["x", "y"],
            ),
            FixtureCase(
                name="exact_zeros_and_origin",
                # Force x=0 (limit) and integer x (zeros of sinc) into the grid.
                matlab_code=(
                    "x = unique([linspace(-3, 3, 200), -3, -2, -1, 0, 1, 2, 3]);\n"
                    "y = sinc(x);\n"
                ),
                capture=["x", "y"],
            ),
        ],
    ),

    # ----- Phase 2: preprocessing & measurements ------------------
    # TODO: detrend, findpeaks, snr, thd, rms, peak2peak, etc.
    # FunctionSpec(func="findpeaks", module="measurements", cases=[...]),

    # ----- Phase 3: transforms ------------------------------------
    # CRITICAL: hilbert (Python returns complex; MATLAB also; verify imag part).
    # TODO: fft, dct, hilbert, czt
    # FunctionSpec(func="hilbert", module="transforms", cases=[...]),

    # ----- Phase 4: filtering -------------------------------------
    # CRITICAL: this is the highest-stakes phase. Common parity gotchas:
    #   * butter/cheby1/cheby2/ellip: scipy returns (b, a) by default;
    #     MATLAB returns (b, a) too — but watch the sos vs ba choice.
    #   * filtfilt: MATLAB padlen ~ 3*max(len(a), len(b)); scipy default differs.
    #     Pin padlen explicitly in your wrapper.
    #   * Wn normalization: both use [0, 1] normalized to Nyquist for digital.
    # TODO: butter, cheby1, cheby2, ellip, filter, filtfilt, freqz
    # FunctionSpec(func="filtfilt", module="filtering", cases=[...]),

    # ----- Phase 5: spectral --------------------------------------
    # TODO: periodogram, pwelch, spectrogram, cpsd, mscohere
    # Note: pwelch default windowing differs subtly between MATLAB and SciPy.

    # ----- Phase 6: io --------------------------------------------
    # I/O fixtures are awkward — usually golden output is the file itself.
    # Probably out-of-scope for this generator; handle separately.
]


# --------------------------------------------------------------------------
# Backends
# --------------------------------------------------------------------------

class MatlabBackend:
    """Abstract base. Subclasses execute a MATLAB snippet and return the
    requested workspace variables as a dict[str, np.ndarray]."""

    def run(self, matlab_code: str, capture: list[str]) -> dict[str, np.ndarray]:
        raise NotImplementedError

    def time_only(self, matlab_code: str) -> float | None:
        """Run ``matlab_code`` and return its execution time in seconds,
        excluding any Python↔MATLAB IPC overhead.

        Implementations should use MATLAB's own ``tic``/``toc`` (or the
        equivalent in their backend) so the recorded time reflects MATLAB's
        cost in isolation, not the round-trip from Python. Return ``None``
        to signal that timing is unsupported in this backend (e.g. the batch
        backend, where each call is dominated by MATLAB's ~10 s startup).
        """
        return None

    def close(self) -> None:
        pass


class EngineBackend(MatlabBackend):
    """matlab.engine — fastest, requires `pip install matlabengine`."""

    def __init__(self):
        try:
            import matlab.engine  # type: ignore
        except ImportError as e:
            raise SystemExit(
                "matlab.engine is not installed.\n"
                "Either run:  pip install matlabengine\n"
                "or use:      python scripts/gen_fixtures.py --backend batch"
            ) from e
        print("Starting MATLAB engine (this takes ~10 s)…")
        self.eng = matlab.engine.start_matlab()

    def run(self, matlab_code: str, capture: list[str]) -> dict[str, np.ndarray]:
        # Run the snippet inside the persistent engine. ``evalc`` returns the
        # captured stdout as a string; we discard it and pull variables from
        # workspace afterwards.
        self.eng.evalc(matlab_code, nargout=0)
        out: dict[str, np.ndarray] = {}
        for name in capture:
            val = self.eng.workspace[name]
            out[name] = np.asarray(val).squeeze()
        return out

    def time_only(self, matlab_code: str) -> float:
        """Time MATLAB execution using its own ``tic``/``toc``.

        Wraps the snippet so the elapsed time is measured *inside* MATLAB —
        Python only sees one ``evalc`` round-trip but reads back the
        MATLAB-clocked elapsed value. This avoids contaminating fast
        functions (~50 µs) with the millisecond-scale Python↔MATLAB IPC
        overhead.

        Variable naming gotcha: MATLAB rejects identifiers that start with
        an underscore (the parser only accepts ``letter | letter digit_``).
        We use the ``pyspt_t_*`` prefix instead of the Python-idiomatic
        ``_t_*`` so the wrapped script parses cleanly under MATLAB's rules.
        The prefix also makes accidental name collisions with user code
        practically impossible.
        """
        timing_code = (
            "pyspt_t_start_ = tic;\n"
            f"{matlab_code}\n"
            "pyspt_t_elapsed_ = toc(pyspt_t_start_);\n"
        )
        self.eng.evalc(timing_code, nargout=0)
        return float(self.eng.workspace["pyspt_t_elapsed_"])

    def close(self) -> None:
        self.eng.quit()


class BatchBackend(MatlabBackend):
    """`matlab -batch` subprocess — no extra Python deps, slower."""

    def __init__(self):
        # Verify matlab is on PATH so we fail early with a clear message.
        try:
            subprocess.run(
                ["matlab", "-batch", "disp('ok')"],
                check=True, capture_output=True, text=True, timeout=60,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            raise SystemExit(
                "Could not invoke `matlab -batch`. Make sure MATLAB is "
                "installed and `matlab` is on PATH (or use --backend engine "
                "if you have matlab.engine installed)."
            ) from e

    def run(self, matlab_code: str, capture: list[str]) -> dict[str, np.ndarray]:
        from scipy.io import loadmat  # local import: optional dep
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            mat_file = tmp_path / "out.mat"
            script_file = tmp_path / "run.m"

            save_args = ", ".join(f"'{n}'" for n in capture)
            script_file.write_text(
                f"{matlab_code}\n"
                f"save('{mat_file.as_posix()}', {save_args}, '-v7');\n"
            )

            subprocess.run(
                ["matlab", "-batch", f"run('{script_file.as_posix()}')"],
                check=True, capture_output=True, text=True,
            )

            data = loadmat(str(mat_file))
            return {n: np.asarray(data[n]).squeeze() for n in capture}


class McpBackend(MatlabBackend):
    """Stub for the matlab-agentic-toolkit MCP path.

    When Claude Code is driving this script via the MCP, it should patch
    or subclass this method to call ``evaluate_matlab_code`` instead. Plain
    Python invocation can't reach the MCP, so we raise a helpful error.
    """

    def run(self, matlab_code: str, capture: list[str]) -> dict[str, np.ndarray]:
        raise NotImplementedError(
            "The 'mcp' backend is intended to be driven by Claude Code with "
            "the matlab-agentic-toolkit MCP loaded. Have Claude call "
            "evaluate_matlab_code(matlab_code) for each spec and write the "
            "fixture files itself, or run this script with --backend engine "
            "or --backend batch."
        )


def make_backend(name: str) -> MatlabBackend:
    if name == "engine":
        return EngineBackend()
    if name == "batch":
        return BatchBackend()
    if name == "mcp":
        return McpBackend()
    raise ValueError(f"Unknown backend: {name!r}")


# --------------------------------------------------------------------------
# Fixture I/O
# --------------------------------------------------------------------------

def fixture_path(spec: FunctionSpec, case: FixtureCase) -> Path:
    return FIXTURE_DIR / spec.module / f"{spec.func}__{case.name}.npz"


def write_fixture(path: Path, data: dict[str, np.ndarray], meta: dict[str, Any]) -> None:
    """Save the captured arrays plus a JSON metadata blob.

    The metadata is serialised to a single string and stored under the key
    ``_meta`` so that ``np.load(path, allow_pickle=True)['_meta'].item()``
    yields the original dict. This keeps fixtures introspectable without
    requiring a sidecar .json file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        _meta=np.array(json.dumps(meta), dtype=object),
        **data,
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate MATLAB-golden fixtures for pyspt-v2 parity tests.",
    )
    p.add_argument(
        "--funcs", nargs="*", default=None,
        help="Restrict to these MATLAB function names (default: all).",
    )
    p.add_argument(
        "--backend", choices=["engine", "batch", "mcp"],
        default=DEFAULT_BACKEND,
        help=f"Which MATLAB driver to use (default: {DEFAULT_BACKEND}).",
    )
    p.add_argument(
        "--force", action="store_true",
        help="Regenerate fixtures even if they already exist.",
    )
    p.add_argument(
        "--no-timing", action="store_true",
        help="Skip per-case MATLAB timing collection (faster regen, but "
             "fixtures won't carry matlab_time_median_us in their _meta).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    backend = make_backend(args.backend)

    n_written = 0
    n_skipped = 0
    n_failed = 0

    try:
        for spec in FIXTURE_SPEC:
            if args.funcs and spec.func not in args.funcs:
                continue

            print(f"\n=== {spec.func}  ({spec.module}, {len(spec.cases)} case(s)) ===")
            if spec.notes:
                print(f"    note: {spec.notes}")

            for case in spec.cases:
                path = fixture_path(spec, case)
                if path.exists() and not args.force:
                    print(f"  skip  {case.name:20s}  (exists; use --force to regen)")
                    n_skipped += 1
                    continue

                try:
                    data = backend.run(case.matlab_code, case.capture)
                except Exception as e:  # broad: report and move on
                    print(f"  FAIL  {case.name:20s}  {type(e).__name__}: {e}")
                    n_failed += 1
                    continue

                # Optional MATLAB timing collection. The first ``backend.run``
                # call above doubles as the first warmup pass; we then run the
                # snippet N_WARMUP + N_TIMING_RUNS more times via tic/toc and
                # keep only the last N_TIMING_RUNS samples. Median + stddev go
                # into _meta so parity tests (and CI) can compare against
                # pyspt's runtime without re-spawning MATLAB.
                timing_samples: list[float] = []
                if not args.no_timing:
                    for i in range(N_WARMUP + N_TIMING_RUNS):
                        elapsed = backend.time_only(case.matlab_code)
                        if elapsed is None:
                            # Backend doesn't support per-call timing — drop it.
                            timing_samples = []
                            break
                        if i >= N_WARMUP:
                            timing_samples.append(elapsed)

                meta = {
                    "matlab_function": spec.func,
                    "module": spec.module,
                    "case": case.name,
                    "matlab_code": case.matlab_code,
                    "tolerance": FIXTURE_TOL,
                    "captured": list(data.keys()),
                }
                if timing_samples:
                    meta["matlab_time_median_us"] = float(np.median(timing_samples)) * 1e6
                    meta["matlab_time_stddev_us"] = float(np.std(timing_samples)) * 1e6
                    meta["matlab_time_n_runs"] = len(timing_samples)

                write_fixture(path, data, meta)
                rel = path.relative_to(REPO_ROOT)
                if timing_samples:
                    t_med = meta["matlab_time_median_us"]
                    print(f"  ok    {case.name:20s}  -> {rel}  [matlab: {t_med:7.1f} us]")
                else:
                    print(f"  ok    {case.name:20s}  -> {rel}")
                n_written += 1

        print(
            f"\nDone. {n_written} written, {n_skipped} skipped, {n_failed} failed."
        )
        return 0 if n_failed == 0 else 1
    finally:
        backend.close()


if __name__ == "__main__":
    sys.exit(main())


# --------------------------------------------------------------------------
# Reference: a minimal parity test that consumes the fixtures above.
# Save this as tests/waveforms/test_square_parity.py (or similar).
# --------------------------------------------------------------------------
# import json
# from pathlib import Path
# import numpy as np
# import pytest
# from pyspt.waveforms import square
#
# FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "waveforms"
#
# @pytest.mark.parametrize("case", ["default", "duty25"])
# def test_square_matches_matlab(case):
#     data = np.load(FIXTURES / f"square__{case}.npz", allow_pickle=True)
#     meta = json.loads(str(data["_meta"]))
#     t = data["t"]
#     y_matlab = data["y"]
#
#     # Reproduce the MATLAB call in pyspt
#     if case == "default":
#         y_py = square(2 * np.pi * 5 * t)
#     elif case == "duty25":
#         y_py = square(2 * np.pi * 5 * t, duty=25)
#
#     assert np.max(np.abs(y_py - y_matlab)) < meta["tolerance"]
