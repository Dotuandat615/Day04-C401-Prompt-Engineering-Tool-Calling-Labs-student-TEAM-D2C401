"""
app.py — Research Agent Streamlit UI
Chạy từ thư mục starter_v0/: streamlit run app.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# ── Page config (phải là lệnh đầu tiên) ────────────────────────────────────
st.set_page_config(
    page_title="Research Agent — D2C401",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Research Agent — Day04 Lab | TEAM D2C401",
    },
)

# ── Load CSS ────────────────────────────────────────────────────────────────
def load_css() -> None:
    css_path = Path(__file__).parent / "ui" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

load_css()

# ── Ensure starter_v0 is importable ────────────────────────────────────────
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Try to import agent components ─────────────────────────────────────────
_AGENT_AVAILABLE = False
try:
    from env_loader import load_lab_env
    from providers import make_provider
    from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
    from versioning import build_artifact_version
    load_lab_env(ROOT)
    _AGENT_AVAILABLE = True
except Exception as _import_err:
    _import_err_msg = str(_import_err)

# ── Constants ───────────────────────────────────────────────────────────────
ARTIFACTS_DIR = ROOT / "artifacts"
RUNS_DIR = ROOT / "runs"
TRANSCRIPTS_DIR = ROOT / "transcripts"

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini"]
VERSIONS = ["v3", "v2", "v1", "v0"]

SUGGESTION_PROMPTS = [
    "🔍 Tìm tweet gần nhất của @OpenAI",
    "📰 Tin tức AI tuần này",
    "🐦 Trending về ChatGPT hôm nay",
    "📄 Đọc bài: https://openai.com/blog",
    "📚 Paper về RAG mới nhất",
    "📋 Policy về AI research",
]

# ── Session state initialization ────────────────────────────────────────────
def init_state() -> None:
    defaults = {
        "messages": [],
        "history": [],       # LLM conversation history
        "tool_events": [],   # All tool call records
        "error_log": [],     # Error log
        "total_queries": 0,
        "failed_queries": 0,
        "provider_obj": None,
        "current_provider": None,
        "current_version": None,
        "show_tool_detail": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# ── Helper: load eval metrics from latest run JSON ──────────────────────────
def get_latest_metrics() -> dict[str, Any] | None:
    if not RUNS_DIR.exists():
        return None
    run_files = sorted(RUNS_DIR.glob("*.json"))
    if not run_files:
        return None
    try:
        return json.loads(run_files[-1].read_text(encoding="utf-8")).get("summary", {})
    except Exception:
        return None

def get_run_files() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted(RUNS_DIR.glob("*.json"), reverse=True)[:5]

def get_transcript_files() -> list[Path]:
    if not TRANSCRIPTS_DIR.exists():
        return []
    return sorted(TRANSCRIPTS_DIR.glob("*.transcript.json"), reverse=True)[:5]

# ── Helper: get or create provider ──────────────────────────────────────────
def get_provider(provider_name: str):
    if (
        st.session_state.provider_obj is not None
        and st.session_state.current_provider == provider_name
    ):
        return st.session_state.provider_obj
    try:
        prov = make_provider(provider_name)
        st.session_state.provider_obj = prov
        st.session_state.current_provider = provider_name
        return prov
    except Exception as exc:
        return None

# ── Helper: run agent one turn ───────────────────────────────────────────────
def run_agent_turn(
    user_text: str,
    provider_name: str,
    version: str,
    max_tool_rounds: int = 4,
) -> dict[str, Any]:
    """
    Call the agent with the current message and return structured result.
    Returns: { response, tool_calls, tool_events, error }
    """
    if not _AGENT_AVAILABLE:
        return {
            "response": None,
            "tool_calls": [],
            "tool_events": [],
            "error": f"Agent không khả dụng — lỗi import: {_import_err_msg}",
        }

    try:
        system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"

        if not system_prompt_path.exists():
            return {"response": None, "tool_calls": [], "tool_events": [],
                    "error": "Không tìm thấy artifacts/system_prompt.md"}
        if not tools_path.exists():
            return {"response": None, "tool_calls": [], "tool_events": [],
                    "error": "Không tìm thấy artifacts/tools.yaml"}

        system_prompt = system_prompt_path.read_text(encoding="utf-8")
        tool_declarations = load_tool_declarations(tools_path)
        openai_tools = to_openai_tools(tool_declarations)
        provider = get_provider(provider_name)

        if provider is None:
            return {"response": None, "tool_calls": [], "tool_events": [],
                    "error": f"Không thể khởi tạo provider '{provider_name}' — kiểm tra API key trong .env"}

        # Build messages including conversation history
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.history[-10:])  # last 5 pairs
        messages.append({"role": "user", "content": user_text})

        # Run tool loop
        from chat import run_model_tool_loop, assistant_tool_message, tool_results_message
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=None,
            max_tool_rounds=max_tool_rounds,
        )

        # Extract tool call names for display
        tool_names: list[str] = []
        for round_data in result.get("rounds", []):
            for tc in round_data.get("tool_calls", []):
                tool_names.append(tc.get("name", "unknown"))

        # Update conversation history for next turn
        st.session_state.history.append({"role": "user", "content": user_text})
        assistant_text = result.get("assistant_text", "")
        if assistant_text:
            st.session_state.history.append({"role": "assistant", "content": assistant_text})

        return {
            "response": assistant_text or "(Agent không trả về nội dung)",
            "tool_calls": tool_names,
            "tool_events": result.get("tool_events", []),
            "error": None,
        }

    except Exception as exc:
        from ui.error_handler import friendly_error
        err = friendly_error(exc, context="agent")
        return {
            "response": None,
            "tool_calls": [],
            "tool_events": [],
            "error": err["error"],
        }

# ── Save transcript ──────────────────────────────────────────────────────────
def save_transcript(turn_record: dict, provider: str, version: str) -> Path | None:
    try:
        TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        path = TRANSCRIPTS_DIR / f"ui_{version}_{provider}_{ts}.transcript.json"
        transcript = {
            "source": "streamlit_ui",
            "provider": provider,
            "version": version,
            "created_at": datetime.now().isoformat(),
            "turns": [turn_record],
        }
        path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return path
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── Logo / branding ──────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:12px 0 8px;">
      <div style="font-size:2rem;">🔍</div>
      <div style="font-size:1rem; font-weight:700; color:#f1f5f9;">Research Agent</div>
      <div style="font-size:0.7rem; color:#475569; margin-top:2px;">Day04 Lab · TEAM D2C401</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Configuration ─────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-title">⚙️ Cấu hình</div>', unsafe_allow_html=True)
    provider = st.selectbox("Provider", PROVIDERS, index=0, key="sb_provider")
    version = st.selectbox("Version", VERSIONS, index=0, key="sb_version")
    max_rounds = st.slider("Max tool rounds", min_value=1, max_value=8, value=4, key="sb_rounds")

    # Agent status indicator
    if _AGENT_AVAILABLE:
        st.markdown('<span class="status-ok">● Agent sẵn sàng</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-err">● Agent không khả dụng</span>', unsafe_allow_html=True)
        st.caption(f"Lỗi: {_import_err_msg[:80]}")

    st.markdown("---")

    # ── Eval Metrics ──────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-title">📊 Eval Metrics (latest run)</div>', unsafe_allow_html=True)
    metrics = get_latest_metrics()
    if metrics:
        metric_defs = [
            ("case_accuracy",         "Case accuracy"),
            ("tool_routing_accuracy", "Tool routing"),
            ("argument_accuracy",     "Arg accuracy"),
            ("multiturn_accuracy",    "Multi-turn"),
        ]
        for key, label in metric_defs:
            val = metrics.get(key)
            if val is not None:
                color = "#34d399" if val >= 0.7 else ("#fbbf24" if val >= 0.4 else "#f87171")
                icon = "✅" if val >= 0.7 else ("⚠️" if val >= 0.4 else "❌")
                st.markdown(
                    f'<div class="metric-row">'
                    f'<span class="metric-label">{icon} {label}</span>'
                    f'<span class="metric-val" style="color:{color}">{val:.2f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.caption("📭 Chưa có run data. Chạy eval để xem metrics.")

    st.markdown("---")

    # ── Recent Runs ───────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-title">📁 Runs gần nhất</div>', unsafe_allow_html=True)
    run_files = get_run_files()
    if run_files:
        for rf in run_files:
            st.caption(f"📄 `{rf.name}`")
    else:
        st.caption("Chưa có file run nào.")

    # ── Recent Transcripts ────────────────────────────────────────────────
    transcript_files = get_transcript_files()
    if transcript_files:
        st.markdown('<div class="sidebar-title" style="margin-top:8px;">📝 Transcripts</div>', unsafe_allow_html=True)
        for tf in transcript_files:
            st.caption(f"💬 `{tf.name}`")

    st.markdown("---")

    # ── Error Log ─────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-title">🐛 Error Log</div>', unsafe_allow_html=True)
    if st.session_state.error_log:
        for err_entry in st.session_state.error_log[-4:]:
            st.markdown(f'<div class="error-box">{err_entry}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-ok">✓ Không có lỗi</span>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Actions ───────────────────────────────────────────────────────────
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("🗑 Xoá chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.history = []
            st.session_state.tool_events = []
            st.session_state.error_log = []
            st.session_state.total_queries = 0
            st.session_state.failed_queries = 0
            st.rerun()
    with col_c2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    show_tools = st.toggle("Hiện chi tiết tool calls", value=False, key="toggle_tools")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN AREA — Tabs
# ═══════════════════════════════════════════════════════════════════════════

# ── Header ──────────────────────────────────────────────────────────────────
total = st.session_state.total_queries
failed = st.session_state.failed_queries
ok_rate = f"{((total - failed) / total * 100):.0f}%" if total > 0 else "—"

st.markdown(f"""
<div class="app-header">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
    <div>
      <div class="app-title">🔍 Research Agent</div>
      <div class="app-subtitle">Multi-tool AI assistant · TEAM D2C401</div>
      <div style="margin-top:8px;">
        <span class="app-badge">{provider}</span>
        <span class="app-badge">{version}</span>
        <span class="app-badge">rounds={max_rounds}</span>
      </div>
    </div>
    <div style="display:flex; gap:16px; text-align:center;">
      <div class="stat-card">
        <div class="stat-value">{total}</div>
        <div class="stat-label">Queries</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color:{'#34d399' if total == 0 or failed == 0 else '#fbbf24'}">{ok_rate}</div>
        <div class="stat-label">Success</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color:{'#f87171' if failed > 0 else '#64748b'}">{failed}</div>
        <div class="stat-label">Errors</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_chat, tab_eval, tab_tools, tab_about = st.tabs([
    "💬 Chat",
    "📊 Eval Results",
    "🔧 Tool Inspector",
    "ℹ️ About",
])

