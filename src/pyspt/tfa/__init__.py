"""Time-frequency analysis. 时频分析。

This submodule will host MATLAB SPT "时频分析" category (36 functions):

    Transforms:        stft, istft, spectrogram, pspectrum, fsst, ifsst,
                       wvd, xspectrogram, xwvd, kurtogram, ...
    Spectral descriptors: instbw, instfreq, spectralCrest, spectralEntropy,
                       spectralFlatness, spectralKurtosis, spectralSkewness,
                       tfridge
    Data-adaptive:     emd, ewt, hht, vmd
    Wavelet-based:     cqt, cwt, modwpt, modwt, tqwt, waveletScattering,
                       wcoherence, wsst

Status: scheduled for Phase 7, see 00-ROADMAP.md.
Layer-prefixed functions (cwtLayer, stftLayer, etc.) are out of scope
(Deep Learning Toolbox dependency).
"""

__all__: list[str] = []
