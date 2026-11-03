# US1 契约测试（T011～T013）

日期：2026-11-03。记录 US1 先行契约测试及预期红灯；本文件不代表 T014 以后实现、业务验收或发布完成。
环境：Windows 11，Node 22.21.0；测试使用非系统盘临时目录。映射 FR-001、FR-004、FR-011，
NFR-001、NFR-003、NFR-006，DEC-002、DEC-003、DEC-005、DEC-009，AC-001、AC-002、AC-012、AC-014 本地子集。

## T011 CatalogRecord 契约

文件：`tests/unit/catalog-contract.test.js`。覆盖必填与默认数组、可空字段、日期/URL 边界、
`source_tracking` 结构、catalog 优先与显式 null、frontmatter 别名与 `declared_version` 链、
`field_sources`、已知原件类型错误不可覆写、标准 name/description 独立记录、未知顶层字段、
点路径准入不放过凭证路径，以及不编造作者/版本/日期。

命令：`node --test tests/unit/catalog-contract.test.js`

结果：exit 1，10/10 失败；首因 `TypeError: validateCatalogRecord is not a function`。
这是 T014/T015 尚未实现的预期红灯，不代表测试断言本身失败。

预期实现：T014 提供 `validateCatalogRecord`，T015 提供 `resolveCatalogRecord`。

## T012 四项迁移契约

文件：`tests/integration/migration.test.js`。在隔离项目复制四项六原件、标准样例与 office2md 哨兵，
覆盖默认 `--dry-run` 零写入、`--write` 恰好四项、二次一致 noop、差异冲突保护、非法/缺失原件整批失败、
目标被占用时不留下部分新记录、office2md/标准样例不成为正式记录、原件摘要不变，以及
`--dry-run` 与 `--write` 互斥。

命令：`node --test tests/integration/migration.test.js`

结果：exit 1，7/7 失败；首因 `AssertionError: scripts/migrate-catalog.js 尚未实现`。
这是 T016 尚未实现的预期红灯。

预期实现：T016 提供四固定路径迁移入口；T017 才生成正式四份 catalog 记录。

## T013 构建与预览契约

文件：`tests/integration/build-contract.test.js`、`tests/integration/preview.test.js`。
覆盖索引/详情/raw/ZIP/manifest 同一 `contentRevision` 与 digest、输出白名单、旧 dist 完整替换、
缺主文档/重复 slug/缺本地附件整批失败并保留旧输出、首次失败无残缺 dist、第二次 rename 失败回滚，
以及预览仅映射 `/skill-gallery/`、明确 MIME、拒绝目录列表、链接与编码穿越。

命令：`node --test tests/integration/build-contract.test.js tests/integration/preview.test.js`

结果：exit 1，8/8 失败；构建首因 `Cannot find module '../../scripts/lib/build-site'`，
预览首因 `Cannot find module '../../scripts/preview'`。这是 T018～T023 尚未实现的预期红灯。

预期实现：T018～T020 提供 `buildSite` 及事务；T021 接入命令；T022 适配前端；T023 提供预览服务器。

## 全量回归

命令：`npm test`。结果：exit 1，91 项中 63 通过、27 失败、1 跳过。
其中 25 项是 T011～T013 的预期红灯，2 项仍是本机未安装 Gitleaks/Semgrep 的既有环境失败；
既有 63 项通过，未见原有测试回归。Lint 与格式检查通过。红灯不表示实现或验收完成。

## T014 CatalogRecord schema 实现

文件：`scripts/lib/catalog-values.js`、`scripts/lib/catalog-schema.js`，由 `scripts/lib/validate.js` 重新导出。
实现必填/可空/枚举、slug 与 content_path、日期和 URL 边界、source_tracking 结构、
未知顶层字段、allowed_dot_paths 禁止凭证路径；不请求远程。

命令：`node --test tests/unit/catalog-contract.test.js`

结果：5 通过、5 失败；schema、日期/URL、source_tracking 与点路径用例转绿；
5 项合并/field_sources 用例仍因 `resolveCatalogRecord is not a function` 失败，留给 T015。

## T015 记录合并与 field_sources 实现

文件：`scripts/lib/catalog-merge.js`，由 `scripts/lib/validate.js` 重新导出。实现 catalog 优先与显式 null、
frontmatter 同名/别名回退、`declared_version` 的 catalog → version → metadata.version → null 链、
`skill_name`、`field_sources`、URL/日期/已知字段类型校验，且不修改输入对象。

命令：`node --test tests/unit/catalog-contract.test.js`

结果：exit 0，10/10 通过；T011 契约全部转绿。