# ══════════════════════════════
# TAB 1 — Chat
# ══════════════════════════════
with tab_chat:
    # Empty state
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">🤖</div>
          <div class="empty-text">
            Chào! Tôi là Research Agent. Hãy thử hỏi tôi về tin tức, tweets, papers...<br>
            <span style="color:#475569; font-size:0.8rem;">Gợi ý bên dưới</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Suggestion chips (rendered as buttons in columns)
        st.markdown('<div style="margin-top:8px;">', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, suggestion in enumerate(SUGGESTION_PROMPTS):
            with cols[i % 3]:
                if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                    # Strip emoji prefix for the actual query
                    clean = " ".join(suggestion.split(" ")[1:])
                    st.session_state["_pending_prompt"] = clean
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Render all messages
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg.get("content")
            tools_used = msg.get("tools", [])
            error = msg.get("error")
            tool_events = msg.get("tool_events", [])

            if role == "user":
                st.markdown(
                    f'<div class="msg-user"><span class="role-badge">👤 Bạn</span>{content}</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Tool badges
                if tools_used:
                    badges = "".join(f'<span class="tool-badge">⚡ {t}</span>' for t in tools_used)
                    st.markdown(f'<div class="tool-badges">{badges}</div>', unsafe_allow_html=True)

                if error:
                    st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
                elif content:
                    st.markdown(
                        f'<div class="msg-agent"><span class="role-badge">🤖 Agent</span>{content}</div>',
                        unsafe_allow_html=True,
                    )

                # Tool detail expanders
                if show_tools and tool_events:
                    for event in tool_events:
                        tool_name = event.get("tool", "unknown")
                        args = event.get("args", {})
                        result = event.get("result", {})
                        has_err = "error" in result
                        icon = "❌" if has_err else "✅"
                        args_str = ", ".join(f"{k}={repr(v)[:25]}" for k, v in args.items())
                        with st.expander(f"{icon} {tool_name}({args_str})", expanded=False):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.caption("📥 Args")
                                st.json(args)
                            with c2:
                                st.caption("📤 Result")
                                if has_err:
                                    st.error(result["error"])
                                else:
                                    st.json(result)

    # ── Chat input ────────────────────────────────────────────────────────
    # Handle suggestion chip pre-fill
    pending = st.session_state.pop("_pending_prompt", None)
    prompt = st.chat_input("Nhập câu hỏi... (vd: tìm tweet của @OpenAI, tin AI hôm nay)", key="chat_input")

    # Use pending prompt if available
    if pending and not prompt:
        prompt = pending

    if prompt:
        # Add user message to display
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
        })
        st.session_state.total_queries += 1

        # Run agent with spinner
        with st.spinner("⚡ Agent đang xử lý..."):
            result = run_agent_turn(prompt, provider, version, max_tool_rounds=max_rounds)

        # Handle result
        ts = datetime.now().strftime("%H:%M:%S")
        if result["error"]:
            st.session_state.failed_queries += 1
            st.session_state.error_log.append(f"[{ts}] {result['error']}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": None,
                "tools": result["tool_calls"],
                "error": result["error"],
                "tool_events": result["tool_events"],
            })
        else:
            # Save to tool events history
            st.session_state.tool_events.extend(result["tool_events"])
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "tools": result["tool_calls"],
                "error": None,
                "tool_events": result["tool_events"],
            })

            # Auto-save transcript
            turn_record = {
                "timestamp": ts,
                "user": prompt,
                "assistant": result["response"],
                "tool_calls": result["tool_calls"],
                "tool_events": result["tool_events"],
            }
            save_transcript(turn_record, provider, version)

        st.rerun()

