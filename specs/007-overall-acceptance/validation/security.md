# US-007 安全边界复核

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: T017；凭证、路径/URL 边界、上游脚本不执行、公开产物白名单与未授权副作用。
**方式**: 重新运行 `npm run security` 和 27 项定向安全/路径/不可信内容测试；读取
`specs/003-validate-build-publish/validation/us3-security.md` 与 US-006 冲突证据。未打印凭证，
未执行收录 Skill 的脚本，未写生产内容。

## 1. 扫描结果

```bash
npm run security
```

| 检查 | 文件数 | 发现数 | 退出码 |
|---|---|---|---|
| `security:secrets` | 355 | 0 | 0 |
| `security:code` | 56 | 0 | 0 |
| `security:deps` | 1 | 0 | 0 |

三项均 `status=passed`，`findings` 为空；输出没有凭证值、环境变量或响应正文。扫描器版本以
`config/security-tools.json` 为准（Gitleaks 8.30.1、Semgrep 1.183.0）。T017 首次运行 secrets 为
352 个文件；T021 在新增 US-007 validation 文档后复核为 355，其他计数和结论不变。

## 2. 定向测试

```bash
node --test tests/integration/publish/publish-security.test.js \
  tests/integration/publish/publish-security-workflow.test.js \
  tests/integration/publish/publish-artifact.test.js \
  tests/integration/untrusted-content.test.js \
  tests/unit/path-attacks.test.js
```

结果：27 项通过、0 失败、0 跳过。

| 范围 | 覆盖 | 结果 |
|---|---|---|
| 公开产物白名单 | 多文件/篡改/凭证/过期修订失败关闭；未变化重建稳定；缺附件/非法 catalog 保留旧 `dist` | 通过 |
| 工作流权限 | 非 sync job 只读；deploy 仅 `pages`/`id-token` 写；checkout 不持久化凭证；无 secret/PAT | 通过 |
| 凭证 | 凭证文件名、运行时 token 前缀、私钥块被拒绝；库和 CLI 诊断不回显值 | 通过 |
| 路径/URL | 越界、绝对、盘符、反斜杠、控制字符、重复路径、协议相对、编码分隔、`content_path` 越界被拒绝 | 通过 |
| 上游脚本不执行 | 夹具 Skill 内脚本仅作为普通文件发布；构建和产物校验均未触发哨兵写入 | 通过 |
| 不可信内容 | 活动 HTML 被清理；SVG/伪 PNG 不作为可执行资源；原文/附件仍以 inert 文件保留 | 通过 |
| 硬链接/符号链接 | 硬链接拒绝通过；当前 Windows 环境无法创建符号链接（EPERM/EACCES），该分支未执行 | 部分 |

## 3. 复核结论

- **凭证**：仓库扫描 0 发现；测试中的运行时 token/私钥只用于断言，诊断只含稳定错误码和路径。
- **路径/URL**：构建、详情 URL、公开产物和来源候选均拒绝越界/绝对/编码穿越；`/skill-gallery/`
  前缀未产生绝对 URL。
- **上游脚本**：收录 Skill 的脚本没有在构建、预览或产物校验中执行；不可信 HTML 被清理，原件作为
  下载数据保留。
- **公开产物**：`dist/` 只允许站点、索引、详情、公开原件/ZIP 和静态资源；`catalog/`、`docs/`、
  `specs/`、`handoff/`、工具配置和 Git 数据不进入产物；失败批次保留旧 dist。
- **未授权副作用**：`us3-security.md` 的匿名 POC 请求返回 401、未新增运行或站点 revision 变化；
  本轮未重跑真实远程未授权尝试。

## 4. 未运行与限制

- 真实 fork/受限身份、生产仓库匿名写尝试未运行；生产 environment 审批已补验（见
  `production-environment.md`）。
- 当前 Windows 环境无法创建符号链接；硬链接已覆盖；Linux/macOS runner 的符号链接测试已通过。
- 真实 403 已观察（见 `remote-errors.md`）；真实 source-sync 429、CDN/强刷和真实远程脚本执行
  未运行；MIME/缓存基础头已复核（见 `fixed-address.md`），不能把本轮结果写成生产安全全量验收。
