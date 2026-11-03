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
| `npm run security:deps` | 审计根锁文件；high/critical 阻断，其他级别报告 |
| `npm run check` / `npm run security` | 分别汇总规范/测试、安全检查；保留真实失败退出码 |

安全结果只输出规则、位置、级别及状态，不输出凭证或源码片段。
见[诊断约定](specs/001-preserve-skill-content/validation/diagnostics.md)和[本次验证](specs/001-preserve-skill-content/validation/bootstrap.md)。
当前审计仍有 6 个 moderate 受影响依赖，无 high/critical；通过阻断阈值不表示零漏洞。
Windows 下由 `.gitattributes` 保持项目文本为 LF，测试夹具使用 junction；安装器支持 Windows zip 与
`gitleaks.exe`/`semgrep.exe`，但仍需网络。扫描器未安装时，`npm test` 中两项扫描器用例与 `npm run check`
会失败，不能视为通过；当前环境复核见 [跨平台基线与缺口修正](specs/001-preserve-skill-content/validation/baseline-remediation.md)。

本轮已接入本地 `npm run build` 与 `npm run preview`（仅 `dist`，不发布）。
US-001 的内部 US1 切片（T001–T024）已完成本地闭环：四份 catalog、四项迁移、完整 dist 构建、只读预览和旧 Hash 链接已在隔离项目验证
（见 [US1 迁移验收](specs/001-preserve-skill-content/validation/us1-migration.md)）。
US2 的完整查阅、复制和下载已实现并完成本地浏览器验收（见 [US2 验收](specs/001-preserve-skill-content/validation/us2-browser.md)）；
US3 的非法内容、路径攻击、构建故障与恢复已完成本地验收（见 [US3 验收](specs/001-preserve-skill-content/validation/us3-failures.md)）；
Polish 的跨平台与总验收仍未完成；上传、自动更新和生产发布仍待后续故事。
本地验收使用 Windows + Node 22.21.0；声明的 Node 26.3.0/Linux 由 CI 覆盖，结果见下方 T052 run。
初始化按步骤验证并提交，提交不等于推送或上线。

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
`main` 尚未合并该补强，默认分支仍使用旧版 quality workflow；`pull_request`/手动触发配置存在但本次未单独执行。
quality 合并必需项仍需单独配置。
本次没有修改分支保护、通知设置或 Pages 配置；推送触发的既有 Pages 发布也已成功。
失败首先表现为 Actions 失败运行；是否收到邮件取决于自己的 GitHub 通知设置，不能把本地测试当通知已送达。

公开仓库长期无活动时，GitHub 可在 60 天后停用定时 workflow，需要维护者重新启用；
不要通过定期空提交规避停用。说明依据：[定时触发](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)、
[运行通知](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs)。
首页标识或索引切换新版契约时，同步修改监测断言与测试；浏览器交互、JS 异常和完整下载一致性另行验收。
实测与边界见[CI/监测验证记录](specs/001-preserve-skill-content/validation/ci-monitor.md)。

### 换电脑或更换 Code Agent

完整开发基线位于 `codex/development-baseline-20261102` 分支；该分支已包含 US1 本地实现与 T052 CI 补强，
合入主分支前，直接克隆此分支接续开发：

```bash
git clone --branch codex/development-baseline-20261102 https://github.com/chengxuan2002-droid/skill-gallery.git
cd skill-gallery
```

先安装上文指定的 Node、npm 和 uv，再执行上文的安装、工程及安全检查命令。
`node_modules/`、`.tools/`、`.env*`、系统杂项和本机凭证不随仓库迁移；GitHub 写入凭证在新电脑独立授权。
不复制旧电脑的 SSH 私钥、Agent 会话或工具执行授权来替代新环境的授权。

当前功能是 `specs/001-preserve-skill-content`。`.specify/feature.json` 按 Spec Kit 规则保持本机忽略；
首次在新副本运行以下命令，会检查规划文件并恢复这个本地指针：

```bash
export SPECIFY_FEATURE_DIRECTORY=specs/001-preserve-skill-content
bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
```

