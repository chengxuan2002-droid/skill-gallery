# US-005 README 命令走查（T018）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 按 README“Agent 命令（skill-cli）”在系统临时项目与临时裸远端走查预览、新增、noop、
替换冲突/成功与状态查询；不访问 GitHub、不推送真实远端。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 走查命令

```text
node scripts/skill-cli.js preview <candidate>/cli-readme.md --meta <candidate>/cli-readme.json
node scripts/skill-cli.js add <candidate>/cli-readme.md --meta <candidate>/cli-readme.json --publish
node scripts/skill-cli.js add <candidate>/cli-readme.md --meta <candidate>/cli-readme.json --publish
node scripts/skill-cli.js replace cli-readme <candidate>/cli-readme.md --expected-revision <stale>
node scripts/skill-cli.js replace cli-readme <candidate>/cli-readme.md --expected-revision <baseline>
node scripts/skill-cli.js status --run 1
```

## 2. 结果

| 命令 | 退出码 | 结果 |
|---|---|---|
| `preview` | 0 | `status=previewed`，工作区与远端不变 |
| `add --publish` | 0 | `status=submitted`；提交 `7e8c0071938cbffdfa02647ebf1868d5239b216c`；远端含 `catalog/cli-readme.json` 与 `skills/cli-readme.md` |
| 再次 `add --publish` | 0 | `status=noop`，远端 HEAD 不变 |
| `replace`（过期基线） | 4 | `E_CONFLICT`，远端 HEAD/树不变 |
| `replace`（正确基线） | 0 | `status=submitted`，远端 HEAD 前进 |
| `status --run 1` | 5 | `E_SOURCE`（临时裸远端没有 GitHub 运行，符合当前限制） |
| 本地工作区 | — | `git status --porcelain` 为空 |

## 3. 偏差与限制

- README 中 `status` 依赖 GitHub 运行；隔离裸远端无法提供，走查只确认了失败关闭的退出码 `5`。
- `import` 默认使用 `gh api`，本地走查未执行；固定来源树已在 T011/T013 覆盖。
- `--wait` 需要真实运行发现；本地未执行，固定状态语义见 T016。
- 未调用 GitHub Actions/POC-002，`content_status`/`deploy_status` 保持 pending，未报告 published。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。

README 的已测命令、退出码与 JSON 字段与实际一致；未实现的自动更新、ZIP 解压、站内后台和生产
切换在执行时已在 README 标记规划（后续生产 Pages 已切换，见
[production-pages.md](../../003-validate-build-publish/validation/production-pages.md)）。
