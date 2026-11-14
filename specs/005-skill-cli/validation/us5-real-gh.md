# US-005 真实 `gh api` 导入与 `--wait` 运行发现补验

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: 在受控 POC-002 目标仓库和 POC-003 来源仓库执行真实 `gh api` 导入、发布和 `--wait` 运行
发现；不写生产仓库，不执行收录 Skill 的脚本。
**结论**: `通过（受控 POC）`。真实 `gh api` 导入成功；修复默认 reader 与运行发现重试后，
`--wait` 能发现延迟出现的 `maintain.yml` 运行并轮询到 `published`。

## 1. 受控仓库

| 角色 | 仓库 | 状态 |
|---|---|---|
| 来源 | `chengxuan2002-droid/skill-gallery-source-poc-20261112` | 归档只读；`skills/poc-skill` main |
| 目标 | `chengxuan2002-droid/skill-gallery-poc-20261107` | 临时取消归档以允许 push；完成后重新归档 |

来源文件：`SKILL.md`、`LICENSE`、`assets/binary.bin`、`notes.txt`、`references/new.md`，共 5 个。

## 2. 发现并修复的问题

1. **默认 `gh api` reader 未注入**
   - `scripts/lib/skill-cli/source-github.js` 的 `fetchSource` 在未传 reader 时把 `undefined` 传给
     `shared.fetchSource`，真实 import 返回 `E_SOURCE`。
   - 修复：默认使用 `shared.createGhReader()`；新增
     `tests/unit/skill-cli-source-github.test.js` 覆盖默认 reader 和显式注入优先级。
2. **`--wait` 运行发现延迟**
   - 第一次真实发布提交 `19bf63c676fe...` 后立即查询，GitHub 尚未列出运行，命令按契约返回
     `submitted/pending`；约 16 秒后 run `43612050209` 才出现。
   - 修复：`scripts/lib/skill-cli/status.js` 新增 `waitForPublishedRun`，在 60 秒内每 5 秒发现
     对应提交的 `maintain.yml` 运行，找到后交给 `waitForRun`；`scripts/skill-cli.js` 使用该入口。
   - 新增 `tests/unit/skill-cli-status.test.js` 用例覆盖延迟发现、发现超时和 gh 失败。

## 3. 真实预览与发布

```bash
node scripts/skill-cli.js import \
  --repo chengxuan2002-droid/skill-gallery-source-poc-20261112 \
  --path skills/poc-skill --ref main --meta us5-real-meta.json
```

- 修复后 preview：退出码 `0`，`status=previewed`，`content_revision=b2dbc03c...`，
  工作区无写入。

第一次真实发布（修复前 `--wait`）：

| 项 | 值 |
|---|---|
| slug | `us5-real-import` |
| 提交 | `19bf63c676fe6bbe1c7c11c4560484d51cc911a0` |
| 命令输出 | `status=submitted`、`deploy_status=pending` |
| 后续运行 | `43612050209`（push，build/deploy success） |
| 后续 `status --run` | `published`、`built`、`published` |

第二次真实发布（修复后 `--wait`）：

| 项 | 值 |
|---|---|
| slug | `us5-real-wait` |
| 提交 | `1017dd4613ed6374d09c248f5105bccd0a4b5afc` |
| 命令输出 | `status=published`、`content_status=built`、`deploy_status=published` |
| 运行 | [43612262185](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43612262185)（push，build/deploy success） |
| `run_url` | 与运行一致 |

## 4. 保真与站点

- 目标 `skills/us5-real-wait/` 的 5 个文件与来源 `skills/poc-skill/` 逐字节一致：
  `SKILL.md` `5a3cb8b6...`、`LICENSE` `ec43df0d...`、`assets/binary.bin` `ff5d8507...`、
  `notes.txt` `bd4f114f...`、`references/new.md` `fc62dcab...`。
- 目标 catalog：`slug=us5-real-wait`、`content_path=skills/us5-real-wait/SKILL.md`、
  `source_type=github`、备注保留。
- POC 站点 `manifest.json`：HTTP 200，`contentRevision=31baae8c...`，8 项 Skill；
  `us5-real-import` 与 `us5-real-wait` 各 5 个文件，digest 均为 `b2dbc03c...`。
- 从 POC 详情下载 `assets/binary.bin`（`skills/us5-real-wait/ff5d8507....bin`）：5 字节，
  SHA-256 `ff5d8507...` 与来源/详情一致。

## 5. 测试

```bash
node --test tests/unit/skill-cli-source-github.test.js \
  tests/unit/skill-cli-status.test.js tests/integration/skill-cli-import.test.js
```

结果：14 项通过、0 失败、0 跳过。

## 6. 边界与恢复

- 仅操作 POC-002；生产仓库、生产 Pages、生产 environment 未写。
- POC-002 已重新归档；POC-003 保持归档只读。
- 真实 source-sync 403/429、真实截断/子模块/符号链接未在本文件重跑；见 US-006/US-007 证据。
- `--wait` 仍不是无限等待：发现超时为 60 秒，运行轮询沿用 `waitForRun` 的 15 分钟默认超时。
