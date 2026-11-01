# 本地工程初始化验证

日期：2026-11-02；执行 project-bootstrap，用户随后授权每步提交，以及清理四份既有源码的格式/Lint。
固定部署地址：https://chengxuan2002-droid.github.io/skill-gallery/；资源前缀保持 /skill-gallery/。
本记录是工程验证，不能替代 US-001 的业务验收。

## 环境与产物

- Node 26.3.0、npm 11.16.0；保留 CommonJS，没有重新起框架脚手架。
- 五个精确开发依赖及根 package-lock；产品解析、渲染、归档依赖仍归 T002 后续业务工作。
- Gitleaks 8.30.1；官方发布归档 SHA-256 验证后安装至 .tools/bin。
- Semgrep CE 1.183.0，通过已有 uv 0.12.3/Python 3.12.13 安装在独立 .tools 工具环境。
- 自有 ESLint/Prettier/EditorConfig、显式 unit/integration 入口、三类安全检查及脱敏诊断。

## 实际验证

| 检查 | 结果 |
|---|---|
| npm ci（隔离副本） | exit 0，manifest 与锁文件未变；另验证了 --ignore-scripts 安装 |
| npm ls --depth=0 | exit 0，五个开发依赖与精确版本一致 |
| npm run check | exit 0，Lint、格式和 11 项工程测试通过 |
| npm test | exit 0，11/11，包含真实扫描器、受限发现和失败路径 |
| npm run security:secrets | exit 0，无发现；范围为 Git 公开候选及已跟踪原件，排除未纳管 Skill |
| npm run security:code | exit 0，自有 JS 与 ESLint 配置共 5 个文件，有限本地规则无发现 |
| npm run security:deps | exit 0，无 high/critical；报告 6 个 moderate 受影响依赖 |
| npm run security | exit 0，复用上述三个真实检查入口 |
| npm run setup:security 再运行 | exit 0，复用同版本工具；工程源文件无配置漂移 |
| 整理前后 JS AST 核对 | 仅忽略位置/原始引号格式及已授权删除的空 catch 未用绑定，结构一致 |
| 整理前后旧构建（两个隔离副本） | exit 0，四项索引 JSON 完全相等；未在正式目录重建索引 |
| 原件和工作区保护 | 四项六原件及全部 12 个既有 skills 文件字节/模式不变；无关既有文件不变 |

依赖审计中的 moderate：@eslint-community/eslint-utils、@eslint/config-array、@eslint/js、eslint、
eslint-config-prettier、minimatch。阈值按初始化方案固定为 high；这些发现未被忽略、抑制或报告为零漏洞。
后续调整依赖需单独评估兼容性和审计，不能擅自执行 audit fix。

初次检查暴露 assets/app.js 空 catch 的两条 Lint 问题，以及四份源码格式差异。
用户明确授权后，仅格式化 index.html、assets/app.js、assets/style.css、scripts/build-index.js，
将未用异常绑定改为可选绑定并说明原有最佳努力行为；未改变导出/渲染/搜索逻辑。

## 拒绝与保真证据

首个 CLI 契约测试在包装器不存在时 exit 1（未满足约定），实现后通过。
嵌套字段进入诊断的测试先失败，字段类型验证后通过。最终 11 项测试实际验证：

- 非法命令、无效/缺项报告、扫描遗漏、越界报告路径、损坏工具归档均拒绝。
- 真实 ESLint、Prettier、Gitleaks、Semgrep 拒绝各自受控违规样例；非法规则与审计网络故障保留失败。
- 命中结果不回显假值、源码或子进程任意错误；报告仅保留安全白名单字段。
- 只执行受信任 unit/integration 测试；不执行收录测试哨兵，原件不被 Lint/格式修改。
- 已跟踪公开 Skill 参加凭证扫描；未纳管 office2md 不自动扫描入库，数据始终保持不变。

## 阶段与提交

步骤 1～7 已按各自产物分步提交；既有源码清理是用户追加授权的独立提交。
步骤 8 检查型 CI 未纳入本轮授权，未创建工作流；本记录随步骤 9 提交，开发命令随步骤 10 提交。
只暂存明确路径，不使用 git add .；已有 README 的其他修改以单独索引内容保留在工作区。

T001、T044～T047 按对应阶段真实证据更新；T002/T003 的业务依赖和完整数据夹具未完成。
US-001 迁移、图库记录、保真原文/ZIP、M-01～M-04、业务 PoC 与业务 AC 未实施。
没有创建 build/preview 空脚本、上传/同步入口、生产监控、CI、分支保护或部署；没有执行 push。
网站线上状态未作为本地初始化成果验证或改变。
