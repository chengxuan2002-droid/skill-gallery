# Contract: 发布前校验与状态（C-07 子集）

**Feature**: US-003 | **Date**: 2026-11-07 | **Spec**: [../spec.md](../spec.md)

本契约定义 `scripts/lib/publish.js` 与 `scripts/publish-check.js` 的输入、输出和错误边界。
它是 M-07 在 US-003 的公共子集，后续 US-005/US-006 复用这些函数，不另写发布校验器。

## 1. `verifyArtifact(distDir)`

**输入**: `distDir`（字符串，必须存在且为目录）。

**检查**:

1. 读取 `manifest.json`：`schemaVersion=1`、`contentRevision` 非空、`artifacts` 为数组。
2. 实际文件集合（递归普通文件）必须与 `manifest.artifacts` 双向完全一致，`manifest.json` 除外。
3. 每个文件：路径安全（POSIX 相对、无 `..`/反斜杠/控制字符/空段/绝对路径）、大小与 SHA-256 一致。
4. 路径前缀仅允许：`index.html`、`.nojekyll`、`assets/`、`details/`、`downloads/`、`skills/`、`media/`。
5. 拒绝符号链接、非普通文件、重复路径、隐藏文件（`.nojekyll` 除外）、凭证类文件名
   （`.env`、`.npmrc`、`.netrc`、`.git-credentials`、`id_rsa`、`*.pem`、`*.key`、`*.p12` 等）。
6. `assets/search-index.json` 与每个 `details/<slug>.json` 的 `contentRevision` 必须等于 manifest；
   detail 的 `slug`/`digest` 必须与索引一致。
7. 对文本类文件（`.html`、`.js`、`.css`、`.json`、`.md`、`.txt`、`.yml`、`.yaml`、`.xml`、`.svg`）
   复用 `scripts/lib/secrets.js` 的 `scanSecrets`；诊断只报告路径与规则 ID，不回显值。

**成功输出**（stdout 单行 JSON）:

```json
{
  "status": "verified",
  "content_revision": "<revision>",
  "files": 42,
  "diagnostics": []
}
```

**失败输出**:

```json
{
  "status": "failed",
  "content_revision": null,
  "files": 0,
  "diagnostics": [
    { "code": "E_ARTIFACT_EXTRA_FILE", "path": "docs/plan.md", "message": "产物包含未允许文件" }
  ]
}
```

退出码：`0` 通过；`2` 参数/读取错误；`6` 产物无效（白名单、摘要、同快照或凭证问题）。

## 2. `evaluateDeployTarget({ targetSha, remoteHead })`

**规则**: 两个值必须为 40 位小写十六进制；相等返回 `current`，否则返回 `superseded`。
无法读取 `remoteHead` 时不猜测，返回参数错误。

**成功输出**:

```json
{ "decision": "current", "target_sha": "<sha>", "remote_head": "<sha>" }
```

退出码：`0` current；`4` superseded；`2` 参数错误。工作流在 `superseded` 时跳过部署并写入摘要，
不得标记为已发布。

## 3. `createRunStatus(input)`

**输入字段**: `runId`、`trigger`、`targetSha`、`commitStatus`、`contentRevision`、`contentStatus`、
`deployStatus`、`reason`、`startedAt`、`finishedAt`、`runUrl`。只接受
[data-model.md](../data-model.md) 第 1 节的枚举值；未知字段和未知状态必须被拒绝，不做静默丢弃。

**输出**: 封闭字段 JSON；`reason` 只允许稳定错误码，不包含自由文本、响应正文或凭证；
`startedAt`/`finishedAt` 未知时为 null，不能编造。

## 4. `renderSummary(status, context)`

**输入**: RunStatus、`serverUrl`、`repository`、`runId`。

**输出**: Markdown 文本，至少包含：

- 运行标识/链接、触发方式、目标提交、内容标识；
- 提交状态、内容状态与部署状态（分开显示）；
- 运行开始/结束时间；缺失时提供 `run_url`，不编造时间；
- 失败码或 `superseded` 说明；
- 不包含 token、cookie、响应正文、环境变量或用户文件内容。

## 5. CLI `scripts/publish-check.js`

```text
node scripts/publish-check.js artifact --dist dist
node scripts/publish-check.js target --target <sha> --remote <sha>
```

- stdout 只输出单行机器 JSON；诊断到 stderr 且脱敏。
- 不接受任意 URL、远端写入参数或凭证；不执行 `dist/` 中的脚本。
- 参数错误返回 `2`，不抛出未捕获异常。

## 6. 不变量

- 只有 `status=verified` 且 `decision=current` 的产物可以进入部署。
- 产物、索引、详情和 manifest 必须来自同一 `content_revision`。
- `content_status=noop` 只表示内容未变化；允许部署同一快照，但不得创建空内容提交或标记为新内容。
- 校验失败不得删除、覆盖或修改现有 `dist/`；只报告并退出非零。
- 任何日志、摘要或 JSON 不得回显凭证值；只报告位置/类型/规则。
