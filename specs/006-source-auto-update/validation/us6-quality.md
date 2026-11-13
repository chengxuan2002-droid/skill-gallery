# US-006 质量检查

**日期**: 2026-11-12（Asia/Shanghai）
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0 未在本机复验）。

## 1. 完整测试

```bash
npm test
```

结果：**282 项，280 通过，0 失败，2 跳过**。跳过项为当前环境无法创建符号链接的既有测试，不是
US-006 新增功能通过。

新增覆盖：

- `tests/unit/github-source.test.js`：来源解析、固定 SHA、限制、mode、许可、错误映射和脱敏。
- `tests/unit/source-sync-state.test.js`：状态/报告/退出码/CLI 参数。
- `tests/unit/catalog-contract.test.js`：`source_tracking` 结构化字段边界。
- `tests/integration/source-sync-check.test.js`：检查零写入、noop/candidate、失败隔离。
- `tests/integration/source-sync-apply.test.js`：完整替换、增删附件、单文件/目录互换、幂等。
- `tests/integration/source-sync-conflict.test.js`：许可、本地修改、基线冲突、非法候选、推送拒绝；
  含单文件 `last_synced_license` 建立与后续许可变化阻断。
- `tests/integration/publish/publish-sync-workflow.test.js`：schedule/dispatch/权限/target SHA/无第二条发布链。

## 2. 静态检查与安全

```bash
npm run lint
npm run format:check
npm run security
```

结果：

- lint：退出码 0。
- format:check：所有匹配文件符合 Prettier。
- security:secrets：340 文件，findings 0。
- security:code：56 文件，findings 0。
- security:deps：1 文件，findings 0。

诊断只输出稳定码和位置；未输出 token、上游响应正文或原始异常。

## 3. 未运行

- Node 26.3.0/Linux 本地复验（由 CI 覆盖）。
- 生产构建、生产 Pages 部署、生产 MIME/缓存、environment 审批和真实调度。
- 真实部署失败注入；见 [us6-status.md](us6-status.md)。
