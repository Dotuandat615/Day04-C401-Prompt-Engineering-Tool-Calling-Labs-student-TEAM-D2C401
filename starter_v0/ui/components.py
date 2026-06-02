"""
ui/components.py — Reusable Streamlit render components.
"""
from __future__ import annotations

from typing import Any

import streamlit as st


def render_message(role: str, content: str | None, tools: list[str] | None = None, error: str | None = None) -> None:
    """Render a single chat message bubble."""
    if role == "user":
        st.markdown(
            f'<div class="msg-user"><span class="role-badge">👤 Bạn</span>{content}</div>',
            unsafe_allow_html=True,
        )
    else:
        parts = []
        if tools:
            badges = "".join(
                f'<span class="tool-badge">⚡ {t}</span>' for t in tools
            )
            parts.append(f'<div class="tool-badges">{badges}</div>')
        if error:
            parts.append(f'<div class="error-box">❌ {error}</div>')
        elif content:
            parts.append(
                f'<div class="msg-agent"><span class="role-badge">🤖 Agent</span>{content}</div>'
            )
        st.markdown("\n".join(parts), unsafe_allow_html=True)


def render_metric_card(label: str, value: float | None, threshold_ok: float = 0.7, threshold_warn: float = 0.4) -> None:
    """Render a colored metric row in sidebar."""
    if value is None:
        return
    if value >= threshold_ok:
        color = "#34d399"
        icon = "✅"
    elif value >= threshold_warn:
        color = "#fbbf24"
        icon = "⚠️"
    else:
        color = "#f87171"
        icon = "❌"
    st.markdown(
        f'<div class="metric-row">'
        f'<span class="metric-label">{icon} {label}</span>'
        f'<span class="metric-val" style="color:{color}">{value:.2f}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_tool_event(event: dict[str, Any], expanded: bool = False) -> None:
    """Render a tool call event as an expander."""
    tool_name = event.get("tool", "unknown")
    args = event.get("args", {})
    result = event.get("result", {})
    has_error = "error" in result

    icon = "❌" if has_error else "✅"
    label = f"{icon} {tool_name}({', '.join(f'{k}={repr(v)[:30]}' for k, v in args.items())})"

    with st.expander(label, expanded=expanded):
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("📥 Arguments")
            st.json(args)
        with col_b:
            st.caption("📤 Result")
            if has_error:
                st.error(result["error"])
            else:
                st.json(result)


def render_status_badge(text: str, status: str = "ok") -> str:
    """Return HTML for a status badge."""
    colors = {"ok": "#34d399", "warn": "#fbbf24", "err": "#f87171", "info": "#38bdf8"}
    color = colors.get(status, "#94a3b8")
    return f'<span style="color:{color}; font-weight:600;">{text}</span>'
