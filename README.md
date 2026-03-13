<p align="center">
  <strong>PySPT</strong><br>
  <em>Python Signal Processing Toolbox</em>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9%2B-blue.svg" alt="Python 3.9+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
  <a href="https://numpy.org"><img src="https://img.shields.io/badge/numpy-%E2%89%A51.22-orange.svg" alt="NumPy"></a>
  <a href="https://scipy.org"><img src="https://img.shields.io/badge/scipy-%E2%89%A51.9-orange.svg" alt="SciPy"></a>
</p>

---

**PySPT** (Python Signal Processing Toolbox) 是一个面向教学与科研的信号处理 Python 库，参考 MATLAB Signal Processing Toolbox 体系架构设计，提供与 MATLAB 函数对应的 Python 实现。

**PySPT** is a teaching-oriented signal processing library for Python, modeled after MATLAB's Signal Processing Toolbox. It provides Python implementations that correspond to MATLAB functions, making it easy for students and researchers to transition between the two environments.

## 特性 | Features

- **MATLAB 函数命名对齐** -- 函数名、参数名尽量与 MATLAB Signal Processing Toolbox 保持一致，降低迁移成本
- **双语文档** -- 所有函数均提供中英文 docstring，适合中文教学环境
- **类型注解完整** -- 全部公开 API 附带 Python type hints，IDE 友好
- **轻量依赖** -- 仅依赖 NumPy、SciPy、Matplotlib 三个核心科学计算库
- **现代工程规范** -- src layout、pyproject.toml、ruff lint、pytest 测试、CI/CD

## 安装 | Installation

### 开发安装（推荐）

```bash
git clone https://github.com/Zebedee2021/pyspt-v2.git
cd pyspt-v2
pip install -e ".[dev]"
```

### 最小安装

```bash
pip install -e .
```

### 可选依赖组

| 依赖组 | 命令 | 说明 |
|--------|------|------|
| `dev` | `pip install -e ".[dev]"` | pytest, ruff 等开发工具 |
| `docs` | `pip install -e ".[docs]"` | Sphinx 文档构建 |
| `full` | `pip install -e ".[full]"` | ruptures, pandas 等扩展功能 |
| `tutorials` | `pip install -e ".[tutorials]"` | JupyterLab 交互教程 |

## 快速上手 | Quick Start

```python
import numpy as np
import matplotlib.pyplot as plt
from pyspt.waveforms import square, chirp, gauspuls

# 生成时间轴
t = np.linspace(0, 1, 1000)

# 方波 (占空比 30%)
y_sq = square(2 * np.pi * 5 * t, duty=30)

# 线性调频信号 (1 Hz → 50 Hz)
y_chirp = chirp(t, f0=1, t1=1, f1=50)

# 高斯脉冲 (中心频率 100 Hz)
t2 = np.linspace(-0.5, 0.5, 1000)
y_gp = gauspuls(t2, fc=100, bw=0.5)

# 绘图
fig, axes = plt.subplots(3, 1, figsize=(10, 6))
axes[0].plot(t, y_sq);   axes[0].set_title("Square Wave (duty=30%)")
axes[1].plot(t, y_chirp); axes[1].set_title("Chirp (1→50 Hz)")
axes[2].plot(t2, y_gp);   axes[2].set_title("Gaussian Pulse (fc=100 Hz)")
plt.tight_layout()
plt.show()
```

## 模块总览 | Module Overview

| 子模块 | 说明 | 状态 |
|--------|------|------|
| `pyspt.waveforms` | 波形生成 -- square, sawtooth, chirp, gauspuls 等 | **已完成** |
| `pyspt.preprocessing` | 信号预处理 -- 去趋势、归一化、重采样 | 开发中 |
| `pyspt.measurements` | 测量与特征提取 -- 峰值检测、SNR、THD | 开发中 |
| `pyspt.transforms` | 信号变换 -- FFT、DCT、Hilbert、CZT | 开发中 |
| `pyspt.correlation` | 相关与卷积 -- xcorr, conv, aligned | 开发中 |
| `pyspt.filtering` | 数字/模拟滤波器 -- butter, cheby1, filtfilt | 开发中 |
| `pyspt.spectral` | 频谱分析 -- periodogram, spectrogram, pwelch | 开发中 |
| `pyspt.io` | 数据读写 -- WAV, CSV, MAT 文件支持 | 开发中 |
| `pyspt.plotting` | 可视化辅助 -- 频谱图、信号对比绘图 | 开发中 |

