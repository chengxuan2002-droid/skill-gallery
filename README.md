# Skill Gallery

## 本地工程开发

固定站点：[Skill Gallery](https://chengxuan2002-droid.github.io/skill-gallery/)，资源前缀为 `/skill-gallery/`。
本项目已部署；本地初始化不重新建仓、不修改部署地址，也不自动发布。

运行环境：Node **26.3.0**（见 `.node-version`）、npm **11.16.0**。首次安装安全扫描器还需要
[uv](https://docs.astral.sh/uv/) 和网络；安装器为 Semgrep 选择 Python 3.12.13，工具保存在被忽略的 `.tools/`，不安装收录 Skill 的依赖。

```bash
npm ci
npm run setup:security
npm run check
npm run security
```

| 命令 | 用途 |
|---|---|
| `npm run lint` | 自有浏览器/Node JS 的 ESLint 检查 |
| `npm run format:check` | 自有站点与工程文件的只读格式检查 |
| `npm test` | 显式运行受信任的 unit/integration 测试，包含真实扫描器拒绝样例 |
| `npm run setup:security` | 安装/核对固定版本 Gitleaks、Semgrep；重复运行复用已匹配工具 |
| `npm run security:secrets` | 对公开候选和已跟踪原件做脱敏凭证检查 |
| `npm run security:code` | 对自有 JS 执行本地固定安全规则 |
| `npm run security:deps` | 通过官方 npm registry 审计根锁文件；high/critical 阻断，其他级别报告 |
| `npm run check` / `npm run security` | 分别汇总规范/测试、安全检查；保留真实失败退出码 |

安全结果只输出规则、位置、级别及状态，不输出凭证或源码片段。
见[诊断约定](specs/001-preserve-skill-content/validation/diagnostics.md)和[本次验证](specs/001-preserve-skill-content/validation/bootstrap.md)。
当前本地审计为 0 个漏洞（通过 `minimatch@11.0.4` override 清除开发工具传递依赖的 4 个 moderate；
历史 CI 运行曾报告 6 个 moderate），证据见
[US-002 质量门禁](specs/002-search-detail-share-redesign/validation/us2-quality.md)。
本机默认镜像 registry 不实现 npm audit 端点，`security:deps` 固定使用官方 registry；原因与验证见
[依赖审计记录](specs/001-preserve-skill-content/validation/dependency-audit.md)。
Windows 下由 `.gitattributes` 保持项目文本为 LF，测试夹具使用 junction；安装器支持 Windows zip 与
`gitleaks.exe`/`semgrep.exe`，但仍需网络。扫描器未安装时，`npm test` 中两项扫描器用例与 `npm run check`
会失败，不能视为通过；当前环境复核见 [跨平台基线与缺口修正](specs/001-preserve-skill-content/validation/baseline-remediation.md)。

本轮已接入本地 `npm run build` 与 `npm run preview`（仅 `dist`，不发布）。
US-001 的内部 US1/US2/US3 切片已完成本地交付：四份 catalog、四项迁移、完整 dist 构建、只读预览、
完整查阅/复制/下载和故障恢复均有本地证据；T041 仅 Linux/WSL 通过、macOS 未运行，2026-11-04 用户确认
将该缺口记录为未验证并据此收口本地交付，T041 不标记为通过。
US-002 的检索、详情、分享、响应式和键盘可访问改造已完成 T001–T026 的本地实现、验收与文档收口：
- 检索/详情/分享：[US2 检索](specs/002-search-detail-share-redesign/validation/us2-search.md)、
  [详情/分享](specs/002-search-detail-share-redesign/validation/us2-detail.md)、
  [可访问性](specs/002-search-detail-share-redesign/validation/us2-accessibility.md)。
- 质量/性能/构建/回归：[质量门禁](specs/002-search-detail-share-redesign/validation/us2-quality.md)、
  [性能](specs/002-search-detail-share-redesign/validation/us2-performance.md)、
  [隔离构建](specs/002-search-detail-share-redesign/validation/us2-build.md)、
  [US-001 取用回归](specs/002-search-detail-share-redesign/validation/us2-regression.md)、
  [跨浏览器](specs/002-search-detail-share-redesign/validation/us2-cross-browser.md)、
  [生产只读预检](specs/002-search-detail-share-redesign/validation/us2-production-preflight.md)。
- US-002 收口时本地 `npm test` 为 163 项（162 通过、0 失败、1 跳过）；Gitleaks/Semgrep 无发现，
  依赖审计为 0 个漏洞。
- 浏览器证据来自 Chrome 152（Chromium）、Edge 156、Firefox 157.0 和 WebKit 27.2；
  1,000 项/10 MiB 隔离夹具上 50 次查询 p95 分别为 Chrome 39.9ms、Firefox 48.0ms、WebKit 50.0ms，
  不是生产网络或设备承诺。仍需补 Safari/移动实机。
- US-002 的 T025 文档更新和 T026 最终复核已完成。2026-11-06 已推送功能分支；
  [Quality checks #42170060519](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/42170060519)
  在 Node 26.3.0/Linux 成功；该时点尚未合并 main，后续已合并并启用生产发布；
  自动更新仍待 US-006。

2026-11-07 US-003 的 T001–T032 与 T033 已完成本地/受控验证：发布产物校验、`publish-check.js`、
`maintain.yml`、US1 快照/子路径、US2 状态/失败/恢复、US3 凭证/权限/匿名未授权尝试、US4 同次运行/noop、
隔离恢复演练与取用回归见
[US-003 validation](specs/003-validate-build-publish/validation/)；临时公开仓库 POC-002 验证了
部署失败/旧站保留/同提交重跑、同次运行发布和匿名未授权拒绝。US-003 收口时本地 `npm test` 为 211 项
（209 通过、0 失败、2 跳过）；已推送并创建
[PR #1](https://github.com/chengxuan2002-droid/skill-gallery/pull/1)
（Quality checks 42382079287/42382097367 通过），已合并到 main；生产 Pages 已切换为 GitHub Actions 并成功发布（run 42396936423 / 42397297833）。

2026-11-07 US-004 的 T001–T015 已完成本地验证：GitHub 后台手动维护步骤、页脚低权重“管理”外链、
必填字段与失败/替换/下架/恢复说明，以及隔离构建、失败批次、生命周期和入口证据见
[US-004 validation](specs/004-manual-skill-maintenance/validation/)；当前本地 `npm test` 为 220 项
（218 通过、0 失败、2 跳过）。T016/T017 已完成受控发布与最终复核；生产 Pages 已切换，
手动提交/本地构建需经 Actions 发布，不把本地结果当作线上发布。

2026-11-08 US-005 的 T001–T023 已完成本地/受控验证：`skill-cli` 的 preview/add/import/replace/status、
JSON 输出与退出码、隔离 worktree、临时裸远端和 POC-002 新增/替换/状态查询证据见
[US-005 validation](specs/005-skill-cli/validation/)；US-005 收口时本地 `npm test` 为 241 项
（239 通过、0 失败、2 跳过），2026-11-12 复核为 242 项（240 通过、0 失败、2 跳过）。T023 quickstart
走查已完成；生产 Pages 已切换，Agent 命令/本地构建需经 Actions 发布，不把本地结果当作线上发布。

本地验收使用 Windows + Node 22.21.0；声明的 Node 26.3.0/Linux 由 CI 覆盖，结果见下方 Quality checks。
初始化按步骤验证并提交，提交不等于推送或上线。

### 手动维护（GitHub 后台）

访客只读；新增、修改、显式替换和下架由管理员通过 GitHub 仓库后台完成，不提供站内登录或上传接口。
前提是对仓库有写权限；生产 Pages 已使用 “GitHub Actions” Source，内容合并到默认分支后由
`maintain.yml` 发布。

1. 在 GitHub 网页后台添加原件：单文件为 `skills/<slug>.md`；目录型为 `skills/<slug>/SKILL.md`
   及其附件。目录按文件夹上传，不要求 ZIP 解压。
2. 添加或更新 `catalog/<slug>.json`，至少包含：

   | 字段 | 必填 | 说明 |
   |---|---|---|
   | `schemaVersion` | 是 | 固定为 `1` |
   | `slug` | 是 | 小写字母、数字和短横线，≤64，与目录/文件名一致 |
   | `display_name` | 是 | 站点显示名 |
   | `description` | 是 | 一句话简介 |
   | `content_path` | 是 | `skills/<slug>.md` 或 `skills/<slug>/SKILL.md` |

   `tags`、`platforms` 可省略或为空数组；其他字段可选，未知字段会被拒绝。
3. 提交到默认分支。`Maintain site` 工作流会执行既有检查、构建、产物校验与发布；非法批次整批阻止。
4. 在 Actions 运行记录中查看结果：提交、构建和部署状态分开显示；失败时旧站保留。提交成功或本地
   `npm run build` 成功不等于已发布，只有部署成功且站点可访问才算上线。

**失败处理**：任一非法条目会让整批校验/构建失败，不上传产物、不部署，现有站点保持可读。先按运行
记录中的稳定错误码定位，再修复并重新提交：

| 错误码 | 常见原因 | 处理方式 |
|---|---|---|
| `E_SCHEMA` | 缺必填字段、未知字段、字段类型错误 | 按记录中的 slug/字段补齐；不要猜测或添加未定义字段 |
| `E_PATH` | `content_path` 与 slug 不匹配、越界或使用反斜杠 | 改为 `skills/<slug>.md` 或 `skills/<slug>/SKILL.md` |
| `E_MAIN_MISSING` | 主文档不存在 | 补回主文档并确认路径大小写 |
| `E_REFERENCE_MISSING` | 正文引用的本地附件缺失 | 补回附件或移除失效引用 |
| `E_SECRET` | 疑似凭证（token、私钥、密码赋值） | 移除真实凭证并轮换；示例用 `YOUR_*_HERE`；诊断只报位置，不回显值 |

修复后重新提交即可；失败不会自动产生新内容提交，也不需要新建空提交。不要手动修改 `dist/`、删除
旧产物或降低分支保护来“通过”失败；运行日志和内部错误不进入访客页面。

**替换、下架与恢复**：

- **显式替换**：用完整新内容替换同一 slug 的原件（单文件或目录），保持 `catalog` 记录中的 slug 与
  `content_path` 不变后提交。构建只保留一个当前版本，新清单之外的旧附件会从详情、目录 ZIP 和
  索引关联中移除；不要为旧内容保留第二份目录或重复卡片。
- **下架**：删除对应原件（单文件或整个 Skill 目录）与 `catalog/<slug>.json` 后提交。构建后该条目从
  索引、详情和下载中消失；未纳管的本地文件不受影响，旧分享链接回到列表/未找到状态。
- **受控恢复**：需要回到上一份有效内容时，通过 GitHub 历史或 `git revert` 生成恢复提交，再走同一
  构建/发布流程；保持既有 slug、旧链接和单版本，不 force push、不清除历史。不要通过手工改
  `dist/` 或直接覆盖线上文件“恢复”。

自动来源检查/调度（US-006）、ZIP 解压和站内上传后台不属于当前能力；Agent CLI 见下节。

### Agent 命令（skill-cli）

前提：Node 26.3（本机可为 22.21）、Git 与已登录的 `gh`。命令复用现有 Git/gh 授权，
不要把 token 写入参数、仓库或示例。

```bash
node scripts/skill-cli.js preview <path> --meta <record.json>
node scripts/skill-cli.js add <path> --meta <record.json> [--publish] [--wait]
node scripts/skill-cli.js import --repo owner/repository --path skills/example --ref main --meta <record.json> [--publish] [--wait]
node scripts/skill-cli.js replace <slug> <path> --expected-revision <sha> [--meta <record.json>] [--publish] [--wait]
node scripts/skill-cli.js status --run <run-id>
```

- `preview` 与不带 `--publish` 的 `add` 只校验并输出预览，不写入、不提交、不推送。
- `add`/`import` 需要 `--meta`；`replace` 缺省保留原站内记录，传 `--meta` 时整体更新。
- `--publish` 才允许远端写入；`--wait` 只能与 `--publish` 使用，只有找到对应运行才轮询，
  否则保持 `submitted/pending`，不误报已发布。
- `import` 只接受结构化 `owner/repository`、`path`、`ref`；不接受普通网页 URL。
- stdout 只有一行 JSON：`status`、`slug`、`content_revision`、`content_status`、`deploy_status`、
  `commit_sha`、`run_url`、`public_url`、`errors`；诊断只含稳定码与位置，不回显凭证或正文。

| 退出码 | 含义 |
|---|---|
| `0` | 预览/noop/submitted/published 按要求完成 |
| `2` | 参数、元数据或校验失败 |
| `3` | 未授权或无写权限 |
| `4` | 冲突（期望基线不匹配、远端变化或非 fast-forward） |
| `5` | 来源读取失败（404/403/限流/截断/不支持） |
| `6` | 构建或产物校验失败 |
| `7` | 部署失败 |
| `8` | `--wait` 等待超时（保留运行链接） |

示例输出（占位值）：

```json
{"status":"submitted","slug":"example","content_revision":null,"content_status":"pending","deploy_status":"pending","commit_sha":"<COMMIT_SHA>","run_url":null,"public_url":null,"errors":[]}
```

排错：冲突时重新读取远端基线并用正确的 `--expected-revision`；来源错误检查定位是否结构化、
是否被截断；构建/部署失败查看运行记录；等待超时保留 `run_url`，不要重复提交制造空提交。
`status` 从运行和 job/step 派生；build 成功但 deploy 步骤跳过时为 `superseded`，未完成时为 pending。

**当前边界**：`skill-cli` 的新增/替换/状态查询已在受控 POC-002 完成真实发布；真实 `gh` 来源导入与
`--wait` 运行发现仍需补验。自动来源检查/调度（US-006）、ZIP 解压和站内后台尚未实现；生产 Pages
已切换为 Actions 并成功发布，但生产 environment 审批、部署失败注入和发布后 MIME/缓存验证未运行。
后续生产发布仍需单独授权。

### 当前内容与构建契约

- 原件位于 `skills/<slug>.md` 或 `skills/<slug>/SKILL.md`；`catalog/<slug>.json` 是独立站内记录。构建只读取 catalog 指向的内容，不扫描未纳管目录，不执行 Skill 脚本、测试或安装其依赖。
- 初始限额：每 Skill 最多 500 个普通文件、原始总字节 20 MiB、主文档 1 MiB。
- 迁移：`node scripts/migrate-catalog.js --dry-run`（默认）与 `--write` 仅处理四项固定记录；先验证全部候选，冲突不覆盖已有记录。
- 精确依赖：yaml 2.9.1、marked 18.1.2、sanitize-html 2.18.1、yazl 3.3.1、minisearch 6.3.0；yauzl 3.4.0 仅开发测试。ESLint/Prettier 等开发依赖见 `package.json` 与锁文件。
- `npm run build` 只写 `dist/`，不写根 `assets/search-index.json`；`npm run preview` 只映射 `dist` 的 `/skill-gallery/`。成功状态是本地 `built`，不是已发布。
- 构建事务使用 `.dist.lock/owner.json` 与 `.dist.transaction.json`。发现遗留锁时不要删除 dist、stage 或 backup；先确认原进程已退出并核对 owner 的 run_id/pid，只移除匹配锁，再重跑 `npm run build`。提交后清理失败会返回 `built` + `cleanup_status=pending`，保留记录/backup，不能当作发布成功。
- 凭证规则 SECRET-01～04 只报告安全位置和类型；示例使用 `YOUR_*_HERE`、`<REDACTED>`、`***` 或 `$ENV`，不得写入真实凭证。标题 ID 由构建器生成；重复标题使用后缀，未知本文锚点移除 href 并提示。
- `skill-cli` 已完成本地/受控验收并合并 main；自动更新（US-006）尚未实现。GitHub 后台手动维护见上文，
  Agent 命令见“Agent 命令（skill-cli）”。不要让旧版根索引/直接 Pages 教程冒充当前流程；生产 Pages
  已切换，MIME、缓存和直接资源安全仍需完整发布后验证。

### 检查 CI 与现站基础监测

- [Quality checks](.github/workflows/quality.yml)：所有 push、PR 和手动触发，安装固定工具后运行 `npm run check`，并显式执行 Gitleaks、Semgrep 与根依赖审计；任一步失败汇总为失败。
- [Site availability](.github/workflows/site-monitor.yml)：默认分支定时/手动运行，只读取既有网站，不安装项目依赖，不部署或写回。
- 监测按用户确认每小时一次，UTC 每小时第 7 分（北京时间分钟数相同）；GitHub 调度可能延迟或跳过，不是严格准点服务。

手动探测当前网站：

```bash
npm run monitor:site
```

命令固定读取 `https://chengxuan2002-droid.github.io/skill-gallery/` 的首页、JS、CSS、搜索索引。
每次请求超时 8 秒，失败重试一次；检查状态码、MIME、非空内容、首页标识及旧版索引结构。
返回内容始终作为数据，不执行 JS/Skill，不输出正文；本地测试只使用本地 HTTP 服务，不依赖线上站点。

**启用状态：main 的检查 CI 与首次手动网站监测已通过，每小时监测计划已启用。**
2026-11-03 的安全扫描补强已推送到开发分支；US1 时点 [Quality checks #41628358392](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/41628358392)
与 US2 后 [Quality checks #41639767607](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/41639767607)
均在 Node 26.3.0/Linux 上通过，`npm run check`、Gitleaks、Semgrep 与依赖审计四个步骤均成功。
2026-11-04 推送 US3/Polish 与依赖审计修复后，[Quality checks #41816996159](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/41816996159)
复验 138 项测试（137 通过、0 失败、1 跳过），Gitleaks/Semgrep 无发现，依赖审计通过并报告 6 个 moderate。
2026-11-05/06 本地 US-002 复验为 163 项（162 通过、0 失败、1 跳过），依赖审计报告 0 个漏洞；
这是本地结果，不表示远程 CI 已更新为该计数，详见
[US-002 质量门禁](specs/002-search-detail-share-redesign/validation/us2-quality.md)。
`main` 已合并该补强，默认分支使用更新版 quality workflow；PR/手动触发路径以最新运行记录为准。
2026-11-08 合并 PR #1–#4 后，quality workflow 在 main 运行成功。
quality 合并必需项仍需单独配置。
本次没有修改分支保护、通知设置或 Pages 配置；推送触发的既有 Pages 发布也已成功。
失败首先表现为 Actions 失败运行；是否收到邮件取决于自己的 GitHub 通知设置，不能把本地测试当通知已送达。

公开仓库长期无活动时，GitHub 可在 60 天后停用定时 workflow，需要维护者重新启用；
不要通过定期空提交规避停用。说明依据：[定时触发](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)、
[运行通知](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs)。
首页标识或索引切换新版契约时，同步修改监测断言与测试；浏览器交互、JS 异常和完整下载一致性另行验收。
实测与边界见[CI/监测验证记录](specs/001-preserve-skill-content/validation/ci-monitor.md)。

### 换电脑或更换 Code Agent

当前 `main` 已包含 US-001～US-005 的实现、发布配置与生产启用记录；历史开发基线仍保留在
`codex/development-baseline-20261102` 等分支，仅作历史参考。换电脑或 Agent 时应先核对当前分支、
远程跟踪状态和 `.specify/feature.json`，不要用旧基线分支代替当前 `main`。

```bash
git clone --branch main https://github.com/chengxuan2002-droid/skill-gallery.git
cd skill-gallery
```

先安装上文指定的 Node、npm 和 uv，再执行上文的安装、工程及安全检查命令。
`node_modules/`、`.tools/`、`.env*`、系统杂项和本机凭证不随仓库迁移；GitHub 写入凭证在新电脑独立授权。
不复制旧电脑的 SSH 私钥、Agent 会话或工具执行授权来替代新环境的授权。

当前指针是 `specs/006-source-auto-update`（US-006 规格、计划与 tasks 已建立；实施尚未开始），
`.specify/feature.json` 按 Spec Kit 规则保持本机忽略。首次在新副本运行以下命令，会检查规划文件并
恢复这个本地指针：

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/006-source-auto-update
bash .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

新 Agent 先读 [AGENTS.md](AGENTS.md)、[宪章](.specify/memory/constitution.md)、四份规范、当前功能的
[spec](specs/006-source-auto-update/spec.md)、[plan](specs/006-source-auto-update/plan.md)、
[tasks](specs/006-source-auto-update/tasks.md) 与
[checklist](specs/006-source-auto-update/checklists/requirements.md)。
US-005 的 [plan](specs/005-skill-cli/plan.md) 等已收口资料作为基线参考。
项目级 Skills 保存在 `.agents/skills/`，Spec Kit 初始化来源记录为 1.2.5/Codex；其他 Agent 若不自动发现，
应按其机制读取这些文件或配置入口，不能因更换工具而覆盖规范、重新生成任务或重跑 `specify init`。
可选的 Specify CLI 及其他 Agent 适配器需在新电脑单独安装并验证；现有 Bash 检查不依赖全局 CLI。

本次基线用于接续开发，不表示 US-001 已完成或已通过新的规格一致性分析。
后续先复核 spec/plan/tasks，再按明确授权实施。交接记录保留在独立交接分支，未收录的 `office2md` 不属于此基线。
此开发分支不合入 `main`、不修改 Pages 配置；合入前须核对只发布允许公开的静态产物，排除规划和工具资料。

下文保留现有版本和历史部署说明。


> 下一轮改造准备（2026-11-01）：[业界调研](docs/IndustryResearch.md) · [产品需求](docs/DemandAnalysis.md) · [技术方案](docs/TechnicalSolution.md) · [AI 编程规范](docs/AiProgrammingGuide.md)。该段为 2026-11-01 时点；后续 US-003～US-005 已完成后台、上传命令与生产发布，自动更新仍待 US-006。下文保留历史版本说明，当前命令和行为以上方工程章节为准。

个人 AI Agent Skill 收藏夹——统一管理、快速查找、跨平台复用、一键分享。

> 🔗 [在线浏览](https://chengxuan2002-droid.github.io/skill-gallery/)

## ✨ 特性

- **统一格式** — 原件以 markdown + YAML frontmatter 或目录形式保真保存，站内记录独立在 `catalog/`
- **精准/模糊搜索** — 名称、简介、标签、平台、来源、作者、用途、备注和正文检索
- **多维筛选** — 标签/平台/来源/作者；同维 OR、跨维 AND；可恢复的 Hash 分享地址
- **完整取用与分享** — 原文复制、原件/目录 ZIP/附件下载、详情和列表链接复制
- **静态部署** — 原生前端；本地使用 Node 工程检查，不需要后台服务
- **暗色模式与键盘可访问** — 优先手动主题，无保存值时跟随系统；响应式布局和焦点状态

---

## 🚀 快速开始

### 本地预览

当前构建只写 `dist/`，预览服务只映射 `/skill-gallery/` 子路径：

```bash
npm ci
npm run build
npm run preview
# 打开 http://localhost:8000/skill-gallery/
```

`npm run build` 成功只表示本地生成 `dist`，不表示 GitHub Pages 已发布。不要直接把仓库根目录作为
静态站点发布；上传、自动更新和发布流程仍属后续故事。

### 部署到 GitHub Pages（历史通用说明）

本站已有固定部署地址，下列通用建仓说明不属于当前初始化或发布操作。

#### 第一步：创建 GitHub 仓库

1. 打开 [github.com/new](https://github.com/new)
2. Repository name 填 `skill-gallery`（或你喜欢的名字）
3. 选择 Public（公开，才能用 GitHub Pages 免费托管）
4. **不要**勾选 Initialize with README（本地已经有了）
5. 点击 Create repository

#### 第二步：推送本地代码到 GitHub

回到终端，在项目目录下执行：

```bash
# 1. 初始化 git（如果还没初始化）
git init

# 2. 添加所有文件
git add .

# 3. 第一次提交
git commit -m "init: skill gallery"

# 4. 重命名主分支为 main
git branch -M main

# 5. 关联远程仓库（把下面的用户名和仓库名换成你自己的）
git remote add origin https://github.com/<你的用户名>/skill-gallery.git

# 6. 推送到 GitHub
git push -u origin main
```

> 💡 如果你用 SSH 方式，远程地址换成：`git@github.com:<你的用户名>/skill-gallery.git`

#### 常见问题：HTTPS 推送提示用户名或密码错误

GitHub 已不再支持用登录密码直接 push。HTTPS 方式下，你需要用 **Personal Access Token (PAT)** 代替密码。

**生成 PAT：**

1. 打开 <https://github.com/settings/tokens>
2. 点击 **Generate new token** → **Generate new token (classic)**
3. Note 填一个名字（比如 `skill-gallery`）
4. Expiration 选合适的有效期
5. 勾选 **repo** 权限
6. 拉到底部点 **Generate token**
7. **立即复制保存**（只显示一次，关掉就看不到了）

**推送时输入：**

- **Username**：你的 GitHub 用户名（不是邮箱）
- **Password**：刚才复制的 PAT（不是登录密码）

**让 git 记住凭证（不用每次输）：**

```bash
git config --global credential.helper osxkeychain
# 然后 push 一次输入用户名 + PAT，以后就不用了
```

**更推荐：配置 SSH（一劳永逸）：**

```bash
# 生成密钥（一路回车）
ssh-keygen -t ed25519 -C "你的邮箱"

# 复制公钥内容
cat ~/.ssh/id_ed25519.pub
# 粘贴到 https://github.com/settings/keys → New SSH key

# 把远程地址换成 SSH 格式
git remote set-url origin git@github.com:<你的用户名>/skill-gallery.git

# 以后 push 就不用输密码了
git push -u origin main
```

#### 第三步：启用 GitHub Pages

1. 打开你的仓库页面：`https://github.com/<你的用户名>/skill-gallery`
2. 点击顶部 **Settings**
3. 左侧菜单找到 **Pages**
4. **Build and deployment → Source** 选择 **Deploy from a branch**
5. **Branch** 选择 **main** 分支，目录选 **/ (root)**
6. 点击 Save
7. 等 1-2 分钟，页面顶部会显示你的站点地址，形如：
   `https://<你的用户名>.github.io/skill-gallery/`

#### 第四步：后续更新

当前已纳管内容的新增、替换和下架通过 GitHub 后台手动维护（见“手动维护（GitHub 后台）”），
本地/来源维护使用“Agent 命令（skill-cli）”。维护 `skills/` 与 `catalog/` 后，本地只可验证：

```bash
npm run build
npm run preview
```

这不会自动提交、推送或发布；不要手工编辑根 `assets/search-index.json`，也不要按旧教程把仓库根目录
直接当作 Pages 发布目录。

---

## 📖 使用教程

### 一、添加 Skill

所有 skill 都存放在 `skills/` 目录下，每个 skill 是一个 `.md` 文件。文件名即 `slug`（URL 中显示的标识），只用小写字母、数字和短横线。

站内没有面向访客的上传入口；新增、替换、下架与发布通过 GitHub 后台手动维护（见上文）或
“Agent 命令（skill-cli）”。
以下内容只说明原件格式和 `catalog/` 记录结构；可执行步骤见“手动维护（GitHub 后台）”。已纳管内容用
`npm run build` 验证 `dist`；不要手工编辑根 `assets/search-index.json`。

下面按不同来源分别给出格式示例：

---

#### 方式 1：自建 Skill

自己写的 skill，从本地直接添加。支持两种形式：

**形式 A：单文件 Skill**（简单场景，只有一份说明文档）

直接在 `skills/` 下建一个 `.md` 文件即可。

**示例：** 新建 `skills/git-workflow.md`

```markdown
---
name: Git 工作流助手
description: 规范化的 Git 分支、提交、PR 工作流指导
tags: [git, workflow, 协作]
platforms: [codex, claude-code, generic]
source: self-built
author: 你的名字
created_at: 2026-08-02
updated_at: 2026-08-02
usage_notes: |
  团队协作时特别有用，统一 PR 描述格式。
  注意先确认团队用的是 GitFlow 还是 Trunk Based。
---

# Git 工作流助手

帮助遵循规范的 Git 工作流。

## 提交规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

<body>
```

类型说明：
- `feat` - 新功能
- `fix` - 修复 bug
- `docs` - 文档变更
- `style` - 格式调整
- `refactor` - 重构
- `test` - 测试相关
- `chore` - 构建/工具链
```

---

**形式 B：目录型 Skill**（复杂场景，包含脚本、配置等附属文件）

如果你的 skill 带有脚本、配置文件、模板等附属内容，整个目录放进去。

**规则：**
- 在 `skills/` 下建一个子目录，目录名就是 skill 的 slug
- 目录里必须有一个 `SKILL.md`（注意全大写）作为主文档
- 其他文件/子目录随意组织，构建脚本会自动识别并列入"附件文件"

**示例：** 收录本地自建的 `handoff-codex` skill

目录结构：

```
skills/
└── handoff-codex/
    ├── SKILL.md              ← 主文档（必须，含 frontmatter）
    ├── scripts/
    │   └── create_handoff.sh ← 附属脚本
    └── agents/
        └── openai.yaml       ← 附属配置
```

`SKILL.md` 的 frontmatter 格式跟单文件完全一致：

```markdown
---
name: handoff-codex
description: 长会话结束前自动生成交接文档，写入项目 handoff/ 目录。
tags: [productivity, handoff, workflow]
platforms: [codex]
source: self-built
author: chengxuan
version: 1.0.0
created_at: 2026-07-20
updated_at: 2026-08-02
usage_notes: |
  适合多轮长对话、暂停工作、或用户说"交接/保存进度/记录一下"时使用。
---

# Handoff Codex

...正文内容...
```

> **小提示：** 详情页会显示所有附属文件的下载链接，访问路径为 `skills/<slug>/<文件路径>`。
>
> **来源标记说明：** `source: self-built` 表示自建

---

#### 方式 2：从 GitHub 发现的 Skill

在 GitHub 上看到好的 skill，把内容收录进来。

**示例：** 收录一个 GitHub 上的测试 skill

1. 找到原始文件（如 `https://github.com/someone/repo/blob/main/skills/test-driven.md`）
2. 复制内容，新建 `skills/test-driven-development.md`
3. 填写 frontmatter，标注来源

```markdown
---
name: 测试驱动开发指南
description: TDD 红绿重构循环的完整实践流程
tags: [testing, tdd, workflow]
platforms: [codex, generic]
source: github
source_url: https://github.com/someone/repo/blob/main/skills/test-driven.md
author: Someone
created_at: 2026-07-20
updated_at: 2026-07-28
usage_notes: |
  适合新功能开发时用。
  老旧代码先补集成测试再重构。
---

# 测试驱动开发

TDD 的核心循环：红 → 绿 → 重构。

## 红（Red）

先写一个会失败的测试，描述你想要的行为。

## 绿（Green）

用最少的代码让测试通过。

## 重构（Refactor）

在测试保护下优化代码结构。
```

> **来源标记说明：** `source: github` + `source_url` 填写原始链接

---

#### 方式 3：Agent 平台自带的 Skill

Codex、Claude Code 等平台内置或官方提供的 skill。

**示例：** 收录 Claude Code 的官方 skill

```markdown
---
name: Claude Code 架构师模式
description: 系统性的软件架构设计流程
tags: [architecture, design, planning]
platforms: [claude-code]
source: platform-native
source_url: https://docs.anthropic.com/...
author: Anthropic
created_at: 2026-06-15
updated_at: 2026-07-30
usage_notes: |
 做大型重构前先用这个走一遍。
 产出的架构文档可以作为后续任务的基础。
---

# 架构师模式

## 步骤

1. 理解需求和约束
2. 列出可选方案
3. 评估权衡
4. 推荐方案并说明理由
5. 设计实现路径
```

> **来源标记说明：** `source: platform-native` 表示平台原生自带

---

#### 方式 4：Skill 市场/平台上发现的

从各种 skill 市场、社区、分享平台上找到的。

**示例：** 收录一个市场上的代码重构 skill

```markdown
---
name: 大模型代码重构专家
description: 针对大模型生成代码的重构和优化方法论
tags: [refactoring, llm, quality]
platforms: [codex, claude-code, cursor]
source: marketplace
source_url: https://skill-marketplace.example.com/refactor-pro
author: Marketplace Author
created_at: 2026-05-10
updated_at: 2026-08-01
usage_notes: |
  LLM 写的代码能用但经常不优雅，
  用这个 skill 做第二轮优化。
---

# LLM 代码重构

## 常见问题

1. 命名不规范
2. 重复逻辑
3. 错误处理缺失
4. 测试覆盖不足

## 重构顺序

先补测试 → 再提取函数 → 最后优化结构
```

> **来源标记说明：** `source: marketplace` 表示来自 skill 市场

---

### 二、Skill 文件格式详解

每个 skill 文件由两部分组成：**YAML frontmatter（元数据）** + **Markdown 正文**

```markdown
---                    ← frontmatter 开始
name: Skill 名称
description: 一句话描述
tags: [标签1, 标签2]
...
---                    ← frontmatter 结束

# Skill 正文标题

正文内容...
```

#### 字段说明

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `name` | ✅ | 字符串 | 显示名称 |
| `description` | ✅ | 字符串 | 一句话摘要，列表页会显示 |
| `tags` | ✅ | 数组 | 标签，用于分类筛选 |
| `platforms` | ✅ | 数组 | 适用平台，见下方常用值 |
| `source` | ✅ | 字符串 | 来源类型，见下方可选值 |
| `source_url` | ❌ | 字符串 | 原始链接 |
| `author` | ❌ | 字符串 | 原作者 |
| `created_at` | ✅ | 日期 | 添加日期 (YYYY-MM-DD) |
| `updated_at` | ✅ | 日期 | 最后更新日期 |
| `usage_notes` | ❌ | 多行文本 | 个人使用心得 |

#### `platforms` 常用值

| 值 | 说明 |
|---|---|
| `codex` | OpenAI Codex |
| `claude-code` | Claude Code |
| `cursor` | Cursor |
| `cline` | Cline |
| `generic` | 通用，任何 agent 都能用 |
| 其他 | 自定义平台名 |

#### `source` 可选值

| 值 | 说明 |
|---|---|
| `self-built` | 自己写的 |
| `github` | GitHub 上发现的 |
| `marketplace` | skill 市场/平台 |
| `platform-native` | agent 平台自带 |
| `other` | 其他来源 |

---

### 三、取用与分享

当前详情页提供以下已验证操作：

- **查看/复制原文**：从 raw 原件读取并校验大小和摘要后展示或写入剪贴板；复制失败会保留可手动复制的原文。
- **下载原件**：单文件按原名下载；目录型 Skill 下载完整 ZIP，包含附件和许可文件。
- **下载附件**：详情附件区按文件清单提供下载，响应大小和 SHA-256 校验通过后才发起。
- **复制分享链接**：详情地址为当前文档目录下的 `#/skill/<slug>`；列表页可复制包含查询、模式、筛选和排序的地址。
- **失败反馈**：剪贴板拒绝显示 `copy_failed` 和手动复制值；资源缺失或摘要不符显示 `download_failed`，不误报成功。
- **返回列表**：从卡片进入详情时恢复进入前的列表条件；直接打开旧链接或刷新详情时回到列表根。

当前不提供 Codex/Claude Code 平台格式导出，也不提供旧版本选择。详情旧链接
`#/skill/<slug>` 仍指向当前单版本；Git 历史保留仅用于受控恢复，不是公开旧版入口。

分享示例：

```text
https://chengxuan2002-droid.github.io/skill-gallery/#/skill/systematic-debugging
https://chengxuan2002-droid.github.io/skill-gallery/#/?q=debug&mode=exact&tag=debugging
```

---

### 四、搜索与筛选

#### 全文搜索

- 搜索范围：名称、简介、标签、平台、来源、作者、用途、备注和正文纯文本。
- **模糊模式**（默认）：英文允许轻微拼写误差，中文至少按连续子串命中。
- **精准模式**：对规范化文本做连续片段匹配；未加引号的多词按完整连续片段处理，
  双引号表示完整短语，不自动纠错。
- 名称命中优先于简介/标签，简介/标签优先于正文；同分按 slug 稳定排序。

#### 筛选与排序

- 标签、平台、来源类型、作者均有筛选；同维度多选为 **OR**，不同维度为 **AND**。
- 缺失字段不匹配对应筛选条件；筛选选项只来自当前索引实际值。
- 排序：`自动`（有关键词按相关度，无关键词按更新时间倒序）、`名称`、`更新时间`；
  显式选择在查询/筛选变化后保持，同分/同日期按 slug。
- 当前查询、模式、筛选和排序显示为可单项清除的条件 chip；可一键清除全部。
- 条件保存在可分享的 Hash 地址：`#/?q=...&mode=exact&tag=...&platform=...&source=...&author=...&sort=...`。
- 移动端筛选默认收起，使用“筛选”按钮展开；结果数量和操作状态通过 `aria-live` 提示。

---

### 五、常见问题

**Q: 添加了新 Skill 但页面上看不到？**
A: 站内没有面向访客的上传入口；新增、替换、下架通过 GitHub 后台手动维护（见“手动维护（GitHub 后台）”），
或使用“Agent 命令（skill-cli）”。已纳管内容可用 `npm run build` 在本地验证，但不能把本地 `built` 当作网站已发布。

**Q: 可以批量导入吗？**
A: 尚未实现。不要按旧教程提交根 `assets/search-index.json`，也不要把仓库根目录当作站点发布目录。

**Q: 能导出 Codex/Claude Code 格式吗？**
A: 当前只提供原件/目录 ZIP/附件下载、原文复制和详情/列表链接分享，不提供平台格式转换导出。

**Q: 怎么换主题？**
A: 点击右上角主题按钮切换；有手动选择时持久化，没有保存值时跟随系统
`prefers-color-scheme`。

---

## 📁 项目结构

```
skill-gallery/
├── skills/                  # 保真原件（单文件或 SKILL.md 目录）
├── catalog/                 # 站内记录与来源配置
├── assets/                  # 前端源码与旧版索引基线
│   ├── app.js
│   ├── app-dom.js
│   ├── app-search.js
│   ├── app-filters.js
│   ├── app-views.js
│   ├── app-detail.js
│   ├── app-actions.js
│   └── style.css
├── scripts/                 # 校验、迁移、构建和预览
├── tests/                   # 受信任的 unit/integration 测试与夹具
├── specs/                   # 当前功能规格、计划、任务和验收记录
├── dist/                    # 构建产物（生成目录，不提交）
├── index.html
├── .nojekyll
└── README.md
```

## 📄 许可证

收录的外部 skill 遵循原作者的许可证，详见各 skill 的来源链接。
