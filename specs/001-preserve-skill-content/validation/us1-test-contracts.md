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
