---
name: cct-slash
description: |
  Send a Claude Code slash command to the current tmux pane. Use when someone says
  "/clear", "/compact", "/memory", "/new ...", "/review", "/help", "send /X", "execute
  /X here", "在当前 session 执行 /X", or pastes any slash command for the same Claude
  to run. ONLY works when the calling Claude is itself running inside tmux — refuses
  otherwise.
allowed-tools: [Bash]
---

# cct-slash

Forwards a Claude Code slash command to the **current** tmux pane via `tmux send-keys`.
All logic lives in `scripts/cct_slash.py`; this skill is a thin trigger.

## Run

```bash
python3 .claude/skills/cct-slash/scripts/cct_slash.py "<slash-command>"
```

Pass the full slash command as one argument — including arguments, e.g.
`"/new build a payment service"`. The script handles the literal-key send and the
post-send pane capture.

## Output

Success — JSON on stdout:

```json
{"ok": true, "session": "ws-a", "pane": "%17", "sent": "/clear"}
```

Failure — JSON on stderr, non-zero exit. Most common case:

```json
{"ok": false, "error": "当前 Claude 进程不在 tmux 内（$TMUX 或 $TMUX_PANE 未设置）。..."}
```

The script intentionally does NOT capture the pane after sending: when the bot's
own Claude is the target pane, it cannot process the keystroke until this skill
returns, so any captured tail would just show the echoed command, not the response.
Use `cct-snapshot` afterwards if the user wants to see the new pane state.

## Refuse path

If the error mentions `不在 tmux 内`, do NOT retry from outside tmux. Reply to the
user (via Telegram if that's the source):

> 当前 Claude 不在 tmux 中，无法转发 slash 命令。请先在终端执行 `tmux new -s ws` 启动 Claude 再重试。

Note: send this as plain `text` format — do NOT HTML-encode any characters.

## Reporting back via Telegram

After a successful send, reply briefly with `mcp__plugin_telegram_telegram__reply`:

> ✓ 已向 `<session>` 发送 `<command>`。

If the user also wants to see the resulting pane, follow up by invoking
`cct-snapshot` and attaching the PNG.
