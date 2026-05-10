---
name: telegram:access
description: |
  本工作区级别的 Telegram 访问控制，覆盖全局 telegram:access skill。
  操作本工作区的 .claude/channels/telegram/access.json，而非全局路径。
  触发：/telegram:access pair <code>、pair <code>、approve、allowlist 等。
allowed-tools: [Bash, Read, Write]
---

# telegram:access（工作区本地覆盖）

此 skill 覆盖全局 `telegram:access`，所有操作限定在本工作区路径：
`.claude/channels/telegram/access.json`

## pair <code>

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

## access.json 结构

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
