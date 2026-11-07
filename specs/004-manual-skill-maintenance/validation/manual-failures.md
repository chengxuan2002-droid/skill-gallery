# US-004 失败批次与旧站保留验收（T007）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 在系统临时目录复制仓库内容与 `scripts/`，通过真实 `node scripts/build-index.js` 运行合法
构建后注入缺字段、缺附件、越界路径和凭证内容，记录退出码、诊断码与旧 `dist/` 是否保持；
不写工作区 `dist/`、不推送、不部署。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 方法

1. 复制 `index.html`、`assets/`、`catalog/`、`skills/`、`scripts/`、`.nojekyll`、`package.json` 到
   临时目录，并以 junction 复用工作区 `node_modules`（不复制依赖、不访问网络）。
2. 加入 `manual-single` 与 `manual-pack` 手动样例，运行 `node scripts/build-index.js` 确认合法构建
   退出码 `0`、`status=built`，记录 `dist/` 文件摘要快照。
3. 依次注入失败条件后重新运行同一 CLI；记录退出码、诊断码与失败前后 `dist/` 摘要。
4. 每个用例使用独立临时目录，结束后删除；演练脚本未提交。

## 2. 结果

合法构建基线：退出码 `0`、`status=built`、`contentRevision` 均为
`fc98d709f96dc2e88a5289d4202d897bee32260423186a575a8d1f096bdf22fa`。

| 用例 | 失败退出码 | 状态 | 诊断码 | 旧 `dist/` 不变 | 凭证回显 |
|---|---|---|---|---|---|
| 缺必填字段（删除 `display_name`） | 1 | failed | `E_SCHEMA` | 是 | 否 |
| 缺附件（删除被引用的 `references/note.md`） | 1 | failed | `E_REFERENCE_MISSING` | 是 | 否 |
| 越界路径（`content_path=skills/../index.html`） | 1 | failed | `E_PATH` | 是 | 否 |
| 凭证内容（运行时拼接的 token 写入附件） | 1 | failed | `E_SECRET`（token 与赋值规则各一次） | 是 | 否 |

失败输出只有 `status=failed`、诊断码/路径/固定消息；token 值未出现在 JSON 输出中。失败构建未上传
产物、未触发部署，符合“整批阻止、旧站保留”的发布链语义。

## 3. 未运行与限制

- 未在 GitHub 网页后台或 Actions runner 执行失败批次；远程行为留给受控仓库 T016。
- 未验证失败后的浏览器访问或缓存行为；旧站保留只以旧 `dist/` 摘要和 US-003 发布链证据为准。
- 未使用真实凭证；token 为运行时拼接的测试值，未写入仓库。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
