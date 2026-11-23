# Skill Gallery

[在线站点](https://chengxuan2002-droid.github.io/skill-gallery/) · [管理员部署](#部署管理员) · [技术方案](docs/TechnicalSolution.md) · [验收状态](specs/007-overall-acceptance/validation/final-review.md)

[![Quality checks](https://github.com/chengxuan2002-droid/skill-gallery/actions/workflows/quality.yml/badge.svg?branch=main)](https://github.com/chengxuan2002-droid/skill-gallery/actions/workflows/quality.yml)
[![Maintain site](https://github.com/chengxuan2002-droid/skill-gallery/actions/workflows/maintain.yml/badge.svg?branch=main)](https://github.com/chengxuan2002-droid/skill-gallery/actions/workflows/maintain.yml)
[![Site availability](https://github.com/chengxuan2002-droid/skill-gallery/actions/workflows/site-monitor.yml/badge.svg?branch=main)](https://github.com/chengxuan2002-droid/skill-gallery/actions/workflows/site-monitor.yml)

Skill Gallery 是一个个人精选 AI Agent Skill 的静态图库：访客可以搜索、查看、复制、下载和分享 Skill；
管理员通过 GitHub 仓库和 Actions 维护内容；受支持的 GitHub 来源可以定期检查并自动更新当前版本。
网站不需要访客登录，也不在浏览器内保存 GitHub token。

- 搜索：精准/模糊匹配，标签、平台、来源、作者筛选和排序
- 详情：用途、用法、原文、附件、版本、作者、来源和分享链接
- 下载：原件 raw、目录 ZIP、单文件附件；下载内容与详情 SHA-256 对应
- Agent 友好：公开静态 JSON 索引和详情，Agent 可直接检索、下载和安装
- 管理：GitHub 后台手动维护、`skill-cli` Agent 命令、GitHub 来源自动更新
- 安全：原件与展示文本分离，展示内容清理活动 HTML，构建不执行 Skill 脚本

当前生产站点：<https://chengxuan2002-droid.github.io/skill-gallery/>。资源前缀为 `/skill-gallery/`。

## 快速使用（访客）

无需注册或登录：

1. 打开站点，在搜索框输入关键词；可切换精准/模糊模式。
2. 用标签、平台、来源或作者筛选，必要时调整排序。
3. 打开卡片进入详情，查看用途、用法、原文和附件。
4. 需要文件时使用“复制原文”“下载原件”或“下载目录 ZIP”。
5. 需要分享时复制详情链接或列表链接。

可分享的地址：

- 详情：`https://chengxuan2002-droid.github.io/skill-gallery/#/skill/<slug>`
- 列表/搜索：`https://chengxuan2002-droid.github.io/skill-gallery/#/?q=<关键词>`

详情里的 `download_name` 是建议的本地文件名；`download_sha256` 或 `files[].sha256` 用于校验。
`content_text` 只是搜索投影，可能不包含完整代码块或表格，**不是原件**；请使用 raw/ZIP 下载取用原件。

## 用 Agent 检索、下载和安装

访客侧只需要公开只读数据，不需要 GitHub 凭证。Agent 应读取静态 JSON，而不是解析页面 HTML。

### 数据入口

| 用途 | 路径 | 说明 |
|---|---|---|
| 检索索引 | `assets/search-index.json` | `schemaVersion`、`contentRevision`、`skills[]`；含标题、描述、标签、平台、作者和 `content_text` |
| 详情 | `details/<slug>.json` | 文件清单、raw/download URL、`download_sha256`、许可和版本信息 |
| 原件/ZIP | 详情中的 `download_url` | 相对站点根路径；保存为 `download_name` |
| 分享 | `#/skill/<slug>`、`#/?q=...` | 前端 Hash 路由，刷新后仍可打开 |

### 推荐给 Agent 的提示词

把下面内容交给具备网页/命令执行能力的 Agent，并替换 `<我的 Agent skills 目录>`：

```text
你是我的 Skill 安装助手。只读访问 Skill Gallery：
1. 读取 https://chengxuan2002-droid.github.io/skill-gallery/assets/search-index.json。
2. 根据我的需求，在 display_name、description、content_text、tags、platforms 中检索；
   返回最多 3 个候选，列出 slug、摘要、标签、平台和更新时间，不要直接安装。
3. 我选定 slug 后，读取 https://chengxuan2002-droid.github.io/skill-gallery/details/<slug>.json，
   确认来源、作者、许可、文件清单和下载地址。
4. 下载前告诉我将安装到 <我的 Agent skills 目录>/<slug>/；没有许可或来源不明时先询问我。
5. 下载 download_url，保存为 download_name，并用 download_sha256 校验；
   目录 ZIP 解压到 skills 目录（ZIP 根目录通常是 <slug>/），单文件放入 <slug>/ 目录。
6. 如果我的 Agent 要求主文档名为 SKILL.md，可在安装目录本地复制/改名，但保留原始下载文件和名称。
7. 不要执行 Skill 内的脚本、测试或安装其依赖；不要打印任何凭证；最后报告本地路径、来源和 SHA-256。
```

### macOS / Linux 示例

```bash
BASE="https://chengxuan2002-droid.github.io/skill-gallery"
curl -fsSL "$BASE/assets/search-index.json" -o index.json

# 按关键词搜索（示例：debug）
jq -r '.skills[]
  | select((.display_name + " " + .description + " " + .content_text) | test("debug"; "i"))
  | [.slug, .display_name, (.platforms | join(","))] | @tsv' index.json

SLUG="<slug>"
DETAIL_URL=$(jq -r --arg s "$SLUG" '.skills[] | select(.slug == $s) | .detail_url' index.json)
curl -fsSL "$BASE/$DETAIL_URL" -o detail.json

URL=$(jq -r '.download_url' detail.json)
NAME=$(jq -r '.download_name' detail.json)
curl -fsSL "$BASE/$URL" -o "$NAME"

# 校验（Linux）
echo "$(jq -r '.download_sha256' detail.json)  $NAME" | sha256sum -c -

# 目录 ZIP 或单文件：安装到 Agent skills 目录
mkdir -p "$AGENT_SKILLS_DIR"
if [[ "$NAME" == *.zip ]]; then
  unzip -q "$NAME" -d "$AGENT_SKILLS_DIR"
else
  mkdir -p "$AGENT_SKILLS_DIR/$SLUG"
  cp "$NAME" "$AGENT_SKILLS_DIR/$SLUG/"
fi
```

### PowerShell 示例

```powershell
$Base = 'https://chengxuan2002-droid.github.io/skill-gallery'
$Index = Invoke-RestMethod "$Base/assets/search-index.json"

$Index.skills |
  Where-Object { ($_.display_name + ' ' + $_.description + ' ' + $_.content_text) -match 'debug' } |
  Select-Object slug, display_name, platforms, updated_at

$Slug = '<slug>'
$DetailUrl = ($Index.skills | Where-Object slug -eq $Slug).detail_url
$Detail = Invoke-RestMethod "$Base/$DetailUrl"
$Out = Join-Path $env:TEMP $Detail.download_name
Invoke-WebRequest "$Base/$($Detail.download_url)" -OutFile $Out

$Actual = (Get-FileHash $Out -Algorithm SHA256).Hash.ToLower()
if ($Actual -ne $Detail.download_sha256) { throw 'SHA-256 mismatch' }

# 目录 ZIP 或单文件：安装到 Agent skills 目录
$AgentSkillsDir = '<我的 Agent skills 目录>'
if ($Detail.download_name -like '*.zip') {
  Expand-Archive -LiteralPath $Out -DestinationPath $AgentSkillsDir -Force
} else {
  $Target = Join-Path $AgentSkillsDir $Slug
  New-Item -ItemType Directory -Force $Target | Out-Null
  Copy-Item -LiteralPath $Out -Destination $Target
}
```

### 安装位置

- 目录型 Skill：解压后目录名为 `<slug>/`，放入 Agent 的 skills 目录即可。
- 单文件 Skill：在 skills 目录下创建 `<slug>/`，放入 `download_name`；如果 Agent 要求
  `SKILL.md`，在本地复制/改名，但不要修改下载的原件。
- Claude Code 用户级目录通常为 `~/.claude/skills/<slug>/`；Codex 或其他 Agent 以各自文档为准。
- 安装后让 Agent 先读取 `SKILL.md`（或对应主文档），不要直接执行附件脚本。

### 安全边界

- 下载内容是不可信的第三方数据；不要自动执行其中的脚本、测试或安装依赖。
- 安装前核对 `license`、`repository_url`、作者和 `updated_at`；没有许可或来源不明时先询问用户。
- 不要从页面文本重建原件；以 raw/ZIP 和详情 SHA-256 为准。
- 不要把 GitHub token、cookie 或私有仓库凭证交给外部 Agent。

## 部署（管理员）

### 前置条件

| 项 | 要求 |
|---|---|
| 仓库权限 | 对目标仓库有写权限；生产发布由管理员或授权 Agent 执行 |
| Node/npm | 基线 Node `26.3.0`、npm `11.16.0`；本机 Node 22 可做大部分本地验证，CI 以 Node 26.3 为准 |
| GitHub 功能 | Actions 启用；Pages Source 使用 “GitHub Actions”；默认分支为 `main` |
| 安全扫描器 | `npm run setup:security` 需要 `uv` 和网络，安装固定 Gitleaks/Semgrep 到 `.tools/` |
| 站点路径 | 本站按 `/skill-gallery/` 子路径部署；资源使用相对路径 |

### 首次部署

```bash
git clone https://github.com/chengxuan2002-droid/skill-gallery.git
cd skill-gallery
npm ci
npm run setup:security
npm run check
npm run build
npm run preview
# 打开 http://localhost:8000/skill-gallery/
```

确认本地预览正常后推送到 `main`。在 GitHub 仓库设置中：

1. `Settings → Pages → Build and deployment → Source` 选择 **GitHub Actions**。
2. 确认 Actions 允许运行工作流；默认分支为 `main`。
3. `github-pages` environment 的 branch policy 至少允许 `main`；如需审批，可配置 required reviewer。
4. 推送到 `main` 后由 `maintain.yml` 构建并发布；不要手工上传 `dist/` 或直接覆盖线上文件。

若部署到 fork 或不同仓库名：更新 `index.html` 的仓库外链、README 中的站点地址，以及
`scripts/check-site.js` 的固定 `SITE_URL`（该监测脚本默认只检查本站）；重新构建并验证子路径资源。

### 工作流与权限

| 工作流 | 触发 | 作用 |
|---|---|---|
| `.github/workflows/quality.yml` | push、PR、手动 | lint/format、测试、凭证/源码/依赖检查 |
| `.github/workflows/maintain.yml` | push `main`、每日 03:17、手动 dispatch | 来源检查、构建、产物校验、Pages 发布 |
| `.github/workflows/site-monitor.yml` | 每小时 | 只读检查现站首页、脚本、样式和索引 |

工作流使用最小权限、固定 Action SHA、checkout 不持久化凭证；不要把 PAT、token 或 secret 写入仓库。
生产发布状态以 Actions 运行记录为准，不能把本地 `built` 或提交成功当作已发布。

## 日常管理（管理员）

### 内容模型

| 路径 | 用途 |
|---|---|
| `skills/<slug>.md` | 单文件 Skill 原件 |
| `skills/<slug>/SKILL.md` | 目录型 Skill 主文档；附件放在同一目录 |
| `catalog/<slug>.json` | 站内元数据；与原件分离 |
| `dist/` | 构建生成目录；唯一发布产物，不手动编辑 |

必填字段：

| 字段 | 说明 |
|---|---|
| `schemaVersion` | 固定为 `1` |
| `slug` | 小写字母、数字和短横线，≤64，与路径一致 |
| `display_name` | 站点显示名 |
| `description` | 一句话简介 |
| `content_path` | `skills/<slug>.md` 或 `skills/<slug>/SKILL.md` |

常用可选字段：`tags`、`platforms`、`author`、`homepage_url`、`repository_url`、`source_type`、
`usage`、`notes`、`license`、`created_at`、`updated_at`、`declared_version`、`allowed_dot_paths`。
不要添加未定义字段；未知字段会整批失败。目录型 Skill 的附件只从 `skills/<slug>/` 读取，
未纳管文件不会自动进入站点。当前限额：每个 Skill 最多 500 个普通文件、原始总字节 20 MiB、
主文档 1 MiB。

### 新增 Skill（GitHub 后台或 PR）

1. 添加 `skills/<slug>.md`，或 `skills/<slug>/SKILL.md` 及附件。
2. 添加 `catalog/<slug>.json`，填写必填字段；需要时补充标签、平台、作者、许可和用法。
3. 提交到分支并创建 PR；`quality.yml` 会检查格式、测试、凭证和依赖。
4. 合并到 `main` 后等待 `maintain.yml` 的 build/deploy 成功。
5. 打开生产详情、raw/ZIP 和分享链接核对内容；下载文件后按详情 SHA-256 校验。

### 替换、下架与恢复

- **替换**：用完整新内容替换同一 slug 的原件，保持 `catalog` 的 slug 和 `content_path`；构建会删除
  新清单之外的旧附件，只保留一个当前版本。不要把旧内容另存为第二个目录。
- **下架**：删除对应原件（文件或整个目录）和 `catalog/<slug>.json`，提交并发布；索引、详情和下载
  会移除该项，旧分享链接回到列表或“未找到”状态。
- **恢复**：通过 GitHub 历史或受控 `git revert`/restore 生成恢复提交，再走同一构建/发布流程；
  保持 slug、旧链接和单版本，不 force push，不手工改 `dist/`。

### 来源自动更新（可选）

在 `catalog/<slug>.json` 中配置 `source_tracking`；未配置时保持 `null`，不会自动更新：

```json
{
  "source_tracking": {
    "provider": "github",
    "repository": "owner/repository",
    "path": "skills/example",
    "ref_policy": "branch",
    "ref": "main",
    "enabled": true,
    "last_synced_revision": null,
    "last_synced_digest": null,
    "last_synced_license": null,
    "synced_at": null
  }
}
```

- `ref_policy` 支持 `branch`、`release`、`pinned`；`pinned` 不自动前移，`release` 取最新非草稿、
  非预发布 Release。
- 单文件来源为 `skills/<slug>.md`；目录来源为 `skills/<slug>/SKILL.md` 及附件。
- 成功替换只保留一个当前版本，上游删除的附件会从详情、索引和 ZIP 中移除。
- 许可缺失/变化会阻断；目录来源优先使用子树许可，子树没有时回退仓库根 `LICENSE/NOTICE`。
  当前内容偏离 `last_synced_digest` 或远端基线前进会 conflict；失败保留当前版。

手动检查与应用：

```bash
node scripts/sync-skills.js --slug example --json
node scripts/sync-skills.js --slug example --apply --push --report sync-report.json --summary sync-summary.md
```

退出码：`0` 完成（逐来源失败在报告中表达）、`2` 参数/catalog 无效、`4` 冲突/推送被拒绝、
`5` 全局来源读取失败、`6` 提交或报告写入失败。

`maintain.yml` 每日 03:17 Asia/Shanghai 运行同一 sync 入口；平台可能延迟或跳过，不承诺准点 SLA。
手动 `sync=false` 只按当前提交重发，`sync=true` 执行来源检查。生产 `sepia` 已在手动 run
45160746326 建立首次基线（revision `0eb11d6...`、digest `785e07...`、license `LICENSE`）；
每日 schedule 会继续检查上游变化。其余 6 项仍为 `null`，不会自动更新。

### 新增 GitHub 来源 Skill 的配置步骤

以下是新增一个 GitHub 来源 Skill 的推荐流程：

1. 添加上游对应的原件和 catalog：
   - 单文件：`skills/<slug>.md`；
   - 目录：`skills/<slug>/SKILL.md` 及附件；
   - `catalog/<slug>.json` 填写 `schemaVersion`、`slug`、`display_name`、`description`、
     `content_path`，并按需补 `tags`、`platforms`、`author`、`repository_url`、`license`、
     `declared_version`。
2. 在 catalog 中加入上面的 `source_tracking` 模板：
   - `repository` 必须是 `owner/repository`；
   - `path` 是上游 POSIX 相对路径；
   - `ref_policy` 使用 `branch`、`release` 或 `pinned`；
   - 首次配置保持 `last_synced_*` 为 `null`，由后续 apply 自动写入。
3. 让本地内容与上游一致：
   - 推荐用 `skill-cli import` 从同一来源导入并发布；
   - 或手工复制上游 `SKILL.md`/附件后，用 `node scripts/sync-skills.js --slug <slug> --json`
     做只读检查。
4. 只读检查应看到 `status: unchanged`、`license_status: present` 和上游不可变 SHA；
   如果内容不同，首次检查会返回 `conflict`/`E_CONFLICT_BASELINE`，不要强行覆盖，先对齐内容。
5. 提交 catalog/原件，走 PR；Quality checks 通过后合并。
6. 建立基线：
   - 等待下一次每日 schedule；或
   - 授权执行一次 `maintain.yml` 手动 dispatch（`sync=true`）。
   成功后 catalog 的 `last_synced_revision`、`last_synced_digest`、`last_synced_license`、
   `synced_at` 会被写入；内容不变时不应改写 Skill 原件。
7. 后续按状态处理：上游变化为 `candidate`（授权 apply 后单版本替换）；无变化为 `unchanged`；
   许可缺失/变化为 `policy_blocked`；本地修改或基线前进为 `conflict`；404/403/429/截断为 `failed`。

补充边界：默认同步器只能读取公开 GitHub 来源；其他私有仓库需要单独授权和凭证方案。目录来源的
许可优先取子树，子树没有时回退仓库根 `LICENSE/NOTICE`；仍缺失则阻断。同步只处理内容，不执行
上游脚本、测试或依赖安装。

### Agent CLI（管理员）

前提：Node/NPM、Git 和已登录的 `gh`；不要把 token 写入参数、仓库或示例。

```bash
node scripts/skill-cli.js preview <path> --meta catalog/<slug>.json
node scripts/skill-cli.js add <path> --meta catalog/<slug>.json --publish --wait
node scripts/skill-cli.js import --repo owner/repository --path skills/example --ref main \
  --meta catalog/<slug>.json --publish --wait
node scripts/skill-cli.js replace <slug> <path> --expected-revision <sha> \
  --meta catalog/<slug>.json --publish --wait
node scripts/skill-cli.js status --run <run-id>
```

- `preview`/不带 `--publish` 的 `add` 只校验并输出预览，不写入、不提交、不推送。
- `--publish` 才允许远端写入；`--wait` 只能与 `--publish` 使用。推送后最多 60 秒发现对应
  `maintain.yml` 运行，找到后轮询到终态；未发现则保留 `submitted/pending`，不误报已发布。
- `import` 只接受结构化 `owner/repository`、`path`、`ref`；不接受普通网页 URL。
- `replace` 使用 `--expected-revision` 防止覆盖已变化的基线；冲突时重新读取远端后重试。
- stdout 是单行 JSON：`status`、`slug`、`content_revision`、`content_status`、`deploy_status`、
  `commit_sha`、`run_url`、`public_url`、`errors`。

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

## 用 Agent 维护 Skill

管理员可以让 Agent 完成“准备 → 预览 → 审批 → 发布 → 验证”，但必须保留人工审批和仓库权限边界。

### 推荐给管理员的 Agent 提示词

```text
你是 Skill Gallery 的维护 Agent。先阅读 README.md、AGENTS.md 和
specs/007-overall-acceptance/validation/final-review.md。
1. 检查 git status、当前分支和 gh auth status；确认我有发布授权；没有授权时只做 preview。
2. 新增或更新 Skill 时，先准备 skills/ 原件和 catalog/ 元数据，运行 skill-cli preview，
   展示 JSON、目标文件差异和将产生的提交范围，等待我确认。
3. 我确认后才允许 --publish：
   - 本地路径：add <path> --meta catalog/<slug>.json
   - 更新：replace <slug> <path> --expected-revision <sha> --meta catalog/<slug>.json
   - GitHub 来源：import --repo owner/repository --path skills/example --ref main
     --meta catalog/<slug>.json
   以上发布命令加 --publish --wait，并报告 commit、run_url、content_status、deploy_status。
4. 如果使用分支/PR 方式：创建分支、提交目标文件、运行 npm run build、npm run check、
   npm run security，推送并开 PR；等 CI 通过并经我审阅后再合并。
5. 不执行 Skill 内的脚本/测试/依赖，不打印 token，不 force push，不手工修改 dist/，
   不降低检查标准；失败时保留当前版本并报告稳定错误码。
```

### CLI 方式的完整步骤

1. Agent 读取当前仓库状态和 `AGENTS.md`，确认 `gh` 已登录、工作区干净。
2. 准备候选文件与 `catalog/<slug>.json`；必要时先创建分支。
3. 运行 `skill-cli preview`；检查 `status=previewed`、`slug`、`content_revision` 和 `errors`。
4. 人工确认后运行 `add`/`replace`/`import --publish --wait`；Agent 只报告 JSON，不自行扩大授权。
5. 若输出 `submitted/pending`，先用
   `gh run list --commit <commit_sha> --workflow maintain.yml --limit 1 --json databaseId` 找到运行，
   再运行 `status --run <run-id>`；等待完成后重试，超时不要重复造空提交。
6. 合并/发布成功后核对生产详情、raw/ZIP、分享链接和 SHA-256；报告本地/远端状态及回滚提交。

### PR 方式（适合批量或复杂元数据）

1. 从 `main` 创建分支，例如 `codex/add-<slug>`。
2. 添加/替换 `skills/` 和 `catalog/`，保持一个 slug 一个版本；不要提交 `dist/`。
3. 运行 `npm run build`、`npm run check`、`npm run security`，必要时 `npm run preview`。
4. 提交目标文件，推送分支并创建 PR；等待 `quality.yml` 通过。
5. 人工审阅后合并；`maintain.yml` 负责构建和发布。
6. 核对生产索引/详情/raw/ZIP 和旧链接；失败时保留旧站并走恢复流程。

### 来源更新由 Agent 执行

```bash
# 只检查，不写入
node scripts/sync-skills.js --slug example --json

# 人工确认后应用并推送
node scripts/sync-skills.js --slug example --apply --push --report sync-report.json --summary sync-summary.md
```

Agent 应逐来源报告 `unchanged`、`candidate`、`updated`、`failed`、`conflict` 或
`policy_blocked`；许可变化、本地修改、远端基线前进和 403/429 不得绕过。默认优先让每日
`maintain.yml` 执行；手动命令只用于检查和受控补跑。

## 运维、恢复与故障处理

### 每日检查

- 查看 [Maintain site](https://github.com/chengxuan2002-droid/skill-gallery/actions/workflows/maintain.yml)
  最近运行：sync、build、deploy 是否分别为 success/skipped/failure。
- 查看 [Site availability](https://github.com/chengxuan2002-droid/skill-gallery/actions/workflows/site-monitor.yml)
  是否通过；监测每小时一次，只读站点，不部署。
- 手动探测本站：`npm run monitor:site`（固定检查 canonical 站点）。
- 每日调度为 03:17 Asia/Shanghai，平台可能延迟或跳过；以运行记录为准，不承诺准点 SLA。

### 状态、重跑与恢复

- **提交、内容、部署分开看**：提交成功不等于构建成功，构建成功不等于已发布。
- **无变化**：build/deploy skipped，保留当前站点；不要为了“刷新”重复提交空内容。
- **部署失败**：旧站保留；修复后在 Actions 手动 dispatch `sync=false` 重跑同一提交，或重新触发发布。
- **过期**：目标提交落后于远端时报告 `superseded`，不要强推。
- **恢复**：使用受控 `git revert`/restore 提交并重新构建发布；保持 slug、旧链接和单版本，不 force push。

### 故障速查

| 现象 | 检查 | 处理 |
|---|---|---|
| 页面没有更新 | Maintain site 的 build/deploy、Pages 状态、缓存 | 等发布成功；必要时 dispatch `sync=false` 重跑；不要手改 `dist/` |
| 新 Skill 不显示 | 索引、详情、catalog 必填字段、构建日志 | 修正 catalog 后重新提交整批；未知字段会整批失败 |
| `E_SCHEMA` / `E_PATH` / `E_MAIN_MISSING` | 字段、slug、`content_path`、主文档路径 | 按错误码修正路径和字段，不猜字段名 |
| `E_REFERENCE_MISSING` | 正文引用的本地附件 | 补回附件或移除失效引用 |
| `E_SECRET` | 凭证/私钥/密码赋值 | 移除并轮换真实凭证；示例用 `YOUR_*_HERE`，诊断不回显值 |
| 来源 404/403/429/截断 | `source_tracking`、来源可见性、错误码 | 修正仓库/路径/分支；限流等待后重试；不要伪造成功 |
| `policy_blocked` | 许可缺失/变化 | 补许可或确认变更；当前版本保留 |
| `conflict` | 本地修改、远端基线前进、过期 expected revision | 重新读取远端和 `last_synced_digest` 后重试 |
| `submitted/pending` | 运行尚未出现或未完成 | 用 `status --run` 查询；超时保留 `run_url`，不要重复提交 |
| 构建残留锁 | `.dist.lock/owner.json`、事务记录 | 先确认原进程退出并核对 owner/run_id/pid，只删除匹配锁后重跑 |

### 安全

- Skill 正文、脚本和 Agent 配置是不可信数据；构建和预览不执行其中的脚本、测试或依赖。
- 展示 HTML 会清理活动内容；原件下载保真，但下载者仍需自行审查。
- 密码、token、私钥、cookie 不进入仓库、页面、日志或示例；诊断只报告位置和类型。
- 公开产物只包含站点、索引、详情、公开原件/ZIP 和静态资源；不要提交 `docs/`、`specs/`、
  `handoff/`、工具配置或 Git 数据到发布产物。
- 工作流保持最小权限；不要让 fork 或未授权身份触发写入/部署。

## 开发与验收

当前实现覆盖 US-001～US-006 的本地/受控验收；US-007 的 T001–T022 已执行，结论为
**有条件验收/交接**。生产 Pages 已启用，T041 macOS runner、US-005 真实 `gh api`/`--wait`、
生产 environment 审批/部署失败保留/MIME 基础头已补验；剩余项见
[residual-gaps.md](specs/007-overall-acceptance/validation/residual-gaps.md)，不得计为通过。
完整验收结论见 [final-review.md](specs/007-overall-acceptance/validation/final-review.md)。

常用命令：

| 命令 | 用途 |
|---|---|
| `npm ci` | 按根锁安装开发依赖 |
| `npm run setup:security` | 安装/复用固定 Gitleaks、Semgrep |
| `npm run lint` / `npm run format:check` | 自有源码和工程文件检查 |
| `npm test` | 单元/集成/发布链测试 |
| `npm run build` | 生成 `dist/`，不发布 |
| `npm run preview` | 本地只读预览 `/skill-gallery/` |
| `npm run check` | lint + format + tests |
| `npm run security` | 凭证、源码规则和依赖审计 |
| `npm run monitor:site` | 只读检查 canonical 站点 |

开发约定：先在分支上修改；保留原件字节和第三方许可；只保留一个当前版本；不提交 `dist/`；
不执行收录 Skill 的脚本；PR 必须通过 Quality checks。更详细的架构、需求和验收证据见：

- [AGENTS.md](AGENTS.md) — 维护约定和当前项目边界
- [docs/DemandAnalysis.md](docs/DemandAnalysis.md) — 范围、FR/NFR/US/AC
- [docs/TechnicalSolution.md](docs/TechnicalSolution.md) — 架构、模块和数据契约
- [docs/AiProgrammingGuide.md](docs/AiProgrammingGuide.md) — 实施和验证规则
- [.specify/memory/constitution.md](.specify/memory/constitution.md) — 项目宪章
- [specs/007-overall-acceptance/validation/](specs/007-overall-acceptance/validation/) — 当前验收矩阵和证据

## 常见问题

**Q：需要登录才能浏览或下载吗？**

A：不需要。访客只读；管理写入只通过 GitHub 仓库和授权 Agent 完成。

**Q：为什么页面上看不到刚提交的 Skill？**

A：先看 Quality checks 和 Maintain site 是否成功，再核对 catalog 必填字段、`content_path` 和构建日志。
本地 `npm run build` 成功不等于线上已发布。

**Q：可以批量导入或解压 ZIP 吗？**

A：当前没有面向访客的批量导入/站内上传；管理员可用 GitHub 后台、`skill-cli` 或 GitHub 来源更新。
ZIP 解压和平台格式导出不属于当前能力。

**Q：能导出 Codex/Claude Code 专用格式吗？**

A：站点提供原件、目录 ZIP、原文复制和分享链接，不提供平台专用格式转换。

**Q：自动更新现在就在生产运行吗？**

A：生产调度已启用；`sepia` 已配置 `source_tracking` 并通过手动 run `45160746326` 建立首次基线，
之后每日 schedule 检查上游变化；其余 6 项仍为 `null`。Demo-002 的自动更新证据来自受控 POC。

**Q：Agent 可以帮我上传/更新吗？**

A：可以。使用本文的“用 Agent 维护 Skill”提示词，先 preview，人工确认后才 `--publish`；
Agent 不应执行 Skill 脚本、打印 token、force push 或手工改 `dist/`。

## 许可与第三方内容

仓库当前没有单独的仓库级 LICENSE 文件；各 Skill 的许可以其 `catalog` 字段和来源仓库为准。
下载、再分发或商用前请自行核对作者和许可；本站的展示/搜索文本不能替代原件许可信息。
