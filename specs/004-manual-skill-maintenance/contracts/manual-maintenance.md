# Contract: 管理员手动维护（M-05 子集）

**Feature**: US-004 | **Date**: 2026-11-07 | **Spec**: [../spec.md](../spec.md)

本契约定义 GitHub 手动维护的输入、页面入口和不变量。手动维护不新增 CLI；执行基础仍是现有
`maintain.yml`、构建/校验模块和 US-003 发布链。Agent 命令由 US-005 按 C-05 实现。

## 1. 管理入口（页面）

```html
<a href="https://github.com/chengxuan2002-droid/skill-gallery" target="_blank" rel="noopener">管理</a>
```

- 位置：页脚低权重外链；不是主操作，不遮挡搜索/详情。
- MUST 指向受信任 GitHub 仓库；MUST NOT 包含凭证、token 或可写参数。
- MUST NOT 出现站内登录表单、`<input type="file">`、上传按钮或“本站后台”文案。
- 入口存在不代表访客获得写权限；权限完全由 GitHub 控制。

## 2. 手动维护输入

| 操作 | 输入 | 规则 |
|---|---|---|
| 新增（`add`） | `skills/<slug>.md` 或 `skills/<slug>/SKILL.md` + `catalog/<slug>.json` | slug 不得与现有条目重复；记录必填字段完整 |
| 修改信息（`update_metadata`） | 仅编辑 `catalog/<slug>.json` | 不改写原件字节；必填字段保持完整 |
| 显式替换（`replace`） | 用完整新内容替换同 slug 原件，并按需更新记录 | 保持同一 slug；旧附件按新清单清理；不累积版本 |
| 下架（`remove`） | 删除原件与记录 | 索引/详情/下载不再包含该条目；不处理未纳管文件 |

必填记录字段与类型见 [data-model.md](../data-model.md) 第 2 节。目录型 Skill MUST 使用
`content_path=skills/<slug>/SKILL.md`；单文件 MUST 使用 `skills/<slug>.md`。

## 3. 执行与结果

1. 管理员通过 GitHub 后台提交到默认分支；提交即“内容提交”动作。
2. `maintain.yml` 执行 `npm run check`、`npm run security`、`npm run build`、产物校验，再上传/部署。
3. 任一校验或构建失败：整批阻止，不上传 artifact、不部署；平台保留上次正常站点。
4. 运行记录与 Step Summary 分开显示提交、构建和部署状态，提供稳定错误码与运行标识。
5. 部署成功只表示本次发布完成；提交成功或本地构建成功不得报告为已发布。

错误码沿用现有诊断，不新增自由文本：

| 场景 | 稳定错误码 |
|---|---|
| 缺字段/未知字段/字段类型错误 | `E_SCHEMA` |
| 路径越界、非法 content_path | `E_PATH` |
| 主文档缺失 | `E_MAIN_MISSING` |
| 疑似凭证 | `E_SECRET` |
| 构建失败/产物校验失败 | `E_BUILD`/`E_ARTIFACT_*` |
| 部署失败或过期 | `E_DEPLOY_FAILED`/`E_SUPERSEDED` |

## 4. 不变量

- 访客只读；无站内写入入口；未授权尝试不产生仓库、产物或线上副作用。
- 不执行 `skills/` 中的脚本/测试，不安装其依赖；第三方内容只作为数据处理。
- 凭证 MUST NOT 进入页面、产物、日志、README 示例或运行摘要；示例使用 `YOUR_*_HERE`。
- 替换保持单一当前版本；下架移除当前索引/详情/下载；恢复通过受控历史提交重建。
- 失败批次 MUST NOT 删除、覆盖或修改当前有效内容与线上站点。
- 手动维护与其他入口共用同一校验和发布规则；不得因入口不同绕过检查。

## 5. 与发布契约的关系

- 产物校验、目标 SHA 判定、状态与摘要沿用
  [US-003 publish 契约](../../003-validate-build-publish/contracts/publish.md) 与
  [workflow 契约](../../003-validate-build-publish/contracts/workflow.md)。
- 本契约只新增手动输入约束和页面入口；不改变部署权限、触发范围、并发或 Pages 设置。

## 6. 不在本轮

- Agent CLI（US-005）、来源自动检查/调度（US-006）、ZIP 解压、站内后台、生产 Pages 切换。
- 未实现的命令或能力 MUST 在 README 标记“规划”，不得作为当前可执行步骤。
