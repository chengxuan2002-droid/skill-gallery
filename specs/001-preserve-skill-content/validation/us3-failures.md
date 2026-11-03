# US3 非法内容与故障保护验收

日期：2026-11-03。范围：US-001 内部 US3 切片（T031–T038）；T030 的 US2 证据见
[us2-browser.md](us2-browser.md)。映射 FR-001、FR-004、FR-011，NFR-001、NFR-003、NFR-006，
DEC-002、DEC-003、DEC-005、DEC-009，AC-001、AC-002、AC-012、AC-014 本地部分，
US001-SC-04、US001-SC-07。本记录不表示上游 US-001 整体完成、已推送或已发布。

## 环境

- Windows 11；Node 22.21.0、npm 10.9.4；Microsoft Edge 156.0.4314.58 headless。
- 使用临时项目、隔离 dist、真实 ZIP/raw 文件与本地 preview；不执行收录 Skill 的脚本。
- 未安装本机 Gitleaks/Semgrep；完整 `npm test` 的 2 项扫描器用例仍失败，不能算作通过。
- 用户要求本轮不推送、不发布；因此没有新增 GitHub Actions 运行，CI 结果仍停留在 US2 时点。

## 自动化结果

| 验证 | 结果 |
|---|---|
| `node --test tests/integration/invalid-batch.test.js` | 6/6 通过；缺/空主文档、坏 YAML、类型/未知字段/版本、重复 slug/来源、越界 content_path、主文档/附件/排除项引用、文件数/主文档/总字节上限均整批失败 |
| `node --test tests/unit/path-attacks.test.js` | 7/7 通过；合法目录内 `../`；越界、单次编码、二次编码、编码分隔、绝对路径、盘符、反斜杠、NUL、协议相对、危险 scheme、点路径准入、硬链接/符号链接、大小写/NFC 碰撞 |
| `node --test tests/integration/build-failures.test.js` | 12/12 通过；ZIP 写流、产物校验、提交前源变化、事务写失败、第二次 rename、补偿失败、并发锁、提交后清理 pending、未知临时项、prepare/promoted/damaged 事务 |
| `node --test tests/integration/build-recovery.test.js` | 4/4 通过；prepared 旧输出保留、dist 缺失恢复 backup、候选回滚、promoted 保留候选、损坏产物拒绝、首次构建清理候选 |
| `node --test tests/integration/untrusted-content.test.js` | 6/6 通过；脚本/iframe/object/form/事件/style/危险 URL/伪造 id/name 清理，raw/SVG/脚本仅作数据，栅格签名，preview `.bin` MIME，文件与 catalog 凭证拒绝及占位放行 |
| 上述 US3 相关测试汇总 | 52/52 通过 |
| `npm test` | 135 项中 132 通过、2 失败、1 跳过；两项失败为本机未安装 Gitleaks/Semgrep |
| `npm run lint` / `npm run format:check` | exit 0 |
| `npm run build` | exit 0，`status=built`、`cleanup_status=complete`，contentRevision `07bd1a2ad1e61e6b7d6e42bdbe62a4f3f300d40e85539fa4cb27116e9f9b5c1d` |

非法批次每例均断言 diagnostics 含预期错误码、原件/输入摘要不变、旧 dist 的 manifest 与 sentinel
字节不变；失败不产生部分新输出。诊断只含 code/slug/path/message/severity，不打印凭证值或 parser 原文。

## 浏览器恶意展示与取用

使用真实站点源文件、隔离 untrusted 夹具和本地 preview，Edge headless 结果：

- 页面标题为“不可信内容样例 · Skill Gallery”；正文 `script/iframe/object/form` 0 个，
  `onerror/style` 0 个，危险 `javascript:/data:/file:` href 0 个，伪造 `#forged/[name=bad]` 0 个。
- 受控标题 ID 为 `skill-heading-1`、`skill-heading-2`；合法 `https://example.com/path` 保留。
- 页面内 `UNTRUSTED_SCRIPT_EXECUTED`、`UNTRUSTED_IMG_EXECUTED`、`UNTRUSTED_SVG_EXECUTED`、
  `UNTRUSTED_FAKE_EXECUTED` 均为未定义；脚本/Agent 配置/Skill 自带 tests 未被调用。
- 下载 `assets/evil.svg` 得到同字节 `.bin`，SHA-256 与详情清单一致；状态 `ready`，
  提示“资源已校验，下载已发起”，不把下载说成已安装。
- 构建/浏览后未出现 `UNTRUSTED_SENTINEL`；伪造 SVG/PNG 未生成 `media_url`，真实 PNG 使用受控媒体副本。
- preview 对 `.bin` 返回 `application/octet-stream`，不按 HTML 嗅探，dist 外文件不可读。

## 恢复与状态

- `E_BUSY`：已有 `.dist.lock` 时不抢占、不覆盖旧 dist。
- `E_SOURCE_CHANGED`：提交前源/记录/网页/锁变化时失败，旧 dist 保留；本轮在 `beforeCommit` 注入验证。
- `E_BUILD`：ZIP 写流、产物校验、事务初始写失败时恢复/保留旧输出，首次失败无半成品。
- `E_RECOVERY_REQUIRED`：补偿恢复失败、promoted 但 dist 缺失、记录损坏、候选产物摘要不符时保留
  backup/记录与可用 dist，不猜测删除；恢复表覆盖 prepared/promoted 的旧输出、缺失 dist、候选回滚、
  首次构建和损坏候选。
- 提交后清理失败返回 `status=built`、`cleanup_status=pending`，新 dist 有效，backup/事务记录保留。
- 未知 `.dist.stage-*`/`.dist.backup-*` 不被成功构建顺带删除。
- 两次 rename 仍存在短暂间隙：不承诺强杀/断电时连续服务；中断后的恢复依赖持锁检查和 C-03 恢复表。

## 未运行与限制

- 未推送、未运行新的远程 CI，未部署或修改 Pages；本记录全部为本地验证。
- 未验证生产 Pages 的 MIME、缓存和直接资源响应头；属于 US-003/发布前门禁。
- Windows 上符号链接创建被环境拒绝（EPERM）；硬链接、越界和链接拒绝已用可用场景验证；
  FIFO/设备文件与 POSIX 执行位未验证，跨平台仍由 T041 复核。
- 未做完整 US-002 检索/视觉/性能、US3 远程并发、断电压测或生产回滚。
- 未执行收录 Skill 的脚本/测试，也未安装其依赖。

## 追溯

T031 非法批次、T032 路径攻击、T033 构建故障、T034 不可信内容、T035 引用拒绝、T036 事务恢复与
输入复核、T037 展示/预览安全、T038 本记录。上游 US-001 仍需 Polish（T039–T043）和真实发布前检查，
不能以本记录宣称完成或已上线。
