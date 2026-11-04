# 依赖审计不可用问题处理

日期：2026-11-04。范围：`npm run security:deps` 的 `AUDIT_UNAVAILABLE`。
映射 NFR-003、NFR-006，DEC-005、DEC-009，AC-012、AC-014 的工程支撑子集。
本记录不改变高/严重级别阻断规则，也不把 6 个 moderate 报告成零漏洞。

## 原因

本机 `npm config get registry` 为 `https://registry.npmmirror.com/`。该镜像对
`POST /-/npm/v1/security/audits/quick` 返回 `404 NOT_IMPLEMENTED`，npm 因而输出错误对象，
`scripts/check-project.js` 按设计将其归类为 `AUDIT_UNAVAILABLE`。这不是依赖树损坏，
也不是审计规则失败；直接使用官方 registry 可以正常取得审计报告。

## 修正

- `scripts/check-project.js` 的依赖审计固定使用 `https://registry.npmjs.org/`，
  通过 `npm audit --registry ... --json --audit-level=high` 查询；
  网络、端点或报告异常仍返回非零并保留 `AUDIT_UNAVAILABLE`，失败不伪装为通过。
- `tests/integration/bootstrap.test.js` 的审计拒绝样例记录子进程参数，断言官方 registry 参数存在；
  同时继续验证子进程原始诊断和假凭证不回显。

## 实际结果

环境：Windows 11、Node 22.21.0、npm 10.9.4；声明的 Node 26.3.0/Linux 由推送后的 CI 复验。

| 检查 | 结果 |
|---|---|
| `npm audit --registry=https://registry.npmjs.org/ --json --audit-level=high` | exit 0；6 个 moderate，无 high/critical |
| `npm run security:deps` | exit 0；`status=passed`；列出 6 个 moderate 受影响依赖 |
| `node --test tests/integration/bootstrap.test.js` | 5/5 通过；含审计 registry 参数与脱敏拒绝样例 |

6 个 moderate：@eslint-community/eslint-utils、@eslint/config-array、@eslint/js、eslint、
eslint-config-prettier、minimatch。均为开发/检查工具链，不是站点运行依赖；本次不执行
`npm audit fix`，也不把阈值从 high 降低。后续升级依赖需单独评估兼容性。

## 远程复验

2026-11-04 推送 `84e6c27..36049b1` 后，[Quality checks #41816996159](https://github.com/chengxuan2002-droid/skill-gallery/actions/runs/41816996159)
在 Node 26.3.0/Linux 通过；依赖审计步骤返回 `status=passed`，报告 6 个 moderate、无 high/critical。
同一运行完成 138 项测试（137 通过、0 失败、1 跳过），Gitleaks 181 个文件与 Semgrep 30 个文件均无发现。

## 边界

- 本记录证明本机与官方 registry 的审计路径，并有远程 CI 复验；不覆盖其他镜像或代理环境。
- 审计报告只保留包名与级别，不输出 registry 原始错误、凭证或源码片段。
- 高/严重级别仍阻断；moderate 仍报告，不能称为零漏洞或全部安全门禁通过。
