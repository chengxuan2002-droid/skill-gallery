# US-007 最终复核

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: T022；对照 `spec.md`、`plan.md`、`tasks.md`、`acceptance-matrix.md` 和全部 validation
做最终复核。只做只读检查和已有证据汇总，不新增功能、不写生产内容。
**结论**: **有条件验收/交接**。22 项任务已执行；Demo-001～003 为受控通过；所有 AC 至少有一条
证据（4 项通过、11 项受控通过），但受控通过项含未运行子项，**不判定整包通过**。

## 1. 任务与矩阵

| 项 | 结果 |
|---|---|
| tasks.md | T001–T022 全部 `[X]`；22/22 执行 |
| Demo-001 维护到取用 | `受控通过`（手动/CLI/生产数据；浏览器复制未重跑） |
| Demo-002 来源升级到单一新版 | `受控通过`（POC-003；生产来源未配置） |
| Demo-003 失败/冲突到恢复 | `受控通过`（POC/隔离 + 49 项定向测试） |
| AC-001～AC-015 | 4 项 `通过`、11 项 `受控通过`、0 项 `未运行` 行、0 项 `失败` |
| 故事汇总 US-001～US-006 | 均为 `受控通过` |

`通过`：AC-001、AC-002、AC-006、AC-007。其余 AC 为 `受控通过`，因为仍有未运行的远程/生产/设备
子项；这些子项集中在 `residual-gaps.md`，没有计入通过。

## 2. 证据覆盖

| 领域 | 证据 |
|---|---|
| 矩阵与索引 | `acceptance-matrix.md`、`evidence-index.md` |
| 维护到取用 | `demo-001.md`、`fidelity.md` |
| 来源升级 | `demo-002.md`；`specs/006-source-auto-update/validation/us6-poc.md`、`us6-license.md`、`us6-status.md` |
| 失败与恢复 | `demo-003.md`；`us3-recovery.md`、`us6-conflict.md`、`us6-status.md` |
| 固定地址/浏览器 | `fixed-address.md`；`us2-accessibility.md`、`us2-cross-browser.md` |
| MIME/缓存与远程错误 | `fixed-address.md`、`remote-errors.md` |
| 生产 env/部署失败 | `production-environment.md` |
| macOS runner | `macos-ci.md`；`specs/001-preserve-skill-content/validation/platform.md` |
| US-005 真实导入/等待 | `specs/005-skill-cli/validation/us5-real-gh.md` |
| 保真 | `fidelity.md`；`tests/integration/distribution.test.js` |
| 安全 | `security.md`；`tests/integration/publish/publish-security.test.js`、`tests/unit/path-attacks.test.js` |
| 汇总检查 | `quality.md` |
| 交接 | `handoff.md`、`residual-gaps.md` |
| 文档状态 | README 的 US-007 章节、AGENTS.md 的 US-007 段落 |

## 3. 实际验证命令与结果

