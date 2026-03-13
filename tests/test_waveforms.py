"""Tests for pyspt.waveforms module."""

import numpy as np
import pytest

from pyspt.waveforms import (
    chirp,
    diric,
    gauspuls,
    gmonopuls,
    pulstran,
    rectpuls,
    sawtooth,
    sinc,
    square,
    tripuls,
)


# ---------------------------------------------------------------------------
# square
# ---------------------------------------------------------------------------
class TestSquare:
    def test_basic_50_duty(self):
        t = np.linspace(0, 2 * np.pi, 1000, endpoint=False)
        y = square(t)
        # 50% duty: roughly half +1, half -1
        assert np.sum(y == 1) > 0
        assert np.sum(y == -1) > 0

    def test_values_range(self):
        t = np.linspace(0, 4 * np.pi, 2000, endpoint=False)
        y = square(t, duty=30)
        unique_vals = np.unique(y)
        assert set(unique_vals).issubset({-1.0, 1.0})

    def test_duty_0_all_minus_one(self):
        t = np.linspace(0.01, 2 * np.pi - 0.01, 500)
        y = square(t, duty=0)
        assert np.all(y == -1)

    def test_duty_100_all_plus_one(self):
        t = np.linspace(0.01, 2 * np.pi - 0.01, 500)
        y = square(t, duty=100)
        assert np.all(y == 1)

    def test_scalar_input(self):
        y = square(np.pi / 4)
        assert isinstance(y, (float, np.floating, np.ndarray))


# ---------------------------------------------------------------------------
# sawtooth
# ---------------------------------------------------------------------------
class TestSawtooth:
    def test_rising_sawtooth(self):
        t = np.linspace(0, 2 * np.pi, 1000, endpoint=False)
        y = sawtooth(t, width=1)
        assert y.min() >= -1.0
        assert y.max() <= 1.0

    def test_triangle_wave(self):
        """width=0.5 should produce a symmetric triangle wave."""
        t = np.linspace(0, 2 * np.pi, 1000, endpoint=False)
        y = sawtooth(t, width=0.5)
        # Triangle wave peaks at about t=pi
        peak_idx = np.argmax(y)
        assert 400 < peak_idx < 600  # roughly at midpoint

    def test_output_range(self):
        t = np.linspace(0, 10 * np.pi, 5000)
        y = sawtooth(t)
        assert np.all(y >= -1.0 - 1e-10)
        assert np.all(y <= 1.0 + 1e-10)


# ---------------------------------------------------------------------------
# diric
# ---------------------------------------------------------------------------
class TestDiric:
    def test_at_zero(self):
        """diric(0, n) should be 1 for all n."""
        for n in [3, 5, 7, 10]:
            assert np.isclose(diric(0.0, n), 1.0)

    def test_known_values_odd(self):
        """For odd n, diric(2*pi*k, n) = 1."""
        for n in [3, 5, 7]:
            assert np.isclose(diric(2 * np.pi, n), 1.0)

    def test_output_bounded(self):
        x = np.linspace(-4 * np.pi, 4 * np.pi, 1000)
        y = diric(x, 5)
        assert np.all(np.abs(y) <= 1.0 + 1e-10)


# ---------------------------------------------------------------------------
# gauspuls
# ---------------------------------------------------------------------------
class TestGauspuls:
    def test_peak_at_zero(self):
        t = np.linspace(-1, 1, 1001)
        y = gauspuls(t, fc=5, bw=0.5)
        peak_idx = np.argmax(np.abs(y))
        assert abs(t[peak_idx]) < 0.01  # peak near t=0

    def test_returns_tuple_with_retquad(self):
        t = np.linspace(-1, 1, 100)
        result = gauspuls(t, fc=5, bw=0.5, retquad=True)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_tuple_with_retenv(self):
        t = np.linspace(-1, 1, 100)
        result = gauspuls(t, fc=5, bw=0.5, retenv=True)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_envelope_nonnegative(self):
        t = np.linspace(-1, 1, 200)
        _, env = gauspuls(t, fc=10, bw=0.5, retenv=True)
        assert np.all(env >= -1e-15)


# ---------------------------------------------------------------------------
# gmonopuls
# ---------------------------------------------------------------------------
class TestGmonopuls:
    def test_zero_at_origin(self):
        """Gaussian monopulse should be zero at t=0."""
        y = gmonopuls(0.0, fc=1000)
        assert np.isclose(y, 0.0, atol=1e-10)

    def test_antisymmetric(self):
        """The monopulse should be odd (antisymmetric)."""
        t = np.linspace(-0.5, 0.5, 1001)
        y = gmonopuls(t, fc=5)
        # y(-t) ≈ -y(t)
        y_flip = y[::-1]
        np.testing.assert_allclose(y, -y_flip, atol=1e-10)

    def test_unit_peak(self):
        """Peak amplitude should be approximately 1."""
        t = np.linspace(-1, 1, 10001)
        y = gmonopuls(t, fc=5)
        assert abs(np.max(np.abs(y)) - 1.0) < 0.02


# ---------------------------------------------------------------------------
# rectpuls
# ---------------------------------------------------------------------------
class TestRectpuls:
    def test_unit_rectangle(self):
        t = np.linspace(-2, 2, 4001)
        y = rectpuls(t, width=1.0)
        # Inside: |t| < 0.5 → 1
        inside = t[(np.abs(t) < 0.5) & (np.abs(t) != 0.5)]
        assert np.all(rectpuls(inside, 1.0) == 1.0)

    def test_outside_zero(self):
        t = np.array([-2.0, -1.0, 1.0, 2.0])
        y = rectpuls(t, width=1.0)
        assert np.all(y == 0.0)

    def test_boundary_half(self):
        """At exactly |t| = width/2, value should be 0.5."""
        t = np.array([-0.5, 0.5])
        y = rectpuls(t, width=1.0)
        np.testing.assert_allclose(y, 0.5)

    def test_different_widths(self):
        t = np.array([0.0])
        for w in [0.1, 1.0, 5.0, 100.0]:
            assert rectpuls(t, width=w)[0] == 1.0


