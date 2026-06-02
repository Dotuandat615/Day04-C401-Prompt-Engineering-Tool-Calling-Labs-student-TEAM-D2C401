from __future__ import annotations

import re
from typing import Any

from tools._shared import err


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using punctuation heuristics."""
    # Split on sentence-ending punctuation
    raw = re.split(r"(?<=[.!?])\s+|(?<=\n)\n+", text.strip())
    sentences = [s.strip() for s in raw if s.strip() and len(s.strip()) > 20]
    return sentences


def _extract_bullets(text: str, max_bullets: int) -> list[str]:
    """Extract key sentences as bullet points."""
    # Prefer lines that start with capital or are clearly sentences
    sentences = _split_sentences(text)
    if not sentences:
        # Fallback: split by newline
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and len(ln.strip()) > 15]
        sentences = lines

    # Score by position (first and last sentences tend to be more important)
    # and by length (very short or very long sentences are less informative)
    scored: list[tuple[float, str]] = []
    total = len(sentences)
    for idx, sent in enumerate(sentences):
        position_score = 1.0 if idx == 0 else (0.8 if idx == total - 1 else 0.5)
        length_score = min(len(sent), 200) / 200
        score = position_score + length_score
        scored.append((score, sent))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [s for _, s in scored[:max_bullets]]

    # Truncate each bullet to 200 chars
    bullets = []
    for sent in top:
        if len(sent) > 200:
            sent = sent[:197] + "..."
        bullets.append(sent)
    return bullets


def summarize_text(
    text: str = "",
    max_bullets: int = 5,
    language: str = "vi",
) -> dict[str, Any]:
    """
    Tóm tắt văn bản dài thành danh sách bullet points.

    Args:
        text: Nội dung cần tóm tắt.
        max_bullets: Số bullet tối đa (1-15, mặc định 5).
        language: Ngôn ngữ label ('vi' hoặc 'en').

    Returns:
        dict với summary (markdown) và bullets (list).
    """
    try:
        if not text or not text.strip():
            return {
                "tool": "summarize",
                "error": "empty_input",
                "message": "Không có nội dung để tóm tắt.",
            }

        max_bullets = max(1, min(int(max_bullets or 5), 15))
        word_count = len(text.split())
        char_count = len(text)

        bullets = _extract_bullets(text, max_bullets)

        if language == "en":
            header = "**Summary**"
            bullet_label = "Key points"
        else:
            header = "**Tóm tắt**"
            bullet_label = "Điểm chính"

        bullet_md = "\n".join(f"- {b}" for b in bullets)
        summary_md = f"{header}\n\n{bullet_md}"

        return {
            "tool": "summarize",
            "summary": summary_md,
            "bullets": bullets,
            "word_count": word_count,
            "char_count": char_count,
            "bullet_label": bullet_label,
            "language": language,
        }
    except Exception as exc:
        return err("summarize", exc)
