# Changelog

## 2.1.0 (2026-11-23)

交付物由「一篇合并文稿」改为「逐字稿 + 总结」两个文件，并把专名校正与可靠性说明固化为附录。

### 新增

- `scripts/dy_tomd.py`：默认产出 `<前缀>-逐字稿.md` 与 `<前缀>-总结.md`；新增
  `--annotations`（专名校正 / 总结要点 / 可靠性说明）与 `--single-file`（旧行为）。
- **附录 A 语音识别专名校正对照表**：原识别结果 / 校正结果 / 出现位置（时间节点，
  可带章节名）；校正由脚本应用到正文并自动记录位置，未命中的条目保留并解释，不删除。
- **附录 B 可靠性说明**：客观依据（素材来源、转写引擎、转写覆盖与时间轴空白、校正命中率、
  要点统计）+ 结论支撑 + 需解释 / 澄清 / 特别说明（自动检查项 + agent 标注）。
- 总结渲染：`## 视频主题` + `## 核心方法`，一条要点一行、逐条校验章节或时间节点；
  缺位置渲染为「未标注 ⚠️」并计入附录 B，超出视频时长会告警，过长要点提示压缩。
- `examples/示例输出-逐字稿.md`、`examples/示例输出-总结.md`、`examples/标注示例.json`。
- `tests/test_tomd_bundle.py`（26 例）+ `tests/test_cli.py` 两条透传用例。

### 变更

- `douyin2md/cli.py` / `scripts/dy.py`：`url` / `batch` / `to-md` 透传 `--annotations` /
  `--single-file`；批量模式显式拒绝 `--annotations`（标注是单条内容，避免张冠李戴）。
- `SKILL.md`：输出形态改写为两文件契约、总结写法约束（不写文章）、标注 JSON 必做流程、
  不产出两文件的例外；注意事项补充「两个文件一起交」「校正必须留痕」。
- `README.md` / `docs/architecture.md` / `docs/troubleshooting.md`：同步契约、渲染边界与
  「两个文件的常见失败」排查表。
- 版本 `2.0.0` → `2.1.0`。

### 兼容

- `build()` 的旧单文件渲染逻辑未改：`--single-file` / `--stdout` 产物与 `main`（`7532d16`）
  逐字一致，仅 `transcribed_at` 与生成时间随运行时刻变化（已逐字对比验收）。
- `metadata_only`（视频号降级）与转写为空时仍只产出一篇元数据文稿，不生成总结。

## 1.1.0 (2026-11-20)

来源适配与一等降级契约。依据 2026-11-19 的微信视频号提取失败归因方案落地
（该诊断文档是运行时产物，位于被 `.gitignore` 排除的 `notes/`，不在仓库内）。

### 新增

- `douyin2md/sources.py`：**唯一来源判定源**（抖音 / 微信视频号 / 未知），含 5 个结果状态、
  统一 `meta_id()` 与分级提示；纯标准库、不联网、可离线单测。
- `scripts/wx_fetch.py`：视频号预览页只读适配器。桌面 UA 浏览器渲染 → 拦截
  `get_feed_info` 响应 → 压缩为统一 `meta.json` 契约（`extraction_status` / `playability` /
  `missing` / `evidence`）→ 下载去缩图参数的高清封面。**不尝试下载视频流**。
- `doctor --json` 增加 `supported_sources`；`url` 增加来源即时提示。
- 新增 7 个测试文件、累计 116 个用例：来源判定、URL 归一化、适配器契约、空 `feedInfo`
  对抗式检查、模板降级与抖音产物回归、批量状态机、封面 OCR 契约、会话验证授权前置、
  抖音风控自动兜底的字段契约/会话策略/分支与参数透传。

### 变更

- `scripts/dy.py`：按来源分流；新增状态机与结束时的分级状态清单；用 `meta_id()`
  统一中间文件命名，避免非抖音条目出现 `None`。转写与清理流程保持原样，仅修复
  「单条模式跳过转写」的分支条件（见补做段）。
