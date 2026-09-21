"""Signal detrending. 信号去趋势。

Provides a MATLAB-compatible ``detrend`` wrapper around
``scipy.signal.detrend``.

提供与 MATLAB 兼容的去趋势函数封装。
"""

from __future__ import annotations

import numpy as np
from scipy.signal import detrend as scipy_detrend

__all__ = ["detrend"]


def detrend(
    data: np.ndarray,
    type: str = "linear",
    bp: int | list[int] | np.ndarray = 0,
    axis: int | None = None,
    overwrite_data: bool = False,
) -> np.ndarray:
    """Remove the mean or best-fit line from data.

    去除数据的均值或最佳拟合直线（去趋势）。

    Wraps ``scipy.signal.detrend`` to emulate MATLAB's ``detrend``.

    Parameters
    ----------
    data : array_like
        Input signal.
        输入信号。
    type : {'linear', 'constant'}, optional
        ``'linear'`` removes a best-fit line (MATLAB default);
        ``'constant'`` removes the mean. Default is ``'linear'``.
        ``'linear'`` 去除最佳拟合直线（MATLAB 默认）；``'constant'`` 去除均值。
        默认 ``'linear'``。
    bp : int or sequence of int, optional
        Breakpoint indices where the fit restarts, enabling piecewise
        linear detrending. Default is 0 (no breakpoints).
        拟合重启的断点索引，用于分段线性去趋势。默认 0（无断点）。
    axis : int, optional
        Axis along which to operate. If ``None`` (default), operates along
        the first non-singleton dimension, matching MATLAB behaviour.
        操作的轴。默认 ``None`` 时沿第一个长度大于 1 的维度操作，
        与 MATLAB 行为一致。
    overwrite_data : bool, optional
        If True, perform the computation in-place. Default is False.
        若为 True 则原地计算。默认 False。

    Returns
    -------
    y : ndarray
        Detrended signal, same shape as ``data``.
        去趋势后的信号，形状与输入相同。

    Examples
    --------
    >>> import numpy as np
    >>> from pyspt.preprocessing import detrend
    >>> t = np.linspace(0, 1, 100)
    >>> x = 3 * t + 5 + 0.1 * np.sin(2 * np.pi * 10 * t)
    >>> y = detrend(x)                 # remove best-fit line
    >>> y = detrend(x, type='constant')  # remove mean only

    .. note:: MATLAB equivalent: ``y = detrend(x)`` / ``y = detrend(x, 'constant')``
       MATLAB also accepts a numeric ``bp`` vector for piecewise linear
       detrending, which maps directly to the ``bp`` parameter here.

    .. warning:: MATLAB does not expose ``axis``/``overwrite_data``; MATLAB
       always operates along the first non-singleton dimension. The default
       ``axis=None`` reproduces that behaviour for 2D inputs.
    """
    data = np.asarray(data)

    if axis is None:
        # Find the first dimension with length > 1 (MATLAB semantics:
        # operations run along the first non-singleton dimension).
        for i, dim in enumerate(data.shape):
            if dim > 1:
                axis = i
                break
        else:
            # Fallback to 0 if all dimensions are length 1 or array is
            # empty/scalar.
            axis = 0

    return scipy_detrend(
        data, axis=axis, type=type, bp=bp, overwrite_data=overwrite_data
    )