# ══════════════════════════════
# TAB 2 — Eval Results
# ══════════════════════════════
with tab_eval:
    st.markdown("### 📊 Eval Results")

    run_files_all = sorted(RUNS_DIR.glob("*.json"), reverse=True) if RUNS_DIR.exists() else []

    if not run_files_all:
        st.info("Chưa có file run nào. Chạy eval bằng lệnh:\n```\npython run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json\n```")
    else:
        selected_run = st.selectbox(
            "Chọn run file",
            options=run_files_all,
            format_func=lambda p: p.name,
            key="sel_run",
        )
        if selected_run:
            try:
                run_data = json.loads(selected_run.read_text(encoding="utf-8"))
                summary = run_data.get("summary", {})

                # Summary cards
                st.markdown("#### Summary")
                cols = st.columns(4)
                metric_keys = [
                    ("case_accuracy", "Case Acc."),
                    ("tool_routing_accuracy", "Tool Routing"),
                    ("argument_accuracy", "Arg Acc."),
                    ("multiturn_accuracy", "Multi-turn"),
                ]
                for i, (key, label) in enumerate(metric_keys):
                    val = summary.get(key)
                    with cols[i]:
                        if val is not None:
                            color = "normal" if val >= 0.7 else ("off" if val < 0.4 else "inverse")
                            st.metric(label, f"{val:.2f}")
                        else:
                            st.metric(label, "N/A")

                # Version info
                art = run_data.get("artifact_version", {})
                st.markdown("#### Artifact Version")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption(f"**Prompt hash:** `{art.get('prompt_hash', 'N/A')[:16]}...`")
                    st.caption(f"**Tools hash:** `{art.get('tools_hash', 'N/A')[:16]}...`")
                with col_b:
                    st.caption(f"**Version:** `{art.get('artifact_version', 'N/A')}`")
                    st.caption(f"**Suite:** `{run_data.get('suite', 'N/A')}`")

                # Results table
                st.markdown("#### Per-Case Results")
                results = run_data.get("results", [])
                for res in results:
                    case_id = res.get("id", "?")
                    r = res.get("result", {})
                    passed = r.get("passed", False)
                    failures = r.get("failures", [])
                    icon = "✅" if passed else "❌"
                    label = f"{icon} [{case_id}]"
                    if not passed:
                        label += f" — {', '.join(failures[:2])}"
                    with st.expander(label, expanded=False):
                        st.json(r)

            except Exception as exc:
                st.error(f"Không đọc được file: {exc}")

