# US-001 最终差异复核

日期：2026-11-04。范围：T043。对照 T001 基线、[acceptance.md](acceptance.md) 与四份 0.2 规范。
本记录确认本地代码/文档状态，不表示已推送、已合并、已部署或 US-001 全部跨平台完成。

## 分支与发布状态

- 当前分支 `codex/development-baseline-20261102`，相对 `origin/main`（`365d577`）复核时领先 50 个提交；
  `origin/main` 是当前 HEAD 的祖先，无 force push 或历史重写记录。
- 远程同名分支仍为 `84e6c27`；`main` 仍为 `365d577`。本轮 T039–T043 未推送、未创建 PR、未部署。
- 本地提交按任务拆分；T043 记录按用户“每步验证后提交”的指令单独提交，未附带推送或发布。

## 内容与原件

| 检查 | 结果 |
|---|---|
| 六原件 SHA-256/大小 | 与 `migration-baseline.json` 全部一致，0 处不匹配 |
| `git diff origin/main...HEAD -- skills` | 空；未改动原件目录 |
| `skills/office2md/` | 当前工作区不存在；未扫描、未导入、未提交 |
| 图库记录 | `catalog/` 恰四份，slug 唯一：`superpower-systematic-debugging`、`code-review-assistant`、`refactoring-workflow`、`handoff-codex` |
| 单版本 | 当前 dist 索引 4 项，无旧版目录/版本选择器；Git 历史保留 |
| 旧根索引 | `git diff origin/main...HEAD -- assets/search-index.json` 为空；`git hash-object` 与 `origin/main` blob 一致（`2d631fe1...`），构建只写 dist |

Windows 不保留 POSIX 执行位（工作区显示 0666）；Linux WSL 上 `create_handoff.sh` 的 ZIP 条目为 0755、
其他文件 0644，详见 [platform.md](platform.md)。Windows 模式不能替代 Linux 结果，macOS 仍缺。

## 依赖、生成物与范围

- 精确依赖：yaml 2.9.1、marked 18.1.2、sanitize-html 2.18.1、yazl 3.3.1、minisearch 6.3.0；
  yauzl 3.4.0 仅开发测试；另有已锁定的 ESLint/Prettier 开发工具。`npm ls --depth=0` exit 0，无额外依赖。
- `git ls-files dist node_modules .tools` 为空；生成目录/扫描器/依赖不进入版本控制。
- 变更文件限定于 AGENTS/README、站点前端、构建/预览/迁移/校验模块、catalog、测试夹具与测试、
  当前功能 spec/plan/tasks/validation；旧 v1 设计和计划仅加历史提示，未按旧计划重建项目。
- 四份 0.2 主文档的业务范围未被降低；当前实现只完成了其中 US-001 的本地切片。

## 凭证、格式与检查

- `npm run security:secrets`：exit 0，Gitleaks 8.30.1 扫描 179 个文件，无发现。
- `npm run security:code`：exit 0，Semgrep 1.183.0 扫描 30 个文件，无发现。
- `npm run security:deps`：exit 2，`AUDIT_UNAVAILABLE`；依赖审计未通过，不能称为零漏洞或全部安全门禁通过。
- `npm test`（Windows，扫描器已安装）：138 项，137 通过、0 失败、1 跳过。
- `npm run lint` / `npm run format:check`：exit 0；未格式化 `skills/` 原件，未做全库无关重排。
- 诊断与报告未打印真实凭证；示例使用文档化占位值。

## 链接、快照与取用

- 四个旧 `#/skill/<slug>` 链接在 US2/US3 浏览器验收中直接访问、刷新、复制和下载均保持同一身份；
  子路径资源在 `/skill-gallery/` 下加载。
- `contentRevision`、detail digest、raw/ZIP 摘要同快照校验通过；同 slug 第二次构建后旧链接仍指向新版，
  无旧文件残留；US2/US3 证据见 [us2-browser.md](us2-browser.md)、[us3-failures.md](us3-failures.md)。
- 本地构建返回 `built`；提交后清理失败只报 `cleanup_status=pending`，不冒充发布成功。

## 未完成与上线门禁

- **T041 macOS 未运行**；T041 保持未完成。Linux/WSL 结果不能替代 macOS。
- 未验证生产 GitHub Pages 的 MIME、缓存、直接资源安全、授权恢复和部署回滚。
- 上传 CLI、GitHub 后台维护、自动更新、发布与 Q-004 调度未实现/未启用。
- NFR-002 的 1,000 项/10 MiB/p95 与 NFR-005 的完整多视口/键盘/多浏览器未执行。
- 依赖审计不可用；干净 Linux 副本未装扫描器时仍有 2 项扫描器用例失败。
- 两次 rename 的短暂间隙、断电/强杀和网络文件系统恢复不在本轮保证内。

结论：本地内容保真、US1/US2/US3 取用与故障保护、Polish 的可复现/文档/验收证据已具备；但 T041 macOS、
生产发布前检查及后续维护/自动更新未完成，不能宣称 US-001 完整交付或原地址已更新。
