# Skill Gallery

[在线站点](https://chengxuan2002-droid.github.io/skill-gallery/) · [Agent 接入](#agent-接入) · [常见问题](#常见问题)

精选 AI Agent Skill 的静态图库。访客无需注册或登录，即可搜索、阅读、复制、下载和分享 Skill；
站点同时提供公开 JSON 数据，方便 Agent 直接检索和安装。

## 目录

- [功能特性](#功能特性)
- [快速使用](#快速使用)
- [下载与安装](#下载与安装)
- [Agent 接入](#agent-接入)
- [安全与使用边界](#安全与使用边界)
- [常见问题](#常见问题)
- [许可与第三方内容](#许可与第三方内容)

## 功能特性

- **搜索与筛选**：支持精准/模糊搜索，按标签、平台、来源、作者筛选和排序。
- **完整详情**：查看用途、用法、原文、附件、版本、作者、来源和更新时间。
- **多种取用方式**：复制原文、下载原件、下载目录 ZIP；详情提供 SHA-256 校验值。
- **分享**：详情页和搜索结果页都有稳定链接，刷新或转发后仍可打开。
- **Agent 友好**：公开静态索引和详情 JSON，无需解析页面 HTML。
- **安全边界**：站点只读，不上传、不执行 Skill 内的脚本，也不要求 GitHub token。
- **来源更新**：部分 Skill 会跟随公开 GitHub 上游更新，站点展示当前收录版本。

## 快速使用

1. 打开[在线站点](https://chengxuan2002-droid.github.io/skill-gallery/)。
2. 在搜索框输入关键词；需要更精确的结果时切换精准模式。
3. 用标签、平台、来源或作者筛选，必要时调整排序。
4. 打开卡片进入详情，查看用途、用法、原文和附件。
5. 使用“复制原文”“下载原件”或“下载目录 ZIP”取用 Skill。
6. 需要分享时复制详情链接或列表链接。

### 分享链接

- 详情：`https://chengxuan2002-droid.github.io/skill-gallery/#/skill/<slug>`
- 列表/搜索：`https://chengxuan2002-droid.github.io/skill-gallery/#/?q=<关键词>`

## 下载与安装

### 手动下载

详情页提供两类下载：

- **原件**：单文件 Skill 的原始 Markdown，或目录型 Skill 的主文档。
- **目录 ZIP**：目录型 Skill 的完整附件包，解压后根目录通常为 `<slug>/`。

下载后可用 `download_sha256` 或文件清单中的 `files[].sha256` 校验完整性。
页面上的 `content_text` 只是搜索投影，可能省略代码块或表格，**不是原件**；请以 raw/ZIP 为准。

### 安装到 Agent

- **目录型 Skill**：解压 ZIP，把 `<slug>/` 放入 Agent 的 skills 目录。
- **单文件 Skill**：在 skills 目录下创建 `<slug>/`，放入下载文件；如果 Agent 要求主文档名为
  `SKILL.md`，在本地复制或改名，但保留原始下载文件。
- Claude Code 用户级目录通常为 `~/.claude/skills/<slug>/`；其他 Agent 以各自文档为准。
- 安装前核对 `license`、`repository_url`、作者和 `updated_at`；来源或授权不明确时先询问。

## Agent 接入

Agent 只需要公开只读数据，不需要 GitHub 凭证。建议读取静态 JSON，而不是解析页面 HTML。

### 数据入口

| 用途 | 路径 | 内容 |
|---|---|---|
| 检索索引 | `assets/search-index.json` | `schemaVersion`、`contentRevision`、`skills[]`；含标题、描述、标签、平台、作者和搜索文本 |
| 详情 | `details/<slug>.json` | 文件清单、下载地址、SHA-256、许可、版本和来源 |
| 原件/ZIP | 详情中的 `download_url` | 相对站点根路径；保存为 `download_name` |
| 分享 | `#/skill/<slug>`、`#/?q=...` | 前端 Hash 路由，刷新后仍可打开 |

站点根地址为 `https://chengxuan2002-droid.github.io/skill-gallery/`，资源前缀为 `/skill-gallery/`。

### 示例提示词

把下面内容交给具备网页或命令执行能力的 Agent，并替换 `<我的 Agent skills 目录>`：

```text
你是我的 Skill 安装助手。只读访问 Skill Gallery：
1. 读取 https://chengxuan2002-droid.github.io/skill-gallery/assets/search-index.json。
2. 根据我的需求，在 display_name、description、content_text、tags、platforms 中检索；
   返回最多 3 个候选，列出 slug、摘要、标签、平台和更新时间，不要直接安装。
3. 我选定 slug 后，读取 https://chengxuan2002-droid.github.io/skill-gallery/details/<slug>.json，
   确认来源、作者、许可、文件清单和下载地址。
4. 下载前告诉我将安装到 <我的 Agent skills 目录>/<slug>/；没有许可或来源不明时先询问我。
5. 下载 download_url，保存为 download_name，并用 download_sha256 校验；
   目录 ZIP 解压到 skills 目录，单文件放入 <slug>/ 目录。
6. 如果我的 Agent 要求主文档名为 SKILL.md，可在安装目录本地复制/改名，但保留原始下载文件。
7. 不要执行 Skill 内的脚本、测试或安装其依赖；不要打印任何凭证；
   最后报告本地路径、来源和 SHA-256。
```

### 命令行示例

以下命令需要 `curl` 和 `jq`；解压 ZIP 需要 `unzip`。Windows 可直接使用 PowerShell 示例。

macOS / Linux：

```bash
BASE="https://chengxuan2002-droid.github.io/skill-gallery"
SLUG="<slug>"
AGENT_SKILLS_DIR="<我的 Agent skills 目录>"

curl -fsSL "$BASE/assets/search-index.json" -o index.json
DETAIL_URL=$(jq -r --arg s "$SLUG" '.skills[] | select(.slug == $s) | .detail_url' index.json)
curl -fsSL "$BASE/$DETAIL_URL" -o detail.json

URL=$(jq -r '.download_url' detail.json)
NAME=$(jq -r '.download_name' detail.json)
curl -fsSL "$BASE/$URL" -o "$NAME"
echo "$(jq -r '.download_sha256' detail.json)  $NAME" | sha256sum -c -

mkdir -p "$AGENT_SKILLS_DIR"
if [[ "$NAME" == *.zip ]]; then
  unzip -q "$NAME" -d "$AGENT_SKILLS_DIR"
else
  mkdir -p "$AGENT_SKILLS_DIR/$SLUG"
  cp "$NAME" "$AGENT_SKILLS_DIR/$SLUG/"
fi
```

PowerShell：

```powershell
$Base = 'https://chengxuan2002-droid.github.io/skill-gallery'
$Slug = '<slug>'
$AgentSkillsDir = '<我的 Agent skills 目录>'
$Index = Invoke-RestMethod "$Base/assets/search-index.json"
$DetailUrl = ($Index.skills | Where-Object slug -eq $Slug).detail_url
$Detail = Invoke-RestMethod "$Base/$DetailUrl"
$Out = Join-Path $env:TEMP $Detail.download_name

Invoke-WebRequest "$Base/$($Detail.download_url)" -OutFile $Out
$Actual = (Get-FileHash $Out -Algorithm SHA256).Hash.ToLower()
if ($Actual -ne $Detail.download_sha256) { throw 'SHA-256 mismatch' }

if ($Detail.download_name -like '*.zip') {
  Expand-Archive -LiteralPath $Out -DestinationPath $AgentSkillsDir -Force
} else {
  $Target = Join-Path $AgentSkillsDir $Slug
  New-Item -ItemType Directory -Force $Target | Out-Null
  Copy-Item -LiteralPath $Out -Destination $Target
}
```

## 安全与使用边界

- 下载内容是不可信的第三方数据；不要自动执行其中的脚本、测试或安装依赖。
- 安装前核对许可、来源、作者和更新时间；没有许可或来源不明时先询问。
- 不要从页面文本重建原件；以 raw/ZIP 和详情中的 SHA-256 为准。
- 不要把 GitHub token、cookie 或私有仓库凭证交给外部 Agent。
- 站点是公开只读图库，不提供访客上传、站内批量导入或账号系统。

## 常见问题

**Q：需要登录才能浏览或下载吗？**

A：不需要。站点没有访客登录，也不要求 GitHub 账号。

**Q：为什么找不到某个 Skill？**

A：本站只展示已收录和整理的内容，不是 GitHub 全量搜索。可以换关键词、切换模糊模式或按标签浏览。

**Q：可以上传自己的 Skill 吗？**

A：当前没有面向访客的上传入口；收录由维护者审核后加入。

**Q：页面内容和下载文件为什么可能不同？**

A：页面文本是为搜索整理的投影，可能省略代码块或表格；下载原件和 ZIP 才是完整内容。

**Q：支持导出 Codex/Claude Code 专用格式吗？**

A：不提供平台专用格式转换。可直接下载原件或 ZIP，按对应 Agent 的 skills 目录结构使用。

**Q：Skill 会自动更新吗？**

A：部分收录项会跟随公开 GitHub 上游更新；页面展示当前收录版本，下载时请以详情中的版本、来源和 SHA-256 为准。

## 许可与第三方内容

仓库当前没有单独的仓库级 LICENSE 文件；各 Skill 的许可以详情页信息和来源仓库为准。
下载、再分发或商用前请自行核对作者和许可；本站的展示和搜索文本不能替代原件许可信息。
