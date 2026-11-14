# US-007 Demo-002：上游升级到单一新版（受控）

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: T008–T010；POC-003 受控证据、许可基线、T020 重跑/恢复、生产调度现状。
**复核方式**: 读取 `specs/006-source-auto-update/validation/`，并用 GitHub API 核对来源提交、tag、
POC 运行 job、许可摘要和生产 catalog/运行记录。未重新执行 POC 同步，未写生产内容。

复核命令（节选，均只读）：

```bash
gh api repos/chengxuan2002-droid/skill-gallery/contents/catalog/code-review-assistant.json
gh api repos/chengxuan2002-droid/skill-gallery/actions/runs/43533439066/jobs
gh api repos/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43208983544/jobs
gh api repos/chengxuan2002-droid/skill-gallery-source-poc-20261112/commits/7e8437e664af276afa4343d324d40dda9a69cb1d
gh api repos/chengxuan2002-droid/skill-gallery-source-poc-20261112/git/tags/00907bf1422bf620316e320b682e2d48a857babc
```

**结论**: `受控通过`。POC-003 验证了 v1→v2 单版本替换、旧附件清理、许可基线、无变化、部署失败、
同提交重跑和受控 revert；生产 `source_tracking` 仍全部为 `null`，没有发生生产自动更新。

## 1. T008 POC-003 复核

### 1.1 来源与修订

| 角色 | 仓库 | 说明 |
|---|---|---|
| 源 | `chengxuan2002-droid/skill-gallery-source-poc-20261112`（公开） | 含 `skills/poc-skill`、LICENSE、二进制与多修订 |
| 消费端 | `chengxuan2002-droid/skill-gallery-poc-20261107`（公开） | 复用 POC-002，运行 US-006 sync/build/deploy |

本次 API 复核确认：

| 修订 | 提交信息 | 复核结果 |
|---|---|---|
| `e679bab62906c77efb79168e99c8d53271ef1b64` | `source: v1` | 存在；annotated tag `v1.0.0`（`00907bf1...`）指向该提交，Release 非草稿、非预发布 |
| `7e8437e664af276afa4343d324d40dda9a69cb1d` | `source: v2 adds and removes attachments` | 存在；文件状态为 `SKILL.md` modified、`notes.txt`/`references/new.md` added、`references/old.md` removed |
| `592e3634a7e7abddc60785bd270aa8a0bb594f7b` | `source: v3 content change for license baseline` | 存在；用于建立许可基线 |
| `f9e30352a82d03e0f70ffc54247c3e41c448c9e4` | `source: change license to Apache-2.0` | 存在；许可变化阻断场景 |
| `7b02195f4ce62f6c01eecf938bf633303c5a7190` | `source: restore MIT license` | 存在；恢复 MIT 后为 `unchanged` |
| `4965bdae91c75089f2a74bb3134a565a411aecf0` | `source: v5 for same-commit rerun drill` | 当前源 `main` HEAD；用于 T020 重跑 |

仓库级检查结果沿用 `us6-check.md`：`branch` 解析为 `candidate`，`release latest` 与 `pinned` 保持
`unchanged`，不存在的仓库返回 `failed`/`E_SOURCE_NOT_FOUND`。本次未重新执行远程检查。

### 1.2 单版本替换与无变化

| 场景 | run | 本次 API 复核 | 结果 |
|---|---|---|---|
| 基线同步（v1） | `43208732789` | sync/build/deploy 均 success | 只更新来源基线字段 |
| v2 替换 | `43208983544` | sync/build/deploy 均 success | 提交 `7b439a18f6d3`；旧附件删除、新增文件出现 |
| 无变化 | `43209635536` | sync success；build/deploy skipped | 未创建空提交 |
| 当前 POC 树 | — | 仅 `skills/source-poc` 一个版本；含 `LICENSE`、`SKILL.md`、`assets/binary.bin`、`notes.txt`、`references/new.md`，无 `references/old.md` | 单版本成立 |

当前 POC 消费端 catalog 的 `source_tracking` 为：

```json
{"provider":"github","repository":"chengxuan2002-droid/skill-gallery-source-poc-20261112",
 "path":"skills/poc-skill","ref_policy":"branch","ref":"main","enabled":true,
 "last_synced_revision":"4965bdae91c75089f2a74bb3134a565a411aecf0",
 "last_synced_digest":"b2dbc03c8eb73b1aa3b59f1dbf5e08c74d3774e2643258b97cbb4f4f9d1196f5",
 "last_synced_license":{"path":"LICENSE","sha256":"ec43df0d8f2e9fab215c219f27be7498c7cf8d37b34c580fcdd38e124935551d"}}
```

复核时另见 POC 消费端 2026-11-14 08:21:58 CST 的 schedule run `43533694919`：sync/build/deploy
均 success，提交 `e68b78c7583c`，将当前来源 v5 再次同步为单一版本。该运行属于受控 POC，不是生产，
也不改变 T020 已记录历史运行的结论。

### 1.3 许可基线

| 源修订/场景 | 消费端 run | 本次 API 复核 | 结果 |
|---|---|---|---|
| v3 内容变化、许可 MIT | `43373881404` | sync/build/deploy 均 success | 提交 `40d8cfc33d69`，写入 `last_synced_license` |
| 许可改为 Apache-2.0 | `43374128999` | sync success；build/deploy skipped | `policy_blocked`/`E_LICENSE_CHANGED`；无新提交 |
| 恢复 MIT | `43374438621` | sync success；build/deploy skipped | `unchanged`；未新建提交 |

本次直接核对了来源许可字节：

