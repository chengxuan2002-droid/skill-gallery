# Implementation Plan: US-002 检索、详情、分享与视觉改版

**Branch**: 功能标识 002-search-detail-share-redesign；实际 Git 分支 `codex/us-002-search-detail-share`，基于 `codex/development-baseline-20261102`。

**Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: `specs/002-search-detail-share-redesign/spec.md`，含 2026-11-05 复核后记录的分享地址、精准多词、排序保持、筛选值及更新时间默认规则。

**Implementation Status**: 2026-11-05 T001–T026 已完成本地实现、验收和文档收口；证据入口为
[validation/](validation/)。分支 `codex/us-002-search-detail-share` 已推送到 origin 同名功能分支，
尚未合并 main 或发布；T041 macOS、生产 Pages 新产物 MIME/缓存/回滚和 US-003～US-007 仍未完成。

## Summary

在保留 US-001 已验收的原件、catalog、详情、复制、下载和旧链接契约的前提下，把现有最小列表/详情升级为
可分享的多维检索、完整详情和响应式可访问界面。新增一个不依赖 DOM 的浏览器搜索/URL 状态模块，复用已锁定的
MiniSearch 6.3.0 处理英文模糊检索，中文以连续子串兜底；索引与详情仍使用既有 `schemaVersion=1` 契约，
只把新前端资产纳入构建复制和 `contentRevision`。用 1,000 项/总正文 10 MiB 夹具和真实浏览器证据验证
AC-015，不把四项数据或 Node 微基准冒充浏览器 p95。

## Technical Context

**Language/Version**: 浏览器原生 JavaScript（ES2022 语法，现有 script 加载方式）；构建脚本 CommonJS；
本地基线 Node 26.3.0、npm 11.16.0（`package.json` engines 已锁定 `>=26.3.0 <27`）。

**Primary Dependencies**: 仅复用现有产品依赖 MiniSearch 6.3.0（本地静态分发）；不新增框架、搜索服务、
UI 组件库或 E2E 框架。marked/sanitize-html/yaml/yazl 继续用于既有构建链路，本故事不改变其用法。

**Storage**: 无新增持久存储。检索与详情读取现有 `dist/assets/search-index.json`、`dist/details/<slug>.json`、
`dist/skills/**`；搜索状态保存在可分享 Hash 地址，主题偏好沿用现有 `localStorage` 键；无数据库、后端、
浏览器写入凭证或公开版本选择。

**Testing**: `node:test` 显式运行 `tests/unit/*.test.js`、`tests/integration/*.test.js`；新搜索核心用
`node:vm` 加载纯浏览器模块做单元测试；构建测试验证新资产被复制且进入 `contentRevision`；
浏览器、详情、性能和可访问证据使用隔离临时项目/dist 与现有 Edge/Chromium CDP 或人工浏览器流程，
不新增 E2E 框架；Polish 显式运行 `npm run security`（secrets/code/deps），工具缺失不算通过。

**Target Platform**: GitHub Pages 静态站，地址保持 `https://chengxuan2002-droid.github.io/skill-gallery/`，
资源兼容 `/skill-gallery/`；当前稳定 Chromium、Firefox、WebKit，360/768/1440px、明暗主题和键盘操作。

**Project Type**: 现有单一原生静态站点及本地构建脚本，只改造 M-04 前端；M-03 仅增加前端资产复制与
`contentRevision` 输入。

**Performance Goals**: 1,000 项、总正文 10 MiB 的可复现夹具；数据加载后 50 次固定中英查询，
查询到结果可见 p95 ≤ 200ms，排除网络；记录设备、浏览器和查询集。搜索核心每个输入最多执行一次
MiniSearch 查询和一次筛选/排序，不对每张卡片重复全库搜索。

**Constraints**: 不改变 US-001 的原件保真、复制、原件/ZIP 下载、旧 `#/skill/<slug>` 链接和当前单版本；
不新增 catalog/索引/详情字段或迁移；详情版本缺失时使用现有 `digest` 的短内容标识，不编造版本；
分享地址不含凭证、管理信息或内部路径；不实现上传、后台、自动更新、生产发布或 Q-004 调度；
Q-004 决策已确认为每日 03:17 Asia/Shanghai，T041 macOS 未验证缺口继续保持，不在本故事关闭。

