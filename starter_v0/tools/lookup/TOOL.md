---
name: lookup
version: 1.0.0
author: Nguoi2
track: core
kind: live_api
provider: Tavily Search API
requires_env:
  - TAVILY_API_KEY
inputs:
  - query (string, required): Từ khóa hoặc câu hỏi tìm kiếm
  - topic (string, enum: general|news, default: general): Phân loại tìm kiếm
  - timeframe (string, enum: day|week|month|year, default: week): Lọc thời gian
  - max_results (integer, default: 5): Số kết quả tối đa
outputs:
  - items: Danh sách kết quả (title, url, source, summary, score)
  - answer: Câu trả lời tổng hợp của Tavily (nếu có)
side_effect: false
---

# lookup — Tìm kiếm thông tin trên Web

## Mô tả

Tìm kiếm thông tin trên **internet rộng** thông qua Tavily Search API. Trả về danh sách bài viết/trang web liên quan với nội dung tóm tắt. Khác với `social_search` (chỉ tìm Twitter/X), `lookup` tìm trên toàn bộ web.

## Khi nào dùng `lookup`

✅ **NÊN dùng:**
- User tìm tin tức, bài báo web (`topic="news"`)
- User tìm thông tin tổng quát không gắn với Twitter
- User hỏi "tin tức về X hôm nay", "tình hình X tuần này"
- User muốn tìm web rộng (không cung cấp URL cụ thể)

❌ **KHÔNG dùng:**
- Khi user muốn tìm tweets/posts → dùng `social_search` hoặc `timeline`
- Khi user cung cấp URL cụ thể → dùng `fetch`
- Khi user chỉ đến tài khoản Twitter → dùng `timeline`

## Parameters

| Tên | Kiểu | Default | Mô tả |
|---|---|---|---|
| `query` | string | — | Từ khóa/câu hỏi tìm kiếm. Tiếng Anh cho kết quả tốt hơn. |
| `topic` | "general" \| "news" | "general" | `news` = tìm tin tức báo chí; `general` = tìm kiếm chung |
| `timeframe` | "day" \| "week" \| "month" \| "year" | "week" | Lọc kết quả theo khoảng thời gian |
| `max_results` | integer | 5 | Số kết quả trả về (1–10) |

### Chọn `timeframe` theo ngữ cảnh

| User nói | timeframe |
|---|---|
| "hôm nay", "today", "latest" | `"day"` |
| "tuần này", "this week", "7 ngày" | `"week"` |
| "tháng này", "this month" | `"month"` |
| "năm nay", "this year" | `"year"` |
| (không đề cập) | `"week"` (default) |

## Return Value

```json
{
  "tool": "web_search",
  "query": "AI news today",
  "topic": "news",
  "timeframe": "day",
  "items": [
    {
      "title": "OpenAI Releases GPT-5",
      "url": "https://techcrunch.com/...",
      "source": "techcrunch.com",
      "summary": "OpenAI today announced...",
      "score": 0.92
    }
  ]
}
```

### Khi lỗi
```json
{
  "error": "Missing TAVILY_API_KEY env var"
}
```

## Setup

1. Đăng ký tại [app.tavily.com](https://app.tavily.com)
2. Vào API → tạo key
3. Điền `.env`:
   ```
   TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxx
   ```

## Ví dụ routing đúng

```
User: "Tìm tin tức AI hôm nay"
→ lookup(query="AI news today", topic="news", timeframe="day")

User: "Tình hình thị trường crypto tuần này"
→ lookup(query="crypto market this week", topic="news", timeframe="week")

User: "Tìm thông tin về Anthropic Claude"
→ lookup(query="Anthropic Claude", topic="general", timeframe="month")
```

## Eval cases liên quan

- `group_s04`: `lookup(query="AI news", topic="news", timeframe="week")`
- `group_mt03`: Sau clarify, chọn `lookup` thay vì `social_search`
- `group_mt05`: Gọi cả `social_search` lẫn `lookup` khi user muốn "cả hai"

## Output filtering

Tool giới hạn 500 ký tự/kết quả để tránh overload context window. Nếu cần đọc đầy đủ → dùng `fetch(url=...)` với URL từ kết quả.

## Notes

- Tavily free tier: ~1000 requests/month
- `search_depth="basic"` (mặc định) đủ nhanh; "advanced" chậm hơn nhưng chính xác hơn
- `include_answer=True` trả thêm câu trả lời tổng hợp (đã tắt để tiết kiệm token)
