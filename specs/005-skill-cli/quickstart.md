# Quickstart: US-005 Agent 命令维护

**Date**: 2026-11-08 | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

本指南只描述实施后的可执行验证步骤；命令语法、JSON 字段、退出码和不变量见
[data-model.md](data-model.md) 与 [skill-cli 契约](contracts/skill-cli.md)。真实远端写入与生产
Pages 仍需单独授权。

## 1. 前置条件

- Node 26.3.0、npm 11.16.0（以 `.node-version`、`package.json` 为准）；Git 与 `gh` 已安装。
- 已授权 Git/gh 会话；不要在命令行、配置文件或示例中写入 token。
- 本地安全扫描器：`npm run setup:security`（需要 uv 与网络）。
- 默认验证使用隔离临时仓库或受控 POC-002；不要直接对生产仓库练习。

```bash
npm ci
npm run setup:security
gh auth status
```

## 2. 只读预览

```bash
node scripts/skill-cli.js preview /path/to/my-skill --meta /path/to/catalog-entry.json
```

期望：退出码 `0`；stdout 单行 JSON 含 `slug`、`content_revision`、`content_status=previewed`；
工作区无新增/修改文件，无提交或推送。

非法元数据、越界路径、缺附件或凭证：退出码 `2`，`errors` 只含稳定码与位置，不回显内容。

## 3. 发布（隔离远端）

在临时裸仓库/受控 POC 上验证（需授权）：

```bash
node scripts/skill-cli.js add /path/to/my-skill --meta /path/to/catalog-entry.json --publish --json
node scripts/skill-cli.js status --run <run-id>
```

期望：

- 发布输出 `commit_sha` 与运行链接；`deploy_status` 在未观察到部署成功前不是 `published`；
- `--wait` 超时返回 `8` 并保留 `run_url`；
- 相同内容重复提交返回 noop，不新增内容提交；不同内容未显式替换返回冲突。

## 4. 替换与冲突

```bash
node scripts/skill-cli.js replace example /path/to/new-skill --expected-revision <base-sha> --publish
node scripts/skill-cli.js replace example /path/to/new-skill --expected-revision <stale-sha> --publish
```

期望：第一个成功且单版本、旧附件清理；第二个退出码 `4`，当前内容保留，不 force push。

## 5. 来源导入

```bash
node scripts/skill-cli.js import --repo owner/repository --path skills/example --ref main --meta /path/to/catalog-entry.json
```

期望：同一不可变修订的完整候选；404/403/限流/截断返回 `5`，不覆盖当前内容；普通网页 URL
被拒绝为不支持来源。

## 6. 状态与等待

```bash
node scripts/skill-cli.js status --run <run-id>
node scripts/skill-cli.js add /path/to/my-skill --meta /path/to/meta.json --publish --wait
```

期望：提交/构建/部署状态分开；build 成功且 deploy 跳过时为 `superseded`；失败返回 `7` 或真实
`failed`；超时 `8`；任何情况都不得把提交成功报告为已发布。

## 7. README 与全量检查

```bash
npm test
npm run lint
npm run format:check
npm run security
```

期望：测试与扫描通过；README 命令与退出码和实际一致，示例不含凭证，未实现能力标“规划”。
在 `specs/005-skill-cli/validation/` 记录命令、退出码、JSON 输出、运行 URL 和未运行项。
