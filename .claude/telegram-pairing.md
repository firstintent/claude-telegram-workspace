## Telegram 配对步骤

不要调用技能，直接执行：

1. 读取 `.claude/channels/telegram/access.json`
2. 找到 `pending[<code>]`，若不存在或已过期则告知用户重新发起
3. 提取 `senderId` 与 `chatId`
4. 将 `senderId` 加入 `allowFrom`（去重），删除 `pending[<code>]`，写回文件
5. 写入 `.claude/channels/telegram/approved/<senderId>`，文件内容为 `chatId`
6. 确认配对完成（senderId）
