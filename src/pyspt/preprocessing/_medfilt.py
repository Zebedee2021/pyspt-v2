"""1-D median filtering. 一维中值滤波。

Provides a MATLAB-compatible ``medfilt1`` wrapper around
``scipy.signal.medfilt``.

提供与 MATLAB 兼容的一维中值滤波函数封装。
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage as _ndimage
from scipy import signal as _signal

__all__ = ["medfilt1"]


def medfilt1(
    x: np.ndarray,
    n: int = 3,
    axis: int | None = None,
) -> np.ndarray:
    """Apply a one-dimensional median filter.

    对信号进行一维中值滤波。

    Wraps ``scipy.signal.medfilt`` to emulate MATLAB's ``medfilt1``.
    Useful for smoothing while preserving edges, and especially for
    removing impulsive (spike) noise.

    Parameters
    ----------
    x : array_like
        Input signal.
        输入信号。
    n : int, optional
        Window size (number of samples). Must be a positive odd integer.
        Default is 3. The signal ends are zero-padded, matching MATLAB.
        窗口长度，必须为正奇数。默认 3。信号两端补零，与 MATLAB 一致。
    axis : int, optional
        Axis along which to operate. If ``None`` (default), operates along
        the first non-singleton dimension, matching MATLAB behaviour.
        操作的轴。默认 ``None`` 时沿第一个长度大于 1 的维度操作，
        与 MATLAB 行为一致。

    Returns
    -------
    y : ndarray
        Filtered signal, same shape as ``x``.
        滤波后的信号，形状与输入相同。

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.preprocessing import medfilt1
    >>> t = np.linspace(0, 1, 100)
    >>> x = np.sin(2 * np.pi * 5 * t)
    >>> x[50] += 5.0              # single spike
    >>> y = medfilt1(x, 5)        # spike is removed, sine is preserved

    .. note:: MATLAB equivalent: ``y = medfilt1(x, n)``
       Both zero-pad the signal ends, so outputs match numerically.

    .. warning:: MATLAB also accepts an even ``n`` (window biased toward
       samples before the current point); scipy requires odd ``n``, and
       pyspt therefore supports odd ``n`` only.
    """
    x = np.asarray(x)

    if n < 1:
        raise ValueError(f"n must be a positive integer, got {n!r}")

    if axis is None:
        # Find the first dimension with length > 1 (MATLAB semantics:
        # operations run along the first non-singleton dimension).
        axis = 0
        for i, dim in enumerate(x.shape):
            if dim > 1:
                axis = i
                break

    if x.ndim == 1:
        return _signal.medfilt(x, kernel_size=n)

    # n-D input: filter along one axis only, with zero padding, so the
    # behaviour matches MATLAB's dimension handling. scipy.signal.medfilt
    # cannot do this (it filters along every axis), so we use
    # scipy.ndimage.median_filter with an axis-shaped kernel instead.
    size = [1] * x.ndim
    size[axis] = n
    return _ndimage.median_filter(x, size=size, mode="constant", cval=0.0)
