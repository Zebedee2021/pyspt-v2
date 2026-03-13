"""Modulated waveform and special functions. 调制波形和特殊函数。

Provides MATLAB-compatible wrappers: chirp, sinc.

提供与 MATLAB 兼容的调制波形和特殊函数。
"""

from __future__ import annotations

import numpy as np
from scipy import signal as _signal

__all__ = ["chirp", "sinc"]


def chirp(
    t: np.ndarray | float,
    f0: float,
    t1: float,
    f1: float,
    method: str = "linear",
    phi: float = 0.0,
    vertex_zero: bool = True,
) -> np.ndarray:
    """Generate a frequency-swept cosine (chirp) signal.

    生成频率扫描余弦（啁啾）信号。

    Parameters
    ----------
    t : array_like
        Time array (in seconds).
        时间数组（秒）。
    f0 : float
        Frequency at time ``t=0`` in Hz.
        t=0 时刻的频率 (Hz)。
    t1 : float
        Reference time (in seconds).
        参考时间（秒）。
    f1 : float
        Frequency at time ``t=t1`` in Hz.
        t=t1 时刻的频率 (Hz)。
    method : str, optional
        Sweep method: ``'linear'``, ``'quadratic'``, ``'logarithmic'``,
        or ``'hyperbolic'``. Default is ``'linear'``.
        扫频方法，默认 ``'linear'``。
    phi : float, optional
        Initial phase in degrees. Default is 0.
        初始相位（度），默认 0。
    vertex_zero : bool, optional
        Only used when *method* is ``'quadratic'``. Default is True.

    Returns
    -------
    y : ndarray
        Chirp signal.

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import chirp
    >>> t = np.linspace(0, 1, 1000)
    >>> y = chirp(t, f0=1, t1=1, f1=100)

    .. note:: MATLAB equivalent: ``y = chirp(t, f0, t1, f1, method, phi)``
    """
    t = np.asarray(t, dtype=float)
    return _signal.chirp(
        t, f0=f0, t1=t1, f1=f1, method=method, phi=phi, vertex_zero=vertex_zero
    )


def sinc(
    x: np.ndarray | float,
) -> np.ndarray:
    """Compute the normalized sinc function.

    计算归一化 sinc 函数。

    Defined as ``sinc(x) = sin(pi*x) / (pi*x)`` with ``sinc(0) = 1``.

    This is the *normalized* sinc function used by NumPy and MATLAB.

    Parameters
    ----------
    x : array_like
        Input array.
        输入数组。

    Returns
    -------
    y : ndarray
        Sinc function values.

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import sinc
    >>> x = np.linspace(-5, 5, 200)
    >>> y = sinc(x)

    .. note:: MATLAB equivalent: ``y = sinc(x)``
    """
    x = np.asarray(x, dtype=float)
    return np.sinc(x)
