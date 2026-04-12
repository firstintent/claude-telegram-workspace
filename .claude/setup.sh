#!/usr/bin/env bash
# 一次性初始化：写入 Bot Token 与本机 TELEGRAM_STATE_DIR
# 不修改 tracked 的 settings.json，所有机器相关配置落到 settings.local.json（gitignored）
# 用法：bash .claude/setup.sh （在工作区根目录执行）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TG_DIR="$WORKSPACE_DIR/.claude/channels/telegram"
ENV_FILE="$TG_DIR/.env"
LOCAL_SETTINGS="$WORKSPACE_DIR/.claude/settings.local.json"

mkdir -p "$TG_DIR"

if [[ -f "$ENV_FILE" ]] && grep -q "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE"; then
  echo "✓ 已存在 $ENV_FILE（跳过，如需更新请手动编辑）"
else
  read -r -p "Telegram Bot Token: " TOKEN
  [[ -n "$TOKEN" ]] || { echo "token 为空，终止"; exit 1; }
  umask 077
  echo "TELEGRAM_BOT_TOKEN=$TOKEN" > "$ENV_FILE"
  echo "✓ 写入 $ENV_FILE"
fi

cat > "$LOCAL_SETTINGS" <<EOF
{
  "env": {
    "TELEGRAM_STATE_DIR": "$TG_DIR"
  }
}
EOF
echo "✓ 写入 $LOCAL_SETTINGS"

cat <<EOF

下一步：
  tmux new -s $(basename "$WORKSPACE_DIR")
  claude --channels plugin:telegram@claude-plugins-official
  # 在 Telegram 向 Bot 发任意消息拿 6 位配对码，终端输入 '/pair <码>'
EOF
