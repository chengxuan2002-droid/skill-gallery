# US-001 本地验收汇总

日期：2026-11-04。范围：T042；对应上游 US-001 的本地可执行部分。映射 FR-001、FR-004、FR-011，
NFR-001、NFR-003、NFR-006，AC-001、AC-002、AC-005、AC-012、AC-014 本地部分。
本记录不表示已推送、已部署或 US-001 全部跨平台完成。

## 环境与隔离副本

- 干净副本由 `git archive HEAD` 导出到 WSL `/tmp/sg-accept`；HEAD 为 `5dd043d`。
- WSL2 Ubuntu 24.04（Linux 5.15.167.4-microsoft-standard-WSL2）；Node 26.3.0、npm 11.16.0。
- Windows 11 + Edge 156.0.4314.58 用于既有浏览器验收；Windows 本地 Node 22.21.0 不作为声明基线。
- Linux Node 26.3.0 需加载 Ubuntu `libatomic1` 解出的 `libatomic.so.1`；未修改系统包。
- 未写入正式 catalog、未执行 Skill 脚本、未安装 Skill 依赖、未推送或发布。

## 实际命令与结果

| 命令 | 实际结果 |
|---|---|
| `npm ci --ignore-scripts --no-audit --no-fund` | exit 0；added 103 packages |
| `node scripts/migrate-catalog.js --dry-run` | exit 0；`dry_run`，4 项，诊断空 |
| `node scripts/migrate-catalog.js --write` | exit 0；`noop`，`verified`，4 项，未覆盖已有记录 |
| `node scripts/build-index.js` | exit 0；`built`、`cleanup_status=complete`，contentRevision `1411cac17c3d289fae5d53a470453e59d7b9bf66a0cf696e778cd3d84ed84788` |
| `node --test tests/unit/*.test.js tests/integration/*.test.js`（干净 Linux 副本，未装扫描器） | 138 项中 135 通过、2 失败、1 跳过；两项失败为本机未安装 Gitleaks/Semgrep |
| 同命令（Windows 本地，`npm run setup:security` 后） | 138 项中 137 通过、0 失败、1 跳过；Gitleaks/Semgrep 已安装通过 |
| 分发/复现/恢复定向测试 | 23/23 通过 |
| `node scripts/preview.js` + `curl` | 首页 200 `text/html`；app.js 200 `application/javascript`；`.bin` 200 `application/octet-stream`；dist 外 404 |

六个原件与 `migration-baseline.json` 的路径、大小与 SHA-256 全部一致；当前工作区不存在 `skills/office2md/`，
构建未扫描或导入任何未纳管目录。四个 catalog slug 为 `superpower-systematic-debugging`、
`code-review-assistant`、`refactoring-workflow`、`handoff-codex`。

Windows Node 22 构建的 contentRevision 与本记录不同，因为运行时标识参与 contentRevision；不能据此声称跨环境
内容身份相同。ZIP 容器字节不要求跨环境一致；解包路径/字节/模式按 [platform.md](platform.md) 与
[T039 测试](../../../tests/integration/reproducibility.test.js) 比较。

## 取用与故障证据

- 分发/解包：`distribution.test.js` 4/4；单文件原名/raw/摘要，目录 ZIP 根、附件、许可、二进制、空目录、
  0644/0755，PublicFile URL 边界。
- 复现：`reproducibility.test.js` 3/3；两个干净副本的 slug/digest/raw/文件清单/解包内容一致；重复构建无伪版本/日期；
  删除附件后旧 `.bin` 与 ZIP 条目消失；无私有路径泄漏。
- 故障/安全：`invalid-batch`、`path-attacks`、`build-failures`、`build-recovery`、`untrusted-content`
  合计 52/52；详见 [us3-failures.md](us3-failures.md)。
- 浏览器：四个旧 Hash 链接、刷新、分享、raw 复制、ZIP/附件下载、剪贴板拒绝、快照混读、迟到响应、锚点、
  同 slug 第二快照和安全展示，见 [us2-browser.md](us2-browser.md) 与 [us3-failures.md](us3-failures.md)。

## US001-SC 判定

| 成功标准 | 判定 | 依据 |
|---|---|---|
| US001-SC-01 四项迁移 100% | PASS | 四 slug/catalog、六原件 SHA-256 与基线一致；未纳管目录未入库 |
| US001-SC-02 原件/包零差异 | PASS | distribution 4/4、reproducibility 3/3；逐路径/字节/解包清单 |
| US001-SC-03 旧链接与失败反馈 | PASS | Edge 四旧链接/刷新/下载；copy_failed/download_failed；同 slug 重建 |
| US001-SC-04 非法输入零破坏 | PASS | US3 52/52；整批失败、旧 dist/原件不变、零执行、凭证不回显 |
| US001-SC-05 标准样例与信息分离 | PASS | US1 契约/迁移测试；只改 catalog 不改原件；未知信息不编造 |
| US001-SC-06 干净副本可复现 | PASS | 两个隔离副本身份/原件/解包一致；无私人路径/凭证 |
| US001-SC-07 可修正诊断 | PASS | 非法批次/路径夹具逐类断言错误码、slug/path/message，诊断字段封闭 |

## 未运行与残留风险

- **T041 macOS 未运行**；Linux/WSL 已通过，但 T041 仍不完整，不能称 macOS 验证通过。
- 未验证生产 GitHub Pages 的 MIME、缓存、直接资源响应头、授权恢复或部署回滚；这些属于 US-003/发布前门禁。
- 未实现/未验证上传 CLI、GitHub 后台维护、自动更新、发布和 Q-004 调度。
- Windows 本地已安装固定 Gitleaks/Semgrep，`npm test` 为 138/137/0/1，`security:secrets` 与 `security:code` 无发现；
  依赖审计仍 `AUDIT_UNAVAILABLE`。干净 Linux 副本未装扫描器，仍有 2 项失败；CI 本次未推送，不能用本地结果冒充远程全部通过。
- NFR-002 的 1,000 项/10 MiB/p95 与 NFR-005 的完整 360/768/1440、键盘/读屏/多浏览器验收未执行。
- Windows 不保留 POSIX 执行位；Linux WSL 的 ZIP 模式已验证，macOS 未验证；未测试断电/强杀和网络文件系统。
- 两次 rename 的短暂间隙仍存在；恢复依赖 C-03 锁/事务记录和人工核对。

## 追溯

T042 汇总 T039–T041 与 US1/US2/US3 的本地证据；AC-001/002/005/012/014 仅作本地覆盖声明。
完整 US-001 交付和原地址发布仍需 Polish 收口、T041 macOS、生产发布前检查及明确部署授权。
