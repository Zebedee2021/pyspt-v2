"""Pulse waveform generation functions. 脉冲波形生成函数。

Provides MATLAB-compatible pulse generators:
gauspuls, gmonopuls, rectpuls, pulstran, tripuls.

提供与 MATLAB 兼容的脉冲波形生成函数。
"""

from __future__ import annotations

from typing import Callable

import numpy as np
from scipy import signal as _signal

__all__ = ["gauspuls", "gmonopuls", "rectpuls", "pulstran", "tripuls"]


def gauspuls(
    t: np.ndarray | float,
    fc: float = 1000.0,
    bw: float = 0.5,
    bwr: float = -6.0,
    retquad: bool = False,
    retenv: bool = False,
) -> np.ndarray | tuple[np.ndarray, ...]:
    """Generate a Gaussian-modulated sinusoidal pulse.

    生成高斯调制正弦脉冲。

    Parameters
    ----------
    t : array_like
        Input time array (in seconds).
        输入时间数组（秒）。
    fc : float, optional
        Center frequency in Hz. Default is 1000.
        中心频率 (Hz)，默认 1000。
    bw : float, optional
        Fractional bandwidth (referenced to *fc*). Default is 0.5.
        相对带宽（相对于 fc），默认 0.5。
    bwr : float, optional
        Reference level at which bandwidth is calculated, in dB.
        Default is -6.
        计算带宽的参考电平 (dB)，默认 -6。
    retquad : bool, optional
        If True, also return the quadrature (imaginary) component.
        若 True，同时返回正交分量。
    retenv : bool, optional
        If True, also return the signal envelope.
        若 True，同时返回信号包络。

    Returns
    -------
    yI : ndarray
        In-phase component (real part).
    yQ : ndarray
        Quadrature component (only if *retquad* is True).
    yE : ndarray
        Envelope (only if *retenv* is True).

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import gauspuls
    >>> t = np.linspace(-1, 1, 200)
    >>> yi = gauspuls(t, fc=5, bw=0.5)

    .. note:: MATLAB equivalent: ``yi = gauspuls(t, fc, bw)``
    """
    t = np.asarray(t, dtype=float)
    return _signal.gausspulse(t, fc=fc, bw=bw, bwr=bwr, retquad=retquad, retenv=retenv)


def gmonopuls(
    t: np.ndarray | float,
    fc: float = 1000.0,
) -> np.ndarray:
    """Generate a unit-amplitude Gaussian monopulse.

    生成单位幅度的高斯单脉冲。

    Implements the closed-form MATLAB convention::

        y(t) = sqrt(e) * 2*pi*fc * t * exp(-2 * (pi*fc*t)^2)

    The peak amplitude is exactly +1 at ``t = +1/(2*pi*fc)`` and -1 at
    ``t = -1/(2*pi*fc)``.

    Parameters
    ----------
    t : array_like
        Input time array (in seconds).
        输入时间数组（秒）。
    fc : float, optional
        Center frequency in Hz. Default is 1000.
        中心频率 (Hz)，默认 1000。

    Returns
    -------
    y : ndarray
        Gaussian monopulse signal, unit-amplitude.

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import gmonopuls
    >>> t = np.linspace(-1e-3, 1e-3, 200)
    >>> y = gmonopuls(t, fc=1000)

    Notes
    -----
    This is the analytic closed form used in MATLAB's Signal Processing
    Toolbox: the Gaussian monopulse is the (suitably scaled) first
    derivative of a Gaussian, with constants chosen so the peak is unity.
    There is no separate normalization step — the formula is already
    normalized.

    本函数采用 MATLAB SPT 的解析形式：高斯单脉冲是高斯函数的（适当缩放后的）
    一阶导数，常数选择使峰值恰为 ±1，无需额外归一化。

    .. note:: MATLAB equivalent: ``y = gmonopuls(t, fc)``
    """
    t = np.asarray(t, dtype=float)
    return np.sqrt(np.e) * 2.0 * np.pi * fc * t * np.exp(-2.0 * (np.pi * fc * t) ** 2)


def rectpuls(
    t: np.ndarray | float,
    width: float = 1.0,
) -> np.ndarray:
    """Generate a sampled aperiodic rectangle pulse.

    生成非周期矩形脉冲。

    Returns 1 on the left-closed, right-open interval ``[-width/2, +width/2)``
    and 0 elsewhere. This matches MATLAB's rectpuls convention exactly,
    including the asymmetric edge handling at ``t = ±width/2``.

    在左闭右开区间 ``[-width/2, +width/2)`` 上返回 1，其余返回 0；
    严格匹配 MATLAB ``rectpuls`` 的非对称边界约定。

    Parameters
    ----------
    t : array_like
        Input time array.
        输入时间数组。
    width : float, optional
        Width of the rectangular pulse. Default is 1.
        矩形脉冲宽度，默认 1。

    Returns
    -------
    y : ndarray
        Rectangular pulse values (0 or 1).

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import rectpuls
    >>> t = np.linspace(-2, 2, 400)
    >>> y = rectpuls(t, width=1.0)

    Notes
    -----
    The asymmetric edge convention (left-closed, right-open) is intentional:
    when stitching pulses at adjacent delays in :func:`pulstran`, it ensures
    a sample at the seam between two pulses is counted exactly once rather
    than receiving contributions from both sides.

    边界采用"左闭右开"——这是有意设计：在 ``pulstran`` 拼接相邻脉冲时，
    位于接缝处的样本恰好被计入一次，避免双重叠加。

    .. note:: MATLAB equivalent: ``y = rectpuls(t, w)``
    """
    t = np.asarray(t, dtype=float)
    half_w = width / 2.0
    return ((t >= -half_w) & (t < half_w)).astype(float)


