"""Waveform generation functions. 波形生成函数。

This submodule provides functions for generating common signal waveforms,
including periodic waves, pulses, and modulated signals.

本子模块提供常见信号波形的生成函数，包括周期波、脉冲和调制信号。

Functions
---------
Periodic waveforms (周期波形):
    square, sawtooth, diric

Pulse waveforms (脉冲波形):
    gauspuls, gmonopuls, rectpuls, tripuls, pulstran

Modulated / special (调制/特殊函数):
    chirp, sinc

Examples
--------
>>> import numpy as np
>>> from pyspt.waveforms import square, chirp, rectpuls
>>> t = np.linspace(0, 2 * np.pi, 500)
>>> y_sq = square(t, duty=30)
>>> y_rect = rectpuls(t - np.pi, width=2.0)
"""

from pyspt.waveforms._modulated import chirp, sinc
from pyspt.waveforms._periodic import diric, sawtooth, square
from pyspt.waveforms._pulses import gauspuls, gmonopuls, pulstran, rectpuls, tripuls

__all__ = [
    # Periodic
    "square",
    "sawtooth",
    "diric",
    # Pulses
    "gauspuls",
    "gmonopuls",
    "rectpuls",
    "tripuls",
    "pulstran",
    # Modulated / special
    "chirp",
    "sinc",
]
