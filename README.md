# Claude Code 多 Bot 工作区模板

基于 Anthropic 官方 [Telegram 插件](https://github.com/anthropics/claude-plugins-official/blob/main/external_plugins/telegram/README.md) 的推荐模式，在同一台机器上运行多个 Telegram Bot，每个 Bot 对应一个完全隔离的工作区（workspace）。

## 架构

```
机器
 ├── workspace-a/          ← Bot A (token-a)   tmux: ws-a
 │    ├── CLAUDE.md
 │    ├── .claude/
 │    │    ├── settings.json
 │    │    └── channels/telegram/access.json
 │    └── <子项目>/
 │
 ├── workspace-b/          ← Bot B (token-b)   tmux: ws-b
 │    └── ...
 │
 └── workspace-c/          ← Bot C (token-c)   tmux: ws-c
      └── ...
```

每个工作区独立目录、独立 Bot Token、独立 `settings.json` 与 `access.json`，互不干扰。

## 特性

- **多工作区并行** — 同一台机器可运行任意数量工作区，每个工作区对应一个独立 Bot
- **一 Bot 一空间** — Bot Token 与工作区目录严格绑定，消息不跨区
- **权限分级** — `access.json` 管理 owner 与群员，写操作仅限 owner
- **安全加固** — `settings.json` deny 规则硬性拦截破坏性命令（rm、force-push 等）
- **后台任务** — 耗时调研 / 批量处理通过 Agent 后台执行，即时回复不阻塞
- **多项目隔离** — 同一工作区可挂载多个子项目，严禁跨项目混淆

## 快速开始

### 新建一个工作区

```bash
git clone https://github.com/firstintent/claude-telegram-workspace.git <workspace-name>
cd <workspace-name>
```

修改 `.claude/settings.json` 中的 `TELEGRAM_STATE_DIR` 为当前工作区的实际路径：

```json
{
  "env": {
    "TELEGRAM_STATE_DIR": "/path/to/<workspace-name>/.claude/channels/telegram"
  }
}
```

直接写入 Bot Token（**不要使用 `/telegram:configure`**，该技能写死全局路径，多 Bot 场景下会互相覆盖）：

```bash
mkdir -p .claude/channels/telegram
echo "TELEGRAM_BOT_TOKEN=<your-token>" > .claude/channels/telegram/.env
```

启动：

```bash
tmux new -s <workspace-name>
claude --channels plugin:telegram@claude-plugins-official
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
| `.claude/settings.json` | 工具权限白名单与 deny 规则 |
| `.claude/channels/telegram/access.json` | Telegram 用户访问控制 |
| `PROJECTS.md` | 子项目索引 |

## 参考文档

- [Telegram 插件官方文档](https://github.com/anthropics/claude-plugins-official/blob/main/external_plugins/telegram/README.md)
