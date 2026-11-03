# 跨平台基线与 C-01 缺口修正

日期：2026-11-03。范围：修复 Windows 检查基线、换行符保真、空主文档与路径所有权校验。
映射 FR-001、FR-011、NFR-001、NFR-003、NFR-006，DEC-002、DEC-003、DEC-005、DEC-009，
AC-001、AC-002、AC-012 的本地子集。本记录不表示 T011 以后任务、业务构建或生产发布完成。

## 环境

- Windows 11；Node 22.21.0、npm 10.9.4。
- `.node-version` 与 `engines` 仍为 Node 26.3.0；本轮未能在该版本复验，不能冒充 26.3.0、Linux 或 macOS 证据。
- 验证期间系统临时盘写满，容量边界用例改用非系统盘临时目录后通过；未删除用户数据。
- 当前分支 `codex/development-baseline-20261102`，未提交、未推送、未发布。

## 修正内容

| 问题 | 修正 | 文件 |
|---|---|---|
| Windows 检出把跟踪文本转成 CRLF，`format:check` 失败，原件工作区字节偏离基线 | 新增 `.gitattributes`：项目文本 `lf`，`skills/**` 禁止换行转换并保留 diff；规范化 90 个跟踪文本文件 | `.gitattributes` |
| 测试夹具在 Windows 创建目录符号链接报 EPERM | 夹具在 Windows 使用 junction，其他平台仍用目录符号链接 | `tests/integration/bootstrap.test.js` |
| Windows 上 `spawnSync('npm')` 找不到 npm.cmd；扫描器报告路径使用反斜杠 | 新增 npm 命令与扫描器 `.exe` 解析，报告路径统一为 POSIX 分隔符 | `scripts/check-project.js` |
| Windows 安全工具安装仅覆盖 tar.gz | 增加 Windows zip 校验和、`gitleaks.exe` 解包与 `semgrep.exe` 路径；下载失败改为稳定错误码 | `config/security-tools.json`、`scripts/setup-security-tools.js` |
| 空/纯空白主文档、目录型 Skill 缺 SKILL.md 未被拒绝 | 统一返回 `E_MAIN_MISSING`；先确认主文档存在，读取后确认非空白 | `scripts/lib/validate.js` |
| 同一路径可被两项记录拥有 | 新增记录集所有权校验：重复 slug、重复/嵌套内容范围返回 `E_DUPLICATE`，路径与 slug 不匹配返回 `E_SCHEMA` | `scripts/lib/ownership.js`、`scripts/lib/validate.js` |
| `validate.js` 超过 300 行 | 拆分为 `admission-policy`（限额、空白、诊断辅助）、`file-admission`（文件枚举与路径准入）和 `validate`（记录入口），公共导出保持不变 | `scripts/lib/admission-policy.js`、`scripts/lib/file-admission.js`、`scripts/lib/validate.js` |

## 实际验证

| 检查 | 结果 |
|---|---|
| 六项原件工作区 SHA-256/大小 | 与 `migration-baseline.json` 全部一致；未改原件 |
| `git ls-files --eol` | 116 项 `lf/lf`，无 `w/crlf`；二进制夹具保持原样 |
| `npm run lint` | exit 0 |
| `npm run format:check` | exit 0；修正前为 exit 1（17 个文件 CRLF） |
| `node --test tests/unit/*.test.js` | exit 0；46/46 通过 |
| 校验模块行数 | `admission-policy.js` 68、`file-admission.js` 284、`validate.js` 48，均低于 300 |
| `node --test tests/integration/export-regression.test.js tests/integration/site-monitor.test.js` | exit 0；14 通过、1 项按设计跳过 |
| 新增空主文档/目录缺主文档断言 | 修正前失败，修正后通过；`input-boundaries.test.js` 与 `main-document-and-ownership.test.js` 合计 11/11 |
| 新增所有权断言 | 修正前 `validateRecordOwnership` 未定义，修正后通过 |
| `npm test` | exit 1；66 项中 63 通过、2 失败、1 跳过；两项失败均为本机未安装 Gitleaks/Semgrep |
| `npm run check` | exit 1；Lint 与格式通过，测试阶段因上述两项扫描器用例失败 |
| `npm run setup:security` | exit 2，`SCANNER_DOWNLOAD_FAILED`；本环境无法下载固定扫描器 |
| `npm run security:deps` | exit 2，`AUDIT_UNAVAILABLE`；npm 已可执行，审计网络不可用 |
| `npm run security:secrets` / `security:code` | exit 2，`TOOL_UNAVAILABLE`；扫描器未安装，不能算通过 |
| Windows zip 解包路径 | 用本地合成 zip 验证 `tar -xf ... gitleaks.exe` 可解出；未完成真实包安装 |
| Windows junction 清理 | 删除夹具目录后链接目标文件仍存在，未误删共享 node_modules/.tools |
| `audit registry` 集成用例 | Windows 下通过，证明 npm.cmd 与 `.cmd` shim 路径有效 |

## 未运行与剩余风险

- 未在 Node 26.3.0、Linux、macOS 或 GitHub runner 复跑本轮改动；CI 仍是安全扫描的强制入口。
- 扫描器安装与完整 `security` 未通过，当前不能称为安全门禁通过；依赖仍有既有 6 个 moderate，本轮未重新审计。
- Windows 文件系统不保留 POSIX 执行位；原件执行位与 ZIP 模式的跨平台验收仍由 T041 在 macOS/Linux 完成。
- 未提交、未推送、未修改 Pages/分支保护/定时任务；线上站点仍为旧实现。
- `.gitattributes` 只影响后续检出与本次工作区规范化；提交前需确认该文件和既有 CRLF 变更按预期纳入。
