---
name: telegram:configure
description: |
  本工作区级 Telegram 接入，覆写全局 telegram:configure。
  写入 .claude/channels/telegram/.env 与 .claude/settings.local.json
  里的 TELEGRAM_STATE_DIR，绝不碰用户的 settings.json。
  触发：接入 telegram、setup telegram、配 telegram bot、
  /telegram:configure、token 是 <...>。
allowed-tools: [Bash, Read, Write]
---

# telegram:configure（工作区本地覆写）

`TELEGRAM_STATE_DIR` 必须指向**当前工作区**的 `.claude/channels/telegram/`。
**只合并写入** `.claude/settings.local.json`（gitignored），不动 `.claude/settings.json`，不动 `~/.claude/settings.json`。

**前提**：`telegram@claude-plugins-official` 已全局安装。

## 步骤

1. 用户从 @BotFather `/newbot` 拿到 Token（格式 `123456789:AAF...`）。

2. 写入 Token（600 权限）：

```bash
mkdir -p .claude/channels/telegram
install -m 600 /dev/null .claude/channels/telegram/.env
echo "TELEGRAM_BOT_TOKEN=<token>" > .claude/channels/telegram/.env
```

3. 合并 `settings.local.json`（保留已有键，绝不 `cat >` 覆盖）：

```bash
LOCAL=.claude/settings.local.json
DIR="$(pwd)/.claude/channels/telegram"
if [ -f "$LOCAL" ]; then
  jq --arg dir "$DIR" '.env.TELEGRAM_STATE_DIR = $dir' "$LOCAL" > "$LOCAL.tmp" && mv "$LOCAL.tmp" "$LOCAL"
else
  jq -n --arg dir "$DIR" '{env: {TELEGRAM_STATE_DIR: $dir}}' > "$LOCAL"
fi
```

4. 验证 `cat .claude/channels/telegram/.env` 与 `cat .claude/settings.local.json`。

5. 提示用户：

> 配置完成。`/exit` 后重启：
> `claude --channels plugin:telegram@claude-plugins-official`
> 重启后向 Bot 发任意消息获取 6 位配对码，再回 Claude 输入 `pair <code>`。

## 故障排查

| 症状 | 检查 |
|------|------|
| Bot 无响应 | `cat .claude/settings.local.json` 确认 `TELEGRAM_STATE_DIR` 指向本工作区 |
| 收不到配对码 | tmux 内启动命令含 `--channels plugin:telegram@claude-plugins-official` |
| 多工作区 Token 互串 | 每工作区独立 `settings.local.json`，路径互不相同 |
