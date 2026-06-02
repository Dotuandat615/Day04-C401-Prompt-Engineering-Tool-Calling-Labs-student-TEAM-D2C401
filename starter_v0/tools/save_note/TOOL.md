---
name: save_note
track: bonus
kind: action
requires_env: []
inputs: [content, title, tag]
outputs: [tool, status, path, title, tag, char_count]
side_effect: local_file_write
requires_confirmation: true
---
# save_note

Lưu nội dung (ghi chú, trích dẫn, tóm tắt) vào file local trong thư mục `notes/`.

Dùng khi người dùng muốn lưu lại một đoạn văn bản, kết quả research, hoặc
snippet quan trọng để tham khảo sau.

File được lưu dưới dạng Markdown (`.md`) với tên dựa trên `title` và timestamp.
Mỗi note có thể gắn `tag` để phân loại.

**Lưu ý**: Tool này ghi file ra đĩa — cần xác nhận của người dùng trước khi gọi.
