---
description: 配对 Telegram 用户（使用项目级 access.json，不走全局路径）
---

执行本工作区的 Telegram 配对流程，**不要调用 `/telegram:access` skill**（它会读全局 `~/.claude/channels/`，和本工作区的 `TELEGRAM_STATE_DIR` 不匹配）。

配对码：`$ARGUMENTS`

步骤（严格按 `.claude/telegram-pairing.md`）：

1. Read `.claude/channels/telegram/access.json`
2. 找到 `pending[<code>]`；不存在或 `expiresAt < now` → 告知用户重新发起并停止
3. 取出 `senderId` 与 `chatId`
4. 将 `senderId` 加入 `allowFrom`（去重），删除 `pending[<code>]`，写回 JSON（2 空格缩进）
5. `mkdir -p .claude/channels/telegram/approved` 后写入 `.claude/channels/telegram/approved/<senderId>`，内容为 `chatId`
6. 回复用户："已配对 senderId=<senderId>"
