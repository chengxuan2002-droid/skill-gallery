# Sepia 生产来源配置与首次基线

**日期**: 2026-11-23（Asia/Shanghai）
**范围**: 为生产 `sepia` 配置 `source_tracking`，验证目录来源的仓库根 LICENSE 回退，并通过手动
`maintain.yml` dispatch 建立首次同步基线。
**结论**: 配置与首次基线均完成。`sepia` 与上游 `Nanako0129/sepia` 的 `skills/sepia` 内容一致，
只读检查为 `unchanged`/`license_status=present`；基线 run `45160746326` 写入 catalog 同步字段。

## 1. 配置

`catalog/sepia.json` 的 `source_tracking`：

```json
{
  "provider": "github",
  "repository": "Nanako0129/sepia",
  "path": "skills/sepia",
  "ref_policy": "branch",
  "ref": "main",
  "enabled": true,
  "last_synced_revision": null,
  "last_synced_digest": null,
  "last_synced_license": null,
  "synced_at": null
}
```

上游仓库公开、默认分支 `main`、MIT；`skills/sepia` 子树没有 LICENSE，但仓库根有 `LICENSE`。
因此同步器增加目录来源的根许可回退：子树许可优先，子树没有时读取仓库根 `LICENSE/NOTICE`。
对应代码为 `scripts/lib/github-source.js`，回归测试见 `tests/unit/github-source.test.js`。

## 2. 只读检查

```bash
node scripts/sync-skills.js --slug sepia --json
```

结果（2026-11-23）：

```json
{"status":"unchanged","slug":"sepia","changed":false,
 "resolved_revision":"0eb11d6c64c962fcc35f596c167c6e38045d6cb8",
 "content_digest":"785e07ec8e706945c6c325c2272846ca6b774fcef61ab7f48cf9687b3e98629e",
 "previous_digest":null,"license_status":"present","error_code":null}
```

没有写入、提交或推送。上游 `skills/sepia` 的 20 个文件 blob SHA 与生产 `skills/sepia` 全部一致。

## 3. 首次基线

```bash
gh workflow run maintain.yml --ref main -f sync=true
```

- run：`45160746326`（workflow_dispatch，2026-11-23 18:57 CST）
- jobs：sync success、build success、deploy success
- 同步提交：`25123a423cb610ed60641ed66308f05d79a7117d`（`sync: update sepia`）
- catalog 写入：revision `0eb11d6...`、digest `785e07...`、
  license `LICENSE`/`7d3d6c...`、`synced_at=2026-11-23T10:57:39.827Z`
- 生产 revision：`ed8abb5...`；首页 200，7 项 Skill
- 内容未变化；只写入来源基线字段

## 4. 后续

- 下一次 `maintain.yml` schedule 会按基线检查上游变化；当时其余 6 个 catalog 仍为
  `source_tracking: null`，不会自动更新。
- 需要继续观察上游真实变更、许可变化、冲突/失败保留和实际替换发布。
