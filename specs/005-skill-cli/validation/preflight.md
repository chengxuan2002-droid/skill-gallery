# US-005 基线预检（T001）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 固定 Agent CLI 开始前的分支、工具链、测试基线、生产 Pages 与受控仓库状态；
不读取或打印凭证，不修改远程仓库、页面或 Pages 设置。

## 1. 分支与提交

| 项 | 值 |
|---|---|
| 分支 | `codex/us-005-skill-cli`（从 US-004 分支堆叠） |
| HEAD | `d2ace245f409c1b891a35599af04b580d0a3f219` |
| 已推送 | 否（US-005 分支仅本地） |
| 工作区 | 干净 |

## 2. 工具链与认证

| 项 | 值 |
|---|---|
| Node / npm 实际版本 | `v22.21.0` / `10.9.4` |
| 锁定版本 | Node `26.3.0` / npm `11.16.0`（未在本机复验） |
| Git | `2.45.2.windows.1` |
| gh | `2.88.1`；已登录 `chengxuan2002-droid`（keyring），未读取 token |
| gh scopes | `gist`、`read:org`、`repo`、`workflow`（仅记录名称） |
| `npm test` 基线 | 220 项：218 通过、0 失败、2 跳过 |

## 3. 生产与受控环境

| 项 | 值 |
|---|---|
| 生产 Pages | `build_type=legacy`、`source=main:/`、`status=built`（未切换） |
| 生产 `main` | `365d577e8eb7460d3619d98201425a4b3a93c255` |
| 开放 PR | US-003 PR #1、US-004 PR #2 均 OPEN/MERGEABLE，未合并 |
| POC-002 | `chengxuan2002-droid/skill-gallery-poc-20261107`，公开，Pages `build_type=workflow` |
| POC HEAD | `e05dd3e4a2ad7e7a7a237b9554105f15ae8556e4` |

## 4. 授权与边界

- T001–T004 只做本地预检、测试与命令骨架；不推送、不发布、不切换生产 Pages。
- 默认测试使用临时目录/临时裸仓库与注入边界，不访问网络、不推真实远端。
- POC-002 真实发布/状态查询（后续 T021）需单独确认；生产 Pages 保持 `legacy`。
- 不执行 `skills/` 中的脚本或测试，不安装其依赖；不读取或打印任何凭证。
