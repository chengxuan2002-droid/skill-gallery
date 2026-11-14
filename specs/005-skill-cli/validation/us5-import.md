# US-005 GitHub 来源导入验收（T013）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 在系统临时项目与裸远端中，用注入的结构化来源执行单文件/目录预览、发布和错误映射；
不访问 GitHub、不使用凭证、不推送真实远端。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 方法

使用 `tests/support/skill-cli-fixture.js` 创建临时项目/裸远端与固定来源树；通过
`importCandidate` 注入来源读取结果，验证：

- 单文件来源预览与发布；
- 目录来源（`SKILL.md` + `references/note.md`）预览；
- 404、`truncated`、可变 revision、路径越界、符号链接模式全部失败关闭；
- 普通网页地址/非法 path/非法 ref_policy 由来源定位校验拒绝（测试覆盖）。

结束后删除临时项目与裸远端；默认 `gh api` 读取器未在本次演练中访问网络。

## 2. 结果

| 场景 | 结果 |
|---|---|
| 单文件预览 | `ok=true`、`status=previewed`，`content_revision` 为 64 位内容摘要 |
| 单文件发布 | `ok=true`、`status=submitted`；远端提交只含 `catalog/cli-single.json`、`skills/cli-single.md` |
| 目录预览 | `ok=true`、`status=previewed` |
| 404 | `ok=false`、`E_SOURCE` |
| 文件树截断 | `ok=false`、`E_SOURCE` |
| 可变 revision（`main`） | `ok=false`、`E_SOURCE` |
| 路径越界（`../evil.md`） | `ok=false`、`E_SOURCE` |
| 符号链接模式（`120000`） | `ok=false`、`E_SOURCE` |
| 本地工作区 | `git status --porcelain` 为空 |

来源失败未产生提交或写入；诊断只含稳定码与位置，不回显文件内容或凭证。

## 3. 真实 gh api 导入（2026-11-14 补验）

在 POC-002 目标仓库和 POC-003 来源仓库执行真实导入，详见 [us5-real-gh.md](us5-real-gh.md)：

- 发现并修复 `source-github.fetchSource` 未默认创建 `createGhReader()` 的问题；
- 真实 preview 成功，`content_revision=b2dbc03c...`，工作区无写入；
- 真实发布 `us5-real-wait` 提交 `1017dd4...`，运行 `43612262185` build/deploy success；
  目标 5 个文件与来源逐字节一致，catalog slug/content_path/source_type 正确；
- 目标 POC 站点 manifest `contentRevision=31baae8c...`，包含 8 项 Skill。

## 4. 未运行与限制

- `release` 策略的最新 Release 解析未单独演练；普通网页 URL 已由校验拒绝。
- 未覆盖真实 403/429/超时的响应，只覆盖注入的错误路径。
- 真实导入在 POC-002/POC-003 受控仓库执行，不代表生产来源或生产发布。
- 本机为 Node 22.21.0/Windows；Node 26.3.0/Linux 的完整测试由 CI 覆盖。
