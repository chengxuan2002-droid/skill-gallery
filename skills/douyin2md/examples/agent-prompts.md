# Agent 提示词示例

安装到任一框架后，直接说自然语言即可；框架读 `SKILL.md` 的 `description` 自动触发。
以下示例在 Claude Code / Codex / WorkBuddy / Cursor / Gemini CLI 中措辞相同。

## 单条

```text
把这个抖音视频转成 md：https://v.douyin.com/xxxx/
```

```text
7.43 KJi:/ U@y.TY 生活可以忙碌 https://v.douyin.com/xxxx/ 复制此链接
帮我把内容整理成笔记
```

## 批量

```text
这几个链接都转成 md，一个链接一篇：
https://v.douyin.com/aaa/
https://v.douyin.com/bbb/
https://v.douyin.com/ccc/
```

```text
把 examples/urls.txt 里的视频全部提取成 Markdown，失败的单独列出来。
```

## 本地音视频

```text
把 ./访谈集/ 这个目录里的录音全部转录成带时间戳的文稿，模型只加载一次。
```

```text
转一下 ./会议录音.mp4，不用联网，输出 JSON 就行。
```

## 只要总结（不是逐字稿）

```text
这个视频讲了什么？把核心方法和实施步骤整理成一份结构化总结，标注转写来源。
```

> 用户说「总结 / 核心内容 / 有哪些方法」时，`SKILL.md` 要求产出结构化总结文档，
> 不是把逐字稿原样交上去。

## 运维类

```text
检查一下 douyin2md 的运行环境缺什么，不要安装任何东西。
```

对应 `bash bin/douyin2md doctor`（纯只读）。

```text
现在生效的配置是什么？不要打印任何 API Key。
```

对应 `bash bin/douyin2md config`（密钥只显示 set/not set）。

## 给维护者的安装提示词

```text
把 douyin2md 技能装到我的 Claude Code 和 Codex 用户级目录，
先 dry-run 看会改什么，不要安装依赖，最后跑一次 doctor 并报告结果。
```

对应 `bash install.sh --target claude,codex --skip-deps --dry-run`。