| 修订 | LICENSE SHA-256 | 首行 |
|---|---|---|
| `f9e30352a82d...` | `1c85b4439c882ab6d23b99ffc8c8274589cc7d30184e94ef430f1aa6928947e5` | Apache-2.0 |
| `7b02195f4ce6...` | `ec43df0d8f2e9fab215c219f27be7498c7cf8d37b34c580fcdd38e124935551d` | MIT |

恢复 MIT 的摘要与 POC catalog `last_synced_license.sha256` 完全一致，说明许可按路径与字节摘要比较，
不是只看文件名或仓库级声明。

### 1.4 T020 部署失败、同提交重跑与受控 revert

| 场景 | run | 本次 API 复核 job | 记录结果 |
|---|---|---|---|
| 部署失败 | `43420335014` | sync success、build success、deploy failure | 内容提交 `a542e872f2ba`；线上保留旧 revision `e489a35a...` |
| 同一提交重跑 | `43420502326` | sync skipped、build success、deploy success | 无新内容提交；线上 revision 变为 `e52d42db...` |
| 受控 revert | `43420712186` | sync skipped、build success、deploy success | 恢复提交 `8e93adaf924b`；线上回到 `e489a35a...`，slug/digest 保持，历史未改写 |

`43420335014` 的 workflow 总结论为 failure，不能让 build 成功掩盖 deploy 失败；job 级复核与
`us6-status.md` 一致。受控 revert 后，POC 后续 schedule run 已按当前来源重新同步 v5（见 1.2），
这是受控环境的正常更新，不构成第二版本。

### 1.5 未运行与限制

- 真实 403、限流等待、真实截断树、真实子模块/符号链接、真实二进制下载逐字节对比未运行；
  由注入测试覆盖，不能写成远程通过。
- 生产 environment 审批、生产部署失败注入、发布后 MIME/缓存未运行。
- POC-003 是受控公开仓库验证，不替代生产调度、生产来源配置或生产发布授权。

## 2. T009 生产 catalog 与调度状态

### 2.1 生产 catalog

生产 `main` HEAD 为 `243c5df94c3658e7b5663bb90035b6cfbd27bea3`（2026-11-14 05:16 CST）。
通过 GitHub API 读取 `catalog/` 四项：

| slug | source_type | source_tracking |
|---|---|---|
| `code-review-assistant` | `github` | `null` |
| `handoff-codex` | `self-built` | `null` |
| `refactoring-workflow` | `marketplace` | `null` |
| `superpower-systematic-debugging` | `self-built` | `null` |

即使 `code-review-assistant` 的 `source_type` 为 `github`，其 `source_tracking` 仍为 `null`，没有配置
可检查/应用的来源。生产尚无真实来源。

### 2.2 Maintain site 运行

生产 `main` 的 `.github/workflows/maintain.yml`（同一 SHA）包含：

- `schedule: - cron: '17 19 * * *'`（UTC），对应每日 03:17 Asia/Shanghai；
- `workflow_dispatch` 提供 `sync` 输入；
- `sync` job 仅在 schedule 或手动 `sync=true` 时运行。

2026-11-14 延迟 schedule run：

| 项 | 值 |
|---|---|
| run | `43533439066`（Maintain site，`schedule`，run_attempt 1） |
| 触发时间 | 2026-11-14T00:19:43Z = 08:19:43 CST |
| head_sha | `243c5df94c3658e7b5663bb90035b6cfbd27bea3` |
| sync job | success（00:19:46Z–00:20:03Z） |
| build job | skipped（00:20:04Z） |
| deploy job | skipped（00:20:04Z） |
| 总结论 | success |

预期窗口为 2026-11-14 03:17 CST；实际出现时间晚约 5 小时 2 分 43 秒。`us6-workflow.md` 记录的
03:17–05:10 CST 轮询未出现 run，与此一致。运行列表中同日没有其他 Maintain site schedule run；
`Site availability` 的小时级 schedule 属于独立监测，不是内容同步。

同一天的生产 push run `43509219426` 为 sync skipped、build success、deploy success，head_sha 同为
`243c5df`；它触发于 2026-11-14 05:16 CST，与上述延迟 schedule run 是不同事件。

### 2.3 结论

- **配置已启用**：生产 `main` 的每日 03:17 CST schedule 已存在并可触发。
- **实际来源未配置**：四项 catalog 的 `source_tracking` 均为 `null`，因此当场 sync 没有来源可检查，
  build/deploy skipped，未产生内容提交，也没有生产自动更新。
- **准点未承诺**：首次 03:17 CST 窗口未按时出现，08:19 CST 出现延迟 run；只能记录为“已观察到的
  延迟 schedule 触发”，不能写成准点 SLA，也不能把该 run 写成生产自动更新。
- **下一窗口**：2026-11-15 03:17 CST 尚未到达，未运行。

## 3. T010 状态与边界

- Demo-002：`受控通过`（POC-003 受控仓库证据）。
- AC-009（自动替换/单版本/增删附件/站内字段）：`受控通过`；生产来源未配置，未发生生产自动更新。
- AC-010（404/限流/非法/许可/本地修改/冲突/重跑）：`受控通过`；真实 403/限流未运行。
- AC-011（状态与恢复）、AC-014（构建部署/固定地址）：仍为 `未运行`，分别由待执行的 T012–T013、
  T014 复核；本文件只提供 T020 受控运行和生产调度记录，不提前判定通过。
- 未运行项：真实 403/限流、真实截断/子模块/符号链接、生产 environment 审批、生产部署失败注入、
  发布后 MIME/缓存、2026-11-15 03:17 CST 窗口。均不计为通过。
