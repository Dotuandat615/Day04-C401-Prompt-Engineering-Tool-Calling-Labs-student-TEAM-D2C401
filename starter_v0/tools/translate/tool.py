from __future__ import annotations

from typing import Any

from tools._shared import err


# Supported language display names
LANG_NAMES: dict[str, str] = {
    "vi": "Tiếng Việt",
    "en": "English",
    "zh": "中文 (Chinese)",
    "ja": "日本語 (Japanese)",
    "ko": "한국어 (Korean)",
    "fr": "Français (French)",
    "de": "Deutsch (German)",
    "es": "Español (Spanish)",
    "pt": "Português (Portuguese)",
    "it": "Italiano (Italian)",
    "ru": "Русский (Russian)",
    "ar": "العربية (Arabic)",
    "th": "ภาษาไทย (Thai)",
    "id": "Bahasa Indonesia",
}


def _detect_lang(text: str) -> str:
    """Heuristic language detection based on character ranges."""
    if not text:
        return "en"
    text_lower = text.lower()
    # Vietnamese diacritics check
    vi_chars = set("àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ")
    if any(ch in vi_chars for ch in text_lower):
        return "vi"
    # CJK check
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "zh"
    if any("\u3040" <= ch <= "\u30ff" for ch in text):
        return "ja"
    if any("\uac00" <= ch <= "\ud7af" for ch in text):
        return "ko"
    return "en"


def translate_text(
    text: str = "",
    target_lang: str = "vi",
    source_lang: str = "auto",
) -> dict[str, Any]:
    """
    Dịch văn bản sang ngôn ngữ đích.

    Args:
        text: Nội dung cần dịch.
        target_lang: Mã ngôn ngữ đích (vi, en, zh, ja, ko, fr, de, es...).
        source_lang: Mã ngôn ngữ nguồn ('auto' để tự detect).

    Returns:
        dict với original_text, target_lang, source_lang, và note hướng dẫn cho model.
    """
    try:
        if not text or not text.strip():
            return {
                "tool": "translate",
                "error": "empty_input",
                "message": "Không có nội dung để dịch.",
            }

        target_lang = (target_lang or "vi").strip().lower()
        source_lang = (source_lang or "auto").strip().lower()

        detected_lang = _detect_lang(text) if source_lang == "auto" else source_lang
        target_name = LANG_NAMES.get(target_lang, target_lang.upper())
        source_name = LANG_NAMES.get(detected_lang, detected_lang.upper())

        word_count = len(text.split())
        # Truncate very long texts
        max_chars = 5000
        truncated = False
        text_to_translate = text
        if len(text) > max_chars:
            text_to_translate = text[:max_chars]
            truncated = True

        return {
            "tool": "translate",
            "original_text": text_to_translate,
            "source_lang": detected_lang,
            "source_lang_name": source_name,
            "target_lang": target_lang,
            "target_lang_name": target_name,
            "word_count": word_count,
            "truncated": truncated,
            "note": (
                f"Translate the 'original_text' from {source_name} to {target_name}. "
                "Provide the translation as your final response. "
                "Preserve formatting and technical terms where appropriate."
            ),
        }
    except Exception as exc:
        return err("translate", exc)
