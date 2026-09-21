"""Signal preprocessing functions. 信号预处理函数。

Provides MATLAB-compatible preprocessing utilities:
detrend (and, in later phases, smoothdata, resample, ...).

提供与 MATLAB 兼容的信号预处理函数。
"""

from ._detrend import detrend

__all__ = ["detrend"]
