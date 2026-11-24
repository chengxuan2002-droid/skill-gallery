# douyin2md 仓库根来源与基线

**日期**: 2026-11-24
**范围**: 为生产 `douyin2md` 启用 GitHub 仓库根目录来源，更新到上游 2.1.0，并建立首次来源基线。
**上游**: `chengxuan2002-droid/douyin2md`，public，MIT，默认分支 `main`，基线 commit
`802b3456f0e0b155639e88ec9b83f1525dcc78c3`。

## 1. 根目录来源支持

上游 `SKILL.md`、许可和附件位于仓库根，不在子目录。同步器原先只支持单文件和子目录，新增：

- `source_tracking.path: "."` 表示仓库根目录；根目录必须直接包含 `SKILL.md`。
- 其他 `path` 仍必须是安全的 POSIX 相对子目录。
- 根目录来源读取 tree 中全部 blob，许可仍按 `LICENSE/NOTICE` 规则检查。
- 单元测试覆盖 `path: "."` 的 catalog 校验、根目录文件选择和许可读取。

相关提交：`cf20108`（根来源支持）、`dda1616`（非 ASCII tracked path 修复）。

修复说明：`git ls-files` 默认转义中文路径，`replace`/`commitBatch` 曾把带引号的路径传给
`git add`，导致生产基线 dispatch run `45344457719` 在提交阶段失败。改为
`git -c core.quotepath=false ls-files -z` 后，run `45345462657` 成功建立基线。

## 2. 上游内容更新

- `catalog/douyin2md.json`：`source_type: github`，`path: "."`，`ref_policy: branch`，
  `ref: main`，`enabled: true`；首次 `last_synced_*` 为 null。
- 上游版本 `2.1.0`；收录 47 个文件 / 364220 字节。
- 仅对上游 `tests/test_wx_session_check.py` 的测试占位符做语义等价改写
  （`SUPER_SECRET_SESSION_VALUE` → `YOUR_SESSION_VALUE_HERE`），避免站点 SECRET-03 误报；
  该改写已作为上游 commit `802b345` 发布。其余内容保持上游字节。
- 原 `examples/示例输出.md` 被上游重命名/拆分，生产目录已按上游完整清单替换，不保留旧附件。

## 3. 合并与构建证据

| 项目 | 结果 |
|---|---|
| PR #16 | 根来源支持 + douyin2md 2.1.0 内容；quality checks `45344053285`、`45344123286` 通过 |
| PR #17 | 非 ASCII tracked path 修复；quality checks `45344985548`、`45345039849` 通过 |
| 本地 `npm run build` | 成功，content_revision `e801e38d...` |
| 本地 `npm run check` | 288 项：286 通过、0 失败、2 跳过 |
| 本地 `npm run security` | secrets 439 / code 56 / deps 1，findings 0 |
| push run `45344263852` | build/deploy success；内容发布 |
| 基线 run `45345462657` | sync/build/deploy success；sync 提交 `8fb8d41...` |

本机 Windows 不保留 Git 可执行位，独立运行 `sync-skills` 时当前快照与候选的 digest 会因
`bin/douyin2md`、`install.sh`、`examples/cli.sh` 的 executable 位不同而显示
`E_CONFLICT_BASELINE`；Linux 维护运行已按索引模式正确识别并完成基线，不能把本机结果当作
同步失败或线上失败。

## 4. 生产基线

run `45345462657` 的 sync 摘要：

```text
| douyin2md | updated | 802b3456f0e0 | 3105a7c503cf | present |  |
| sepia | unchanged | 0eb11d6c64c9 | 785e07ec8e70 | present |  |
```

`catalog/douyin2md.json` 已写入：

- `last_synced_revision`: `802b3456f0e0b155639e88ec9b83f1525dcc78c3`
- `last_synced_digest`: `3105a7c503cf1f5c643d3e4c4593f8b9c8081ef3e97e560e22b17848f7dcca0f`
- `last_synced_license`: `LICENSE` / `f6ef080eadb2ae3fbadd23e92c2e9f79e603f4b61122253ec892bfaaeb7e7382`
- `synced_at`: `2026-11-24T07:07:07.404Z`

生产只读核对：

- 首页与固定资源通过 `npm run monitor:site`。
- `assets/search-index.json`：7 项，contentRevision `2acbbad2...`；douyin2md digest
  `3105a7c503cf...`。
- `details/douyin2md.json`：版本 `2.1.0`，47 个文件；download ZIP 153186 字节，
  SHA-256 与详情清单一致。

## 5. 边界

- 本次是首次基线建立，不是上游真实变更后的自动替换演练；下一次 schedule 仍以运行记录为准，
  不承诺准点 SLA。
- `douyin2md` 后续上游变化仍按 `unchanged`/`candidate`/`conflict`/`policy_blocked` 处理；
  失败保留当前版本。
- 同步只读取来源，不执行上游脚本、测试或安装其依赖；上游内容仍按不可信数据处理。
