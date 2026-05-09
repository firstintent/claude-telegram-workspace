---
name: cct-telegram
description: |
  管理当前工作区的 Telegram Bot——涵盖初次接入和用户配对两个场景。
  【接入】当用户说"给这个工作区配 Telegram"、"新建 telegram bot"、"setup telegram"、
  "接入 telegram"、"配置 telegram"、"telegram 怎么弄"、"我想通过 telegram 控制 claude" 时触发。
  【配对】当用户输入配对码，如 "pair <code>"、"/pair <code>"、"配对 <code>"、
  "我的配对码是 <code>" 时触发。永远不要调用官方 telegram:access skill。
allowed-tools: [Bash, Read, Write]
---

# cct-telegram

两个场景共用一个 skill：**接入**（首次设置 Bot）和**配对**（绑定 Telegram 用户）。

---

## 场景一：接入 Telegram Bot

### 核心原则

`TELEGRAM_STATE_DIR` 必须指向**当前工作区**的 `.claude/channels/telegram/` 目录，写入
`.claude/settings.local.json`（gitignored），**绝不修改全局 `~/.claude/settings.json`**。
同一台机器可并行运行多个工作区，每个工作区独立 Bot Token 和 `access.json`，互不干扰。
`setup.sh` 已封装好这个逻辑，直接调用，不要手写路径。

### 全局一次性（每台机器只做一次）

告知用户在 Claude Code 终端手动执行，**不要自动执行**：

```
/plugin install telegram@claude-plugins-official
/reload-plugins
```

`/plugins` 确认列表中出现 `telegram@claude-plugins-official` 后退出会话。

### 每工作区独立步骤

**步骤 1 — BotFather 申请 Token**

用户在 Telegram 中搜索 `@BotFather`，发送 `/newbot`，填写名称和用户名（须以 `bot` 结尾），
复制返回的 Bot Token（格式：`123456789:AAF...`）。

**步骤 2 — 初始化工作区**

在工作区根目录执行：

```bash
bash .claude/skills/cct-telegram/scripts/setup.sh
```

脚本交互式要求输入 Token，自动完成：
1. Token 写入 `.claude/channels/telegram/.env`（权限 600，gitignored）
2. `TELEGRAM_STATE_DIR` 写入 `.claude/settings.local.json`（gitignored）

验证：

```bash
cat .claude/channels/telegram/.env      # 应含 TELEGRAM_BOT_TOKEN=...
cat .claude/settings.local.json         # TELEGRAM_STATE_DIR 须指向本工作区，不是 ~/.claude/
```

**步骤 3 — 启动**

```bash
tmux new -s <工作区名>
# tmux 内：
claude --channels plugin:telegram@claude-plugins-official
```

**步骤 4 — 首次配对**

在 Telegram 向 Bot 发任意消息，终端会输出 6 位配对码。用户在 Claude 会话中输入
`pair <6位码>` 后，直接执行场景二的配对流程，无需额外提示。

### 故障排查

| 症状 | 检查点 |
|------|--------|
| Bot 无响应 | `cat .claude/settings.local.json` 确认 TELEGRAM_STATE_DIR 指向本工作区 |
| 配对码不出现 | 确认启动命令含 `--channels plugin:telegram@claude-plugins-official` |
| 多工作区 Token 互串 | 每个工作区必须有独立的 `settings.local.json`，路径各自不同 |

---

## 场景二：配对 Telegram 用户

将一个 Telegram 用户绑定到本工作区。配对数据存储在工作区级别的
`.claude/channels/telegram/access.json`，不操作全局路径。

### 步骤

**1. 读取 access.json**

```
Read .claude/channels/telegram/access.json
```

**2. 验证配对码**

在 `pending[<code>]` 中查找：
- 不存在 → 回复"配对码不存在，请在 Telegram 重新发消息获取新码"，停止
- `expiresAt < 当前时间（秒）` → 回复"配对码已过期，请重新发消息"，停止

**3. 写入配对**

取出 `senderId` 和 `chatId`，执行：
1. `senderId` 加入 `allowFrom`（去重）
2. 删除 `pending[<code>]`
3. 写回 `access.json`（2 空格缩进）

```bash
mkdir -p .claude/channels/telegram/approved
echo "<chatId>" > .claude/channels/telegram/approved/<senderId>
```

**4. 确认**

回复：`已配对 senderId=<senderId>`

### access.json 结构

```json
{
  "allowFrom": ["123456789"],
  "pending": {
    "abc123": {
      "senderId": "987654321",
      "chatId": "-1001234567890",
      "expiresAt": 1700000000
    }
  }
}
```