# ══════════════════════════════
# TAB 3 — Tool Inspector
# ══════════════════════════════
with tab_tools:
    st.markdown("### 🔧 Tool Inspector")

    if st.session_state.tool_events:
        st.caption(f"Tổng {len(st.session_state.tool_events)} tool calls trong session này")

        filter_col, _ = st.columns([1, 2])
        with filter_col:
            tool_names_all = list({e.get("tool", "?") for e in st.session_state.tool_events})
            selected_tool = st.selectbox("Lọc theo tool", ["(all)"] + sorted(tool_names_all), key="tool_filter")

        events_to_show = st.session_state.tool_events
        if selected_tool != "(all)":
            events_to_show = [e for e in events_to_show if e.get("tool") == selected_tool]

        for i, event in enumerate(reversed(events_to_show)):
            tool_name = event.get("tool", "unknown")
            args = event.get("args", {})
            result = event.get("result", {})
            has_err = "error" in result
            icon = "❌" if has_err else "✅"
            args_str = ", ".join(f"{k}={repr(v)[:30]}" for k, v in args.items())

            with st.expander(f"{icon} #{len(events_to_show) - i} {tool_name}({args_str})", expanded=(i == 0)):
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("📥 Arguments")
                    st.json(args)
                with c2:
                    st.caption("📤 Result")
                    if has_err:
                        st.error(result["error"])
                    else:
                        st.json(result)
    else:
        st.info("Chưa có tool calls. Bắt đầu chat để xem tool inspector.")

    # Tool declaration viewer
    st.markdown("---")
    st.markdown("#### 📋 Tool Declarations (tools.yaml)")
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    if tools_path.exists():
        with st.expander("Xem tools.yaml", expanded=False):
            st.code(tools_path.read_text(encoding="utf-8"), language="yaml")
    
    st.markdown("#### 📝 System Prompt")
    sp_path = ARTIFACTS_DIR / "system_prompt.md"
    if sp_path.exists():
        with st.expander("Xem system_prompt.md", expanded=False):
            st.markdown(sp_path.read_text(encoding="utf-8"))

