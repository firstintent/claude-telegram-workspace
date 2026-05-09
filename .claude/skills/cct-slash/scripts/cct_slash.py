#!/usr/bin/env python3
"""cct-slash — send a Claude Code slash command to the current tmux pane.

Refuses if $TMUX or $TMUX_PANE is unset (calling Claude not in tmux).

Usage:
    cct_slash.py <slash-command>

Output: JSON to stdout. On failure, JSON error to stderr + non-zero exit.

Note: this script intentionally does NOT capture the pane after sending. When the
bot's own Claude is the target pane, it cannot process the keystroke until this
script returns — so a post-send capture would only show the echoed command, never
Claude's response. Use cct-snapshot afterwards if you want to see the new state.
"""
import argparse
import json
import os
import subprocess
import sys


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def current_session():
    if not os.environ.get("TMUX") or not os.environ.get("TMUX_PANE"):
        fail(
            "当前 Claude 进程不在 tmux 内（$TMUX 或 $TMUX_PANE 未设置）。"
            "cct-slash 仅在 tmux 中运行的 Claude 会话内可用。"
            "请先 `tmux new -s <name>`，再启动 `claude --channels ...`。"
        )
    pane = os.environ["TMUX_PANE"]
    try:
        out = subprocess.run(
            ["tmux", "display-message", "-t", pane, "-p", "#{session_name}"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as e:
        fail(f"tmux display-message 失败: {(e.stderr or '').strip()}")
    if not out:
        fail("无法从 tmux 获取当前 session 名。")
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Send a slash command to the current tmux Claude pane."
    )
    parser.add_argument("command", help="slash command, e.g. /clear")
    args = parser.parse_args()

    session = current_session()
    pane = os.environ["TMUX_PANE"]

    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", pane, "-l", "--", args.command],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["tmux", "send-keys", "-t", pane, "Enter"],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        fail(f"tmux send-keys 失败: {(e.stderr or '').strip()}")

    print(json.dumps({
        "ok": True,
        "session": session,
        "pane": pane,
        "sent": args.command,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
