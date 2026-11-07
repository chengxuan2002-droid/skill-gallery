# US-004 管理入口验收（T011–T013）

**日期**: 2026-11-07（Asia/Shanghai）
**范围**: 页脚低权重“管理”外链、无登录/上传入口的静态契约与隔离构建检查；不推送、不部署。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 入口契约（T011）

```text
node --test tests/unit/site-entry.test.js
```

契约内容：

- 页脚存在指向 `https://github.com/chengxuan2002-droid/skill-gallery` 的链接，文本为“管理”；
- 链接使用 `target="_blank"` 与 `rel="noopener"`；
- 首页无 `<form>`、无 `<input type="file">`、无密码输入、无“上传/Upload”入口。

首次运行结果：1 项失败（缺少管理链接）、1 项通过；实现后 2 项通过、0 失败。

## 2. 页面实现（T012）

- `index.html` 页脚在原有 `Source` 外链后增加分隔符和“管理”外链，指向受信任仓库；
  未新增按钮、登录表单或上传控件。
- `assets/style.css` 未改动：现有 `.app-footer`/`.app-footer a` 已是低权重页脚样式，新增规则会重复；
  管理入口沿用同一视觉权重。
- 链接只做导航，不携带凭证或可写参数；权限仍由 GitHub 仓库控制。

## 3. 隔离构建检查（T013）

复制首页与前端资产到系统临时项目，调用现有构建后检查 `dist/index.html`：

| 检查 | 结果 |
|---|---|
| 构建 | `ok=true` |
| `contentRevision` | `fe77eb2020df965bd5284306c09c86c4085f4c6fe8be8f0fed83840554ce3212` |
| 产物文件数 | 19 |
| 管理链接存在 | 是（文本“管理”） |
| `target="_blank"` / `rel="noopener"` | 是 / 是 |
| 登录表单 / 文件输入 | 无 |

## 4. 未运行与限制

- 未在浏览器中检查页脚视觉效果、键盘焦点或移动端布局；静态断言不替代视觉验收。
- 未在生产站点部署；生产 Pages 仍为 `legacy`，本链路只在隔离构建与后续受控仓库验收。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 复验；本机为 Node 22.21.0/npm 10.9.4。