# ══════════════════════════════
# TAB 4 — About
# ══════════════════════════════
with tab_about:
    st.markdown("""
    ### ℹ️ About Research Agent

    **Research Agent** là hệ thống AI agent nghiên cứu multi-tool được xây dựng trong khuôn khổ **Day04 Lab**,
    chạy vòng lặp evidence-driven để tối ưu prompt engineering và tool calling.

    ---

    #### 🛠️ Available Tools

    | Tool | Mô tả | API |
    |---|---|---|
    | `clarify` | Hỏi lại user khi thiếu thông tin | — |
    | `timeline` | Lấy tweets của 1 tài khoản cụ thể | RapidAPI Twitter |
    | `social_search` | Tìm tweets theo keyword | RapidAPI Twitter |
    | `lookup` | Tìm kiếm web rộng | Tavily |
    | `fetch` | Đọc nội dung 1 URL | Firecrawl |
    | `format` | Trình bày digest đẹp | — |
    | `send` ⭐ | Gửi lên Telegram (có xác nhận) | Telegram Bot |
    | `policy` | Tìm trong company policy KB | — |
    | `papers` | Tìm paper trên arXiv | arXiv API |
    | `paper_text` | Đọc PDF arXiv | arXiv |

    ---

    #### 🚀 Quick Start
    ```bash
    # Cài đặt
    cd starter_v0
    pip install -r requirements.txt
    cp .env.example .env
    # Điền API keys vào .env

    # Chạy UI
    streamlit run app.py

    # Chạy eval
    python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json

    # Chat CLI
    python chat.py --provider openrouter --version v3
    ```

    ---

    #### 👥 TEAM D2C401
    | Người | Vai trò |
    |---|---|
    | Người 1 | Infrastructure & API Integration |
    | Người 2 | Tool Engineer & Prompt Optimizer |
    | Người 3 | Eval Designer & Report |
    """)
