from scipy.signal import detrend as scipy_detrend


def detrend(data, type='linear', bp=0, axis=0, overwrite_data=False):
    """
    Remove the mean or best-fit line from data.
    Wraps scipy.signal.detrend to emulate MATLAB's detrend.
    """
    return scipy_detrend(data, axis=axis, type=type, bp=bp, overwrite_data=overwrite_data)
