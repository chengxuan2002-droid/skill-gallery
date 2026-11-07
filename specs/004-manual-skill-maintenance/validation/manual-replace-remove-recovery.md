# US-004 替换、下架与恢复验收（T010）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 在系统临时目录复制仓库内容（含 `.gitattributes`、`scripts/`），以真实
`node scripts/build-index.js` 和独立 Git 仓库执行显式替换、下架、撤销下架的恢复提交；
记录命令、产物差异与 `contentRevision`。不写工作区 `dist/`、不推送、不部署。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 方法

1. 复制 `index.html`、`assets/`、`catalog/`、`skills/`、`scripts/`、`.nojekyll`、`package.json`、
   `.gitattributes` 到临时目录，以 junction 复用工作区 `node_modules`。
2. 加入 `manual-single` 与 `manual-pack`（含 `references/note.md`、`references/old.md`），
   初始化 Git 并提交基线；运行 CLI 记录基线产物。
3. **替换**：在 `manual-pack/SKILL.md` 追加内容并删除 `references/old.md`，提交后重新构建。
4. **下架**：删除 `manual-single.md` 与 `catalog/manual-single.json`，提交后重新构建。
5. **恢复**：对下架提交执行 `git revert --no-edit HEAD`，重新构建。
6. 每个阶段读取 `manifest.json`、搜索索引、详情与目录 ZIP；结束后删除临时目录，演练脚本未提交。

`.gitattributes` 中的 `skills/** -text` 是恢复保真的前置条件：首次未复制该文件时，Git 在恢复时按
全局 `core.autocrlf=true` 写入 CRLF，导致恢复后 `contentRevision` 与替换后不一致；复制仓库实际
`.gitattributes` 后字节保持 LF，结果一致。

## 2. 结果

| 阶段 | contentRevision | 关键检查 |
|---|---|---|
| 基线 | `6c10d7bd40d99773c5dab788b7a5246002be73694953ed4eb1c134b2daad3f5a` | 6 个 slug；`manual-pack` 文件含 `SKILL.md`、`references/note.md`、`references/old.md`；ZIP 3 个条目 |
| 替换 | `6024235121ff843b80a9c585f49fab1dcaeac5bc3b978f7e549253377620b800` | `manual-pack` 仅 1 个条目；文件只剩 `SKILL.md`、`references/note.md`；ZIP 无 `old.md` |
| 下架 | `289e462a79a2512f96ef4a9822cc21a0a33fe984dcb790c282ec693658e2100a` | 索引无 `manual-single`；`details/manual-single.json` 不存在；无 `skills/manual-single/` 产物 |
| 恢复 | `6024235121ff843b80a9c585f49fab1dcaeac5bc3b978f7e549253377620b800` | 与替换后一致；`manual-single` 重新出现在索引与详情；slug 集合与基线一致；4 个提交 |

- 替换后单版本：`manual-pack` 在索引中计数为 1，旧附件未残留。
- 下架后索引、详情和产物均移除，其他 5 个 slug 不受影响。
- 恢复使用受控 `git revert` 提交，未 force push、未改写历史；恢复后既有 slug 与旧链接语义不变。
- 替换、下架、恢复三次提交均在同一临时仓库，构建只读取当前提交内容。

## 3. 未运行与限制

- 未在 GitHub 网页后台或 Actions runner 执行替换/下架/恢复；远程行为留给受控仓库 T016。
- 未验证下架后的旧分享链接在浏览器中的实际跳转；只确认索引/详情/产物移除。
- 未切换生产 Pages，未做真实发布。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
