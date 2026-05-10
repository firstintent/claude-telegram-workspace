#!/usr/bin/env bash
# Usage: bash <(curl -sSL https://raw.githubusercontent.com/firstintent/claude-telegram-workspace/main/install.sh)
set -euo pipefail

REPO="https://github.com/firstintent/claude-telegram-workspace.git"
TARGET="$(pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

TELEGRAM_PERMS='[
  "mcp__plugin_telegram_telegram__reply",
  "mcp__plugin_telegram_telegram__react",
  "mcp__plugin_telegram_telegram__edit_message",
  "mcp__plugin_telegram_telegram__download_attachment",
  "Skill(telegram:configure)",
  "Skill(telegram:access)",
  "Skill(cct-slash)",
  "Skill(cct-snapshot)",
  "Read(./.claude/channels/**)"
]'

echo "→ Fetching template..."
git clone --depth 1 --quiet "$REPO" "$TMP/template"

echo "→ Installing skills..."
mkdir -p "$TARGET/.claude/skills"
for skill in telegram-configure telegram-access cct-slash cct-snapshot; do
    src="$TMP/template/.claude/skills/$skill"
    [ -d "$src" ] && cp -r "$src" "$TARGET/.claude/skills/" && echo "  ✓ $skill"
done

echo "→ Creating channels/telegram structure..."
mkdir -p "$TARGET/.claude/channels/telegram/approved"
[ -f "$TARGET/.claude/channels/telegram/.gitkeep" ]          || touch "$TARGET/.claude/channels/telegram/.gitkeep"
[ -f "$TARGET/.claude/channels/telegram/approved/.gitkeep" ] || touch "$TARGET/.claude/channels/telegram/approved/.gitkeep"

echo "→ Merging settings.local.json..."
SETTINGS="$TARGET/.claude/settings.local.json"
mkdir -p "$TARGET/.claude"

# 仅写入 settings.local.json（gitignored）。绝不修改用户项目的 settings.json。
if [ ! -f "$SETTINGS" ]; then
    cat > "$SETTINGS" <<EOF
{
  "enabledPlugins": {
    "telegram@claude-plugins-official": true
  },
  "permissions": {
    "allow": $TELEGRAM_PERMS
  }
}
EOF
    echo "  Created .claude/settings.local.json"
elif command -v jq &>/dev/null; then
    MERGED=$(jq -n \
        --argjson existing "$(cat "$SETTINGS")" \
        --argjson perms "$TELEGRAM_PERMS" \
        '$existing
         | .enabledPlugins["telegram@claude-plugins-official"] = true
         | .permissions.allow = (((.permissions.allow // []) + $perms) | unique)')
    echo "$MERGED" > "$SETTINGS"
    echo "  Merged into existing .claude/settings.local.json"
else
    echo "  ⚠ jq not found — please add manually to .claude/settings.local.json:"
    echo '    "enabledPlugins": { "telegram@claude-plugins-official": true }'
    echo "    permissions.allow: mcp__plugin_telegram_telegram__reply/react/edit_message/download_attachment"
    echo "                       Skill(telegram:configure) Skill(telegram:access) Skill(cct-slash) Skill(cct-snapshot)"
fi

echo "→ Updating .gitignore..."
if ! grep -q "channels/telegram/.env" "$TARGET/.gitignore" 2>/dev/null; then
    cat >> "$TARGET/.gitignore" <<'EOF'

# Claude Telegram (added by claude-telegram-workspace/install.sh)
.claude/channels/telegram/.env
.claude/channels/telegram/access.json
.claude/channels/telegram/approved/*
!.claude/channels/telegram/approved/.gitkeep
.claude/channels/telegram/bot.pid
.claude/settings.local.json
EOF
    echo "  Updated .gitignore"
else
    echo "  .gitignore already has Telegram entries, skipped"
fi

SESSION="$(basename "$TARGET")"
echo ""
echo "✓ 安装完成！后续步骤："
echo ""
echo "  1. 在 tmux 里启动 Claude（带 Telegram 插件参数）："
echo "       tmux new -s $SESSION"
echo "       claude --channels plugin:telegram@claude-plugins-official"
echo ""
echo "  2. 在 Claude 会话中说："
echo "       帮我接入 Telegram，token 是 <BotFather 给的 token>"
echo "     Claude 写入配置后提示重启。"
echo ""
echo "  3. 退出 Claude（/exit），重启使 TELEGRAM_STATE_DIR 生效："
echo "       claude --channels plugin:telegram@claude-plugins-official"
echo ""
echo "  4. 去 Telegram 向 Bot 发任意消息，收到 6 位配对码后回到 Claude 说："
echo "       pair <6位码>"