| 命令/检查 | 结果 |
|---|---|
| `npm run check` | 退出码 0；lint/format 通过；286 项测试：284 通过、0 失败、2 跳过 |
| `npm run security` | 退出码 0；secrets 362、code 56、deps 1，findings 0 |
| Node 26.3/Linux Quality checks | run `43609150035` success（282 项）；US-005 分支 run `43613336137` success（286 项 285 通过/0 失败/1 跳过） |
| 49 项来源/冲突/安全定向测试 | 49/49 通过 |
| 27 项发布安全/路径/不可信内容测试 | 27/27 通过 |
| `node --test tests/integration/distribution.test.js` | 4/4 通过；二进制/许可/空目录/mode |
| `node --test tests/unit/share-link.test.js tests/unit/list-view.test.js` | 6/6 通过 |
| 生产 `npm run monitor:site` | 首页/app.js/style/index 均 200 |
| 生产 MIME/缓存头 | 首页/详情/raw/ZIP 200；JSON/octet-stream/x-zip-compressed；`Cache-Control: max-age=600` |
| 生产详情/raw/ZIP 复核 | 4 项详情与索引 revision 一致；raw/ZIP 字节和 SHA-256 与本地一致；ZIP 3 条，0755/0644 |
| 真实远程错误 | 公开示例仓库 runners 请求返回真实 403（只读、无副作用）；core 限额剩余 4982，未触发 429 |
| 生产 environment 审批 | run `43587421323` deploy 真实等待 required reviewer；审批后 success；设置已恢复 |
| 生产部署失败注入 | run `43588024409` build success/deploy failure，旧站 revision `faa0f345...`；恢复后 run `43588215125` deploy success |
| macOS runner | run `43588719771`：Node 26.3.0，282 项 281 通过/0 失败/1 跳过；安全 0 发现；构建 revision `faa0f345...` |
| US-005 真实 `gh api` 导入 | POC-002 run `43612050209`：`us5-real-import` 提交 `19bf63c...`，build/deploy success |
| US-005 真实 `--wait` | POC-002 run `43612262185`：`us5-real-wait` 提交 `1017dd4...`，命令返回 published/built/published |
| POC 二进制 URL | `assets/binary.bin` 5 字节，SHA-256 `ff5d8507...` 与来源/详情一致 |
| POC run `43420335014` | sync/build success，deploy failure；旧站保留 |
| POC run `43420502326` | 同提交重跑，build/deploy success；无新内容提交 |
| POC run `43420712186` | 受控 revert，恢复线上 revision，历史未改写 |
| 生产 schedule run `43533439066` | 延迟触发（08:19 CST），sync success，build/deploy skipped |
| 干净副本命令 | preview/add/status/build/preview 服务/publish-check/revert 的实际退出码见 `handoff.md` |

## 4. 未运行项与影响

以下项目仍未运行，不能计入通过：

- MIME/缓存基础头已复核；CDN 边缘缓存清除和浏览器强刷后的资源一致性未运行。
- 真实 source-sync 429（已观察一次真实 403；429 未触发）、真实截断树/子模块/符号链接。
- Safari 实机、移动实机、读屏器语音；真实浏览器复制/下载交互。
- 2026-11-15 03:17 CST 调度窗口。
- 生产真实来源自动更新（生产 `source_tracking` 仍全部为 `null`）。
- 物理 Mac、所有 macOS 硬件/文件系统变体（GitHub-hosted macOS runner 已通过）。

影响和补验方式见 `residual-gaps.md`。这些缺口影响关键 AC 的完整性，因此最终结论只能是
有条件验收/交接，不是整包通过。

## 5. 规格与边界

- 本轮未修改 `skills/`、`catalog/`、前端、schema、发布权限或生产内容；只新增/更新 `specs/007-overall-acceptance/`
  证据与 README/AGENTS 状态。
- 未新增依赖或架构；`npm ci` 只恢复本地开发依赖，未改锁文件。
- 生产只读；受控写入仅限 POC/隔离副本。Demo-002 仍是 POC-003 受控证据，不是生产自动更新。
- 未把延迟 schedule run 写成准点 SLA，未把提交/构建成功写成已发布，未把本地/受控结果写成生产验收。

## 6. 最终结论

US-007 的验收矩阵、证据、交接材料和恢复入口已建立；Demo-001～003 的主链路和失败/恢复路径有可追溯
证据，质量与安全检查通过；生产 MIME/缓存基础头、真实 403、生产 environment 审批、生产部署失败
注入、GitHub-hosted macOS runner、US-005 真实 `gh api`/`--wait` 和 POC 二进制 URL 已补验。由于仍有
真实 source-sync 429、真实截断/子模块/符号链接、Safari/移动实机、CDN/强刷、2026-11-15 调度窗口和
生产真实来源等未运行项，**本次仍为有条件验收/交接，不宣称 US-007 整包通过，也不宣称生产自动更新
已发生**。后续按 `residual-gaps.md` 补验并重新评估。
