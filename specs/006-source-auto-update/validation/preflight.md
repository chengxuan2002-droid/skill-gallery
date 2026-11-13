# US-006 Preflight

**日期**: 2026-11-12（Asia/Shanghai）
**范围**: US-006 实施前环境、工具与受控仓库边界；不访问真实来源写入、不启用生产调度。

## 1. 环境

| 项 | 实际值 |
|---|---|
| 操作系统 | Windows 11 |
| Node | `v22.21.0` |
| npm | `10.9.4` |
| 锁定基线 | Node `26.3.0` / npm `11.16.0`（`.node-version`、`packageManager`） |
| Git | 可用；项目 `origin` 使用 SSH 别名 |
| gh | `2.88.1`；已登录 `chengxuan2002-droid`，未打印或写入 token |
| 分支 | `codex/us-006-source-auto-update` |

## 2. 实施前基线

- `main` 包含 US-001～US-005 的实现、发布配置与生产 Pages 启用记录。
- 当前 `npm test` 基线以实施后结果为准，见 [us6-quality.md](us6-quality.md)。
- `maintain.yml` 实施前只有 `push`/`workflow_dispatch` 的 build/deploy；没有 schedule、sync job 或 dispatch 输入。
- `catalog/*.json` 的 `source_tracking` 全部为 `null`；schema 已接受该字段。
- `scripts/lib/skill-cli/source-github.js` 已有 branch/release/pinned 与树读取，但缺少 mode 保真、文件数/主文档限制、许可读取和稳定错误码。

## 3. 官方资料复核

实施前按项目规则查询 Context7 的 GitHub Actions 与 GitHub REST 文档，核对：

- `schedule` 使用 POSIX cron、默认 UTC；`17 19 * * *` 对应每日 03:17 Asia/Shanghai。
- `workflow_dispatch` 支持 boolean/string 输入；`inputs.sync` 在表达式中按布尔使用。
- job 级 `permissions` 可覆盖工作流默认只读权限；checkout 默认持久凭证，需要显式 `persist-credentials: false`。
- Release `latest` 返回最新非草稿、非预发布 Release；Tree API 的 `truncated` 必须失败关闭。
- 上述结论只用于配置实现；真实调度、限流和生产行为仍以运行记录或 POC 为准。

## 4. 受控仓库与授权边界

- 消费端复用 POC-002：`chengxuan2002-droid/skill-gallery-poc-20261107`（公开）。
- POC-003 源仓库：`chengxuan2002-droid/skill-gallery-source-poc-20261112`（公开，本次创建）。
- 仅在 POC 仓库执行真实提交、推送、workflow dispatch 和 Pages 部署；生产 `main` 不推送、不启用每日调度。
- 默认测试使用注入读取器与临时裸远端；POC 证据单独记录，不能替代生产调度或 US-007 验收。

## 5. 未运行

- 生产 `main` 的每日调度启用、environment 审批、真实限流/403 与生产 MIME/缓存复验。
- 真实部署失败注入与同提交重跑（见 [us6-status.md](us6-status.md)）。