**Scale/Scope**: 正式内容仍为四项；测试使用隔离的检索夹具和 1,000 项/10 MiB 合成负载。
只实现 M-04、C-04；M-05～M-07、C-05～C-07 不在本轮。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 宪章原则 | 计划边界 | 设计与证据入口 |
|---|---|---|
| I 地址与稳定身份 | 保留 `#/skill/<slug>`、`/skill-gallery/` 和 slug；查询状态只用 Hash 参数 | 路由契约、四旧链接回归、子路径预览 |
| II GitHub 后台与写入权限 | 不新增管理入口；若保留现有外链则保持低权重；无登录或站内写入 | 前端无写 API/token；T026 验证边界；AC-008 不在本轮但边界保持 |
| III 原件保真与元数据分离 | 检索/详情只读派生数据；不修改原件或从检索文本重建正文 | data-model、detail contract、US-001 回归 |
| IV 可验证来源更新 | 本故事不实现来源检查或自动替换 | 路由/详情不增加来源写入；留 US-006 |
| V 单一当前版本 | 不提供旧版选择；只显示当前内容身份 | detail contract、同 slug 旧链接场景 |
| VI 失败保留与真实状态 | 搜索/详情失败有可区分状态；本地成功不报告为已发布 | UI 状态表、quickstart、browser 证据 |
| VII 凭证与不可信内容 | 分享参数不含凭证；正文继续使用已清理 HTML；外链只允许安全协议 | URL 白名单、detail contract、XSS 回归 |
| VIII 简洁精准 | 复用原生前端和 MiniSearch；不新增产品依赖或框架 | 仅 M-04 改造，新增一个纯模块 |
| IX 规格追溯与证据 | 保留 FR/NFR/AC 编号；规格、契约、测试和验收证据同源 | 下方映射、research、contracts、quickstart |

Phase 1 后复核：新增的纯搜索模块不改变 M-01/M-02/M-03 的数据契约；列表/详情地址不含凭证；
US-001 的复制、下载、旧链接和当前单版本作为回归门禁；未发现新的宪章违反项。
结论：无宪章冲突，无需豁免。GATE 通过的是设计合规性，不是业务验收。

## Project Structure

### Documentation (this feature)

```text
specs/002-search-detail-share-redesign/
├── spec.md                         # 已有，clarification 后
├── checklists/requirements.md       # 已有，规格质量检查
├── plan.md                         # 本文件
├── research.md                     # Phase 0
├── data-model.md                   # Phase 1
├── contracts/
│   ├── search-ui.md                # 检索、过滤、排序、URL 与状态
│   └── detail-share.md             # 详情、内容标识、分享与安全
├── quickstart.md                   # 实施后验证指南
└── tasks.md                        # 已创建，T001–T026
```

### Source Code (repository root)

```text
index.html                          # 新增搜索/筛选/详情结构所需容器与脚本顺序
assets/app-dom.js                   # 2026-11-07 拆分：共享 DOM 与安全文本/链接辅助
assets/app-search.js                # 新增：纯搜索、过滤、排序、URL 状态模块
assets/app.js                       # 路由、加载、状态编排、主题
assets/app-filters.js               # 2026-11-07 拆分：搜索框、模式、筛选与排序控件
assets/app-views.js                 # 列表、结果状态、复制反馈与可访问 DOM
assets/app-detail.js                # 详情分区、内容标识、复制/下载/分享操作
assets/app-actions.js               # 分享地址、复制、下载等浏览器动作
assets/style.css                    # 响应式、明暗主题、焦点、状态样式
scripts/lib/build-outputs.js        # 复制新增前端资产
scripts/lib/build-inputs.js         # contentRevision 纳入新增前端资产
tests/unit/search-core.test.js      # 新增：纯搜索/URL 模块单元测试
tests/integration/search-assets.test.js # 新增：构建复制与 contentRevision 契约
tests/support/search-fixture.js     # 新增：隔离检索/详情项目、1,000 项负载与预览构建辅助
tests/fixtures/search/              # 新增：固定检索样例
dist/                               # 唯一生成目录，不手改
```

**Structure Decision**: 沿用 US-001 的 M-04 文件拆分，只新增 `assets/app-search.js` 承担无 DOM 的纯逻辑；
不新增包、服务层、状态库或 E2E 框架。`scripts/lib/build-outputs.js` 和 `build-inputs.js` 的资产清单必须
同步增加 `assets/app-search.js`，否则构建产物缺少模块或 `contentRevision` 漏算前端变化。

## Complexity Tracking

无宪章违反项，无额外架构豁免。MiniSearch 已在 US-001 锁定并本地分发，本故事不新增依赖；
用纯函数模块替代在 DOM 渲染中散落搜索逻辑；拒绝后端搜索、语义检索、前端框架和专用 E2E 框架。

