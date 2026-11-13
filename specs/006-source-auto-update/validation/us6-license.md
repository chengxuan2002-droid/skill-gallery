# US-006 许可基线持久化验收

**日期**: 2026-11-13（Asia/Shanghai）
**范围**: T029；`source_tracking.last_synced_license` 的 schema、检查、应用与 POC 验证。

## 1. 实现

- `source_tracking.last_synced_license` 为可选对象：`{ path, sha256 }` 或 `null`。
- schema 校验路径为安全 POSIX 相对路径、摘要为 64 位小写十六进制，拒绝未知键。
- 检查优先比较持久化基线；无基线时目录来源回退当前内容许可，单文件在首次 apply 建立基线。
- apply 仅在成功候选提交时写入；`policy_blocked`/`conflict`/`failed` 不写。
- 旧记录字段缺省为 `null`，不提升 `schemaVersion`。

## 2. 自动测试

```bash
node --test tests/unit/catalog-contract.test.js \
  tests/integration/source-sync-apply.test.js \
  tests/integration/source-sync-conflict.test.js
```

结果：全部通过。覆盖：

- 接受 null 与合法对象；拒绝字符串、越界路径、非法 digest 和未知键。
- 单文件首次 apply 写入 `last_synced_license`；后续许可字节变化 → `policy_blocked` / `E_LICENSE_CHANGED`。
- 目录来源缺少许可 → `E_LICENSE_MISSING`；路径/字节变化 → `E_LICENSE_CHANGED`。
- apply 后远端 catalog 含许可路径与 sha256；冲突路径不写入。

## 3. POC

消费端 POC-002 更新代码提交 `feff1ba5e4f6`；源仓库连续修订：

| 源修订 | 内容 | 消费端 run | 结果 |
|---|---|---|---|
| `592e3634a7e7...` | v3 内容变化，许可仍为 MIT | [43373881404](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43373881404) | apply 提交 `40d8cfc33d69`，写入 `last_synced_license` |
| `f9e30352a82d...` | 许可改为 Apache-2.0 | [43374128999](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43374128999) | sync success、build/deploy skipped、无新提交 |
| `7b02195f4ce6...` | 恢复 MIT | [43374438621](https://github.com/chengxuan2002-droid/skill-gallery-poc-20261107/actions/runs/43374438621) | `unchanged`、build/deploy skipped |

许可变化时本地检查输出：

```json
{"slug":"source-poc","status":"policy_blocked","resolved_revision":"f9e30352...","license_status":"changed","error_code":"E_LICENSE_CHANGED"}
```

远端 catalog 的 `last_synced_license` 为：

```json
{"path":"LICENSE","sha256":"ec43df0d8f2e9fab215c219f27be7498c7cf8d37b34c580fcdd38e124935551d"}
```

恢复 MIT 后检查为 `unchanged`，`previous_digest` 与 `content_digest` 相同，没有新建提交。

## 4. 未运行

- 真实 403、限流等待、真实截断树和真实符号链接/子模块。
- 生产 `main` 调度与发布；POC 结果不作为生产启用。
