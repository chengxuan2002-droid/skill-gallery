# macOS 远程验证（T041 补验）

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: 用 GitHub-hosted `macos-latest` runner 补验 T041 的 macOS ZIP 路径/模式、二进制、
rename/回滚和中断恢复；用户已授权临时分支。
**结论**: `通过（远程 macOS runner）`。282 项测试 281 通过、0 失败、1 跳过；安全扫描 0 发现；
构建 contentRevision 与生产一致。临时分支在运行后删除。

## 1. 运行

| 项 | 值 |
|---|---|
| 分支 | `codex/us7-macos-check`（临时） |
| 提交 | `ccafd8e`（仅新增临时 workflow） |
| workflow | `macOS gap check (temporary)`，`macos-latest` |
| run | [43588719771](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/43588719771) |
| Node/npm | `v26.3.0` / `11.16.0` |
| 结果 | success |

步骤全部成功：checkout、setup-node、npm 11.16.0、setup-uv 0.12.3、`npm ci`、
`npm run setup:security`、`npm run check`、`npm run security`、`npm run build`。

## 2. 结果

| 检查 | 结果 |
|---|---|
| `npm run check` | 282 项：281 通过、0 失败、1 跳过 |
| `npm run security` | secrets 350、code 56、deps 1；findings 0 |
| `npm run build` | `built`、`cleanup_status=complete`、contentRevision `faa0f345...` |
| ZIP/模式/二进制/rename/回滚/中断恢复 | 由 `npm test` 的 distribution/reproducibility/build-recovery/build-failures 测试覆盖并通过 |
| 符号链接 | macOS runner 上相关测试实际执行（未出现 Windows 的不可用跳过） |

macOS runner 是 GitHub-hosted macOS 虚拟机，不是物理 Mac；结果可关闭 T041 的“未运行 macOS”缺口，
但不宣称所有 macOS 硬件/文件系统变体都已覆盖。

## 3. 清理

运行完成后删除临时分支 `codex/us7-macos-check`；workflow 文件不进入 `main`，不作为产品能力。