## Design Flow and Boundaries

1. 加载现有索引后只构建一次搜索文档和 MiniSearch 实例；读取 Hash 得到初始 `SearchState`。
2. 搜索核心先规范化查询与字段；精准模式做完整连续片段匹配，模糊模式用 MiniSearch 词项/前缀/拼写容错，
   中文以连续子串合并兜底；合并结果按字段权重与 slug 稳定排序。
3. 筛选在结果集上执行：标签、平台、来源、作者同维 OR、跨维 AND；筛选选项来自当前索引实际值，
   缺失值不提供空选项；每个输入只执行一次搜索和一次筛选/排序。
4. 列表视图保持静态外壳，只更新结果、计数、当前条件和清除入口；输入/筛选变化使用
   `history.replaceState` 更新 Hash，不触发 `hashchange` 重渲染，保持焦点。
5. 详情从现有 `details/<slug>.json` 读取；站点说明（简介、适用场景与用法、备注）与上游原文分区；
   声明版本缺失时显示 `digest` 的短内容标识；复制、下载、分享复用 US-001 的校验与失败反馈。
6. 点击卡片前把当前列表 Hash 记入 `sessionStorage`；详情页返回按钮优先回到该状态，直接打开旧链接时
   回到列表根；详情地址始终保持 `#/skill/<slug>`，不把查询参数写入公开分享身份。
7. 列表分享复制当前列表地址；详情分享复制规范详情地址；成功后提示，剪贴板拒绝时显示可手动复制的值。
8. 视觉改造只改 `index.html`、`assets/*` 与 `style.css`；不改变 catalog、构建内容格式、下载包或原始文件。

详细字段、路由参数和错误状态以 [data-model.md](data-model.md)、
[search-ui 契约](contracts/search-ui.md)、[detail-share 契约](contracts/detail-share.md) 为准；
quickstart 只负责可执行验证步骤，不复制 schema。

## Implementation Sequence and Traceability

| 顺序 | 范围与依赖 | 必须获得的证据 | 上游映射 |
|---|---|---|---|
| 1 | 先写搜索核心/URL 单元测试，再实现 `assets/app-search.js` | 精准/模糊/短语/中文子串、同维 OR/跨维 AND、排序、URL 解析/构建、非法参数 | FR-002、NFR-002；AC-003、AC-015 |
| 2 | 把新资产纳入构建复制和 `contentRevision`，补构建契约 | `dist/assets/app-search.js` 存在；改动该文件会改变 `contentRevision`；旧索引/详情 schema 不变 | FR-004、FR-011；AC-014 本地部分 |
| 3 | 改造列表视图与路由状态，接通模式、筛选、排序、分享地址 | 固定查询集、结果条件、URL 恢复、空/加载/错误状态、旧链接不回归 | FR-002、FR-004；AC-003、AC-005 |
| 4 | 改造详情视图，接入内容标识和分享/复制/下载动作 | 完整/缺失字段、站点说明与原文分区、代码表格附件、剪贴板拒绝、未知 slug | FR-003、FR-004；AC-004、AC-005、AC-012 |
| 5 | 视觉、响应式、主题、键盘与焦点改造 | 360/768/1440、明暗主题、键盘截图、对比度、减少动效、无正文外溢出 | FR-010、NFR-005；AC-013 |
| 6 | 浏览器与性能复验、安全门禁、US-001 回归收口 | 1,000 项/10 MiB、50 次查询 p95、Chromium/Firefox/WebKit 记录、`npm run security` 结果、复制/下载/旧链接回归 | FR-004、NFR-002/003；AC-015、AC-002/014 回归 |

## Planning Verification

本次只读取规格、上游文档、现有前端/构建代码并查证 MiniSearch 6.3.0 的 `boost`、`prefix`、`fuzzy`
搜索选项；未运行新业务实现、未构建、未打开浏览器、未修改站点内容、未发布。
搜索/详情 schema 若不出现新字段，实施时不得为了“顺手”改 schemaVersion 或重建 catalog；
若测试证明必须新增字段，先按宪章 IX 更新规格与契约，再另行实施迁移。

2026-11-05 复核：上述“只读取”描述是规划阶段记录；T001–T026 已完成本地实现、验收和文档收口，
实际命令、测试计数、浏览器/性能证据及未运行项见 [validation/](validation/) 与 [tasks.md](tasks.md)。
