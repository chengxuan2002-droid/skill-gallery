# 跨平台 ZIP 与恢复验证

日期：2026-11-04；2026-11-14 补充 macOS runner。范围：T041。映射 FR-004、FR-011，NFR-001、
NFR-006，DEC-002、DEC-009，AC-002、AC-012。仅记录实际运行的平台；macOS 已由 GitHub-hosted
runner 补验，仍不把本文件当作所有 macOS 硬件/文件系统变体通过。

## 环境

| 平台 | Node/npm | 结果范围 |
|---|---|---|
| Windows 11 | Node 22.21.0 / npm 10.9.4 | 既有 Windows 测试与浏览器验收；非声明基线 |
| WSL2 Ubuntu 24.04（Linux 5.15.167.4-microsoft-standard-WSL2） | Node 26.3.0 / npm 11.16.0 | Linux 定向与全量测试、构建 |
| GitHub-hosted `macos-latest` | Node 26.3.0 / npm 11.16.0 | 2026-11-14 全量测试、安全扫描、构建；run `43588719771` |

Linux Node 26.3.0 官方二进制在 WSL 中需要 `libatomic.so.1`；使用 Ubuntu `libatomic1` 包解出库并设置
`LD_LIBRARY_PATH`，未修改系统包或项目依赖。Windows 与 Linux 的 contentRevision 不同：
Windows 构建使用 Node 22.21.0，Linux 使用 Node 26.3.0；运行时标识属于 contentRevision，不能把两者相等当作跨平台要求。

## Linux 实测

| 检查 | 实际结果 |
|---|---|
| `node --test tests/integration/distribution.test.js tests/integration/reproducibility.test.js tests/integration/build-recovery.test.js tests/integration/build-failures.test.js` | exit 0；23/23 通过 |
| 目录 ZIP | 根目录、`SKILL.md`、嵌套附件、许可、二进制、空目录；脚本条目 0755，其他 0644；解包字节与源一致 |
| 单文件下载 | 原名 `.md`、raw 字节与清单 SHA-256 一致 |
| rename 第二次失败 | 旧 dist 恢复；E_BUILD |
| 补偿失败 | E_RECOVERY_REQUIRED，保留唯一 backup 与事务记录 |
| prepared/promoted 恢复 | 旧输出保留、缺失 dist 从 backup 恢复、候选回滚；损坏候选拒绝 |
| 提交后清理失败 | `built` + `cleanup_status=pending`，新 dist 有效 |
| `node scripts/build-index.js` | exit 0；`built`、`cleanup_status=complete`；contentRevision `068cd50d57fc3a528bd824437f8ec357a8cbea3acb1d4fb75ebec7a30799840a` |
| `node --test tests/unit/*.test.js tests/integration/*.test.js` | 138 项中 135 通过、2 失败、1 跳过；两项失败为 WSL 未安装 Gitleaks/Semgrep |

Linux 上符号链接测试可执行（不同于 Windows 的 EPERM 跳过）；硬链接、路径越界和链接拒绝仍按预期失败。
Windows 不保留 POSIX 执行位；Windows 的 ZIP 模式只按当前平台源状态验证，不能替代上述 Linux 结果。

## macOS

2026-11-14 在用户授权的临时分支 `codex/us7-macos-check` 上，用 GitHub-hosted `macos-latest`
runner 补验；临时 workflow 只用于本次检查，运行后删除分支：

- run：[43588719771](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/43588719771)
- 环境：macOS runner、Node `26.3.0`、npm `11.16.0`
- `npm run setup:security`：Gitleaks 8.30.1 / Semgrep 1.183.0 通过
- `npm run check`：282 项，281 通过、0 失败、1 跳过
- `npm run security`：secrets 350、code 56、deps 1；findings 0
- `npm run build`：`built`、`cleanup_status=complete`，contentRevision
  `faa0f345a85673f60fda1d4cb3b61594b242ae631ab89b264387eec6875c429a`（与生产一致）
- ZIP 路径/0644-0755/二进制/rename/回滚/中断恢复：由 `npm test` 的 distribution、
  reproducibility、build-recovery、build-failures 测试覆盖并通过
- macOS runner 上符号链接相关测试实际执行，未出现 Windows 的不可用跳过

这是 GitHub-hosted macOS 虚拟机，不是物理 Mac；T041 的“未运行 macOS”缺口已关闭，但不宣称所有
macOS 硬件、文件系统或版本变体均已覆盖。2026-11-04 的历史收口记录仍保留，作为此前的未验证状态。

## 限制

- WSL2 是 Linux 兼容环境，不是独立物理 Linux 主机；结果不能覆盖发行版、文件系统或权限差异。
- 未验证断电/强杀、网络文件系统、并发进程或生产部署回滚。
- 两次 rename 的短暂间隙仍然存在；恢复依赖 C-03 锁/事务记录和人工核对。
- 本记录不改变站点内容，不推送、不发布。
