"""
Streamlit UI for the Research Agent (Day04-C401).
Run: streamlit run app.py --server.port 8501
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# ─── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Research Agent 🔍",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"

# ─── Lazy imports (so the page renders before slow imports) ────────────────────
@st.cache_resource(show_spinner="Loading agent modules…")
def load_agent_deps():
    from env_loader import load_lab_env
    from providers import make_provider
    from tools import load_tool_declarations, to_openai_tools
    load_lab_env(ROOT)
    return make_provider, load_tool_declarations, to_openai_tools

@st.cache_resource(show_spinner="Initialising provider…")
def get_provider_and_tools(provider_name: str):
    make_provider, load_tool_declarations, to_openai_tools = load_agent_deps()
    provider = make_provider(provider_name)
    tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    openai_tools = to_openai_tools(tool_declarations)
    return provider, openai_tools

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
}

/* Main header */
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}
.main-header h1 {
    color: white;
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.5px;
}
.main-header p {
    color: rgba(255,255,255,0.8);
    margin: 0.3rem 0 0;
    font-size: 0.9rem;
}

/* Chat messages */
.user-bubble {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.85rem 1.2rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.5rem 0 0.5rem 15%;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.35);
    font-size: 0.95rem;
    line-height: 1.5;
}
.agent-bubble {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    backdrop-filter: blur(10px);
    color: #e8e8f0;
    padding: 0.85rem 1.2rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.5rem 15% 0.5rem 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    font-size: 0.95rem;
    line-height: 1.6;
}
.agent-label {
    font-size: 0.72rem;
    color: #a78bfa;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
.user-label {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.7);
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
    text-align: right;
}

/* Tool call card */
.tool-card {
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 10px;
    padding: 0.6rem 0.9rem;
    margin: 0.4rem 0;
    font-size: 0.82rem;
}
.tool-card-header {
    color: #10b981;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.tool-card-args {
    color: #6ee7b7;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    margin-top: 0.3rem;
    white-space: pre-wrap;
    word-break: break-all;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #e8e8f0 !important;
}

/* Stats badges */
.stat-badge {
    background: rgba(102, 126, 234, 0.15);
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    text-align: center;
    color: #a78bfa;
    font-size: 0.8rem;
    font-weight: 600;
}
.stat-badge .stat-value {
    font-size: 1.4rem;
    color: white;
    display: block;
}

/* Status pill */
.status-waiting {
    background: rgba(251, 191, 36, 0.15);
    border: 1px solid rgba(251, 191, 36, 0.4);
    color: #fbbf24;
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}
.status-answered {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #10b981;
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}

/* Input area */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: white !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.25) !important;
}
.stTextInput > div > div > input::placeholder {
    color: rgba(255,255,255,0.35) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.35) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5) !important;
}

/* Scrollable chat area */
.chat-container {
    max-height: 520px;
    overflow-y: auto;
    padding: 0.5rem;
    scrollbar-width: thin;
    scrollbar-color: rgba(102, 126, 234, 0.4) transparent;
}
.chat-container::-webkit-scrollbar {
    width: 4px;
}
.chat-container::-webkit-scrollbar-thumb {
    background: rgba(102, 126, 234, 0.4);
    border-radius: 4px;
}

/* Divider */
hr {
    border-color: rgba(255,255,255,0.08) !important;
}

/* Eval results table */
.eval-pass { color: #10b981; font-weight: 700; }
.eval-fail { color: #f87171; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ─── Helper functions ──────────────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def json_text(value: Any, *, max_chars: int | None = None) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n...<truncated>"
    return text


def trim_history(history: list[dict], window: int) -> list[dict]:
    if window <= 0:
        return []
    return history[-window * 2:]


def execute_tool_call(call, tool_functions: dict) -> dict:
    func = tool_functions.get(call.name)
    if not func:
        return {"tool": call.name, "result": {"error": "unknown_tool"}}
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}


def tool_results_message(events: list[dict]) -> dict:
    return {
        "role": "user",
        "content": (
            "TOOL_RESULTS_JSON:\n"
            f"{json_text(events, max_chars=24000)}\n\n"
            "Use only these tool results. Answer the user directly with cited sources when available."
        ),
    }


def assistant_tool_message(response_text: str | None, calls: list) -> dict:
    call_summary = [{"name": c.name, "args": c.args} for c in calls]
    content = response_text or "I will call the selected tool(s)."
    return {
        "role": "assistant",
        "content": f"{content}\n\nTOOL_CALLS_JSON:\n{json_text(call_summary)}",
    }


def run_agent_turn(
    provider,
    messages: list[dict],
    openai_tools: list,
    tool_functions: dict,
    max_tool_rounds: int = 4,
) -> dict:
    """Run one user turn through the agent tool loop. Returns result dict."""
    from env_loader import load_lab_env
    load_lab_env(ROOT)

    working = list(messages)
    all_tool_calls = []
    all_tool_results = []

    for _round in range(max_tool_rounds):
        response = provider.complete(working, openai_tools, model=None, temperature=0.0)
        calls = response.tool_calls

        if not calls:
            return {
                "status": "answered",
                "assistant_text": response.text or "",
                "tool_calls": all_tool_calls,
                "tool_results": all_tool_results,
            }

        working.append(assistant_tool_message(response.text, calls))
        non_clarify_events = []

        for call in calls:
            all_tool_calls.append({"name": call.name, "args": call.args})
            event = execute_tool_call(call, tool_functions)
            all_tool_results.append(event)

            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = result.get("question") or call.args.get("question") or "Bạn bổ sung thêm thông tin nhé."
                return {
                    "status": "waiting_for_user",
                    "assistant_text": question,
                    "tool_calls": all_tool_calls,
                    "tool_results": all_tool_results,
                }
            non_clarify_events.append(event)

        working.append(tool_results_message(non_clarify_events))

    return {
        "status": "max_tool_rounds",
        "assistant_text": "⚠️ Đã đạt giới hạn tool rounds. Xem chi tiết trong tab Debug.",
        "tool_calls": all_tool_calls,
        "tool_results": all_tool_results,
    }


def load_runs() -> list[dict]:
    """Load all eval run JSON files from the runs/ directory."""
    runs_dir = ROOT / "runs"
    results = []
    if runs_dir.exists():
        for f in sorted(runs_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append(data)
            except Exception:
                pass
    return results


# ─── Session state ──────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of {role, content, tool_calls, tool_results, status}
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "total_tools_called" not in st.session_state:
    st.session_state.total_tools_called = 0
if "provider_name" not in st.session_state:
    st.session_state.provider_name = "openrouter"
if "input_counter" not in st.session_state:
    # Incrementing this forces the text_input to re-create with an empty value
    st.session_state.input_counter = 0

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Cài đặt Agent")
    st.markdown("---")

    provider_choice = st.selectbox(
        "🌐 Provider",
        ["openrouter", "openai", "anthropic", "gemini"],
        index=0,
        help="Chọn AI provider để gọi model",
    )
    if provider_choice != st.session_state.provider_name:
        st.session_state.provider_name = provider_choice
        # Clear cache so new provider is loaded
        get_provider_and_tools.clear()

    max_rounds = st.slider("🔄 Max Tool Rounds", 1, 8, 4, help="Số vòng tool tối đa mỗi turn")
    history_window = st.slider("💬 History Window", 0, 10, 5, help="Số turn giữ trong context")

    st.markdown("---")
    st.markdown("### 📊 Thống kê phiên")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f'<div class="stat-badge"><span class="stat-value">{st.session_state.turn_count}</span>Turns</div>',
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f'<div class="stat-badge"><span class="stat-value">{st.session_state.total_tools_called}</span>Tools</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.button("🗑️ Xoá lịch sử chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.turn_count = 0
        st.session_state.total_tools_called = 0
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛠️ Tools có sẵn")
    tools_list = [
        ("🔎", "social_search", "Tìm Twitter/X"),
        ("👤", "timeline", "Timeline @user"),
        ("🌐", "lookup", "Tìm web/news"),
        ("🔗", "fetch", "Đọc URL"),
        ("📄", "papers", "Tìm ArXiv"),
        ("📤", "send", "Gửi Telegram"),
        ("💾", "save_note", "Lưu ghi chú"),
        ("📋", "policy", "Chính sách nội bộ"),
        ("🔤", "translate", "Dịch thuật"),
        ("📝", "summarize", "Tóm tắt"),
        ("❓", "clarify", "Hỏi làm rõ"),
        ("🌤️", "weather", "Thời tiết"),
        ("💱", "exchange_rate", "Tỷ giá"),
        ("📈", "trends", "Google Trends"),
    ]
    for icon, name, desc in tools_list:
        st.markdown(
            f'<span style="color:#a78bfa;font-size:0.8rem">{icon} <b>{name}</b></span> '
            f'<span style="color:#6b7280;font-size:0.75rem">— {desc}</span>',
            unsafe_allow_html=True,
        )

# ─── Main layout ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔍 Research Agent</h1>
    <p>AI-powered research assistant · Tool calling · Multi-turn conversation</p>
</div>
""", unsafe_allow_html=True)

