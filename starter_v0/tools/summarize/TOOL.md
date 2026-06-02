---
name: summarize
track: bonus
kind: local_formatter
requires_env: []
inputs: [text, max_bullets, language]
outputs: [tool, summary, bullets, word_count, char_count]
side_effect: false
---
# summarize

Tóm tắt một đoạn văn bản dài thành danh sách bullet points ngắn gọn.
Không cần API — xử lý hoàn toàn local.

Dùng khi người dùng đã có nội dung text (từ `fetch`, `paper_text`, v.v.) và muốn
rút gọn thành bản tóm tắt dễ đọc.

`language` điều chỉnh ngôn ngữ header/label trong output (vi hoặc en).