新 Agent 先读 [AGENTS.md](AGENTS.md)、[宪章](.specify/memory/constitution.md)、四份规范和当前功能
[spec](specs/001-preserve-skill-content/spec.md)、[plan](specs/001-preserve-skill-content/plan.md)、
[tasks](specs/001-preserve-skill-content/tasks.md)，再核对真实文件与验证记录。
项目级 Skills 保存在 `.agents/skills/`，Spec Kit 初始化来源记录为 1.2.5/Codex；其他 Agent 若不自动发现，
应按其机制读取这些文件或配置入口，不能因更换工具而覆盖规范、重新生成任务或重跑 `specify init`。
可选的 Specify CLI 及其他 Agent 适配器需在新电脑单独安装并验证；现有 Bash 检查不依赖全局 CLI。

本次基线用于接续开发，不表示 US-001 已完成或已通过新的规格一致性分析。
后续先复核 spec/plan/tasks，再按明确授权实施。交接记录保留在独立交接分支，未收录的 `office2md` 不属于此基线。
此开发分支不合入 `main`、不修改 Pages 配置；合入前须核对只发布允许公开的静态产物，排除规划和工具资料。

下文保留现有版本和历史部署说明。


> 下一轮改造准备（2026-11-01）：[业界调研](docs/IndustryResearch.md) · [产品需求](docs/DemandAnalysis.md) · [技术方案](docs/TechnicalSolution.md) · [AI 编程规范](docs/AiProgrammingGuide.md)。四份文档描述计划，后台、上传命令和自动更新尚未实现；下文仍为现有版本的使用说明。

个人 AI Agent Skill 收藏夹——统一管理、快速查找、跨平台复用、一键分享。