## T016 四固定路径迁移实现

文件：`scripts/migrate-catalog.js`。仅处理四个固定 slug，默认 `--dry-run`，`--write` 与 dry-run 互斥；
先验证原件与候选记录，再用 `validateCatalogRecord`/`resolveCatalogRecord` 派生记录；
目标缺失才写、相等为 noop、差异或非普通文件为冲突；写入失败只回收本次新文件，退出码 0/1。

命令：`node --test tests/integration/migration.test.js`

结果：exit 0，7/7 通过。另在非仓库临时项目执行 `--write`，生成四份记录且原件未变；
正式 `catalog/` 仍由 T017 生成，本轮未写仓库数据。

## T017 四份正式 catalog 记录

执行：`node scripts/migrate-catalog.js --write`，再执行一次得到 `noop`。
生成 `catalog/{superpower-systematic-debugging,code-review-assistant,refactoring-workflow,handoff-codex}.json`；
四份记录均通过 `validateCatalogRecord`，`source_tracking` 全为 null，`license` 未伪造；
slug/content_path 保持原值。与旧索引的显示名、简介、标签、平台、来源、链接、作者、版本、日期和用法逐项一致；
六项原件 SHA-256 与 `migration-baseline.json` 一致。`office2md` 与标准样例未生成记录。

## T018 C-03 投影、渲染与打包

文件：`scripts/lib/build-render.js`、`build-archive.js`、`build-outputs.js`、`build-inputs.js`、`build-site.js`。
实现 frontmatter 正文渲染、活动内容清理、标题顺序 ID 与别名、Markdown 本地引用校验、
原字节 `.bin`、栅格媒体签名副本、目录根 ZIP、PublicFile 与站点相对 URL；缺失本地附件整批失败。

命令：`node --test tests/unit/build-render.test.js` 与 `node --test tests/integration/build-contract.test.js`

结果：build-render 5/5、build-contract 5/5 通过。另用临时目录型 Skill 验证图片写入 `media/<slug>/<sha>.png`，
详情 `media_url` 与文件存在；单文件样例不拥有邻接附件，符合 C-01。

## T019 索引、详情与 manifest

由 `build-outputs.js` 生成 `assets/search-index.json`、`details/<slug>.json` 与 `manifest.json`；
三者共享 `contentRevision`，索引/详情/manifest 的 digest 一致，manifest 覆盖除自身外的全部产物。
`build-inputs.js` 的 `contentRevision` 使用记录、快照 digest、网页资产、依赖锁、策略与运行时标识，
不含私有绝对路径或日期。验证：`build-contract.test.js` 第 1、2 项通过。

## T020 构建事务与回滚

由 `build-transaction.js` 实现 `.dist.lock/owner.json`、`.dist.transaction.json`、按 run_id 派生的
stage/backup、prepared/promoting/promoted 记录，以及旧输出→backup、stage→dist 的切换；
第二次 rename 失败时恢复 backup，首次失败不留 dist，清理成功报告 `cleanup_status=complete`。
验证：`build-contract.test.js` 第 3～5 项通过。

## T021 构建入口与固定前端依赖

`scripts/build-index.js` 改为完整构建入口，`package.json` 接入 `npm run build`；不接受参数，
公开产物只写 `dist`，不写根 `assets/search-index.json`。旧构建脚本保留为
`tests/fixtures/legacy/build-index.js`，旧导出回归仍可在隔离副本复现。
`build-outputs.js` 同步复制固定 MiniSearch 6.3.0 UMD 与许可到 `assets/vendor/`。

命令：在仓库外临时四项项目运行 `node scripts/build-index.js` 两次。

结果：两次均 exit 0、`status=built`、`cleanup_status=complete`，`content_revision` 相同，
无 `.dist.*` 遗留；根旧索引未被改写。`export-regression.test.js` 1 通过、1 跳过，
T011～T020 相关测试 28 通过、1 跳过。

## T023 只读 dist 预览

文件：`scripts/preview.js`、`package.json`。导出 `createPreviewServer({root, basePath})`，CLI 监听
`127.0.0.1:8000`，只映射 `/skill-gallery/`；拒绝非 GET/HEAD、前缀外路径、目录列表、链接组件和编码穿越；
`.bin` 固定 `application/octet-stream`，不按 HTML 嗅探。

命令：`node --test tests/integration/preview.test.js`

结果：exit 0，3/3 通过。CLI 的 `npm run preview` 需先有本地 `dist`，端到端预览留给 T024 构建后执行；
本轮未启动 8000 端口服务，未发布。
