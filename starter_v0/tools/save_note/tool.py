from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from tools._shared import ROOT, err


NOTES_DIR = ROOT / "notes"


def _safe_filename(title: str) -> str:
    """Convert a title to a safe filename slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "_", slug)
    slug = slug.strip("_")
    return slug[:60] or "note"


def save_note(
    content: str = "",
    title: str = "",
    tag: str = "",
    confirmed: bool = False,
) -> dict[str, Any]:
    """
    Lưu nội dung vào file Markdown trong thư mục notes/.

    Args:
        content: Nội dung cần lưu.
        title: Tiêu đề của ghi chú (dùng làm tên file).
        tag: Nhãn phân loại (ví dụ: research, ai, news, quote).
        confirmed: Phải True mới thực sự ghi file (xác nhận của người dùng).

    Returns:
        dict với status và đường dẫn file đã lưu.
    """
    try:
        if not confirmed:
            preview_title = title.strip() or "(chưa có tiêu đề)"
            preview_content = (content[:200] + "...") if len(content) > 200 else content
            return {
                "tool": "save_note",
                "status": "needs_confirmation",
                "preview_title": preview_title,
                "preview_content": preview_content,
                "tag": tag or "(không có tag)",
                "message": (
                    f"Sắp lưu ghi chú '{preview_title}' vào thư mục notes/. "
                    "Gọi lại với confirmed=true sau khi người dùng xác nhận."
                ),
            }

        if not content or not content.strip():
            return {
                "tool": "save_note",
                "error": "empty_content",
                "message": "Không có nội dung để lưu.",
            }

        NOTES_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        title_clean = title.strip() or "Ghi chú"
        slug = _safe_filename(title_clean)
        filename = f"{timestamp}_{slug}.md"
        file_path = NOTES_DIR / filename

        tag_line = f"tags: [{tag}]" if tag else "tags: []"
        frontmatter = (
            f"---\n"
            f"title: \"{title_clean}\"\n"
            f"{tag_line}\n"
            f"created: {datetime.now().isoformat(timespec='seconds')}\n"
            f"---\n\n"
        )
        full_content = frontmatter + content.strip() + "\n"
        file_path.write_text(full_content, encoding="utf-8")

        return {
            "tool": "save_note",
            "status": "saved",
            "path": str(file_path),
            "filename": filename,
            "title": title_clean,
            "tag": tag or "",
            "char_count": len(content),
            "message": f"Đã lưu ghi chú thành công: notes/{filename}",
        }
    except Exception as exc:
        return err("save_note", exc)
