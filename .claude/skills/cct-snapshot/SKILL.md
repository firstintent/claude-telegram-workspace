---
name: cct-snapshot
description: |
  Render the current tmux pane to a PNG and reply with it via Telegram. Use when the
  user asks for a "screenshot", "snapshot", "看一眼现在的屏幕", "截图", "current pane",
  "current screen", or wants to see what Claude is showing in their terminal right now.
  ONLY works when the calling Claude is itself running inside tmux — refuses otherwise.
allowed-tools: [Bash]
---

# cct-snapshot

Captures the current tmux pane and renders it to a PNG (with ANSI colors). All logic
lives in `scripts/cct_snapshot.py`; this skill is a thin trigger.

## Run

```bash
python3 .claude/skills/cct-snapshot/scripts/cct_snapshot.py
```

Useful flags:
- `--out /tmp/foo.png` — fix the output path
- `--history 200` — include 200 lines of scrollback (default: visible only)
- `--no-color` — skip ANSI parsing, render plain text on the dark background

## Output

Success — JSON on stdout:

```json
{"ok": true, "session": "ws-a", "path": "/tmp/cct-snapshot-ws-a-1715299200.png",
 "width": 1024, "height": 480}
```

Failure — JSON on stderr, non-zero exit. Most common case:

```json
{"ok": false, "error": "当前 Claude 进程不在 tmux 内（$TMUX 未设置）。..."}
```

## Reply via Telegram

Pass `path` to `mcp__plugin_telegram_telegram__reply` as an attachment:

```
mcp__plugin_telegram_telegram__reply(
  chat_id=<chat>,
  text="📸 当前 tmux pane（session=<session>）",
  files=["<path>"]
)
```

## Refuse path

If the script fails with `不在 tmux 内`, do not retry. Tell the user to launch Claude
inside tmux first:

> 当前 Claude 不在 tmux 中，无法截图。请先在终端执行 `tmux new -s ws` 启动 Claude 再试。

Note: send this as plain `text` format — do NOT HTML-encode any characters.