- `scripts/dy_tomd.py`：`source` 驱动 `type` 与 ID 标签；`metadata_only` 时自动输出
  「摘要说明（请先读）」与缺失清单，且不伪造转写正文/时间戳；传入非空转写后自动升级为
  完整文稿。**旧抖音 meta 的产物逐字不变**（不新增任何 frontmatter 字段）。
- `scripts/dy_fetch.py`：`normalize_input()` 复用统一归一化，修复分享文案尾随中文标点
  （如 `）。`）被吞进 URL；非抖音链接独立调用时给出可解释提示而非 `Unsupported URL`。
- `SKILL.md` / `README.md` / `CHANGELOG.md` / `docs/architecture.md` /
  `docs/troubleshooting.md` / `docs/configuration.md` / `config.example.json`：
  同步来源适配层、视频号踩坑（含裸 HTTP 直连接口返回 `permission verification failed`
  的实测证据）、降级话术与新增的 OCR 配置项。
- `douyin2md/cli.py` / `douyin2md/config.py`：`--ocr` 系列参数透传与配置注入，
  对缺少新键的旧配置字典保持兼容。

### 补做（2026-11-20，同一分支内继续）

- **P2-1 封面 OCR**：新增 `scripts/wx_ocr.py`（`auto` / `macos-vision` / `tesseract` / `none`
  四种后端，带置信度与低置信度标记，任何后端失败均降级为 `available=false`）。
  `wx_fetch.py` 加 `--ocr` / `--ocr-backend` / `--ocr-min-confidence`，结果写入
  `meta.json` 的 `cover_ocr`；`dy_tomd.py` 单列「封面文字（OCR，须人工核对）」，并明确
  **不得作为口播、字幕或视频内时间戳依据**。配置模板与 `DOUYIN2MD_OCR` 同步。
- **P2-2 会话验证**：新增 `scripts/wx_session_check.py`。未加 `--authorize` 时直接拒绝
  （rc=2）且不联网；授权后只比对带会话前后的接口字段差异，输出脱敏报告（不写 cookie 值、
  不下载视频）。实测结论：带会话后仍未出现视频流字段；用非微信 cookie 完成的仅是链路
  连通性验证，报告明确标注不能用于判定登录态假设。
- **修复单条链接不转写**：`dy.py` 中 `if audio and batch:` 使单条模式跳过转写阶段，
  已改为单条与批量都进入 `dy_transcribe.py`；批量仍复用音频暂存目录，模型只加载一次。
- **抖音短链解析与诊断**：`dy_fetch.py` 新增 `resolve_short_url()`，先把 `v.douyin.com`
  短链还原成 `www.douyin.com/video/<id>` 长链（解析失败自动回退原链接）；`Fresh cookies`
  的泛化「未知错误」提示改为 Argus / `a_bogus` 精确诊断并指向 `capture` 兜底。
- **真实联网回归（2026-11-19）**：给定抖音样本直连 yt-dlp 仍被风控拦截（属平台/网络限制，
  非本版缺陷）；改用 `dy_browser_capture.py` 取得真实 23MB / 6:18 视频与 `aweme/detail`，
  完成 `sherpa` 转写（2156 字 / 19 段）→ Markdown 全链路；当时的 81 个用例全部通过
  （后续补做与本轮兜底测试累计增至 116 个）。

### 一键链路（2026-11-20 发布前收尾）

- **抖音 `url` 直连失败自动兜底**：`dy_fetch.py` 新增 `slim_from_detail()` 与
  `capture_fallback()`，把浏览器拦截的 `aweme/detail` 映射成与 yt-dlp **完全相同**的
  `meta.json` 契约（含 `audio_path` 指向 mp4），下游 `transcribe` → `to-md` 零改动。
  新增 `--no-capture-fallback` / `--force-capture`；`--no-audio` 透传 `--no-download`。
  `dy.py` 在兜底成功时输出一行说明，`cli.py` / `config.py` / `config.example.json`
  全链路透传两个开关（兼容缺新键的旧配置字典）。
