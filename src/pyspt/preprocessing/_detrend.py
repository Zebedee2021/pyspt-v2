import numpy as np
from scipy.signal import detrend as scipy_detrend


def detrend(data, type='linear', bp=0, axis=None, overwrite_data=False):
    """
    Remove the mean or best-fit line from data.
    Wraps scipy.signal.detrend to emulate MATLAB's detrend.

    If axis is None, it operates along the first non-singleton dimension,
    matching MATLAB's default behavior.
    """
    data = np.asarray(data)

    if axis is None:
        # Find the first dimension with length > 1
        for i, dim in enumerate(data.shape):
            if dim > 1:
                axis = i
                break
        else:
            # Fallback to 0 if all dimensions are length 1 or array is empty/scalar
            axis = 0

    return scipy_detrend(data, axis=axis, type=type, bp=bp, overwrite_data=overwrite_data)
