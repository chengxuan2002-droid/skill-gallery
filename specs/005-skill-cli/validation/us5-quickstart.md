# US-005 Quickstart 复核（T023）

**日期**: 2026-11-08（Asia/Shanghai）
**范围**: 对照 `quickstart.md` 复核命令、退出码与 README/契约一致性；使用现有隔离夹具与
T018/T021 的运行结果，不新增代码、不访问生产 Pages。
**环境**: Windows 11；Node `v22.21.0`、npm `10.9.4`（锁定基线 Node 26.3.0/npm 11.16.0，未在本机复验）。

## 1. 复核命令

```text
node --test tests/unit/skill-cli-args.test.js tests/unit/skill-cli-status.test.js tests/integration/skill-cli-add.test.js tests/integration/skill-cli-replace.test.js tests/integration/skill-cli-import.test.js
```

结果：退出码 `0`；21 项通过、0 失败。

## 2. Quickstart 步骤对照

| Quickstart 步骤 | 实际验证 | 结果 |
|---|---|---|
| 前置：Node/Git/gh、`npm ci`、`setup:security` | 预检已记录工具链与扫描器；本机已安装依赖，未重复执行安装 | 可用；安装步骤未在干净机器重跑 |
| 只读预览 | T018 临时项目 + 单测 | 退出码 0、`previewed`，不写工作区 |
| 发布（隔离远端） | T018 临时裸远端；T021 POC-002 | `submitted`；POC 运行成功且 `status=published` |
| `status --run` | T021 POC 运行 42395342747 / 42395444891 | 退出码 0、`published`；不存在运行返回 5/E_SOURCE |
| 替换/冲突 | T018/T021 | 正确基线提交成功；过期基线退出码 4/E_CONFLICT |
| 来源导入 | T013 注入来源；T021 未执行真实来源 | 结构与错误映射通过；默认 `gh api` 读取未远程验证 |
| `--wait` | T021 替换时立即查询未发现运行，返回 submitted；随后 status 为 published | 文档语义一致；不是“等待必达发布” |
| 全量检查 | T019 | 241 项测试、lint/format/security 均通过（2026-11-12 复核为 242 项：240 通过、0 失败、2 跳过） |

## 3. 偏差与限制

- `npm ci` 与 `setup:security` 未在本次重新安装；本机依赖与固定扫描器已就绪，安装网络步骤未验证。
- `import` 的真实 GitHub 读取、Release/pinned 解析和 `--wait` 运行发现仍未在受控来源完整验证。
- `--wait` 可能因 push 后运行尚未出现而返回 `submitted/pending`；README 已说明“只有找到运行才轮询”。
- 生产 Pages 执行时未切换；后续已切换为 GitHub Actions 并成功发布，见
  [production-pages.md](../../003-validate-build-publish/validation/production-pages.md)；本记录仍不构成
  生产发布验收。
- 未在 Node 26.3.0/npm 11.16.0 或 Linux 本地复验；POC 运行由 GitHub runner 覆盖。

## 4. 结论

Quickstart 的命令语法、JSON 字段与退出码与契约/README 一致；隔离与受控证据覆盖预览、发布、
替换、冲突和状态查询。真实来源导入与“等待必达发布”仍是剩余风险。
