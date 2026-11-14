# US-007 Demo-001：维护到公开取用

**日期**: 2026-11-14
**范围**: T004–T006；手动/命令维护、检索/详情/复制/下载。
**结论**: `受控通过`。手动/CLI/生产数据链路已验证；交互式浏览器复制未在本次重跑，复用 US-002 证据。

## 1. T004 手动维护

```bash
node --test tests/integration/manual-maintenance.test.js
```

结果：7 项全部通过。

| 覆盖 | 结果 |
|---|---|
| 单文件/目录 Skill 通过既有构建发布 | 通过 |
| 仅元数据编辑不改原件字节 | 通过 |
| 非法批次（缺字段/缺附件/越界/凭证）失败关闭并保留旧 dist | 通过 |
| 显式替换只保留一个版本并删除旧附件 | 通过 |
| 下架后从索引/详情/下载消失 | 通过 |
| 受控 revert 恢复基线 revision 与 slug | 通过 |
| 未变化重建保持 revision 和产物集 | 通过 |

失败批次旧站保留、非法输入不产生可部署残缺站点；对应 AC-006。

## 2. T005 Agent CLI

```bash
node --test tests/integration/skill-cli-add.test.js \
  tests/integration/skill-cli-replace.test.js \
  tests/integration/skill-cli-import.test.js \
  tests/unit/skill-cli-status.test.js \
  tests/unit/skill-cli-args.test.js
```

结果：28 项全部通过。覆盖：

- `preview` 零写入、无 worktree/远端变化；
- `add` 只提交目标 Skill 与 catalog；
- `replace` 清理旧附件、保留站内元数据，过期 `--expected-revision` 返回冲突；
- `import` 单文件/目录来源预览与发布，截断/链接/越界失败关闭；
- `status` 区分 submitted/published/pending/superseded 和退出码；stdout 单行 JSON。

对应 AC-007。

## 3. T006 公开站点取用

生产只读检查（2026-11-14）：

| 检查 | 结果 |
|---|---|
| 首页/索引 | 200；4 项 Skill；revision `faa0f345...` |
| 单文件详情 | `code-review-assistant`：display_name/body_html/raw/download 可用 |
| 目录详情 | `handoff-codex`：3 个文件，raw 入口和 `downloads/handoff-codex.zip` 可用 |
| 单文件下载 | raw 字节与本地原件一致；SHA-256 与详情 `download_sha256` 一致 |
| 目录 ZIP | 3 个条目；`SKILL.md`、`agents/openai.yaml`、`scripts/create_handoff.sh` 字节与本地一致 |
| 搜索/复制/分享 | `tests/unit/search-core.test.js`、`list-view.test.js`、`share-link.test.js` 共 16 项通过；浏览器交互复用 US-002 evidence |

生产检查脚本输出：

```json
{"revision":"faa0f345a85673f60fda1d4cb3b61594b242ae631ab89b264387eec6875c429a","skills":4,
 "checks":["code-review-assistant: raw bytes=1044","handoff-codex: zip files=3",
 "refactoring-workflow: raw bytes=1020","superpower-systematic-debugging: raw bytes=1222"]}
```

## 4. 状态

- Demo-001：`受控通过`。
- AC-002（原件/ZIP 保真）：`通过`。
- AC-003（搜索）：`受控通过`（代码测试 + US-002 证据，未重跑生产浏览器）。
- AC-004（详情）：`受控通过`（生产 JSON + US-002 视觉证据）。
- AC-005（旧链接/复制）：`受控通过`（US-002 测试/证据，未重跑真实剪贴板）。
- AC-006（手动维护）：`通过`。
- AC-007（Agent CLI）：`通过`。

未运行：真实浏览器复制/移动实机、生产 OAuth/后台 UI；不计为本次通过。
