---
name: send
version: 1.0.0
author: Nguoi2
track: bonus
kind: action
provider: Telegram Bot API
requires_env:
  - TELEGRAM_BOT_TOKEN
  - TELEGRAM_CHAT_ID
inputs:
  - text (string, required): Nội dung cần gửi lên Telegram
  - confirmed (boolean, default: false): Cờ xác nhận. false = chỉ preview, true = gửi thật
outputs:
  - status: "pending_confirmation" | "sent"
  - message_id: ID của message đã gửi (khi confirmed=true)
side_effect: true
confirmation_required: true
---

# send — Gửi tin nhắn lên Telegram Channel

## Mô tả

Gửi nội dung text lên Telegram channel. Tool này có **cơ chế xác nhận bắt buộc 2 bước** trước khi thực sự gửi, nhằm tránh gửi nhầm nội dung.

## Quy trình bắt buộc (2 bước)

```
BƯỚC 1: Gọi send(text="...", confirmed=false)
        → Tool trả về preview + yêu cầu user xác nhận
        → Agent PHẢI hiện nội dung preview cho user thấy

BƯỚC 2: Sau khi user nói "có", "yes", "gửi đi", "xác nhận"
        → Gọi send(text="...", confirmed=true)
        → Tool gửi thật lên Telegram
```

> ⚠️ **KHÔNG BAO GIỜ** gọi `confirmed=true` ngay lần đầu mà không có bước preview.

## Parameters

| Tên | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `text` | string | ✅ | Nội dung cần gửi. Hỗ trợ Markdown formatting. |
| `confirmed` | boolean | ❌ (default: false) | `false` = chỉ preview, `true` = gửi thật |

## Return Values

### Khi `confirmed=false` (preview)
```json
{
  "status": "pending_confirmation",
  "preview": "AI is changing the world...",
  "message": "Bạn có chắc muốn gửi nội dung này lên Telegram không?..."
}
```

### Khi `confirmed=true` (gửi thật)
```json
{
  "status": "sent",
  "message_id": 42,
  "chat_id": "-100123456"
}
```

### Khi lỗi
```json
{
  "error": "Thiếu TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID trong .env"
}
```

## Setup

1. Tạo bot: Telegram → @BotFather → `/newbot` → copy `BOT_TOKEN`
2. Tạo channel → thêm bot vào với quyền Admin
3. Gửi 1 tin trong channel → truy cập `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Tìm `"chat": {"id": ...}` → đó là `CHAT_ID` (số âm với channel)
5. Điền vào `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=-100123456789
   ```

## Ví dụ routing đúng

```
User: "Đăng bản tin này lên Telegram: AI weekly digest..."
→ Bước 1: send(text="AI weekly digest...", confirmed=false)
→ Agent: "Bạn có muốn gửi nội dung này không? [preview]..."
→ User: "Có, gửi đi"
→ Bước 2: send(text="AI weekly digest...", confirmed=true)
```

## Eval cases liên quan

- `group_mt02`: Sau confirmation, agent gọi `send(confirmed=true)`

## Notes

- Text hỗ trợ Telegram Markdown: `*bold*`, `_italic_`, `` `code` ``
- Giới hạn 4096 ký tự/message (Telegram limit)
- `side_effect: true` — tool này có tác dụng thực tế ra bên ngoài
