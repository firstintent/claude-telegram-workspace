# Claude Code 多 Bot 工作区模板

基于 Anthropic 官方 [Telegram 插件](https://github.com/anthropics/claude-plugins-official/blob/main/external_plugins/telegram/README.md) 的推荐模式，在同一台机器上运行多个 Telegram Bot，每个 Bot 对应一个完全隔离的工作区（workspace）。

## 架构

```
机器
 ├── workspace-a/                          ← Bot A (token-a)   tmux: ws-a
 │    ├── CLAUDE.md
 │    ├── .claude/
 │    │    ├── settings.json
 │    │    └── channels/telegram/          ← 已提交到 git（目录结构）
 │    │         ├── .gitkeep
 │    │         ├── .env                   ← gitignore（Bot Token）
 │    │         ├── access.json            ← gitignore（用户访问控制，运行时生成）
 │    │         └── approved/              ← gitignore（配对通知，运行时生成）
 │    └── <子项目>/
 │
 ├── workspace-b/                          ← Bot B (token-b)   tmux: ws-b
 │    └── ...
 │
 └── workspace-c/                          ← Bot C (token-c)   tmux: ws-c
      └── ...
```

Claude Code 官方支持通过 `TELEGRAM_STATE_DIR` 环境变量为每个工作区指定独立的 Telegram 配置目录，使每个工作区拥有独立 Bot Token、独立 `settings.json` 与 `access.json`，互不干扰。

## 特性

- **多工作区并行** — 同一台机器可运行任意数量工作区，每个工作区对应一个独立 Bot
- **一 Bot 一空间** — Bot Token 与工作区目录严格绑定，消息不跨区
- **权限分级** — `access.json` 管理 owner 与群员，写操作仅限 owner
- **安全加固** — `settings.json` deny 规则硬性拦截破坏性命令（rm、force-push 等）
- **后台任务** — 耗时调研 / 批量处理通过 Agent 后台执行，即时回复不阻塞
- **多项目隔离** — 同一工作区可挂载多个子项目，严禁跨项目混淆

## 快速开始

### 前置依赖

```bash
# 安装 bun
curl -fsSL https://bun.sh/install | bash

# 安装 Telegram 插件（一次性，全局生效）
claude
# /plugin install telegram@claude-plugins-official
# /reload-plugins

# clone 模板
git clone https://github.com/firstintent/claude-telegram-workspace.git <workspace-name>
```

### 新建一个工作区

```bash
cd <workspace-name>

# 一步到位：提示输入 token，生成 .env 与 .claude/settings.local.json（机器相关路径）
bash .claude/setup.sh

# 启动
tmux new -s <workspace-name>
claude --channels plugin:telegram@claude-plugins-official
# 首次需在会话内：
# /plugin install telegram@claude-plugins-official
# /reload-plugins
```

> 机器相关的 `TELEGRAM_STATE_DIR` 落在 `.claude/settings.local.json`（被 `*.local` gitignore），tracked 的 `settings.json` 只承载共享的权限与 deny 规则，不再携带绝对路径。

### 首次配对 Telegram 用户

Bot 启动后，在 Telegram 向 Bot 发送任意消息拿到 6 位配对码，终端 Claude 会话中输入：

```
/pair <6位码>
```

### 同时运行多个工作区

```bash
# 工作区 A
cd /path/to/workspace-a && tmux new -s ws-a
claude --channels plugin:telegram@claude-plugins-official

# 工作区 B（新 tmux 窗口）
cd /path/to/workspace-b && tmux new -s ws-b
claude --channels plugin:telegram@claude-plugins-official
```

## 配置文件说明

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | Claude 行为规范、安全规则、项目说明 |
| `.claude/settings.json` | 共享的工具权限白名单与 deny 规则（tracked） |
| `.claude/settings.local.json` | 机器相关 env（`TELEGRAM_STATE_DIR` 等），`.claude/setup.sh` 生成，gitignored |
| `.claude/setup.sh` | 一次性初始化脚本 |
| `.claude/channels/telegram/access.json` | Telegram 用户访问控制 |
| `PROJECTS.md` | 子项目索引 |

## 参考文档

- [Telegram 插件官方文档](https://github.com/anthropics/claude-plugins-official/blob/main/external_plugins/telegram/README.md)
