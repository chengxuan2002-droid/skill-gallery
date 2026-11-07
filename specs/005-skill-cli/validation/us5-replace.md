# US-005 替换与冲突验收（T010）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 在系统临时项目与临时裸远端执行显式替换、旧附件清理、元数据保留和过期基线冲突；
不访问网络、不推送真实远端、不部署。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 方法

使用 `tests/support/skill-cli-fixture.js` 创建临时项目与裸远端：

1. 以目录型候选 `cli-pack`（含 `references/note.md` 与 `references/old.md`）执行 `add --publish`，
   记录基线提交。
2. 修改 `SKILL.md` 并删除 `references/old.md`，以基线 SHA 执行
   `replace cli-pack <candidate> --expected-revision <baseline>`。
3. 再次修改内容，用伪造的过期基线执行 `replace`，确认冲突且远端不变。

结束后删除临时项目与裸远端；不使用 GitHub 或凭证。

## 2. 结果

| 检查 | 结果 |
|---|---|
| 初始新增 | 退出码 `0`、`status=submitted`；基线提交 `adb8ad391fbcf0d4c408898e0b3f5843fa2fc46a` |
| 替换 | 退出码 `0`、`status=submitted`；提交 `da88cdadd5824739729e51080508a042b255186a` |
| 远端当前树（目标范围） | `catalog/cli-pack.json`、`skills/cli-pack/SKILL.md`、`skills/cli-pack/references/note.md` |
| 旧附件 `references/old.md` | 已从远端树移除 |
| 站内元数据 | `display_name` 保持 `Original Pack`（未传 `--meta` 时保留原记录） |
| 单版本 | 目标 slug 只有一组当前文件，无旧版本目录 |
| 冲突 | 退出码 `4`、`status=failed`、`E_CONFLICT`；远端 HEAD 与目标树均未变化 |
| 本地工作区 | `git status --porcelain` 为空 |

冲突诊断只含稳定码与位置/期望/实际提交标识，不回显文件内容或凭证。

## 3. 未运行与限制

- 未调用真实 GitHub Actions 或 POC-002；`content_status`/`deploy_status` 保持 pending，未报告 published。
- 未单独覆盖“同内容 + 同元数据 replace 返回 noop”和“仅元数据变化提交”；实现已按记录摘要处理，
  留待后续全量测试或 T021 补证。
- 未覆盖单文件与目录互转、替换时远端并发前进、分支保护或未授权推送。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
