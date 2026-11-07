# 跨平台 ZIP 与恢复验证

日期：2026-11-04。范围：T041。映射 FR-004、FR-011，NFR-001、NFR-006，DEC-002、DEC-009，
AC-002、AC-012。仅记录实际运行的平台；macOS 未运行，不能把本文件当作跨平台全部通过。

## 环境

| 平台 | Node/npm | 结果范围 |
|---|---|---|
| Windows 11 | Node 22.21.0 / npm 10.9.4 | 既有 Windows 测试与浏览器验收；非声明基线 |
| WSL2 Ubuntu 24.04（Linux 5.15.167.4-microsoft-standard-WSL2） | Node 26.3.0 / npm 11.16.0 | Linux 定向与全量测试、构建 |
| macOS | 无可用环境 | **未运行** |

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

当前没有 macOS 主机、远程 runner 或获授权的远程写入。未运行 macOS 上的 ZIP 路径/模式、二进制、
rename/回滚和中断恢复测试；**T041 保持未完成**。不能根据 Linux/WSL 或 Windows 结果声称 macOS 通过。

2026-11-04 用户确认：将 macOS 缺口记录为**未验证**，并据此收口 US-001 本地交付。
T041 复选框继续保持未勾选，不作为通过项；后续获得 macOS 环境时仍需补测，
本次收口不改变“未验证跨平台、未生产发布”的结论。

## 限制

- WSL2 是 Linux 兼容环境，不是独立物理 Linux 主机；结果不能覆盖发行版、文件系统或权限差异。
- 未验证断电/强杀、网络文件系统、并发进程或生产部署回滚。
- 两次 rename 的短暂间隙仍然存在；恢复依赖 C-03 锁/事务记录和人工核对。
- 本记录不改变站点内容，不推送、不发布。
