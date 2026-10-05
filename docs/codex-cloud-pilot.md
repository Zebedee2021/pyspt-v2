# PySPT Codex Cloud 最小环境试点

核对日期：2026-10-05。测试基线：`dcd0ae8ece30f2a516484d6221f7e022f6a2f1c5`。

## 当前完成状态

在本次会话的 Linux 执行容器中，创建独立 `.venv`，按仓库原有
`pip install -e ".[dev]"` 安装依赖并运行现有检查：

| 检查 | 结果 |
|---|---|
| Python | 3.12.14，与现有 CI 的 3.12 分支一致 |
| dev 依赖安装 | 成功 |
| `python -m pip check` | No broken requirements found |
| CI 的 pytest 命令 | 73 passed，1.54 s，总覆盖率 86% |
| README 的 `ruff check src/ tests/` | All checks passed |

主要版本：NumPy 2.5.3、SciPy 1.18.1、Matplotlib 3.11.2、pytest 9.1.1、
pytest-cov 7.1.0、Ruff 0.16.10。此处记录一次安装结果，不新增锁文件，
依赖要求仍以 `pyproject.toml` 为准。现有 GitHub Actions 运行 pytest，
并未执行 Ruff；本次额外按 README 执行 Ruff。

上述结果证明 Python 开发流程可在独立 Linux 容器执行。
账户内的可复用 Codex Cloud 环境尚未创建、发布或验证；
跨设备继续同一任务也尚未实测。不能将本次会话容器当成已发布的环境。

## 当前官方配置方式

当前指南：<https://learn.chatgpt.com/docs/environments/cloud-environments>。
旧的 <https://developers.openai.com/codex/cloud/environments> 已重定向至
Codex Cloud (Legacy)，不要把旧版 setup/maintenance/cache 说明套用于当前环境。

1. 网页或桌面端：新任务 → Work in → Cloud → Select environment → Create environment。
   也可进入 Settings → Codex Cloud → Environments → Create environment。
2. 只选择 `Zebedee2021/pyspt-v2`，建议命名 `pyspt-v2-dev`，保留 Only me。
3. Get started 后让 Codex 读取本仓库配置，要求 Python 3.12。
4. Install script：在仓库根目录运行 `bash scripts/codex_setup.sh`。
   无后台服务，无需常驻 Start skill；若填写启动检查说明，要求在仓库根目录
   运行 `bash scripts/codex_check.sh`，失败时报告错误。
5. 安装需要访问 PyPI。采用 Package managers 网络预设即可；本项目不需要
   API Key、代理凭据、VPN、OIDC 或自定义服务。
6. 检查安装与测试报告后 Save，再 Publish。应看到 Environment published。
7. Start a new task，运行 `bash scripts/codex_check.sh`，记录实际版本、提交 SHA、
   测试数与退出码。这一步验证发布快照确实可用。
8. 在手机打开同一任务，补充“再次运行 Ruff，报告当前提交和工作区状态”，
   再在电脑打开该任务确认指令与结果一致。新建任务会产生独立工作区，
   不能作为继续同一任务的验证。

安装脚本使用明确的 `.venv/bin/python`，不依赖 setup shell 的 activate/export
是否传递到后续任务。没有新增 Docker、数据库、包管理器或 CI 配置。
官方说明发布会捕获准备好的文件系统；已有任务保留自己的状态，环境更新
需 Republish，新任务才能使用。仍应通过 Git 保存重要代码。

可粘贴到环境创建对话的要求：

> 为 Zebedee2021/pyspt-v2 配置最小 Python 3.12 环境。复用 pyproject.toml
> 的 dev extras，运行 bash scripts/codex_setup.sh，再运行
> bash scripts/codex_check.sh。保留 Only me，使用 Package managers 网络预设，
> 无密钥、后台服务和硬件依赖。报告提交 SHA、Python 和主要依赖版本、pytest
> 和 Ruff 的完整结果。检查失败时保留错误证据，不修改数值算法、测试或阈值。

## 迁移边界

| 工作 | 处理位置及依据 |
|---|---|
| Python 库开发、现有单元测试、Ruff、覆盖率 | 本次 Linux 容器已通过，可作为云端首批流程；发布后仍需复验 |
| MATLAB 对照测试 | 消费仓库已提交的 `.npz` fixtures，不需要在线 MATLAB，可迁移 |
| 生成/更新 MATLAB fixtures | 先留本机；`scripts/gen_fixtures.py` 的 engine/batch 后端需要 MATLAB 及许可，MCP 后端仍是 stub |
| MATLAB/Python 性能比较 | 参考 fixture 中记录的历史 MATLAB 时间；不同硬件上的比例不能当同机实测结论 |
| 教学 notebook 交互、桌面图窗 | 不属于本次验证范围；仍使用现有本机/Colab 流程，后续单独验收 |
| ROS/Gazebo、GPU、大规模仿真、实机控制 | 不在该仓库依赖中；EICPS 推广前分别验证，实机实时闭环先留本机 |
| 本机 Codex 登录与代理排障 | 仍留本机；云端仓库测试不会修复本机变量、代理或浏览器登录态 |

## 认证与本机边界

本项目自身不调用 OpenAI API，环境无需 `OPENAI_API_KEY`。
不要复制本机 auth.json、API Key 或 localhost 代理配置进入云环境。
云端执行可减少对本机 Python 环境和本机进程变量的依赖；电脑/手机访问
ChatGPT 的认证和网络仍需正常。云端运行成功不等于本机登录网络问题消失。

## 已有工作衔接

开放的 PR #8 正在增加 parity 验证和 CI Ruff/API 导出检查，尚未合入本次
测试基线。本试点不重复实现该工作。待 #8 合并后，应按新的 CI 命令更新
检查脚本，并重新记录测试数；本文的 73 项结果仅对应上述基线。

## 推广门槛

- 发布后新任务的 pytest/Ruff 均通过。
- 同一任务的手机→电脑继续与引导已实测。
- 环境恢复/仓库更新后仍可运行；版本变化时重装并复验。
- 四个现有 Python CI 分支按原流程验收；本次只实测 Python 3.12。

满足上述门槛后，再考虑将 EICPS 的纯 Python、任务模型、约束检查部分
纳入独立试点；不以 PySPT 成功推断机器人仿真与实机系统已可迁移。
