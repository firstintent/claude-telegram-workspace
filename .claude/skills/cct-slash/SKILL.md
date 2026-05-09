---
name: cct-slash
description: |
  Execute Claude Code slash commands in any running tmux session — from Telegram, another Claude session, or the CLI. Use this skill whenever someone asks to run a slash command (/clear, /compact, /memory, /new, /review, /help, etc.) in a specific tmux session, or says "send /X to [session]", "execute /X in [session]", "在 [session] 里执行 /X", or "run /X on the [session] claude". Also triggers for broadcast requests like "在所有 session 执行 /memory". Sends keystrokes via tmux send-keys to the target session's active pane.
allowed-tools: [Bash]
---

# cct-slash

Send any Claude Code slash command to a running tmux session. The target session must already have Claude Code running in its active pane.

## Steps

### 1. Discover sessions

```bash
tmux list-sessions
```

Match the user's stated session against this live list:

| User says | Resolution |
|---|---|
| Exact name | Use it directly |
| Partial name | Pick the session whose name contains the string |
| "all sessions" / "所有 session" | Collect every session |
| Nothing specified | Print the list and ask which session |

### 2. Validate

```bash
tmux has-session -t <name>
```

If the session doesn't exist, report the error and stop.

### 3. Announce

Before sending, tell the user (and reply via Telegram if that's where the request came from):

> 准备向 `<session-name>` 发送 `<slash-command>`…

### 4. Send the slash command

For **each** target session:

```bash
# Send the text literally — no tmux key interpretation
tmux send-keys -t <session-name> -l -- "<slash-command>"
# Submit
tmux send-keys -t <session-name> Enter
```

If the slash command has arguments (e.g. `/new build a payment service`), pass the full string as one literal send.

### 5. Capture and confirm

Wait ~1 second, then capture the tail of the pane:

```bash
sleep 1
tmux capture-pane -t <session-name> -p | tail -20
```

Read the output:
- If it shows the command was received (prompt changed, Claude is responding, or the command echoed) → success
- If the pane looks unchanged → mention it may have been buffered (Claude was busy) or warn the user
- If the pane doesn't look like a Claude Code prompt (looks like a shell) → warn the user the session may not be running Claude Code

### 6. Report

Summarise what happened for each session. If the request came via Telegram, send the result back with `mcp__plugin_telegram_telegram__reply`.

---

## Broadcast mode

When sending to multiple sessions, loop sequentially:

```bash
for session in <list>; do
  tmux send-keys -t "$session" -l -- "<slash-command>"
  tmux send-keys -t "$session" Enter
  sleep 0.5
  echo "=== $session ===" 
  tmux capture-pane -t "$session" -p | tail -10
done
```

Report each session's result individually.

---

## Quick example

User (via Telegram): "在 myproject 里执行 /clear"

```bash
tmux list-sessions          # confirms myproject exists
tmux send-keys -t myproject -l -- "/clear"
tmux send-keys -t myproject Enter
sleep 1
tmux capture-pane -t myproject -p | tail -20
```

Reply: "✓ 已向 `myproject` 发送 `/clear`，Claude Code 已收到指令。"
