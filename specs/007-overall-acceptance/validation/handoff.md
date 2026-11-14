# US-007 交接：干净副本命令复核

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: T019；按 README 在干净副本复核 preview、构建/预览、发布目标、状态和恢复命令与退出码。
**方式**: 从当前仓库 HEAD（`b2b8970`）创建 detached `git worktree`，仅以 junction 复用已安装
`node_modules`；未提交、未推送、未写生产。命令结束后删除临时 worktree。

## 1. 干净副本

```bash
git worktree add --detach <temp> HEAD
```

- HEAD：`b2b8970`；`git status --porcelain` 为空。
- `node_modules` 为指向项目根已安装依赖的 junction；不复制、不提交依赖。
- 临时目录只用于本轮命令，结束后 `git worktree remove --force` 删除。

## 2. preview

```bash
node scripts/skill-cli.js preview skills/code-review-assistant.md \
  --meta catalog/code-review-assistant.json
```

结果：退出码 `0`，stdout 单行 JSON：

```json
{"status":"previewed","slug":"code-review-assistant","content_revision":"7182dd2f...","content_status":"previewed","deploy_status":"pending","commit_sha":null,"run_url":null,"public_url":null,"errors":[]}
```

`git status --porcelain` 仍为空，未写入、未提交、未推送。

## 3. add（不带 --publish）

```bash
node scripts/skill-cli.js add skills/code-review-assistant.md \
  --meta catalog/code-review-assistant.json
```

结果：退出码 `0`，同样返回 `previewed`/`pending`，`commit_sha` 为 `null`；工作区无变化。
说明 `add` 只有显式 `--publish` 才允许远端写入。

## 4. status

```bash
node scripts/skill-cli.js status --run 43421951464
node scripts/skill-cli.js status --run 43421560371
```

| run | 退出码 | 观察 |
|---|---|---|
| `43421951464`（手动 sync，无内容变化） | 0 | `status=pending`、`content_status=pending`、`deploy_status=pending`；这是 no-op 运行，不是 published |
| `43421560371`（生产 push，build/deploy success） | 0 | `status=published`、`content_status=built`、`deploy_status=published`；`commit_sha=27c6b36d...` |

两次均为 stdout 单行 JSON，未写入工作区。`status` 的 `slug`/`content_revision` 为 `null` 是当前
运行级查询的输出字段，未据此推断内容版本。

## 5. 发布目标与恢复

```bash
node scripts/publish-check.js target --target <sha> --remote <sha>
node scripts/publish-check.js target --target <sha> --remote <other>
node scripts/publish-check.js target --target not-a-sha --remote <sha>
```

| 场景 | 退出码 | 输出 |
|---|---|---|
| 目标等于远端 | 0 | `decision=current`，无诊断 |
| 目标落后 | 4 | `decision=superseded`，无诊断 |
| 非法 SHA | 2 | `E_TARGET_SHA`；stdout JSON + stderr 稳定错误码 |

受控恢复命令在临时 worktree 演练：

```bash
git revert --no-edit <temp-content-commit>
```

结果：退出码 `0`，探针文件被删除，历史保留临时提交和 revert 提交（未 force push、未改写历史）。
该演练只验证命令语义；真实站点恢复仍复用 `us6-status.md` 的 POC run `43420712186` 和
`us3-recovery.md` 的隔离演练。

## 6. 构建与 preview 服务

```bash
node scripts/build-index.js
node scripts/preview.js
```

- 构建：退出码 `0`，`status=built`、`cleanup_status=complete`，`dist/manifest.json`
  `contentRevision=3a97b854...`。
- preview：输出 `{"status":"listening","url":"http://127.0.0.1:8000/skill-gallery/"}`；
  `GET /skill-gallery/` 为 200、1,623 字节；`GET /skill-gallery/assets/search-index.json` 为 200、
  4 项。检查后停止进程。
- 本地 `contentRevision` 与生产 `faa0f345...` 不同，原因是本地 Windows/Node 22.21.0 与生产
  Linux/Node 26.3.0 的运行时标识不同（见 `platform.md`）；不代表内容不一致。

## 7. 偏差与限制

- `status --run 43421951464` 返回 `pending` 是 no-op 运行的真实状态，不误报 published；
  发布成功路径使用 `43421560371` 返回 `published`。
- `preview` 服务由 `node scripts/preview.js`（`npm run preview` 的实现）启动；未在浏览器交互，
  仅做 HTTP 200/索引检查。
- 干净副本未运行完整 `npm run check`/`npm run security`；这两项由 T021 在主工作区执行。
- 恢复演练未重新构建/部署；真实 revert 发布证据见 POC `43420712186`。