# ---------------------------------------------------------------------------
# tripuls
# ---------------------------------------------------------------------------
class TestTripuls:
    def test_symmetric_peak_at_center(self):
        t = np.linspace(-1, 1, 1001)
        y = tripuls(t, width=2.0, skew=0.0)
        peak_idx = np.argmax(y)
        assert abs(t[peak_idx]) < 0.01  # peak at t=0
        assert np.isclose(y[peak_idx], 1.0, atol=0.01)

    def test_outside_zero(self):
        t = np.array([-2.0, 2.0])
        y = tripuls(t, width=1.0)
        np.testing.assert_allclose(y, 0.0)

    def test_skew_left(self):
        """Skew=-1 means peak at t=-width/2 (left edge)."""
        t = np.linspace(-1.5, 1.5, 3001)
        y = tripuls(t, width=2.0, skew=-1.0)
        peak_idx = np.argmax(y)
        # Peak should be at t = skew * half_w = -1.0
        assert abs(t[peak_idx] - (-1.0)) < 0.01

    def test_skew_right(self):
        """Skew=+1 means peak at t=+width/2 (right edge)."""
        t = np.linspace(-1.5, 1.5, 3001)
        y = tripuls(t, width=2.0, skew=1.0)
        peak_idx = np.argmax(y)
        assert abs(t[peak_idx] - 1.0) < 0.01

    def test_zero_width(self):
        t = np.linspace(-1, 1, 100)
        y = tripuls(t, width=0)
        assert np.all(y == 0.0)


# ---------------------------------------------------------------------------
# pulstran
# ---------------------------------------------------------------------------
class TestPulstran:
    def test_single_pulse(self):
        t = np.linspace(-2, 2, 4001)
        d = np.array([0.0])
        y = pulstran(t, d, func="rectpuls")
        expected = rectpuls(t, width=1.0)
        np.testing.assert_allclose(y, expected)

    def test_multiple_delays(self):
        t = np.linspace(-1, 5, 6001)
        d = np.array([0.0, 2.0, 4.0])
        y = pulstran(t, d, func="rectpuls")
        # Should have 3 distinct pulse regions
        assert np.sum(y > 0.5) > 100

    def test_with_amplitudes(self):
        t = np.linspace(-1, 3, 4001)
        d = np.array([[0.0, 1.0], [2.0, 0.5]])
        y = pulstran(t, d, func="rectpuls")
        # First pulse at t=0 with amp=1, second at t=2 with amp=0.5
        assert np.isclose(y[np.argmin(np.abs(t - 0.0))], 1.0)
        assert np.isclose(y[np.argmin(np.abs(t - 2.0))], 0.5)

    def test_callable_func(self):
        t = np.linspace(-1, 3, 4001)
        d = np.array([1.0])
        y = pulstran(t, d, func=lambda t: rectpuls(t, width=0.5))
        # Pulse centered at t=1 with width 0.5
        assert y[np.argmin(np.abs(t - 1.0))] == 1.0

    def test_invalid_func_name(self):
        t = np.linspace(0, 1, 100)
        with pytest.raises(ValueError, match="Unknown pulse function"):
            pulstran(t, [0.0], func="nonexistent")

    def test_invalid_func_type(self):
        t = np.linspace(0, 1, 100)
        with pytest.raises(TypeError):
            pulstran(t, [0.0], func=42)


# ---------------------------------------------------------------------------
# chirp
# ---------------------------------------------------------------------------
class TestChirp:
    def test_output_shape(self):
        t = np.linspace(0, 1, 500)
        y = chirp(t, f0=1, t1=1, f1=100)
        assert y.shape == t.shape

    def test_linear_chirp_bounded(self):
        t = np.linspace(0, 1, 1000)
        y = chirp(t, f0=0, t1=1, f1=50, method="linear")
        assert np.all(np.abs(y) <= 1.0 + 1e-10)

    def test_methods(self):
        t = np.linspace(0, 1, 500)
        for method in ["linear", "quadratic", "logarithmic"]:
            y = chirp(t, f0=1, t1=1, f1=10, method=method)
            assert y.shape == (500,)


# ---------------------------------------------------------------------------
# sinc
# ---------------------------------------------------------------------------
class TestSinc:
    def test_at_zero(self):
        assert np.isclose(sinc(0.0), 1.0)

    def test_at_integers(self):
        """sinc(n) = 0 for nonzero integers."""
        for n in [-3, -2, -1, 1, 2, 3]:
            assert np.isclose(sinc(float(n)), 0.0, atol=1e-15)

    def test_symmetry(self):
        x = np.linspace(0.1, 5, 100)
        np.testing.assert_allclose(sinc(x), sinc(-x))

    def test_array_input(self):
        x = np.array([-1.0, 0.0, 1.0])
        y = sinc(x)
        np.testing.assert_allclose(y, [0.0, 1.0, 0.0], atol=1e-15)


# ---------------------------------------------------------------------------
# Import test
# ---------------------------------------------------------------------------
class TestImports:
    def test_all_functions_importable(self):
        """Verify all functions listed in __all__ are importable."""
        from pyspt import waveforms

        for name in waveforms.__all__:
            assert hasattr(waveforms, name), f"{name} not found in waveforms"
            assert callable(getattr(waveforms, name)), f"{name} is not callable"