# Tabs
tab_chat, tab_eval, tab_debug = st.tabs(["💬 Chat", "📊 Eval Results", "🔧 Debug"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: CHAT
# ─────────────────────────────────────────────────────────────────────────────
with tab_chat:
    # Render existing messages
    chat_area = st.container()
    with chat_area:
        if not st.session_state.chat_history:
            st.markdown(
                '<div style="text-align:center;color:rgba(255,255,255,0.3);padding:3rem 0;font-size:0.9rem">'
                '💬 Bắt đầu cuộc hội thoại bằng cách gõ câu hỏi phía dưới…<br><br>'
                '<span style="font-size:0.8rem">Ví dụ: "Tìm tweet mới nhất của @sama" hoặc "Đọc bài này: https://..."</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="user-label">Bạn</div>'
                        f'<div class="user-bubble">{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    status = msg.get("status", "answered")
                    status_html = (
                        '<span class="status-waiting">⏳ Đang chờ xác nhận</span>'
                        if status == "waiting_for_user"
                        else '<span class="status-answered">✅ Đã trả lời</span>'
                    )
                    st.markdown(
                        f'<div class="agent-label">🤖 Research Agent &nbsp;{status_html}</div>'
                        f'<div class="agent-bubble">{msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )

                    # Show tool calls if any
                    tool_calls = msg.get("tool_calls", [])
                    if tool_calls:
                        with st.expander(f"🔧 {len(tool_calls)} tool call(s)", expanded=False):
                            for tc in tool_calls:
                                args_str = json.dumps(tc.get("args", {}), ensure_ascii=False, indent=2)
                                st.markdown(
                                    f'<div class="tool-card">'
                                    f'<div class="tool-card-header">⚡ {tc["name"]}</div>'
                                    f'<div class="tool-card-args">{args_str}</div>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

    st.markdown("---")

    # Input row
    col_input, col_send = st.columns([6, 1])
    with col_input:
        user_input = st.text_input(
            "Nhap tin nhan",
            placeholder="Hoi gi do... (bam Gui de gui)",
            label_visibility="collapsed",
            key=f"user_input_field_{st.session_state.input_counter}",
        )
    with col_send:
        send_clicked = st.button("Send", use_container_width=True)

    # Only trigger when button is clicked AND there is text — prevents infinite rerun loop
    if send_clicked and user_input and user_input.strip():
        user_text = user_input.strip()
        # Increment counter FIRST so next rerun creates a fresh empty text_input
        st.session_state.input_counter += 1

        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_text})
        st.session_state.turn_count += 1

        # Load provider and tools
        with st.spinner("🤖 Agent đang xử lý…"):
            try:
                provider, openai_tools = get_provider_and_tools(st.session_state.provider_name)

                # Import tool functions
                from tools import TOOL_FUNCTIONS
                from env_loader import load_lab_env
                load_lab_env(ROOT)

                system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")

                # Build message history (trim to window)
                history_msgs = []
                for m in st.session_state.chat_history[:-1]:  # exclude current user message
                    if m["role"] in ("user", "assistant"):
                        history_msgs.append({"role": m["role"], "content": m["content"]})

                history_msgs = trim_history(history_msgs, history_window)
                messages = [
                    {"role": "system", "content": system_prompt},
                    *history_msgs,
                    {"role": "user", "content": user_text},
                ]

                result = run_agent_turn(
                    provider, messages, openai_tools, TOOL_FUNCTIONS, max_tool_rounds=max_rounds
                )

                st.session_state.total_tools_called += len(result.get("tool_calls", []))
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result["assistant_text"],
                    "tool_calls": result.get("tool_calls", []),
                    "tool_results": result.get("tool_results", []),
                    "status": result["status"],
                })

            except Exception as exc:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"❌ Lỗi: `{type(exc).__name__}: {exc}`",
                    "tool_calls": [],
                    "tool_results": [],
                    "status": "error",
                })

        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: EVAL RESULTS