def tripuls(
    t: np.ndarray | float,
    width: float = 1.0,
    skew: float = 0.0,
) -> np.ndarray:
    """Generate a sampled aperiodic triangle pulse.

    生成非周期三角脉冲。

    Parameters
    ----------
    t : array_like
        Input time array.
        输入时间数组。
    width : float, optional
        Width of the triangle pulse. Default is 1.
        三角脉冲宽度，默认 1。
    skew : float, optional
        Skew factor in [-1, 1]. ``skew=0`` gives a symmetric triangle.
        ``skew=-1`` gives a right-angle triangle tilted left.
        ``skew=1`` gives a right-angle triangle tilted right.
        Default is 0.
        偏斜因子 [-1, 1]。0=对称三角，-1=左倾直角三角，1=右倾直角三角。

    Returns
    -------
    y : ndarray
        Triangle pulse values in [0, 1].

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import tripuls
    >>> t = np.linspace(-1, 1, 400)
    >>> y = tripuls(t, width=1.0, skew=0.0)

    .. note:: MATLAB equivalent: ``y = tripuls(t, w, s)``
    """
    t = np.asarray(t, dtype=float)
    y = np.zeros_like(t)

    if width <= 0:
        return y

    half_w = width / 2.0
    # The peak is at t_peak = skew * half_w
    t_peak = skew * half_w

    # Left side of triangle: from -half_w to t_peak
    left_w = t_peak - (-half_w)  # = t_peak + half_w
    if left_w > 0:
        mask_left = (t >= -half_w) & (t < t_peak)
        y[mask_left] = (t[mask_left] - (-half_w)) / left_w

    # Right side of triangle: from t_peak to half_w
    right_w = half_w - t_peak
    if right_w > 0:
        mask_right = (t >= t_peak) & (t <= half_w)
        y[mask_right] = (half_w - t[mask_right]) / right_w

    # If t == t_peak exactly (and within bounds), peak should be 1
    # This is already handled by both sides meeting at 1 at t_peak
    return y


def pulstran(
    t: np.ndarray | float,
    d: np.ndarray | list | float,
    func: str | Callable = "rectpuls",
    fs: float | None = None,
) -> np.ndarray:
    """Generate a pulse train from a prototype pulse.

    从原型脉冲生成脉冲列。

    Parameters
    ----------
    t : array_like
        Output time array.
        输出时间数组。
    d : array_like
        Delay times for each pulse. Can be a 1-D array of delay times,
        or a 2-D array where column 0 is delay times and column 1 is
        amplitudes.
        每个脉冲的延迟时间。可以是一维延迟数组，或二维数组（第0列为
        延迟时间，第1列为幅度）。
    func : str or callable, optional
        Prototype pulse function. Can be ``'rectpuls'``, ``'tripuls'``,
        ``'gauspuls'``, or a callable ``func(t)`` that returns a pulse.
        Default is ``'rectpuls'``.
        原型脉冲函数。可以是字符串名称或可调用对象，默认 ``'rectpuls'``。
    fs : float, optional
        If *func* is a sample vector, *fs* is the sample rate. Not used
        when *func* is a string or callable.
        采样率（当 func 为采样向量时使用）。

    Returns
    -------
    y : ndarray
        Pulse train signal.

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import pulstran
    >>> t = np.linspace(0, 1, 1000)
    >>> d = np.array([0.1, 0.3, 0.7])
    >>> y = pulstran(t, d, func='rectpuls')

    .. note:: MATLAB equivalent: ``y = pulstran(t, d, func)``
    """
    t = np.asarray(t, dtype=float)
    d = np.atleast_2d(np.asarray(d, dtype=float))

    # If d is 1-D (row vector after atleast_2d), reshape
    if d.shape[0] == 1 and d.ndim == 2 and d.shape[1] > 2:
        # d was a 1-D array of delays
        d = d.T  # Make it a column vector
    if d.ndim == 2 and d.shape[1] == 1:
        # Only delays, no amplitudes
        delays = d[:, 0]
        amps = np.ones_like(delays)
    elif d.ndim == 2 and d.shape[1] >= 2:
        delays = d[:, 0]
        amps = d[:, 1]
    else:
        delays = d.ravel()
        amps = np.ones_like(delays)

    # Resolve built-in pulse functions
    builtin_funcs = {
        "rectpuls": rectpuls,
        "tripuls": tripuls,
        "gauspuls": gauspuls,
    }

    if isinstance(func, str):
        if func not in builtin_funcs:
            raise ValueError(
                f"Unknown pulse function '{func}'. "
                f"Choose from {list(builtin_funcs.keys())} or pass a callable."
            )
        pulse_func = builtin_funcs[func]
    elif callable(func):
        pulse_func = func
    else:
        raise TypeError("func must be a string name or a callable.")

    # Vectorise the delay-dimension via broadcasting:
    #   T[i, j] = t[j] - delays[i]                   shape (N_delays, N_t)
    #   pulse_func(T) evaluates all delays at once    shape (N_delays, N_t)
    #   amplitude-weighted sum along delays           shape (N_t,)
    #
    # This replaces a Python-level loop over delays with one NumPy
    # broadcast operation, which is the dominant performance gain
    # over the previous implementation. Requires pulse_func to
    # broadcast over multidimensional input — every NumPy-based pulse
    # function in this module does so naturally.
    #
    # Memory note: the (N_delays × N_t) intermediate is ~80 KB for the
    # 10-delay × 1k-sample test grids, but grows to ~8 GB for an
    # ECG-scale 1k-pulse × 1M-sample workload. If used with such large
    # inputs, chunking by delays is straightforward to add.
    if delays.size == 0:
        return np.zeros_like(t)

    T = t[None, :] - delays[:, None]
    return (amps[:, None] * pulse_func(T)).sum(axis=0)
