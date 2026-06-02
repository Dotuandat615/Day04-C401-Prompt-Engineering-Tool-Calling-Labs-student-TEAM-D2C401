---
name: translate
track: bonus
kind: local_formatter
requires_env: []
inputs: [text, target_lang, source_lang]
outputs: [tool, translated, source_lang, target_lang, note]
side_effect: false
---
# translate

Dịch đoạn văn bản sang ngôn ngữ mục tiêu.

Tool này hoạt động ở chế độ **pass-through**: trả về text gốc kèm metadata ngôn ngữ
và hướng dẫn để model LLM tự thực hiện dịch trong câu trả lời cuối cùng.
Không yêu cầu API key bên ngoài.

Hỗ trợ các mã ngôn ngữ phổ biến: vi (tiếng Việt), en (English),
zh (Chinese), ja (Japanese), ko (Korean), fr (French), de (German), es (Spanish).
