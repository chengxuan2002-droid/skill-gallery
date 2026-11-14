# US-007 残留缺口与未运行项

**日期**: 2026-11-14（Asia/Shanghai）
**范围**: T018；逐项列出未运行/未验证项、影响和补验方式。未运行不计为通过；本文件不改变
`acceptance-matrix.md` 的既有状态。

## 1. 必列缺口

| 缺口 | 当前状态/证据 | 影响 | 补验方式 |
|---|---|---|---|
| T041 macOS（已关闭） | `macos-ci.md`、`specs/001-preserve-skill-content/validation/platform.md`：GitHub-hosted `macos-latest` run `43588719771`，282 项 281 通过/0 失败/1 跳过，安全 0 发现，构建 revision `faa0f345...` | 物理 Mac、所有 macOS 硬件/文件系统变体仍未覆盖 | 如需要物理 Mac，补跑同一测试集；当前不宣称全部 macOS 变体通过 |
| US-005 真实 `gh api` 导入（已关闭） | `specs/005-skill-cli/validation/us5-real-gh.md`：POC-002/POC-003 真实 preview/publish；`us5-real-wait` 提交 `1017dd4...` | `release` 策略仍未单独真实演练；生产来源未配置 | 保留 POC 证据；如需要再补 release/pinned 真实网络演练 |
| US-005 `--wait` 运行发现（已关闭） | 首次发布记录 run 延迟；修复 `waitForPublishedRun`（60s/5s）后 `us5-real-wait` `--wait` 返回 published，run `43612262185` | 发现超时/gh 不可用仍按 submitted/pending 保留；不是无限等待 | 保留真实 run；如调整发现窗口，更新 README/contract 并重测 |
| 生产 environment 审批（已关闭） | `production-environment.md`：run `43587421323` 真实等待 required reviewer，审批后 deploy success；设置已恢复 | 生产部署门禁/审批路径已实测；不覆盖团队审批策略变体 | 保留本次 run 记录；如需团队审批再单独演练 |
| 生产部署失败注入（已关闭） | `production-environment.md`：临时只允许测试分支，run `43588024409` build success/deploy failure，旧站 revision 保持；恢复 main 策略后 run `43588215125` deploy success | 真实部署失败/旧站保留已实测；CDN/缓存清理未覆盖 | 保留 run 记录；后续如改 environment 策略需重新验证 |
| 发布后 MIME/缓存 | `fixed-address.md` 已复核首页/app.js/index/详情/raw/ZIP 的 200、Content-Type 和 `Cache-Control: max-age=600`；`remote-errors.md` 记录 404 | CDN 边缘缓存清除、浏览器强刷后资源一致性和完整直接资源审计未验证 | 发布后在浏览器硬刷新并检查 CDN/缓存头；变更后确认旧缓存不残留 |
| 真实 403/限流 | `remote-errors.md` 记录一次真实 GitHub API 403（公开示例仓库 runners，只读、无副作用）和 core/search 限额；未触发 429 | 真实 source-sync 403/429 映射和退避未端到端验证；主动耗尽配额不安全 | 在获授权来源上制造/等待真实限流或 403，记录稳定错误码；不得伪造远程结果或滥用配额 |
| 真实截断树/子模块/符号链接 | `github-source.test.js` 为注入夹具；Windows 符号链接分支未执行 | 真实远程树边界和链接拒绝未在 GitHub API 上验证 | 用受控源仓库构造截断/子模块/符号链接，执行 `sync-skills --json` 并核对失败关闭 |
| POC 二进制逐字节下载（已关闭） | `us5-real-gh.md`：从 POC 详情下载 `assets/binary.bin`，5 字节、SHA-256 `ff5d8507...` 与来源/详情一致 | 仅 POC 受控站点；生产无二进制附件 | 保留 POC 证据；生产如新增二进制另行核对 |
| Safari/移动实机/读屏器 | `us2-accessibility.md`、`us2-cross-browser.md` 仅 Chrome/Firefox/WebKit（Windows） | 真实 Safari、触摸手势和读屏器语音未验证 | 在 Safari/移动设备运行 360/768/1440、明暗主题、键盘/触摸和减少动效；记录设备 |
| 真实浏览器复制/下载 | `us2-detail.md` 主要为本地夹具；本次未重跑真实剪贴板/下载交互 | 复制失败提示和浏览器下载行为可能受权限/浏览器差异影响 | 在至少一个真实浏览器执行复制成功/失败、raw/ZIP 下载并核对文件 |
| 生产未授权写尝试 | `us3-security.md` 为 POC 匿名 401；生产未重跑 | 生产仓库/fork/受限身份的写拒绝未观察 | 在获授权范围用未认证请求尝试 dispatch/写，核对 401/403 与无副作用；禁止使用凭证 |
| 2026-11-15 03:17 窗口 | 2026-11-14 只有延迟 run `43533439066`；下一窗口未到 | 不能把一次延迟触发写成每日准点 SLA | 2026-11-15 后查看 `maintain.yml` schedule 运行，记录实际触发时间、sync/build/deploy 结果 |
| 生产真实来源自动更新 | 四项 catalog `source_tracking` 均为 `null`；Demo-002 仅 POC-003 | 生产自动检查/替换、单版本和许可基线未实际发生 | 获授权后配置一个真实公开来源，观察 check/apply/同次发布；在此之前只能写“受控通过” |

## 2. 其他限制

- Node 22.21.0/Windows 为本次本机环境；Node 26.3.0/Linux 与 macOS runner 以 CI/runner 为准。
- 生产 environment 审批和部署失败注入已完成受控演练并恢复设置（见 `production-environment.md`）；
  生产真实来源配置仍涉及生产写入，必须单独授权。
- US-005 真实 `gh api`/`--wait` 和 POC 二进制 URL 对比已关闭（见
  `specs/005-skill-cli/validation/us5-real-gh.md`）；`release` 策略真实网络演练仍未运行。
- 未运行项不进入通过计数；最终结论仍是“有条件/未完成”，不是整包通过。