- **全新游客会话避开验证码**：`dy_browser_capture.py` 新增 `--fresh` / `--profile-dir` /
  `--no-download`，未捕获 detail 时返回 rc=3 并打印 `[risk]` 诊断。实测复用旧 profile
  + 1028 条登录 cookie 会命中「验证码中间页」，而全新空 profile 游客态稳定取得
  `aweme/detail`；自动兜底默认先 fresh，失败再用常规会话互补重试一次，显式 cookie 时
  优先尊重登录态。`capture` 子命令同步暴露 `--fresh`。
- **真实样本一键验收**：`bash bin/douyin2md url "<分享文案>" -o <目录>`（默认参数，
  两次连续执行）均 rc=0，自动走兜底 → sherpa 转写 2156 字 / 19 段 →
  7355 字节带时间戳文稿，状态 `ok`；`meta.json` 带 `capture_fallback: true`。
  旧抖音 meta 与 `main` 分支产物重验仍逐字一致（含/不含转写两种）。
- 文档同步 `SKILL.md` / `README.md` / `docs/architecture.md` /
  `docs/configuration.md` / `docs/troubleshooting.md`。

### 已知边界

- 视频号预览页由平台限制，产物恒为 `metadata_only`；逐字稿需用户提供微信客户端保存的
  视频/录屏，再走 `transcribe` → `to-md`。
- 抖音**直连** yt-dlp 仍受 `aweme/detail` Argus / `a_bogus` 风控影响，静态 cookie 不保证
  成功；但 `url` 会自动切浏览器拦截兜底，故**承诺的是一键链路成功率，不是直连成功率**。
  兜底依赖本机 `playwright` + Chrome；遇验证码中间页会换会话重试一次，仍失败则如实报
  平台限制，不破解验证码、不伪造签名、不高并发重试。
- 2.0.0 段落中「`scripts/*.py` 逐字节保持不变」描述的是该版本当时的状态，
  **不适用于本版**；本版对 4 个既有脚本做了增量修改并新增 3 个脚本，
  命令行参数与抖音产物格式保持兼容。

## 2.0.0 (2026-11-15)

通用化改造与仓库整理。目标是「同一份文件，无需修改即可被主流 agent 框架识别调用」。

### 新增

- 统一入口 `bin/douyin2md`：9 个子命令（url / batch / transcribe / to-md / capture /
  model / cookie / doctor / config），用 `BASH_SOURCE` 自定位技能根，任意 cwd 可调用。
- 接口层包 `douyin2md/`：`cli.py`（参数归并 + 转发）、`config.py`（配置优先级 + 脱敏）、
  `__main__.py`（`python3 -m douyin2md`）。
- 统一依赖声明：`pyproject.toml`（core / local / browser / all / dev extras + console script）
  与 `requirements.txt`。
- 统一配置：`config.example.json`、`DOUYIN2MD_*` 环境变量、四级优先级、密钥只走环境变量。
- `doctor` 只读环境体检、`config` 脱敏配置打印。
- 文档：`docs/agent-compatibility.md`、`configuration.md`、`architecture.md`、`troubleshooting.md`。
- 示例：`examples/urls.txt`、`cli.sh`、`agent-prompts.md`；零依赖单测 `tests/`。
- `LICENSE`（MIT）与完善的 `.gitignore`（排除 cookie、模型、媒体、本地配置）。

### 变更

- `SKILL.md` 重写为通用版：移除本机绝对路径与解释器踩坑，统一为 `bin/douyin2md` 调用；
  环境相关记录迁至 `docs/troubleshooting.md`，知识不丢失。
- `README.md` 重写，补齐框架接入、依赖分层、命令速查与仓库结构。
- `install.sh` 新增 `workbuddy` 目标并在帮助中标注统一入口。

### 未变更

- `scripts/*.py` 全部 9 个原始脚本**逐字节保持不变**，继续可单独调用；新入口仅做转发，
  历史命令 `python3 scripts/dy.py ...` 仍然有效。
