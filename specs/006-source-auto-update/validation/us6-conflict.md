# US-006 许可、本地修改与冲突验收

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: T015–T017；许可缺失/变化、本地修改、基线前进、非法候选与失败保留。

## 1. 自动测试

```bash
node --test tests/integration/source-sync-conflict.test.js
node --test tests/unit/source-sync-state.test.js
```

结果：全部通过。覆盖：

- 目录来源缺少许可 → `policy_blocked` / `E_LICENSE_MISSING`，当前内容保留。
- 许可字节变化 → `policy_blocked` / `E_LICENSE_CHANGED`。
- 当前内容偏离 `last_synced_digest` → `conflict` / `E_CONFLICT_LOCAL`，不覆盖本地修改。
- 首次启用且候选与当前内容不同 → `conflict` / `E_CONFLICT_BASELINE`。
- 首次启用且候选与当前内容相同 → 只提交来源基线字段。
- 越界候选路径 → `failed` / `E_PATH`。
- 远端基线前进 → `pushBaseline` 以 `E_CONFLICT` 拒绝，不 force push。

## 2. POC 观察

在 POC-002 临时副本准备 release/pinned/branch 记录时，首次从 Git worktree 复制 v1 文件产生了
CRLF，而源提交与 GitHub Blob 为 LF；许可摘要因此不同，检查返回 `E_LICENSE_CHANGED`。改为复制
提交字节后，三个策略分别得到 `candidate`/`unchanged`，说明许可按路径和字节摘要比较，而不是只看
文件名或仓库级声明。

## 3. 失败保留

所有 `policy_blocked`/`conflict`/`failed` 分支在测试和 POC 中均未写入目标原件，当前版本、当前站点和
Git 历史保持；诊断只输出稳定错误码和路径。POC 的 `missing-poc` 真实 404 返回
`E_SOURCE_NOT_FOUND`，没有删除或覆盖现有内容。

## 4. 未运行

- 真实 403、限流等待、子模块/符号链接的真实远程读取；由注入测试覆盖。
- 生产部署失败注入；见 [us6-status.md](us6-status.md)。
