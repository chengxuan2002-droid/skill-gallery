# US2 失败保留、过期与重跑验收（T017）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 运行 T014–T016；在隔离项目模拟部署失败、`superseded` 和同一提交重跑；不修改工作区
`dist/`、不触发真实 Pages 部署、不写入远程仓库。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线仍为 Node 26.3.0/npm 11.16.0）。

## 1. 测试契约

```text
node --test tests/unit/publish-status.test.js tests/integration/publish-superseded.test.js tests/integration/publish-deploy-workflow.test.js
```

结果：退出码 `0`；11 项通过、0 失败、0 跳过。覆盖状态分离、`superseded` 非成功、CLI
`0/4/2` 退出码、目标检查先于部署、无 `continue-on-error` 和破坏性回滚命令。

## 2. 隔离项目

使用 `tests/support/publish-fixture.js` 创建系统临时项目并调用 `scripts/lib/build-site.js`
生成临时 `dist/`；未复制工作区 `dist/`，未执行收录 Skill 的脚本。临时脚本只作本地演练，
未提交到仓库。

| 项 | 结果 |
|---|---|
| 首次构建 | `ok=true` |
| `contentRevision` | `c48791d508cf5e3b306d21f8ce60330c391538d5505e248704bae35bac980578` |
| `verifyArtifact` | `status=verified`，`files=20`，`diagnostics=[]` |
| 隔离内容提交 | 临时 Git 仓库提交 1 个基线内容提交；`git rev-list --count HEAD=1` |

## 3. 部署失败模拟

在合法产物校验通过后，用 `node -e "process.exit(1)"` 模拟部署步骤失败；未调用
`actions/deploy-pages`，未访问网络。

| 检查 | 结果 |
|---|---|
| 失败退出码 | `1` |
| 旧 `dist/` 文件集合、大小、SHA-256 | 与失败前完全一致 |
| RunStatus | `content_status=built`、`deploy_status=failed`、`commit_status=committed` |
| 摘要 | 分别显示 `Content status: built` 与 `Deploy status: failed`，不显示 `published` |
| 失败原因 | `E_DEPLOY_FAILED` |

## 4. `superseded` 模拟

使用伪造的目标 SHA `34a04005bcaf206eec990bd9637d9fdb6725e0a0` 与远端 SHA
`b71199ebd070b36beab7317920c2c2f1d777df8d` 调用：

```text
node scripts/publish-check.js target --target <target> --remote <remote>
```

结果：退出码 `4`，`decision=superseded`。旧 `dist/` 未变化；RunStatus 为
`content_status=built`、`deploy_status=superseded`；摘要显示 `Deploy status: superseded`，
不显示 `published`。

## 5. 同一提交重跑

对同一隔离项目再次构建并校验：

| 检查 | 结果 |
|---|---|
| 第二次构建 | `ok=true` |
| `contentRevision` | 与第一次相同 |
| 产物集合、大小、SHA-256 | 与第一次相同 |
| 临时 Git 提交数 | 重跑前 `1`，重跑后 `1`，未新增内容提交 |

## 6. 受控仓库 POC-002（T018）

**状态**: 已完成（临时公开仓库）。临时仓库在私有状态下创建 Pages 返回 HTTP 422（当前计划
不支持私有仓库 Pages），经用户授权将同一临时仓库
`chengxuan2002-droid/skill-gallery-poc-20261107` 改为公开后继续。该仓库只包含站点、脚本、测试和 workflow
所需文件，排除 `docs/`、`specs/`、`handoff/`、`.agents/`、`.specify/`、`AGENTS.md` 与
`instructions.md`。为隔离 Pages 部署机制，临时仓库的 workflow 是 POC 精简版：保留
build、artifact 校验、上传、目标判定、摘要和失败注入，移除 `setup:security`、`npm run check`
与 `npm run security`；生产 `maintain.yml` 未修改。临时仓库当前仍为公开状态，尚未删除。

