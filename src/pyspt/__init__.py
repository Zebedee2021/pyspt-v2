"""
PySPT - Python Signal Processing Toolbox
Python 信号处理工具箱

A comprehensive signal processing library for Python, designed as a
teaching-friendly alternative to MATLAB's Signal Processing Toolbox.

基于 Python 的信号处理工具箱，参考 MATLAB Signal Processing Toolbox
体系架构设计，适用于教学和科研。

Submodules
----------
waveforms
    Waveform generation (波形生成)
preprocessing
    Signal preprocessing (信号预处理)
measurements
    Measurements and feature extraction (测量和特征提取)
transforms
    Signal transforms (变换)
correlation
    Correlation and convolution (相关性和卷积)
filtering
    Digital and analog filters (数字和模拟滤波器)
spectral
    Spectral analysis (频谱分析)
tfa
    Time-frequency analysis (时频分析) — Phase 7
vibration
    Vibration analysis (振动分析) — Phase 8 (EICPS-aligned)
modulation
    Modulation and quantization (调制和量化) — Phase 2
io
    Data I/O utilities (数据读写)
plotting
    Visualization helpers (可视化辅助)
"""

from pyspt._version import __version__


def about() -> None:
    """Print PySPT version and environment information.

    打印 PySPT 版本及运行环境信息。
    """
    import platform
    import sys

    print(f"PySPT version : {__version__}")
    print(f"Python version: {sys.version}")
    print(f"Platform      : {platform.platform()}")

    # Check core dependencies
    deps = ["numpy", "scipy", "matplotlib"]
    for dep in deps:
        try:
            mod = __import__(dep)
            ver = getattr(mod, "__version__", "unknown")
            print(f"{dep:14s}: {ver}")
        except ImportError:
            print(f"{dep:14s}: NOT INSTALLED")


__all__ = ["__version__", "about"]
