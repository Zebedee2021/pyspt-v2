"""Periodic waveform generation functions. 周期波形生成函数。

Provides MATLAB-compatible periodic waveform generators:
square, sawtooth, diric.

提供与 MATLAB 兼容的周期波形生成函数。
"""

from __future__ import annotations

import numpy as np
from scipy import signal as _signal
from scipy import special as _special

__all__ = ["square", "sawtooth", "diric"]


def square(
    t: np.ndarray | float,
    duty: float = 50.0,
) -> np.ndarray:
    """Generate a periodic square wave.

    生成周期方波信号。

    Parameters
    ----------
    t : array_like
        Input time array (in radians). The period is 2*pi.
        输入时间数组（弧度）。周期为 2*pi。
    duty : float, optional
        Duty cycle in percent (0 ~ 100). Default is 50.
        占空比，百分比 (0~100)，默认 50。

    Returns
    -------
    y : ndarray
        Square wave with values +1 and -1.

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import square
    >>> t = np.linspace(0, 2 * np.pi, 100)
    >>> y = square(t, duty=30)

    .. note:: MATLAB equivalent: ``y = square(t, duty)``
       MATLAB duty is also in percent (0~100).
    """
    t = np.asarray(t, dtype=float)
    # scipy.signal.square expects duty as a fraction [0, 1]
    return _signal.square(t, duty=duty / 100.0)


def sawtooth(
    t: np.ndarray | float,
    width: float = 1.0,
) -> np.ndarray:
    """Generate a periodic sawtooth or triangle wave.

    生成周期锯齿波或三角波信号。

    Parameters
    ----------
    t : array_like
        Input time array (in radians). The period is 2*pi.
        输入时间数组（弧度）。周期为 2*pi。
    width : float, optional
        Determines the shape. ``width=1`` gives a rising sawtooth,
        ``width=0`` gives a falling sawtooth, ``width=0.5`` gives a
        symmetric triangle wave. Default is 1.
        决定波形形状。1=上升锯齿，0=下降锯齿，0.5=对称三角波。默认 1。

    Returns
    -------
    y : ndarray
        Sawtooth wave with values in [-1, 1].

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import sawtooth
    >>> t = np.linspace(0, 4 * np.pi, 200)
    >>> y = sawtooth(t, width=0.5)  # triangle wave

    .. note:: MATLAB equivalent: ``y = sawtooth(t, width)``
    """
    t = np.asarray(t, dtype=float)
    return _signal.sawtooth(t, width=width)


def diric(
    x: np.ndarray | float,
    n: int,
) -> np.ndarray:
    """Compute the Dirichlet (periodic sinc) function.

    计算 Dirichlet 函数（周期 sinc 函数）。

    The Dirichlet function is defined as::

        diric(x, n) = sin(n*x/2) / (n*sin(x/2))

    Parameters
    ----------
    x : array_like
        Input array.
    n : int
        Positive integer defining the function order.
        正整数，定义函数阶数。

    Returns
    -------
    y : ndarray
        Dirichlet function values.

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.waveforms import diric
    >>> x = np.linspace(-2 * np.pi, 2 * np.pi, 200)
    >>> y = diric(x, 7)

    .. note:: MATLAB equivalent: ``y = diric(x, n)``
    """
    x = np.asarray(x, dtype=float)
    return _special.diric(x, n)