# ─────────────────────────────────────────────────────────────────────────────
with tab_eval:
    st.markdown("### 📊 Eval Run History")

    runs = load_runs()
    if not runs:
        st.info("Chưa có eval run nào. Chạy `python run_eval.py` để bắt đầu.")
    else:
        # Summary cards
        latest_runs = {}
        for run in runs:
            suite = run.get("suite", "unknown")
            if suite not in latest_runs:
                latest_runs[suite] = run

        cols = st.columns(len(latest_runs) or 1)
        for i, (suite, run) in enumerate(latest_runs.items()):
            s = run.get("summary", {}) or {}
            accuracy = s.get("case_accuracy") or 0
            passed = s.get("passed_cases") or 0
            total = s.get("total_cases") or 0
            color = "#10b981" if accuracy == 1.0 else "#fbbf24" if accuracy >= 0.8 else "#f87171"
            with cols[i]:
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);'
                    f'border-radius:12px;padding:1rem;text-align:center">'
                    f'<div style="font-size:0.75rem;color:#a78bfa;font-weight:600;text-transform:uppercase;letter-spacing:1px">{suite}</div>'
                    f'<div style="font-size:2rem;font-weight:700;color:{color}">{accuracy:.0%}</div>'
                    f'<div style="font-size:0.8rem;color:#9ca3af">{passed}/{total} PASS</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # All runs table
        for run in runs:
            s = run.get("summary", {}) or {}
            accuracy = s.get("case_accuracy") or 0
            suite = run.get("suite") or "?"
            version = run.get("version") or "?"
            provider = run.get("provider") or "?"
            model = run.get("model") or "?"
            gen_at = (run.get("generated_at") or "")[:16]

            with st.expander(
                f"{'✅' if accuracy == 1.0 else '⚠️'} [{suite.upper()}] v{version} | "
                f"{accuracy:.0%} accuracy | {gen_at}",
                expanded=False,
            ):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Accuracy", f"{accuracy:.1%}")
                col2.metric("Routing", f"{(s.get('tool_routing_accuracy') or 0):.1%}")
                col3.metric("Args", f"{(s.get('argument_accuracy') or 0):.1%}")
                col4.metric("Multi-turn", f"{(s.get('multiturn_accuracy') or 0):.1%}")

                # Individual cases
                st.markdown("**Case Results:**")
                results = run.get("results", [])
                case_data = []
                for r in results:
                    passed = r.get("result", {}).get("passed", False)
                    ftype = r.get("result", {}).get("failure_type") or "—"
                    actual = r.get("result", {}).get("actual_tool_calls", [])
                    actual_names = ", ".join(c.get("name", "?") for c in actual) or "(no tool)"
                    case_data.append({
                        "ID": r.get("id", "?"),
                        "Status": "✅ PASS" if passed else "❌ FAIL",
                        "Failure Type": ftype,
                        "Actual Tools": actual_names,
                    })
                if case_data:
                    import pandas as pd
                    df = pd.DataFrame(case_data)
                    st.dataframe(df, width="stretch", hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: DEBUG
# ─────────────────────────────────────────────────────────────────────────────
with tab_debug:
    st.markdown("### 🔧 Debug — Tool Results")

    if not st.session_state.chat_history:
        st.info("Chưa có conversation nào. Hãy chat thử trước!")
    else:
        agent_msgs = [m for m in st.session_state.chat_history if m["role"] == "assistant"]
        if not agent_msgs:
            st.info("Chưa có agent response.")
        else:
            for i, msg in enumerate(reversed(agent_msgs)):
                turn_num = len(agent_msgs) - i
                tool_calls = msg.get("tool_calls", [])
                tool_results = msg.get("tool_results", [])

                with st.expander(
                    f"Turn {turn_num} — {len(tool_calls)} tools called",
                    expanded=(i == 0),
                ):
                    if not tool_calls:
                        st.markdown(
                            '<span style="color:#6b7280;font-size:0.85rem">No tool calls — direct answer</span>',
                            unsafe_allow_html=True,
                        )
                    for j, (tc, tr) in enumerate(zip(tool_calls, tool_results)):
                        st.markdown(
                            f'<div class="tool-card-header" style="margin-top:0.8rem">⚡ {tc["name"]}</div>',
                            unsafe_allow_html=True,
                        )
                        col_args, col_result = st.columns(2)
                        with col_args:
                            st.markdown("**Args:**")
                            st.json(tc.get("args", {}))
                        with col_result:
                            st.markdown("**Result:**")
                            result_data = tr.get("result", {})
                            if isinstance(result_data, dict):
                                # Truncate large results for display
                                display_data = json.dumps(result_data, ensure_ascii=False, default=str)
                                if len(display_data) > 2000:
                                    display_data = display_data[:2000] + "... (truncated)"
                                    st.code(display_data, language="json")
                                else:
                                    st.json(result_data)
                            else:
                                st.write(result_data)

    st.markdown("---")
    st.markdown("### 📂 System Info")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Artifacts:**")
        prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"
        st.markdown(f"- `system_prompt.md`: {prompt_path.stat().st_size if prompt_path.exists() else '?'} bytes")
        st.markdown(f"- `tools.yaml`: {tools_path.stat().st_size if tools_path.exists() else '?'} bytes")
    with col2:
        st.markdown("**Session state:**")
        st.json({
            "turns": st.session_state.turn_count,
            "tools_called": st.session_state.total_tools_called,
            "provider": st.session_state.provider_name,
            "history_length": len(st.session_state.chat_history),
        })
