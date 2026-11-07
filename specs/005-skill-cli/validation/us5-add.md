# US-005 预览与新增验收（T007）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 在系统临时项目与临时裸远端中运行 `skill-cli` 的预览、单文件新增、目录新增与重复提交
noop；不访问网络、不写工作区、不推送真实远端、不部署。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）；
Git `2.45.2.windows.1`。

## 1. 方法

使用 `tests/support/skill-cli-fixture.js` 创建临时项目与裸远端，基线提交包含站点资产、4 个示例
Skill 与 catalog 记录；分别执行：

```text
node scripts/skill-cli.js preview <candidates>/cli-single.md --meta <candidates>/cli-single.json
node scripts/skill-cli.js preview <candidates>/cli-pack --meta <candidates>/cli-pack.json
node scripts/skill-cli.js add <candidates>/cli-single.md --meta <candidates>/cli-single.json --publish
node scripts/skill-cli.js add <candidates>/cli-single.md --meta <candidates>/cli-single.json --publish
node scripts/skill-cli.js add <candidates>/cli-pack --meta <candidates>/cli-pack.json --publish
```

临时项目与裸远端在结束后删除；不访问 GitHub，不使用凭证。

## 2. 结果

### 2.1 预览

| 场景 | 退出码 | 状态 | 检查 |
|---|---|---|---|
| 单文件预览 | 0 | `previewed` | 工作区 `git status` 不变；远端 HEAD 不变 |
| 目录预览 | 0 | `previewed` | 同上；未创建 worktree 残留 |

预览输出 `content_revision` 为候选内容摘要（64 位十六进制），`commit_sha=null`。

### 2.2 发布

| 场景 | 退出码 | 状态 | 远端提交 | 文件集合 |
|---|---|---|---|---|
| 单文件新增 | 0 | `submitted` | `161581046945d99c64727c2d88327ff7c9ee0eca` | `catalog/cli-single.json`、`skills/cli-single.md` |
| 目录新增 | 0 | `submitted` | 新提交 | `catalog/cli-pack.json`、`skills/cli-pack/SKILL.md`、`skills/cli-pack/references/note.md` |

- `content_status=pending`、`deploy_status=pending`、`commit_sha` 与远端 HEAD 一致；
  未观察构建/部署，因此没有输出 `published` 或运行链接。
- 远端提交只包含目标 Skill 与记录；临时项目工作区保持干净（候选目录被 `.gitignore` 忽略）。

### 2.3 重复提交

| 场景 | 退出码 | 状态 | 检查 |
|---|---|---|---|
| 同内容再次发布 | 0 | `noop` | `commit_sha=null`；远端 HEAD 不变 |

## 3. 未运行与限制

- 未调用真实 GitHub Actions，未获得构建产物 `contentRevision` 或运行链接；`content_status` 保持
  pending 是当前阶段的真实状态。
- 未使用 POC-002 或生产仓库；真实远端发布留给 T021（需授权）。
- 未覆盖替换/冲突、来源导入、状态查询与等待；这些属于后续任务。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
