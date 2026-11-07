# US3 凭证、权限与内容不执行验收（T019–T021）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 执行 T019/T020 安全契约测试与 `npm run security`（secrets/code/deps）；只做本地/隔离验证，
不执行收录 Skill 的脚本、不使用真实凭证、不访问生产 Pages、不写入远程仓库。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线仍为 Node 26.3.0/npm 11.16.0，未在本机复验）；
Gitleaks 8.30.1、Semgrep 1.183.0（版本以 `config/security-tools.json` 为准）；依赖审计固定查询
`https://registry.npmjs.org/`。

## 1. 安全契约测试

```text
node --test tests/integration/publish-security.test.js tests/integration/publish-security-workflow.test.js
```

结果：退出码 `0`；9 项通过、0 失败、0 跳过。

| 文件 | 项数 | 覆盖 |
|---|---|---|
| `tests/integration/publish-security.test.js` | 5 | 凭证文件名、token 前缀、私钥块、越界/绝对/重复路径、内容不执行 |
| `tests/integration/publish-security-workflow.test.js` | 4 | 最小权限、checkout 凭证、无 secret/PAT/fork 触发、摘要字段白名单 |

### 1.1 产物凭证与路径边界（T019）

| 场景 | 期望与结果 |
|---|---|
| `.env`、`assets/tls.pem`、`assets/tls.key`、`assets/id_rsa`、`.git-credentials` | 全部 `E_ARTIFACT_CREDENTIAL_PATH`，诊断只含 `code`/`path`/固定 `message` |
| 运行时拼接的 `ghp_` token 前缀写入 `assets/leak.txt` | `E_SECRET`；库函数与 CLI（退出码 `6`）的 stdout/stderr 均不回显 token |
| 运行时拼接私钥块写入 `assets/key-material.txt` | `E_SECRET`，私钥正文不回显 |
| manifest 注入 `../outside.txt`、`/etc/passwd`、`C:/Windows/win.ini`、反斜杠、控制字符、`.` 段 | 全部 `E_ARTIFACT_PATH` |
| manifest 重复路径 | `E_ARTIFACT_DUPLICATE` |
| 夹具 Skill 内的哨兵脚本 | 构建后作为 `skills/<slug>/<sha256>.bin` 普通文件存在；`verifyArtifact` 与 CLI 均未触发哨兵写入 |

token 前缀与私钥块均由测试运行时拼接；源码中不含完整 token 或私钥块，也没有使用真实凭证。

### 1.2 工作流权限（T020）

- 工作流级权限精确为 `contents: read`；`build` 未授予写权限（无 job 级 permissions，继承只读）。
- `deploy.permissions` 精确为 `contents: read`、`pages: write`、`id-token: write`；
  其他 job 不含 `pages`/`id-token`，也不含任何 `write`。
- 两个 checkout 均为 `persist-credentials: false`；无 `secrets.*`、`github.token`、PAT 字样。
- 无 `pull_request`、`pull_request_target`、`workflow_run`、`issue_comment`、`repository_dispatch` 触发。
- Step Summary 步骤的 env 键均匹配 `^PUBLISH_[A-Z0-9_]+$`，值不引用 secrets/token/password/cookie/
  authorization/credential；工作流与 job 无额外 `env`。

## 2. `npm run security`

| 命令 | 扫描文件数 | 发现数 | 退出码 |
|---|---|---|---|
| `npm run security:secrets` | 244 | 0 | 0 |
| `npm run security:code` | 37 | 0 | 0 |
| `npm run security:deps` | 1 | 0 | 0 |

`security:secrets` 覆盖新测试文件与本记录（含运行时拼接的 token/私钥构造），结果 0 个发现；输出只有检查名、
状态、文件数与空的 findings 数组，未打印命中值、文件内容或环境变量。依赖审计通过（0 个漏洞）。

## 3. 验收映射

| 上游验收 | 本轮证据 | 覆盖程度 |
|---|---|---|
| AC-008 | 凭证文件名/内容、诊断脱敏、最小权限、无 secret/PAT/fork 触发、摘要字段白名单 | 发布与部署路径的本地静态/隔离覆盖；未授权远程尝试见 T022（未运行） |
| AC-012 | 哨兵脚本未被触发；越界/绝对/反斜杠/控制字符路径被拒绝 | 构建与产物路径；上传/同步路径留 US-004/US-006 |
| US-003.C 场景 4、5 | T019 凭证与内容不执行用例 | 本地通过；不含真实凭证或收录脚本执行 |
| US-003.C 场景 2、3 | T020 权限静态断言 | 仅静态；受控环境未授权尝试未运行 |

## 4. 未运行与限制

- T022 的无权限身份/不受信来源触发构建与部署未运行：需要受控仓库与单独授权，本轮未执行。
- 未在 GitHub Actions runner 实际运行；权限与触发只有静态断言，未观察远程行为。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
- 未修改生产 Pages 源、environment、分支保护；未推送、未部署，本记录不是生产安全验收。

## 5. 结论

T019–T021 的本地契约与扫描全部通过：凭证/路径/内容执行边界可被测试识别，工作流权限保持最小化，
诊断不回显值。该结果只证明本地与静态契约，不代表受控仓库或线上部署已通过。
