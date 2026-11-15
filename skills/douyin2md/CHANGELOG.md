# Changelog

## 2.0.0 (2026-11-15)

通用化改造与仓库整理。目标是「同一份文件，无需修改即可被主流 agent 框架识别调用」。

### 新增

- 统一入口 `bin/douyin2md`：9 个子命令（url / batch / transcribe / to-md / capture /
  model / cookie / doctor / config），用 `BASH_SOURCE` 自定位技能根，任意 cwd 可调用。
- 接口层包 `douyin2md/`：`cli.py`（参数归并 + 转发）、`config.py`（配置优先级 + 脱敏）、
  `__main__.py`（`python3 -m douyin2md`）。
- 统一依赖声明：`pyproject.toml`（core / local / browser / all / dev extras + console script）
  与 `requirements.txt`。
- 统一配置：`config.example.json`、`DOUYIN2MD_*` 环境变量、四级优先级、密钥只走环境变量。
- `doctor` 只读环境体检、`config` 脱敏配置打印。
- 文档：`docs/agent-compatibility.md`、`configuration.md`、`architecture.md`、`troubleshooting.md`。
- 示例：`examples/urls.txt`、`cli.sh`、`agent-prompts.md`；零依赖单测 `tests/`。
- `LICENSE`（MIT）与完善的 `.gitignore`（排除 cookie、模型、媒体、本地配置）。

### 变更

- `SKILL.md` 重写为通用版：移除本机绝对路径与解释器踩坑，统一为 `bin/douyin2md` 调用；
  环境相关记录迁至 `docs/troubleshooting.md`，知识不丢失。
- `README.md` 重写，补齐框架接入、依赖分层、命令速查与仓库结构。
- `install.sh` 新增 `workbuddy` 目标并在帮助中标注统一入口。

### 未变更

- `scripts/*.py` 全部 9 个原始脚本**逐字节保持不变**，继续可单独调用；新入口仅做转发，
  历史命令 `python3 scripts/dy.py ...` 仍然有效。
