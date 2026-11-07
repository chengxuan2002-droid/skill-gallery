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

**状态**: 未运行。未提供受控测试仓库、Pages 源切换和 environment 修改授权；用户要求
不自动推送或发布。当前 `origin` 仍是生产仓库 `chengxuan2002-droid/skill-gallery`，当前分支
`codex/us-003-validate-build-publish` 未推送。

只读核对（未修改任何远程设置）：

| 检查 | 结果 |
|---|---|
| `gh api repos/chengxuan2002-droid/skill-gallery/pages` | `build_type=legacy`，`source=main:/`，`status=built` |
| `gh api repos/chengxuan2002-droid/skill-gallery/environments/github-pages` | `protection_rules=[branch_policy]` |
| `npm run monitor:site` | 通过；首页、`assets/app.js`、`assets/style.css`、`assets/search-index.json` 均 HTTP 200 |
| `git remote -v` | 仅配置生产仓库 `origin`，未发现受控测试仓库 |

上述只读探测只证明当前站点可读和 Pages 仍为旧源，不证明部署失败保留、同一提交重跑或
受控环境权限。本轮未推送、未切换 Pages 源、未触发 workflow、未部署。

解除条件：提供受控测试仓库及明确授权后，按 [quickstart.md](../quickstart.md) 第 6 节切换
Pages 源，注入部署失败，确认旧站可用，再按同一 commit 重跑成功，并记录运行 URL、目标 SHA、
状态和未运行项。

## 7. 未运行与限制

- T018 的受控仓库 POC-002 未运行，原因见第 6 节；不得把本记录的本地模拟当作远程发布通过。
- 未在 Node 26.3.0/npm 11.16.0、Linux/CI 或真实 GitHub runner 上运行。
- 未验证浏览器刷新、线上 MIME/缓存或真实回滚；这些留待受控环境验证。
- T033 已在 build/deploy Step Summary 中补齐完整 RunStatus 字段，见
  [us3-summary.md](us3-summary.md)；本记录只验证状态模型和失败保留语义，不代表远程运行通过。
