# Claude Code 多 Bot 工作区模板

基于 Anthropic 官方 [Telegram 插件](https://github.com/anthropics/claude-plugins-official/blob/main/external_plugins/telegram/README.md) 的推荐模式，在同一台机器上运行多个 Telegram Bot，每个 Bot 对应一个完全隔离的工作区（workspace）。

## 特性与用法

### 🤖 多工作区独立 Bot
每个工作区绑定独立的 Bot Token，通过 `TELEGRAM_STATE_DIR` 隔离，同一台机器可并行运行多个 Bot 互不干扰。解决了 Claude Code 官方 Telegram 插件全局单 Bot 的限制，是当前的最佳实践。

```bash
# 同机并行多个工作区，每个 tmux session 一份独立 Bot
tmux new -s ws-a   # workspace-a/  →  Bot A
tmux new -s ws-b   # workspace-b/  →  Bot B
```

### ⌨️ Telegram 内执行 Claude Code 命令
通过 `cct-slash` skill，可直接在 Telegram 消息中让本机工作区 session 执行 Claude Code slash 命令。注意：Telegram 会把以 `/` 开头的消息当作 bot 命令拦截，所以**要在前面加自然语言**：

```
你（Telegram）→  执行 /clear
你（Telegram）→  帮我跑一下 /compact
你（Telegram）→  在当前 session 执行 /review
```

Bot 会回复 `✓ 已向 <session> 发送 /clear`，本机 tmux pane 内 Claude 立即执行该命令。无需切换终端，随时随地控制自己的工作区。

### 📸 远程截图当前 tmux pane
通过 `cct-snapshot` skill，让 Telegram bot 把当前 tmux pane 截图（JetBrains Mono + ANSI 颜色 + 中文）发回来，秒看 Claude 当下在做什么：

```
你（Telegram）→  截图
你（Telegram）→  看一眼现在的屏幕
你（Telegram）→  current pane
```

Bot 回一张 PNG，文字、diff 红绿底色、box-drawing 都清晰可见。`cct-slash` 与 `cct-snapshot` 都强制要求 Claude 本身跑在 tmux 内，否则拒绝。

## 快速开始

```bash
# === 前置依赖（每台机器只做一次）===
claude
#  在 Claude Code 会话中：
#  /plugin install telegram@claude-plugins-official
#  /reload-plugins

git clone https://github.com/firstintent/claude-telegram-workspace.git <workspace-name>

# === 新建一个工作区 ===
cd <workspace-name>
tmux new -s <workspace-name>
claude --channels plugin:telegram@claude-plugins-official
#  在 Claude 会话中：
#  帮我接入 Telegram，token 是 <BotFather给的token>

# === 首次配对 Telegram 用户 ===
#  在 Claude 会话中：
#  pair <6位码>

# === 同时运行多个工作区 ===
# 工作区 A
cd /path/to/workspace-a && tmux new -s ws-a
#  claude --channels plugin:telegram@claude-plugins-official
#  帮我接入 Telegram，token 是 <token-a>

# 工作区 B
cd /path/to/workspace-b && tmux new -s ws-b
#  claude --channels plugin:telegram@claude-plugins-official
#  帮我接入 Telegram，token 是 <token-b>
```

## 架构

```
机器
 ├── workspace-a/                          ← Bot A (token-a)   tmux: ws-a
 │    ├── CLAUDE.md
 │    ├── .claude/
 │    │    ├── settings.json
 │    │    ├── skills/                     ← 项目级 skills
 │    │    │    ├── cct-telegram/          ← Bot 接入 + 用户配对
 │    │    │    ├── cct-slash/             ← tmux slash 命令转发
 │    │    │    └── cct-snapshot/          ← tmux pane 截图（PNG）
 │    │    └── channels/telegram/          ← 已提交到 git（目录结构）
 │    │         ├── .gitkeep
 │    │         ├── .env                   ← gitignore（Bot Token）
 │    │         ├── access.json            ← gitignore（用户访问控制，运行时生成）
 │    │         └── approved/              ← gitignore（配对通知，运行时生成）
 │    └── <子项目>/
 │
 ├── workspace-b/                          ← Bot B (token-b)   tmux: ws-b
 │    └── ...
 └── workspace-c/                          ← Bot C (token-c)   tmux: ws-c
      └── ...
```

Claude Code 通过 `TELEGRAM_STATE_DIR` 环境变量为每个工作区指定独立的 Telegram 配置目录，使每个工作区拥有独立 Bot Token、独立 `access.json`，互不干扰。

## 配置文件说明

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | Claude 行为规范、安全规则、项目说明 |
| `.claude/settings.json` | 共享的工具权限白名单（tracked） |
| `.claude/settings.local.json` | 机器相关 env（`TELEGRAM_STATE_DIR`），setup.sh 生成，gitignored |
| `.claude/skills/cct-telegram/` | Bot 接入与用户配对 skill |
| `.claude/skills/cct-telegram/scripts/setup.sh` | 一次性初始化脚本 |
| `.claude/skills/cct-slash/` | tmux slash 命令转发 skill |
| `.claude/skills/cct-snapshot/` | tmux pane 截图 skill（Pillow 渲染 PNG） |
| `.claude/channels/telegram/access.json` | Telegram 用户访问控制，运行时生成 |
| `PROJECTS.md` | 子项目索引 |

## 参考文档

- [Telegram 插件官方文档](https://github.com/anthropics/claude-plugins-official/blob/main/external_plugins/telegram/README.md)