### waveforms 模块已实现函数

| 类别 | 函数 | 对应 MATLAB 函数 |
|------|------|-----------------|
| 周期波形 | `square(t, duty)` | `square` |
| | `sawtooth(t, width)` | `sawtooth` |
| | `diric(x, n)` | `diric` |
| 脉冲波形 | `gauspuls(t, fc, bw, ...)` | `gauspuls` |
| | `gmonopuls(t, fc)` | `gmonopuls` |
| | `rectpuls(t, width)` | `rectpuls` |
| | `tripuls(t, width, skew)` | `tripuls` |
| | `pulstran(t, d, func, ...)` | `pulstran` |
| 调制/特殊 | `chirp(t, f0, t1, f1, ...)` | `chirp` |
| | `sinc(x)` | `sinc` |

## MATLAB 兼容性说明

PySPT 在设计上尽量对齐 MATLAB 的调用习惯，但也遵循 Python 社区的惯例：

| 差异项 | MATLAB | PySPT | 说明 |
|--------|--------|-------|------|
| 占空比 | `duty` 取 0~1 | `duty` 取 0~100 | 百分比更直观，与 MATLAB `square` 行为一致 |
| sinc 定义 | `sin(πx)/(πx)` | `sin(πx)/(πx)` | 归一化 sinc（与 NumPy 一致） |
| 索引 | 1-based | 0-based | Python 标准 |
| 返回类型 | MATLAB matrix | `numpy.ndarray` | Python 标准 |

## 项目来源 | Origin

本项目是 [spaitlab/pyspt](https://github.com/spaitlab/pyspt) 的 v2 重构版本。原始仓库包含 157 个 Jupyter 教学笔记本和 54 个分散的 Python 脚本，v2 版将这些功能整合为标准的可安装 Python 包。

## 开发路线 | Roadmap

- [x] **Phase 0** -- 项目脚手架（pyproject.toml, src layout, CI 配置）
- [x] **Phase 1** -- waveforms 模块（10 个波形生成函数，41 项测试）
- [ ] **Phase 2** -- preprocessing + measurements 模块
- [ ] **Phase 3** -- transforms + correlation 模块
- [ ] **Phase 4** -- filtering 模块
- [ ] **Phase 5** -- spectral 模块
- [ ] **Phase 6** -- io + plotting 模块
- [ ] **Phase 7** -- 文档站点 + 教学笔记本更新
- [ ] **Phase 8** -- PyPI 发布 + 质量保证

## 运行测试 | Testing

```bash
# 运行全部测试
pytest

# 带覆盖率
pytest --cov=pyspt --cov-report=term-missing

# 代码风格检查
ruff check src/ tests/
```

## 项目结构 | Project Structure

```
pyspt-v2/
├── src/pyspt/              # 源代码
│   ├── __init__.py
│   ├── _version.py
│   ├── waveforms/          # 波形生成 ✅
│   ├── preprocessing/      # 信号预处理
│   ├── measurements/       # 测量与特征提取
│   ├── transforms/         # 信号变换
│   ├── correlation/        # 相关与卷积
│   ├── filtering/          # 滤波器设计
│   ├── spectral/           # 频谱分析
│   ├── io/                 # 数据读写
│   └── plotting/           # 可视化
├── tests/                  # 测试用例
├── tutorials/              # Jupyter 教学笔记本
├── courseware/              # 配套教材资料
├── docs/                   # 文档源文件
├── pyproject.toml          # 项目配置
└── LICENSE                 # MIT 许可证
```

## 引用 | Citation

如果 PySPT 对你的教学或研究有帮助，欢迎引用：

```bibtex
@software{pyspt2024,
  author    = {Zhiguo Zhou},
  title     = {PySPT: Python Signal Processing Toolbox},
  year      = {2024},
  publisher = {GitHub},
  url       = {https://github.com/Zebedee2021/pyspt-v2}
}
```

## 许可证 | License

本项目采用 [MIT License](LICENSE) 开源。

Copyright (c) 2022-2026 Zhiguo Zhou, Beijing Institute of Technology