| 检查 | 结果 |
|---|---|
| 临时仓库 | `https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107`，`main` |
| Pages source / environment | `build_type=workflow`；`github-pages` environment `branch_policy` |
| 目标提交 | `8c86a3972580cb8053a4843d17fd17f4d32a909e` |
| `contentRevision` | `82afef70fa4bedfe243723263a11c75a900d433f8e35e7374f2ae747ae0d23b8` |
| 首次 push 运行 | [42355651634](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42355651634)：build/deploy 均成功 |
| 部署失败运行 | [42355755607](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42355755607)：build 成功；deploy 失败于 `POC deploy failure injection`，`Deploy to GitHub Pages` 跳过，`Write publish summary` 成功 |
| 同一提交重跑 | [42355846761](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/42355846761)：同一目标提交，build/deploy 均成功 |
| 临时站点 | `https://chengxuan2002-droid.github.io/skill-gallery-poc-20261107/`；失败前、失败后、重跑后均 HTTP 200、1,417 字节，SHA-256 均为 `4B87C0B98586D551A3FB18FB899B66079CB2F7512CE2ABB286F55D19014E53F2` |
| 失败开关 | 临时仓库变量 `POC_FAIL_DEPLOY=1` 触发失败；重跑前已删除，当前变量列表为空 |
| artifact 校验 | `status=verified`，`content_revision` 与上表一致，`files=25`，`diagnostics=[]` |
| 生产 Pages | 仍为 `build_type=legacy`、`source=main:/`、`status=built`，未修改 |

失败运行中 build job 成功、deploy job 失败，说明“已构建、部署失败”可区分；失败前后临时站点
响应字节与摘要不变，说明旧站保留。同一目标提交在清除失败开关后重跑成功，说明重跑幂等且不依赖
新内容提交。

## 7. 未运行与限制

- T018 已完成受控 POC-002，但临时仓库使用精简 workflow，未在临时仓库运行完整
  `npm run check`/`npm run security`；生产工作流仍未远程执行。
- T018 已在 GitHub runner（Node 26.3.0/Linux）运行；T014–T017 的本地结果仍来自
  Node 22.21.0/Windows。
- 未验证浏览器刷新、线上 MIME/缓存或真实回滚；T018 只验证 HTTP 200、响应摘要和旧站保留。
- T033 已在 build/deploy Step Summary 中补齐完整 RunStatus 字段，见
  [us3-summary.md](us3-summary.md)；本记录只验证状态模型和失败保留语义，不代表生产发布通过。
- 临时公开仓库尚未删除；如需清理，应单独确认后删除。

## 8. 隔离恢复演练（T031）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 在系统临时目录复制正式站点内容（`index.html`、`assets/`、`catalog/`、`skills/`），
初始化独立 Git 仓库，依次生成基线提交、内容变更提交和 `git revert` 恢复提交；每次重新构建并
记录 `contentRevision`。不配置远程、不推送、不 force push，不触碰工作区 `dist/` 或生产 Pages。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`；构建使用 `scripts/lib/build-site.js`。

### 8.1 提交与内容标识

| 步骤 | 临时提交 | `contentRevision` |
|---|---|---|
| 基线提交 | `80bbe76642b0f576de9489fb935378abacdccce3` | `f8143ad0059b30bd1404c4ef9d05f40559525ecbdcb47d2a8b2dabdbb032006d` |
| 内容变更（`catalog/refactoring-workflow.json` 的 `notes`） | `d9c2f3e4d109503bbc420e870638149f2504b3dd` | `a114c23eac4448f9d7f15277ccede2c810cd122f374fbfe660c8e3a731ac5ca6` |
| `git revert --no-edit HEAD` 恢复提交 | `699aff41533b57da0b205712e2f5683dcee850b5` | `f8143ad0059b30bd1404c4ef9d05f40559525ecbdcb47d2a8b2dabdbb032006d` |

恢复后 `contentRevision` 与基线完全一致；变更提交产生了新的内容标识，说明恢复走的是重新构建而不是
复用旧产物。

### 8.2 一致性与历史

| 检查 | 结果 |
|---|---|
| 临时仓库提交数 | 3（基线、变更、revert），历史保留 |
| 远程配置 | 空；未推送、未 force push |
| 既有 slug | 4 个，与恢复前一致 |
| 旧 `#/skill/<slug>` 链接 | `#/skill/code-review-assistant`、`#/skill/handoff-codex`、`#/skill/refactoring-workflow`、`#/skill/superpower-systematic-debugging`；对应详情文件均存在 |
| 当前单版本 | `details/` 仅 4 个 JSON，索引 4 项，slug 无重复 |
| 产物文件数 | 24，与基线一致 |
| 原文/附件保真 | 6 个原始文件字节与 SHA-256 一致，frontmatter 保留；目录 ZIP 3 个文件字节一致 |

### 8.3 未运行与限制

- 演练在临时副本执行，未在受控仓库或生产环境做真实回滚部署。
- 浏览器刷新、线上 MIME/缓存和旧链接的交互行为仍以 US-001/US-002 既有证据为准，本轮未复验浏览器。
- 临时副本在演练结束后删除；命令与结果仅保留在本记录。
