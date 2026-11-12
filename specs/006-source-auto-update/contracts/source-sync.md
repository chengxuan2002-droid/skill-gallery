# Contract: 来源检查与同步（C-06）

**Feature**: US-006 | **Date**: 2026-11-12 | **Spec**: [../spec.md](../spec.md)

本契约定义 `scripts/sync-skills.js` 的输入、逐来源状态、批次提交、许可/冲突边界和运行报告。
它复用 C-01/C-02/C-03 与 US-005 的候选/工作副本规则；不另写第二套内容校验器，不执行上游内容。

## 1. 命令与选项

```text
node scripts/sync-skills.js [--slug <slug>] [--apply] [--push] [--json]
  [--report <path>] [--summary <path>]

node scripts/sync-skills.js --help
```

- 默认检查模式（check）：读取启用的来源、验证候选并输出状态；不写工作区、不提交、不推送。
- `--apply`：在干净基线中写入通过验证的候选并创建一个批次提交；不自动推送。
- `--push`：仅与 `--apply` 同用；以非 force 方式推送批次提交；失败返回 conflict。
- `--slug`：只处理指定 slug；不存在、禁用或非 GitHub 来源返回对应状态，不扫描其他来源。
- `--json`：stdout 只输出一行机器 JSON；诊断到 stderr，且不含凭证/响应正文。
- `--report`：写入封闭字段运行报告（JSON）；`--summary`：写入脱敏 Markdown 摘要。
- 不接受任意网页 URL、文件内容参数、token/PAT 参数或上游脚本执行参数。

## 2. 逐来源状态

| 状态 | 含义 | 当前内容 |
|---|---|---|
| `unchanged` | 解析成功，候选内容摘要与已同步/当前内容相同；或仅提交变化但内容相同 | 不变，无提交 |
| `candidate` | 候选有效但尚未应用（check 模式） | 不变 |
| `updated` | 候选有效并已写入批次提交（apply 模式） | 被完整替换 |
| `failed` | 来源不可达、截断、非法候选或内部读取失败 | 保留 |
| `conflict` | 本地内容偏离上次同步摘要、远端基线前进或推送被拒绝 | 保留 |
| `policy_blocked` | 许可缺失/变化或来源策略不允许自动替换 | 保留 |
| `unsupported` | provider 非 github、定位不受支持或未配置自动更新 | 保留 |

单项失败不使整批检查停止，也不删除/覆盖其他来源的当前版本。全局错误（参数、基线、内部异常）
返回非零退出码；逐来源失败通过报告表达。

## 3. 运行报告

```json
{
  "run_id": "<string>",
  "trigger": "schedule|workflow_dispatch|manual",
  "started_at": "<ISO 8601>",
  "finished_at": "<ISO 8601>",
  "changed": true,
  "commit_sha": "<40-hex|null>",
  "commit_status": "committed|not_applicable|failed",
  "sources": [
    {
      "slug": "example",
      "status": "updated",
      "resolved_revision": "<40-hex>",
      "content_digest": "<64-hex>",
      "previous_digest": "<64-hex|null>",
      "license_status": "present|missing|changed|not_applicable",
      "error_code": null,
      "checked_at": "<ISO 8601>"
    }
  ]
}
```

要求：字段封闭；`error_code` 只允许稳定错误码；报告和 stdout 不包含 token、cookie、响应正文、
环境变量、文件内容或原始异常。`updated` 必须有非空 `commit_sha`；`unchanged`/失败状态不得
伪造提交。

## 4. 应用与提交

- 应用前确认当前内容摘要等于 `last_synced_digest`；不相等返回 conflict。
- 候选必须来自同一不可变修订，且完整覆盖主文档/附件/许可；校验通过后才写入。
- 只写目标 Skill 的原件与 `catalog/<slug>.json`；整体替换，删除旧清单外文件；不使用
  `git add .`、不 reset/clean 用户工作区、不 force push。
- 一次运行的有效变更合并为一个批次提交；`git commit` 只包含本次目标路径。
- 成功提交后更新 `source_tracking.last_synced_revision`、`last_synced_digest`、`synced_at`；
  站内显示名、标签、备注、用法、分类和来源配置不被覆盖。
- 无变化不创建提交；相同修订/相同内容重复运行幂等。
- `--push` 前重新读取远端基线；远端前进、非 fast-forward 或分支保护拒绝返回 conflict，不降低保护。

## 5. 许可与冲突

- 启用的自动来源必须从同一修订的来源子树找到许可文件；仓库根/其他目录许可只作人工参考，
  不自动视为该子树适用许可；否则 policy_blocked。
- 候选许可路径变化或字节变化返回 policy_blocked，并记录许可状态；不自动假定仓库整体授权。
- 当前内容摘要偏离 `last_synced_digest` 返回 conflict；管理员可恢复跟踪或转手动维护。
- `last_synced_digest` 为空时，候选与当前内容一致可建立基线；不一致返回 conflict，不静默覆盖。
- 任何冲突/阻断都保留当前内容、当前站点和 Git 历史。

## 6. 退出码

| 退出码 | 含义 |
|---|---|
| `0` | 检查/应用完成；逐来源失败已在报告中表达 |
| `2` | 参数、catalog 或报告配置无效 |
| `4` | 全局基线冲突或推送被拒绝 |
| `5` | 全局来源/网络基础设施错误，无法完成运行 |
| `6` | 内部提交/报告写入失败 |

逐来源的 404/403/429/截断/许可/冲突不单独决定进程退出码；它们必须出现在报告和摘要中。

## 7. 不变量

- 不执行上游脚本、测试或安装依赖；不跟随符号链接/子模块。
- 候选、提交、构建和部署来自同一内容快照；同步提交后 build 必须 checkout 该提交。
- 许可、本地修改和并发冲突优先于“有更新”；失败不得删除当前版本。
- 公开页面不展示运行日志或内部错误；运行报告不进入搜索索引。