> 🔗 [在线浏览](https://chengxuan2002-droid.github.io/skill-gallery/)

## ✨ 特性

- **统一格式** — 所有 skill 以 markdown + YAML frontmatter 存储，结构清晰
- **全文搜索** — 按名称、描述、标签、正文内容秒级检索
- **多维筛选** — 按标签、平台、来源多维度过滤
- **多格式导出** — 一键导出为 Codex、Claude Code 等平台格式
- **静态部署** — 原生前端；本地使用 Node 工程检查，不需要后台服务
- **暗色模式** — 跟随系统，也可手动切换

---

## 🚀 快速开始

### 本地预览

```bash
# 1. 构建搜索索引
node scripts/build-index.js

# 2. 启动本地服务器
python3 -m http.server 8000

# 3. 打开浏览器访问
# http://localhost:8000
```

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

以后添加了新 skill，只需：

```bash
node scripts/build-index.js          # 重建索引
git add skills/new-skill.md assets/search-index.json
git commit -m "add: new skill"
git push
```

GitHub Pages 会自动更新，通常几十秒内生效。

---

## 📖 使用教程

### 一、添加 Skill

所有 skill 都存放在 `skills/` 目录下，每个 skill 是一个 `.md` 文件。文件名即 `slug`（URL 中显示的标识），只用小写字母、数字和短横线。

添加流程：**新建文件 → 填写内容 → 重建索引 → 提交推送**

```bash
# 1. 新建 skill 文件
vim skills/my-new-skill.md

# 2. 重建搜索索引
node scripts/build-index.js

# 3. 提交
git add skills/my-new-skill.md assets/search-index.json
git commit -m "add: my new skill"
git push
```

下面按不同来源分别给出示例：

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

### 三、导出 Skill

在 skill 详情页右上角点击 **"Export ↓"** 按钮，有 4 种导出方式：

---

#### 导出方式 1：Codex SKILL.md

导出为 Codex 原生的 `SKILL.md` 格式（frontmatter + markdown 正文）。

**使用方法：**
1. 点击 "Codex SKILL.md" → 自动下载 `.md` 文件
2. 将文件放入你的 Codex skills 目录
3. 重启 Codex 即可使用

**示例输出（节选）：**
```markdown
---
name: Systematic Debugging
description: Step-by-step debugging workflow...
tags: [debugging, workflow, problem-solving]
platforms: [codex, claude-code, generic]
source: self-built
author: Your Name
created_at: 2026-08-02
updated_at: 2026-08-02
usage_notes: |
  Most useful for bugs that are hard to reproduce.
  Always start with reproduction steps before diving into code.
---

# Systematic Debugging

A rigorous, step-by-step approach to debugging any software issue.
...
```

> 💡 我们的统一格式本身就基于 Codex 格式设计，所以导出几乎是原样输出，兼容性最好。

---

#### 导出方式 2：Claude Code 格式

导出为 Claude Code 友好的 markdown 格式（去掉 frontmatter，用标题+引用结构）。

**使用方法：**
1. 点击 "Claude Code format" → 自动下载 `.md` 文件
2. 将文件放入 Claude Code 的 custom skills 目录
3. 根据需要微调格式

**示例输出（节选）：**
```markdown
# Systematic Debugging

> Step-by-step debugging workflow for reproducing and fixing any bug

**Platforms:** codex, claude-code, generic

---

A rigorous, step-by-step approach to debugging any software issue.

## Steps
...
```

> ⚠️ 不同 agent 平台格式可能略有差异，导出后可能需要微调。

---

#### 导出方式 3：复制原始 Markdown

一键复制完整的 skill markdown 内容（含 frontmatter）到剪贴板。

**使用场景：**
- 想快速粘贴到自己的编辑器里修改
- 想贴到聊天中分享
- 想在其他工具中使用

**操作：** 点击 "Raw markdown" → 提示 "Copied markdown to clipboard" → 直接粘贴即可

---

#### 导出方式 4：复制分享链接

复制当前 skill 的网页链接，发送给别人直接查看。

**使用场景：**
- 给朋友推荐某个 skill
- 在文档中引用

**链接格式：**
```
https://chengxuan2002-droid.github.io/skill-gallery/#/skill/systematic-debugging
```

对方打开链接就能直接看到 skill 详情页，也可以自己导出下载。

---

### 四、搜索与筛选

#### 全文搜索

- 在顶部搜索框输入关键词，实时过滤结果
- 搜索范围：名称、描述、标签、正文内容
- 支持模糊匹配（拼写小错误也能搜到）
- 按相关度排序，最匹配的排在前面

#### 标签筛选

- 点击左侧标签可以添加筛选条件
- 多个标签同时选中时是 **AND** 关系（同时满足所有标签）
- 再次点击取消筛选

#### 平台筛选

- 点击平台名筛选特定平台的 skill
- 同样支持多选 AND

#### 排序

- **Recently updated**：按更新时间倒序（默认）
- **Name (A-Z)**：按名称字母排序

---

### 五、常见问题

**Q: 添加了新 skill 但页面上看不到？**
A: 记得运行 `node scripts/build-index.js` 重建搜索索引。

**Q: 可以批量导入吗？**
A: v1 版本只支持手动添加，后续会加入半自动导入脚本。

**Q: 导出的文件在我的 agent 里不能直接用？**
A: 不同平台格式有差异，导出功能做的是"尽力而为"的转换，可能需要手动微调。详情页顶部有兼容性提示。

**Q: 怎么换主题？**
A: 点击右上角的 🌙/☀️ 按钮切换，设置会记住。

---

## 📁 项目结构

```
skill-gallery/
├── skills/                  # Skill 数据源（唯一）
│   ├── README.md            # 格式说明
│   └── *.md                 # 每个 skill 一个文件
├── assets/
│   ├── app.js               # 前端逻辑
│   ├── style.css            # 样式
│   └── search-index.json    # 构建产物（搜索索引）
├── scripts/
│   └── build-index.js       # 构建脚本
├── index.html               # 页面入口
├── .nojekyll                # GitHub Pages 配置
├── specs/                   # 设计文档
└── README.md
```

## 📄 许可证

收录的外部 skill 遵循原作者的许可证，详见各 skill 的来源链接。
