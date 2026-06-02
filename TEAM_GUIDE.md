# 🗂️ Phân công & Hướng dẫn thực hiện — Day04 Lab: Research Agent Tool Eval

> **Mục tiêu:** Build research agent chạy thật, tối ưu qua ≥3 vòng, nộp đủ run JSON + transcript + report.
> **Thời gian:** ~4 giờ | **Nhóm:** 3 người

---

## 📊 Tổng quan phân công

| | Người 1 | Người 2 | Người 3 |
|---|---|---|---|
| **Vai trò** | Infrastructure, API Integration & UI/UX | Tool Engineer & Prompt Optimizer | Eval Designer & Report |
| **Khối lượng** | ⬛⬛⬛⬛⬛ | ⬛⬛⬛⬛⬛ | ⬛⬛⬛⬛⬛ |
| **File chính** | `.env`, `tools/` (3 tools), `app.py`, `ui/error_handler.py`, `runs/`, `transcripts/` | `tools/` (2 tools mới), `artifacts/system_prompt.md`, `artifacts/tools.yaml` | `data/eval_group.json`, `artifacts/version_log.csv`, `artifacts/REPORT.md` |
| **Kỹ năng cần** | API setup, debugging, output filtering, Streamlit, error handling | Python, prompt design, YAML | JSON schema, phân tích log, viết kỹ thuật |

---

## 👤 NGƯỜI 1 — Infrastructure & API Integration

> **Nhiệm vụ cốt lõi:** Dựng toàn bộ hạ tầng, kết nối các API bên ngoài, lọc output, chạy eval.

### Giai đoạn 1 | Setup môi trường (0:00 – 0:25)

```bash
cd starter_v0
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

pip install -r requirements.txt
cp .env.example .env
```

Điền `.env` — cần lấy key từ các dịch vụ sau:

| Biến | Dịch vụ | Lấy key ở đâu |
|---|---|---|
| `OPENROUTER_API_KEY` | OpenRouter (LLM router) | openrouter.ai → Keys |
| `TAVILY_API_KEY` | Tavily (web search) | app.tavily.com → API |
| `FIRECRAWL_API_KEY` | Firecrawl (web scraping) | firecrawl.dev → Dashboard |
| `RAPIDAPI_KEY` | RapidAPI (Twitter/X) | rapidapi.com → My Apps |
| `RAPIDAPI_TWITTER_HOST` | Twitter endpoint | `twitter-api45.p.rapidapi.com` (cố định) |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot | BotFather trên Telegram: `/newbot` |
| `TELEGRAM_CHAT_ID` | Telegram Channel | Thêm bot vào channel, gọi `getUpdates` |

**Cách lấy Telegram credentials:**
```
1. Mở Telegram → tìm @BotFather → gửi /newbot
2. Đặt tên bot → copy BOT_TOKEN
3. Tạo channel → thêm bot vào channel với quyền Admin
4. Gửi 1 tin nhắn trong channel
5. Truy cập: https://api.telegram.org/bot<TOKEN>/getUpdates
6. Tìm "chat":{"id": ...} → đó là CHAT_ID (số âm với channel)
```

```bash
# Kiểm tra kết nối LLM
python scripts/preflight_provider.py --provider openrouter
```

---

### Giai đoạn 2 | Implement & debug 3 tools hiện có (0:25 – 1:15)

Người 1 chịu trách nhiệm đảm bảo **3 tools core** hoạt động đúng và output sạch:

#### Tool `timeline` — lấy bài đăng Twitter theo tài khoản

File: `tools/timeline/tool.py`

```python
import os, requests

def run(screenname: str, limit: int = 10) -> dict:
    """Lấy các bài đăng gần nhất của một tài khoản Twitter/X."""
    url = "https://twitter-api45.p.rapidapi.com/timeline.php"
    headers = {
        "X-RapidAPI-Key": os.environ["RAPIDAPI_KEY"],
        "X-RapidAPI-Host": os.environ.get("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
    }
    params = {"screenname": screenname}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # === LỌC OUTPUT: Chỉ giữ các trường cần thiết ===
        tweets = data.get("timeline", [])[:limit]
        filtered = []
        for t in tweets:
            filtered.append({
                "id": t.get("tweet_id", ""),
                "text": t.get("text", ""),
                "created_at": t.get("created_at", ""),
                "likes": t.get("favorites", 0),
                "retweets": t.get("retweets", 0),
                "url": f"https://twitter.com/{screenname}/status/{t.get('tweet_id', '')}"
            })
        return {"tweets": filtered, "count": len(filtered), "account": screenname}
    
    except requests.exceptions.Timeout:
        return {"error": "Request timeout — Twitter API không phản hồi"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code}: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}
```

#### Tool `social_search` — tìm bài đăng theo keyword

File: `tools/social_search/tool.py`

```python
import os, requests

def run(query: str, search_type: str = "Latest", limit: int = 10) -> dict:
    """Tìm bài đăng Twitter theo keyword. search_type: Latest hoặc Top."""
    url = "https://twitter-api45.p.rapidapi.com/search.php"
    headers = {
        "X-RapidAPI-Key": os.environ["RAPIDAPI_KEY"],
        "X-RapidAPI-Host": os.environ.get("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
    }
    params = {"query": query, "search_type": search_type}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # === LỌC OUTPUT ===
        tweets = data.get("timeline", data.get("tweets", []))[:limit]
        filtered = []
        for t in tweets:
            text = t.get("text", t.get("full_text", ""))
            if not text:
                continue  # bỏ qua tweet trống
            filtered.append({
                "text": text,
                "user": t.get("user", {}).get("screen_name", "unknown"),
                "created_at": t.get("created_at", ""),
                "likes": t.get("favorite_count", t.get("favorites", 0)),
                "url": f"https://twitter.com/i/web/status/{t.get('id_str', t.get('tweet_id', ''))}"
            })
        return {"results": filtered, "query": query, "search_type": search_type}
    
    except Exception as e:
        return {"error": str(e)}
```

#### Tool `fetch` — đọc nội dung URL qua Firecrawl

File: `tools/fetch/tool.py`

```python
import os, requests

def run(url: str, format: str = "markdown") -> dict:
    """Đọc nội dung của một URL và trả về text sạch."""
    api_key = os.environ.get("FIRECRAWL_API_KEY", "")
    
    # Nếu có Firecrawl key thì dùng, không thì fallback về requests
    if api_key:
        try:
            resp = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"url": url, "formats": [format]},
                timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("data", {}).get("markdown", data.get("data", {}).get("content", ""))
            
            # === LỌC OUTPUT: giới hạn độ dài ===
            if len(content) > 3000:
                content = content[:3000] + "\n\n[...nội dung bị cắt bớt...]"
            
            return {
                "url": url,
                "content": content,
                "title": data.get("data", {}).get("metadata", {}).get("title", "")
            }
        except Exception as e:
            return {"error": f"Firecrawl error: {str(e)}", "url": url}
    else:
        # Fallback: dùng requests thuần
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            # Trả về raw text, giới hạn 2000 ký tự
            return {"url": url, "content": resp.text[:2000], "title": ""}
        except Exception as e:
            return {"error": str(e), "url": url}
```

---

### Giai đoạn 3 | Chạy baseline và các vòng eval (1:15 – 1:30 + song song)

```bash
# Chạy baseline v0
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json

# Đọc và chia sẻ kết quả với Người 2
cat runs/v0_*.json | python -c "
import json, sys
data = json.load(sys.stdin)
s = data['summary']
print(f'case_accuracy: {s[\"case_accuracy\"]}')
print(f'tool_routing: {s[\"tool_routing_accuracy\"]}')
print(f'arg_accuracy: {s[\"argument_accuracy\"]}')
print()
for r in data['results']:
    if r['result'].get('failures'):
        print(f'FAIL [{r[\"id\"]}]: {r[\"result\"][\"failures\"]}')
        print(f'  observed: {r[\"result\"].get(\"observed_mismatch\")}')
"
```

Sau mỗi lần Người 2 sửa xong, chạy lại:

```bash
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json

# Parse kết quả ra CSV (optional nhưng hữu ích cho report)
mkdir -p analysis
python scripts/parse_runs.py runs/ --output analysis/base_runs.csv
```

---

### Giai đoạn 4 | Chat live + transcript (2:45 – 3:20)

```bash
python chat.py --provider openrouter --version v3
```

Thực hiện ít nhất 3 lượt:

**Lượt 1 — Request bình thường:**
```
> Tìm các bài đăng gần nhất của @OpenAI
```

**Lượt 2 — Request thiếu thông tin:**
```
> Tóm tắt tin tức về AI hôm nay
# Quan sát: agent có dùng clarify hỏi thêm không?
# Nếu không → ghi vào notes cho Người 2 sửa prompt
```

**Lượt 3 — Test send tool (bonus):**
```
> Đăng bản tin này lên Telegram: "AI news today..."
# Quan sát: agent có hỏi xác nhận trước khi gửi không?
```

Transcript tự động lưu tại `transcripts/*.transcript.json`.

---

### Giai đoạn 5 | UI/UX Streamlit + Error Handling (song song từ 1:30)

> Đây là phần **bonus điểm cao** — Người 1 dựng song song khi Người 2 đang sửa prompt.  
> Cài thêm package trước:

```bash
pip install streamlit
# Thêm vào requirements.txt:
echo "streamlit" >> requirements.txt
```

#### 5.1 — Cấu trúc file UI

```
starter_v0/
  app.py           ← File UI chính
  ui/
    components.py  ← Các hàm render tái sử dụng
    styles.css     ← Custom CSS
```

#### 5.2 — File `app.py` đầy đủ

```python
import streamlit as st
import subprocess, json, sys, os
from pathlib import Path
from datetime import datetime
import time

# ─── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
  /* Font và màu nền */
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
  html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

  /* Chat bubbles */
  .msg-user {
    background: #1a1a2e; color: #e2e8f0;
    border-left: 3px solid #6366f1;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    margin: 8px 0; font-size: 14px;
  }
  .msg-agent {
    background: #0f172a; color: #94a3b8;
    border-left: 3px solid #10b981;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    margin: 8px 0; font-size: 14px;
  }
  /* Tool badge */
  .tool-badge {
    display: inline-block;
    background: #1e293b; color: #38bdf8;
    border: 1px solid #334155; border-radius: 4px;
    padding: 2px 8px; font-size: 11px;
    font-family: 'IBM Plex Mono', monospace;
    margin: 2px;
  }
  /* Error box */
  .error-box {
    background: #1c0a0a; color: #fca5a5;
    border: 1px solid #7f1d1d; border-radius: 6px;
    padding: 10px 14px; margin: 8px 0; font-size: 13px;
  }
  /* Status indicator */
  .status-ok  { color: #34d399; font-weight: 500; }
  .status-err { color: #f87171; font-weight: 500; }
  .status-warn{ color: #fbbf24; font-weight: 500; }

  /* Sidebar metric */
  .metric-row { display: flex; justify-content: space-between;
    padding: 4px 0; border-bottom: 1px solid #1e293b; font-size: 13px; }
  .metric-label { color: #64748b; }
  .metric-val   { color: #e2e8f0; font-family: 'IBM Plex Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# ─── Session state init ─────────────────────────────────────────
if "messages"      not in st.session_state: st.session_state.messages      = []
if "tool_calls"    not in st.session_state: st.session_state.tool_calls     = []
if "error_log"     not in st.session_state: st.session_state.error_log      = []
if "total_queries" not in st.session_state: st.session_state.total_queries  = 0
if "failed_queries"not in st.session_state: st.session_state.failed_queries = 0

# ─── Helper: đọc run JSON mới nhất ──────────────────────────────
def get_latest_metrics():
    run_files = sorted(Path("runs").glob("*.json")) if Path("runs").exists() else []
    if not run_files:
        return None
    try:
        data = json.loads(run_files[-1].read_text())
        return data.get("summary", {})
    except Exception:
        return None

# ─── Helper: gọi agent và parse output ──────────────────────────
def call_agent(prompt: str, version: str, provider: str) -> dict:
    """
    Gọi chat.py và trả về dict: { response, tool_calls, error }
    """
    try:
        result = subprocess.run(
            [sys.executable, "chat.py",
             "--provider", provider,
             "--version",  version,
             "--once",     prompt],
            capture_output=True, text=True, timeout=60, cwd="."
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # Phân tích stderr để lấy tool calls (chat.py thường log ra stderr)
        tool_calls = []
        for line in stderr.splitlines():
            if "tool_call" in line.lower() or "calling" in line.lower():
                tool_calls.append(line.strip())

        if result.returncode != 0:
            return {
                "response": None,
                "tool_calls": tool_calls,
                "error": f"Process exited {result.returncode}: {stderr[:300] or 'no stderr'}"
            }

        return {"response": stdout or "(agent không trả về nội dung)", "tool_calls": tool_calls, "error": None}

    except subprocess.TimeoutExpired:
        return {"response": None, "tool_calls": [], "error": "⏱️ Timeout sau 60 giây — agent không phản hồi"}
    except FileNotFoundError:
        return {"response": None, "tool_calls": [], "error": "❌ Không tìm thấy chat.py — hãy chạy app từ thư mục starter_v0/"}
    except Exception as e:
        return {"response": None, "tool_calls": [], "error": f"Lỗi không xác định: {str(e)}"}

# ─── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình")
    provider = st.selectbox("Provider", ["openrouter", "anthropic", "openai"], index=0)
    version  = st.selectbox("Version",  ["v3", "v2", "v1", "v0"], index=0)

    st.markdown("---")
    st.markdown("### 📊 Eval metrics")
    metrics = get_latest_metrics()
    if metrics:
        for key, label in [
            ("case_accuracy",         "Case accuracy"),
            ("tool_routing_accuracy", "Tool routing"),
            ("argument_accuracy",     "Arg accuracy"),
            ("multiturn_accuracy",    "Multi-turn"),
        ]:
            val = metrics.get(key)
            if val is not None:
                color = "#34d399" if val >= 0.7 else ("#fbbf24" if val >= 0.4 else "#f87171")
                st.markdown(
                    f'<div class="metric-row">'
                    f'<span class="metric-label">{label}</span>'
                    f'<span class="metric-val" style="color:{color}">{val:.2f}</span>'
                    f'</div>', unsafe_allow_html=True
                )
    else:
        st.caption("Chưa có run data. Chạy eval để xem metrics.")

    st.markdown("---")
    st.markdown("### 📁 Runs gần nhất")
    run_files = sorted(Path("runs").glob("*.json"))[-4:] if Path("runs").exists() else []
    for f in reversed(run_files):
        st.caption(f"📄 {f.name}")
    if not run_files:
        st.caption("Chưa có file nào.")

    st.markdown("---")
    st.markdown("### 🐛 Error log")
    if st.session_state.error_log:
        for err in st.session_state.error_log[-3:]:
            st.markdown(f'<div class="error-box">⚠ {err}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-ok">✓ Không có lỗi</span>', unsafe_allow_html=True)

    if st.button("🗑 Xoá lịch sử chat"):
        st.session_state.messages   = []
        st.session_state.tool_calls = []
        st.session_state.error_log  = []
        st.rerun()

# ─── Main area ──────────────────────────────────────────────────
col_title, col_stats = st.columns([3, 1])
with col_title:
    st.markdown("## 🔍 Research Agent")
    st.caption(f"Provider: `{provider}` · Version: `{version}`")
with col_stats:
    total = st.session_state.total_queries
    failed = st.session_state.failed_queries
    ok_rate = f"{((total-failed)/total*100):.0f}%" if total > 0 else "—"
    st.metric("Queries", total)
    st.metric("Success rate", ok_rate)

st.markdown("---")

# ─── Hiển thị lịch sử chat ──────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    role  = msg["role"]
    text  = msg["content"]
    tools = msg.get("tools", [])
    error = msg.get("error")

    if role == "user":
        st.markdown(f'<div class="msg-user">👤 {text}</div>', unsafe_allow_html=True)
    else:
        # Hiện tool badges nếu có
        if tools:
            badges = " ".join(f'<span class="tool-badge">⚡ {t}</span>' for t in tools)
            st.markdown(badges, unsafe_allow_html=True)
        if error:
            st.markdown(f'<div class="error-box">❌ {error}</div>', unsafe_allow_html=True)
        elif text:
            st.markdown(f'<div class="msg-agent">🤖 {text}</div>', unsafe_allow_html=True)

# ─── Input chat ─────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
prompt = st.chat_input("Nhập câu hỏi cho agent... (vd: tìm tweet của @OpenAI)")

if prompt:
    # Thêm message user
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.total_queries += 1

    # Gọi agent với spinner
    with st.spinner("Agent đang xử lý..."):
        result = call_agent(prompt, version, provider)

    # Xử lý kết quả
    if result["error"]:
        st.session_state.failed_queries += 1
        err_msg = result["error"]
        st.session_state.error_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {err_msg}")
        st.session_state.messages.append({
            "role":    "assistant",
            "content": None,
            "tools":   result["tool_calls"],
            "error":   err_msg
        })
    else:
        st.session_state.messages.append({
            "role":    "assistant",
            "content": result["response"],
            "tools":   result["tool_calls"],
            "error":   None
        })

    st.rerun()
```

#### 5.3 — Error Handling tập trung: `ui/error_handler.py`

Tạo file này để xử lý lỗi nhất quán ở tất cả tools:

```python
# ui/error_handler.py
"""
Các loại lỗi và cách xử lý tập trung.
Import và dùng trong tất cả tool.py thay vì try/except riêng lẻ.
"""
import functools, os, time
from typing import Callable

# ── Bảng mã lỗi thân thiện ──────────────────────────────────────
ERROR_MESSAGES = {
    # API key
    "401": "❌ API key không hợp lệ hoặc hết hạn — kiểm tra lại .env",
    "403": "❌ Không có quyền truy cập — kiểm tra key và subscription",
    # Rate limit
    "429": "⏳ Quá nhiều request — đợi 30 giây rồi thử lại",
    # Server errors
    "500": "🔧 Server lỗi tạm thời — thử lại sau 10 giây",
    "502": "🔧 Bad gateway — API provider đang có vấn đề",
    "503": "🔧 Service không khả dụng — thử lại sau",
    # Network
    "timeout": "⏱️ Request timeout — kiểm tra kết nối mạng",
    "connection": "🌐 Không kết nối được — kiểm tra internet hoặc VPN",
    # Missing key
    "missing_key": "🔑 Thiếu API key trong .env — xem TOOL-SETUP.md",
}

def friendly_error(exc: Exception, context: str = "") -> dict:
    """Chuyển exception thành dict lỗi thân thiện cho agent đọc."""
    msg = str(exc)
    prefix = f"[{context}] " if context else ""

    # Map các pattern lỗi phổ biến
    if "401" in msg:     return {"error": prefix + ERROR_MESSAGES["401"]}
    if "403" in msg:     return {"error": prefix + ERROR_MESSAGES["403"]}
    if "429" in msg:     return {"error": prefix + ERROR_MESSAGES["429"]}
    if "500" in msg:     return {"error": prefix + ERROR_MESSAGES["500"]}
    if "502" in msg:     return {"error": prefix + ERROR_MESSAGES["502"]}
    if "503" in msg:     return {"error": prefix + ERROR_MESSAGES["503"]}
    if "timeout" in msg.lower() or "timed out" in msg.lower():
        return {"error": prefix + ERROR_MESSAGES["timeout"]}
    if "connectionerror" in msg.lower() or "connection refused" in msg.lower():
        return {"error": prefix + ERROR_MESSAGES["connection"]}

    # Lỗi thiếu env var
    if "KeyError" in type(exc).__name__ or "environ" in msg.lower():
        key_name = msg.strip("'\"")
        return {"error": prefix + f"🔑 Thiếu biến môi trường: {key_name} — thêm vào .env"}

    # Fallback
    return {"error": prefix + f"Lỗi không xác định: {msg[:200]}"}


def check_env_keys(*keys: str) -> dict | None:
    """Kiểm tra các env key bắt buộc. Trả về None nếu đủ, dict lỗi nếu thiếu."""
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        return {"error": f"🔑 Thiếu key trong .env: {', '.join(missing)} — xem TOOL-SETUP.md"}
    return None


def with_retry(max_retries: int = 2, delay: float = 3.0):
    """Decorator tự động retry khi gặp lỗi tạm thời (429, 500, 502, 503)."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_result = None
            for attempt in range(max_retries + 1):
                result = func(*args, **kwargs)
                last_result = result
                # Chỉ retry với lỗi tạm thời
                if isinstance(result, dict) and "error" in result:
                    err = result["error"]
                    is_retryable = any(code in err for code in ["429", "500", "502", "503", "timeout"])
                    if is_retryable and attempt < max_retries:
                        time.sleep(delay * (attempt + 1))  # exponential backoff
                        continue
                return result
            return last_result
        return wrapper
    return decorator
```

#### 5.4 — Áp dụng error_handler vào tools

Cập nhật `tools/timeline/tool.py` dùng helper trên:

```python
import os, requests
from ui.error_handler import friendly_error, check_env_keys, with_retry

@with_retry(max_retries=2, delay=3.0)
def run(screenname: str, limit: int = 10) -> dict:
    # Kiểm tra key trước khi gọi API
    err = check_env_keys("RAPIDAPI_KEY")
    if err: return err

    url = "https://twitter-api45.p.rapidapi.com/timeline.php"
    headers = {
        "X-RapidAPI-Key": os.environ["RAPIDAPI_KEY"],
        "X-RapidAPI-Host": os.environ.get("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
    }
    try:
        resp = requests.get(url, headers=headers, params={"screenname": screenname}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        tweets = data.get("timeline", [])[:limit]
        filtered = [
            {
                "id":         t.get("tweet_id", ""),
                "text":       t.get("text", ""),
                "created_at": t.get("created_at", ""),
                "likes":      t.get("favorites", 0),
                "retweets":   t.get("retweets", 0),
                "url":        f"https://twitter.com/{screenname}/status/{t.get('tweet_id', '')}"
            }
            for t in tweets
        ]
        return {"tweets": filtered, "count": len(filtered), "account": screenname}
    except Exception as e:
        return friendly_error(e, context="timeline")
```

Làm tương tự cho `social_search/tool.py`, `fetch/tool.py`, và tất cả tools mới.

#### 5.5 — Chạy UI

```bash
# Từ thư mục starter_v0/
streamlit run app.py

# Mở trình duyệt: http://localhost:8501
```

---

## 👤 NGƯỜI 2 — Tool Engineer & Prompt Optimizer

> **Nhiệm vụ cốt lõi:** Viết 2 tool mới (incl. bonus send), tối ưu system_prompt + tools.yaml qua 3 vòng.

### Giai đoạn 1 | Phân tích baseline (1:15 – 1:30)

Nhận run JSON từ Người 1, đọc và ghi chép:

```
Với mỗi case FAIL:
- actual_tool_calls: agent đã gọi gì?
- expect.tool_calls: đáng lẽ phải gọi gì?
- failures + observed_mismatch: lý do cụ thể

→ Ghi ra: Giả thuyết v1, v2, v3 trước khi sửa
```

---

### Giai đoạn 2 | Viết Tool mới #1: `send` với confirmation (1:30 – 2:00)

File: `tools/send/TOOL.md`

```markdown
---
name: send
version: 1.0.0
author: Người 2
---

# Send Tool — Gửi tin nhắn lên Telegram

## Mô tả
Gửi nội dung text lên Telegram channel. 
QUAN TRỌNG: Luôn gọi với confirmed=false trước để xác nhận với user, 
chỉ gửi thật khi confirmed=true.

## Parameters
- `text` (string, required): Nội dung cần gửi
- `confirmed` (bool, default false): Chỉ gửi khi true

## Flow bắt buộc
1. Gọi send(text="...", confirmed=false) → hiện preview cho user
2. User xác nhận → gọi send(text="...", confirmed=true) → gửi thật
```

File: `tools/send/tool.py`

```python
import os, requests

def run(text: str, confirmed: bool = False) -> dict:
    """
    Gửi tin nhắn lên Telegram. Luôn hiện confirmation trước khi gửi.
    confirmed=false: chỉ preview, chưa gửi
    confirmed=true: gửi thật
    """
    if not confirmed:
        # Bước 1: Hiện preview, yêu cầu xác nhận
        preview = text[:200] + "..." if len(text) > 200 else text
        return {
            "status": "pending_confirmation",
            "preview": preview,
            "message": (
                f"Bạn có chắc muốn gửi nội dung sau lên Telegram không?\n\n"
                f"---\n{preview}\n---\n\n"
                f"Trả lời 'có' hoặc 'yes' để xác nhận gửi."
            ),
            "requires_confirmation": True
        }
    
    # Bước 2: Gửi thật khi confirmed=True
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_id:
        return {"error": "Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env"}
    
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()
        
        if result.get("ok"):
            return {
                "status": "sent",
                "message_id": result["result"]["message_id"],
                "chat_id": chat_id,
                "text_preview": text[:100]
            }
        else:
            return {"error": result.get("description", "Telegram API lỗi không rõ")}
    
    except requests.exceptions.Timeout:
        return {"error": "Timeout khi gửi lên Telegram"}
    except Exception as e:
        return {"error": str(e)}
```

---

### Giai đoạn 3 | Viết Tool mới #2: `lookup` nâng cao qua Tavily (2:00 – 2:20)

> Tool `lookup` mặc định trong repo dùng Tavily. Nếu chưa có, implement như sau:

File: `tools/lookup/tool.py`

```python
import os, requests

def run(query: str, topic: str = "general", timeframe: str = "month", max_results: int = 5) -> dict:
    """
    Tìm kiếm web qua Tavily API.
    topic: 'general' hoặc 'news'
    timeframe: 'day', 'week', 'month', 'year'
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return {"error": "Thiếu TAVILY_API_KEY trong .env"}
    
    # Map timeframe sang days
    timeframe_map = {"day": 1, "week": 7, "month": 30, "year": 365}
    days = timeframe_map.get(timeframe, 30)
    
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "topic": topic,          # general hoặc news
                "days": days,
                "max_results": max_results,
                "include_answer": True,  # Tavily tổng hợp câu trả lời ngắn
                "include_raw_content": False  # Không cần raw HTML
            },
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        
        # === LỌC OUTPUT: chỉ lấy những gì cần ===
        results = []
        for r in data.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:500],  # giới hạn 500 ký tự mỗi kết quả
                "published_date": r.get("published_date", ""),
                "score": round(r.get("score", 0), 3)
            })
        
        return {
            "answer": data.get("answer", ""),   # Câu trả lời tổng hợp của Tavily
            "results": results,
            "query": query,
            "topic": topic
        }
    
    except Exception as e:
        return {"error": str(e)}
```

---

### Giai đoạn 4 | Đăng ký tools — 3 chỗ phải đồng bộ (2:20 – 2:30)

**`tools/__init__.py`** — thêm vào dict `TOOL_FUNCTIONS`:

```python
from tools.send.tool import run as send_run
from tools.lookup.tool import run as lookup_run
# ... các tool khác

TOOL_FUNCTIONS = {
    "clarify": clarify_run,
    "timeline": timeline_run,
    "social_search": social_search_run,
    "lookup": lookup_run,       # ← đảm bảo tên khớp với tools.yaml
    "fetch": fetch_run,
    "format": format_run,
    "send": send_run,           # ← tool mới
}
```

**`artifacts/tools.yaml`** — thêm block cho `send`:

```yaml
- name: send
  description: >
    Gửi nội dung text lên Telegram channel.
    QUAN TRỌNG: Luôn gọi với confirmed=false trước để hiện preview và xác nhận với user.
    Chỉ gọi lại với confirmed=true sau khi user nói "có", "yes", hoặc xác nhận rõ ràng.
    KHÔNG BAO GIỜ gửi thẳng mà không hỏi xác nhận trước.
  parameters:
    type: object
    properties:
      text:
        type: string
        description: Nội dung cần gửi lên Telegram
      confirmed:
        type: boolean
        description: "false = hiện preview, true = gửi thật. Mặc định false."
    required:
      - text
```

> ⚠️ **Kiểm tra tên tool không đổi so với eval_base.json:**
> ```bash
> grep -o '"name": "[^"]*"' data/eval_base.json | sort -u
> ```

---

### Giai đoạn 5 | Tối ưu system_prompt.md và tools.yaml (song song chạy v1-v3)

**Nguyên tắc:** Mỗi version sửa đúng 1 thứ, ghi rõ hypothesis trước khi sửa.

#### Ví dụ các thay đổi có ý nghĩa:

**v1 — Thêm routing rule rõ ràng vào system_prompt.md:**
```markdown
## Tool routing rules
- Nếu user nhắc đến tên tài khoản (@username): dùng `timeline`
- Nếu user tìm theo từ khóa/chủ đề KHÔNG có tên account: dùng `social_search`
- Nếu user cần đọc nội dung 1 URL cụ thể: dùng `fetch`
- Nếu user cần tìm tin tức web rộng: dùng `lookup`
- Nếu request thiếu account hoặc URL rõ ràng: dùng `clarify` TRƯỚC
- Nếu user muốn gửi/đăng/post: dùng `send` với confirmed=false TRƯỚC KHI gửi
```

**v2 — Sửa description trong tools.yaml của tool bị nhầm nhiều nhất:**
```yaml
# Ví dụ: làm rõ sự khác biệt timeline vs social_search
- name: timeline
  description: >
    Lấy các bài đăng GẦN NHẤT của MỘT TÀI KHOẢN CỤ THỂ theo screenname.
    Dùng khi user hỏi về "bài đăng của @X", "X đã tweet gì", "feed của X".
    KHÔNG dùng khi user tìm theo keyword hoặc chủ đề — hãy dùng social_search.

- name: social_search
  description: >
    Tìm bài đăng theo TỪ KHÓA hoặc CHỦ ĐỀ, không cần biết tên tài khoản.
    Dùng khi user hỏi "tìm bài về AI", "trending về X", "bài viết nói về Y".
    KHÔNG dùng khi user đã nêu tên account cụ thể — hãy dùng timeline.
```

**v3 — Thêm few-shot example vào system_prompt.md:**
```markdown
## Ví dụ routing đúng
User: "tìm tweet của elon musk" → gọi timeline(screenname="elonmusk")
User: "tìm bài về AI Agent" → gọi social_search(query="AI Agent")
User: "đọc bài này cho tôi: https://..." → gọi fetch(url="https://...")
User: "đăng bản tin lên kênh" → gọi send(text="...", confirmed=false) trước
User: "tìm tin về AI hôm nay nhưng không rõ nguồn" → gọi clarify hỏi cụ thể hơn
```

---

## 👤 NGƯỜI 3 — Eval Designer & Report

> **Nhiệm vụ cốt lõi:** Thiết kế 10 eval cases chất lượng, điền version_log từ log thật, viết REPORT.md.

### Giai đoạn 1 | Viết 10 eval cases (0:55 – 2:00)

File: `data/eval_group.json`

Cần viết **5 single-turn + 5 multi-turn**, đúng schema sau:

```json
[
  {
    "id": "group_001",
    "phase": "B",
    "query": "...",
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [
        { "name": "tên_tool", "args": { "key": "value" } }
      ]
    },
    "metadata": {
      "what_it_tests": "Mô tả 1 câu case này kiểm tra điều gì"
    }
  }
]
```

**`failure_type` phải là 1 trong 6 giá trị:**

| Giá trị | Khi nào dùng |
|---|---|
| `wrong_tool` | Agent chọn sai tool |
| `wrong_arg_value` | Tool đúng nhưng argument sai giá trị |
| `wrong_boundary` | Agent làm vượt ra ngoài scope hợp lệ |
| `unnecessary_tool` | Agent gọi tool khi không cần |
| `out_of_scope` | Request nằm ngoài khả năng agent |
| `missing_info` | Thiếu info để xử lý, cần clarify |

#### 5 Single-turn cases (copy và điền giá trị thật):

```json
[
  {
    "id": "group_s01",
    "phase": "B",
    "query": "Cho tôi xem các bài đăng gần nhất của @OpenAI",
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [{ "name": "timeline", "args": { "screenname": "OpenAI" } }]
    },
    "metadata": { "what_it_tests": "Phân biệt timeline vs social_search khi có @username" }
  },
  {
    "id": "group_s02",
    "phase": "B",
    "query": "Tìm các bài viết trending về large language model tuần này",
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [{ "name": "social_search", "args": { "query": "large language model", "search_type": "Top" } }]
    },
    "metadata": { "what_it_tests": "Dùng social_search khi tìm theo keyword không có account" }
  },
  {
    "id": "group_s03",
    "phase": "B",
    "query": "Đọc nội dung trang này: https://openai.com/blog/gpt-4",
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [{ "name": "fetch", "args": { "url": "https://openai.com/blog/gpt-4" } }]
    },
    "metadata": { "what_it_tests": "Dùng fetch khi user cung cấp URL cụ thể" }
  },
  {
    "id": "group_s04",
    "phase": "B",
    "query": "Tìm tin tức về AI trong tuần qua",
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [{ "name": "lookup", "args": { "query": "AI news", "topic": "news", "timeframe": "week" } }]
    },
    "metadata": { "what_it_tests": "Dùng lookup với topic=news và timeframe=week" }
  },
  {
    "id": "group_s05",
    "phase": "B",
    "query": "Tìm bài đăng về AI",
    "failure_type": "missing_info",
    "expect": {
      "tool_calls": [{ "name": "clarify", "args": {} }]
    },
    "metadata": { "what_it_tests": "Dùng clarify khi query quá mơ hồ (không rõ Twitter hay web)" }
  }
]
```

#### 5 Multi-turn cases — dùng `turns` thay `query`:

```json
[
  {
    "id": "group_mt01",
    "phase": "B",
    "turns": [
      { "role": "user", "content": "Tìm bài của Elon" },
      { "role": "assistant", "content": "Bạn muốn tôi tìm theo tài khoản Twitter của Elon Musk (@elonmusk) hay tìm bài viết về ông ấy trên web?" },
      { "role": "user", "content": "Theo tài khoản Twitter của ông ấy" }
    ],
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [{ "name": "timeline", "args": { "screenname": "elonmusk" } }]
    },
    "metadata": { "what_it_tests": "Sau clarify, agent phải chọn đúng timeline thay vì social_search" }
  },
  {
    "id": "group_mt02",
    "phase": "B",
    "turns": [
      { "role": "user", "content": "Đăng bài này lên kênh: AI is changing the world" },
      { "role": "assistant", "content": "Bạn có chắc muốn gửi nội dung 'AI is changing the world' lên Telegram không?" },
      { "role": "user", "content": "Có, gửi đi" }
    ],
    "failure_type": "wrong_arg_value",
    "expect": {
      "tool_calls": [{ "name": "send", "args": { "text": "AI is changing the world", "confirmed": true } }]
    },
    "metadata": { "what_it_tests": "Sau confirmation, agent gọi send với confirmed=true" }
  },
  {
    "id": "group_mt03",
    "phase": "B",
    "turns": [
      { "role": "user", "content": "Cho tôi xem tin tức AI hôm nay" },
      { "role": "assistant", "content": "Bạn muốn tìm trên Twitter/X hay tìm tin tức web?" },
      { "role": "user", "content": "Trên web thôi" }
    ],
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [{ "name": "lookup", "args": { "query": "AI news today", "topic": "news", "timeframe": "day" } }]
    },
    "metadata": { "what_it_tests": "Sau clarify phân biệt Twitter vs web, agent chọn lookup" }
  },
  {
    "id": "group_mt04",
    "phase": "B",
    "turns": [
      { "role": "user", "content": "Fetch bài báo này rồi tóm tắt: https://techcrunch.com/ai-news" },
      { "role": "assistant", "content": "[kết quả fetch]" },
      { "role": "user", "content": "Bây giờ format thành digest gửi cho tôi" }
    ],
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [{ "name": "format", "args": {} }]
    },
    "metadata": { "what_it_tests": "Sau fetch, agent dùng format để trình bày kết quả thành digest" }
  },
  {
    "id": "group_mt05",
    "phase": "B",
    "turns": [
      { "role": "user", "content": "Tìm bài về crypto crash" },
      { "role": "assistant", "content": "Bạn muốn tìm trên Twitter hay trên web?" },
      { "role": "user", "content": "Cả hai" }
    ],
    "failure_type": "wrong_tool",
    "expect": {
      "tool_calls": [
        { "name": "social_search", "args": { "query": "crypto crash" } },
        { "name": "lookup", "args": { "query": "crypto crash", "topic": "news" } }
      ]
    },
    "metadata": { "what_it_tests": "Khi user muốn cả hai nguồn, agent gọi cả social_search lẫn lookup" }
  }
]
```

---

### Giai đoạn 2 | Chạy group eval và điền version_log (2:30 – 2:45)

**Chạy group eval:**
```bash
python run_eval.py \
  --provider openrouter \
  --version v3 \
  --suite group \
  --eval-cases data/eval_group.json

# Optional: extension eval
python run_eval.py \
  --provider openrouter \
  --version v3 \
  --suite extension \
  --eval-cases data/eval_research_extension.json
```

**Điền `artifacts/version_log.csv`** — lấy hash từ output của run_eval:

```csv
version,author,changed_artifact,artifact_version,prompt_hash,tools_hash,reason,hypothesis,metric_before,metric_after,run_file
v0,Nguoi1,baseline,,<copy hash từ run JSON>,<copy hash từ run JSON>,Chạy baseline để đo điểm ban đầu,N/A,0.00,0.XX,runs/v0_base_<timestamp>.json
v1,Nguoi2,tools.yaml,1.1,<hash>,<hash>,Description tool timeline và social_search quá giống nhau,Làm rõ description sẽ giảm wrong_tool routing,0.XX,0.XX,runs/v1_base_<timestamp>.json
v2,Nguoi2,system_prompt.md,1.2,<hash>,<hash>,Thiếu routing rule tường minh trong prompt,Thêm routing rule + clarify rule sẽ tăng accuracy,0.XX,0.XX,runs/v2_base_<timestamp>.json
v3,Nguoi2,system_prompt.md,1.3,<hash>,<hash>,Agent vẫn đôi khi gửi send không xác nhận,Thêm few-shot example về send flow sẽ fix lỗi này,0.XX,0.XX,runs/v3_base_<timestamp>.json
```

> 📌 `prompt_hash` và `tools_hash` lấy từ field `artifact_version` trong file `runs/*.json`.

---

### Giai đoạn 3 | Viết REPORT.md (3:20 – 3:50)

File: `artifacts/REPORT.md`

> ⚠️ **Quy tắc quan trọng:** Mọi số liệu phải copy từ `runs/*.json` thật. Không viết theo cảm giác.

```markdown
# Report — Research Agent Tool Eval — TEAM D2C401

## 1. Thành viên
| Tên | Vai trò | Đóng góp chính |
|---|---|---|
| [Người 1] | Infrastructure & API | Setup, tools core, chạy eval, transcript |
| [Người 2] | Tool Engineer | tools: send, lookup; tối ưu prompt/tools.yaml |
| [Người 3] | Eval & Report | 10 eval cases, version_log, report này |

## 2. Baseline v0

| Metric | Giá trị |
|---|---|
| case_accuracy | X.XX |
| tool_routing_accuracy | X.XX |
| argument_accuracy | X.XX |
| multiturn_accuracy | X.XX |

**Các lỗi quan sát từ `runs/v0_*.json`:**

| Case ID | Tool thực tế | Tool kỳ vọng | Loại lỗi |
|---|---|---|---|
| [case_id] | social_search | timeline | wrong_tool |
| [case_id] | lookup | clarify | wrong_boundary |

**Phân tích nguyên nhân:**
- [Viết 2-3 câu dựa trên `observed_mismatch` trong JSON]

## 3. Quá trình tối ưu

### v1 — [Tên thay đổi ngắn gọn]
- **Thay đổi:** [Chỉnh sửa gì trong file nào]
- **Giả thuyết:** [Tại sao nghĩ thay đổi này giúp ích]
- **Kết quả:** routing_accuracy: X.XX → X.XX | case_accuracy: X.XX → X.XX
- **Nhận xét:** [Giả thuyết đúng/sai? Tại sao?]

### v2 — [Tên thay đổi]
- **Thay đổi:** ...
- **Giả thuyết:** ...
- **Kết quả:** ...
- **Nhận xét:** ...

### v3 — [Tên thay đổi]
- **Thay đổi:** ...
- **Giả thuyết:** ...
- **Kết quả:** ...
- **Nhận xét:** ...

## 4. Tool mới đã viết

### Tool `send` (Người 2)
- **Mục đích:** Gửi nội dung lên Telegram, có bước confirmation bắt buộc
- **Khi dùng:** User yêu cầu gửi/đăng/post nội dung
- **Hành vi confirmation:** Luôn gọi confirmed=false trước, chờ user xác nhận
- **Test case:** group_mt02

### Tool `lookup` (nâng cao) (Người 2)
- **Mục đích:** Tìm kiếm web qua Tavily với bộ lọc topic và timeframe
- **Output filtering:** Giới hạn 500 ký tự/kết quả, tổng hợp answer

## 5. Team eval cases

Tổng: 10 cases | 5 single-turn, 5 multi-turn
Kết quả v3: X/10 pass (X.XX accuracy)

| ID | Loại | failure_type | Pass v3? | Ghi chú |
|---|---|---|---|---|
| group_s01 | single | wrong_tool | ✅/❌ | |
| group_s02 | single | wrong_tool | ✅/❌ | |
| group_s03 | single | wrong_tool | ✅/❌ | |
| group_s04 | single | wrong_tool | ✅/❌ | |
| group_s05 | single | missing_info | ✅/❌ | |
| group_mt01 | multi | wrong_tool | ✅/❌ | |
| group_mt02 | multi | wrong_arg_value | ✅/❌ | |
| group_mt03 | multi | wrong_tool | ✅/❌ | |
| group_mt04 | multi | wrong_tool | ✅/❌ | |
| group_mt05 | multi | wrong_tool | ✅/❌ | |

## 6. Chat transcript

File: `transcripts/*.transcript.json`

| Lượt | Nội dung request | Tool được gọi | Kết quả |
|---|---|---|---|
| 1 | Request bình thường | [tool] | ✅ Đúng tool |
| 2 | Request thiếu info | clarify / [tool] | ✅/❌ |
| 3 | Gửi lên Telegram | send(confirmed=false) | ✅ Có confirm |

## 7. Điểm mạnh & điểm yếu sau v3

**Điểm mạnh:**
- [Ví dụ: routing giữa timeline và social_search cải thiện từ X% lên Y%]

**Điểm còn yếu:**
- [Ví dụ: multi-turn với context phức tạp vẫn đôi khi fail]

**Nếu có thêm thời gian:**
- [Ví dụ: Thêm tool policy, papers; thêm few-shot vào tools.yaml]
```

---

### Giai đoạn 4 | Checklist nộp bài (3:50 – 4:00)

```bash
# 1. Kiểm tra đủ files bắt buộc
echo "=== BẮT BUỘC ===" 
ls artifacts/system_prompt.md && echo "✓ system_prompt"
ls artifacts/tools.yaml && echo "✓ tools.yaml"
ls artifacts/version_log.csv && echo "✓ version_log"
ls artifacts/REPORT.md && echo "✓ REPORT"
ls data/eval_group.json && echo "✓ eval_group"
ls runs/*.json 2>/dev/null | wc -l | xargs echo "runs files:"
ls transcripts/*.json 2>/dev/null | wc -l | xargs echo "transcripts:"

# 2. Kiểm tra version_log có đủ 4 dòng (v0-v3)
echo "=== VERSION LOG ==="
cat artifacts/version_log.csv | wc -l  # phải là 5 (1 header + 4 versions)

# 3. Kiểm tra eval_group đủ 10 cases
echo "=== EVAL CASES ==="
python -c "import json; d=json.load(open('data/eval_group.json')); print(len(d), 'cases')"

# 4. Đảm bảo .env KHÔNG được commit
echo "=== .ENV CHECK ==="
grep -q ".env" .gitignore && echo "✓ .env trong gitignore" || echo "⚠️ THÊM .env vào .gitignore NGAY"

# 5. Kiểm tra tool mới đăng ký đúng
echo "=== TOOL REGISTRY ==="
grep "send" tools/__init__.py && echo "✓ send trong __init__"
grep "send" artifacts/tools.yaml | head -1 && echo "✓ send trong tools.yaml"

# 6. Không sửa eval_base.json
echo "=== EVAL BASE INTEGRITY ==="
git diff data/eval_base.json 2>/dev/null && echo "✓ eval_base không thay đổi" || echo "eval_base chưa track bởi git (ok nếu chưa init)"
```

---

## 🏆 Bonus — Nếu còn thời gian (điểm thưởng cao)

Để nhận **điểm bonus tối đa**, nhóm cần làm CẢ HAI:

### Bonus A: Thêm ≥3 tool mới (Người 2 dẫn, mọi người hỗ trợ)

| Tool | Mô tả | API cần |
|---|---|---|
| `policy` | Tìm trong `company_policy/` markdown nội bộ | Không cần API ngoài |
| `papers` | Tìm paper trên arXiv | arXiv API (miễn phí) |
| `paper_text` | Tải PDF arXiv và trích text | PyMuPDF hoặc pdfplumber |
| `summarize` | Tóm tắt danh sách bài thành digest | Dùng lại LLM trong agent |

**Template `policy` tool (không cần API):**
```python
import os, glob
from pathlib import Path

def run(query: str) -> dict:
    """Tìm kiếm trong company_policy/ markdown files."""
    policy_dir = Path("company_policy")
    if not policy_dir.exists():
        return {"error": "Thư mục company_policy/ không tồn tại"}
    
    results = []
    query_lower = query.lower()
    for md_file in policy_dir.glob("**/*.md"):
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        if query_lower in content.lower():
            # Tìm đoạn chứa keyword
            lines = content.split("\n")
            matches = [l for l in lines if query_lower in l.lower()]
            results.append({
                "file": str(md_file),
                "matches": matches[:3],  # tối đa 3 dòng match
                "excerpt": "\n".join(matches[:3])
            })
    
    if not results:
        return {"message": f"Không tìm thấy thông tin về '{query}' trong company policy"}
    return {"results": results, "query": query, "found_in": len(results)}
```

### Bonus B: UI Streamlit

> UI đã được Người 1 build đầy đủ ở **Giai đoạn 5** bên trên (`app.py` + `ui/error_handler.py`).  
> Để tính bonus, đảm bảo `app.py` có thể chạy được với `streamlit run app.py`.

```bash
streamlit run app.py
```

---

## 🗓️ Timeline chi tiết

| Thời gian | Người 1 | Người 2 | Người 3 |
|---|---|---|---|
| 0:00 – 0:25 | Setup môi trường, lấy tất cả API keys | Đọc README, hiểu cấu trúc tools | Đọc eval_base.json, lên ý tưởng 10 eval cases |
| 0:25 – 1:15 | Implement & debug 3 tools core (timeline, social_search, fetch) | Review code tools của P1, chuẩn bị viết tool mới | Viết 5 single-turn eval cases |
| 1:15 – 1:30 | Chạy baseline v0, chia sẻ kết quả với P2 | Phân tích run JSON baseline, lập giả thuyết v1-v3 | Viết 5 multi-turn eval cases |
| 1:30 – 2:20 | **Dựng UI `app.py` + `ui/error_handler.py`** | Viết tool `send` có confirmation | Hoàn thiện 10 cases, validate schema JSON |
| 2:00 – 2:20 | **Áp dụng error_handler vào toàn bộ tools** | Viết tool `lookup` nâng cao + đăng ký | Bắt đầu phác thảo REPORT |
| 2:20 – 2:30 | Chạy v1, v2 (khi P2 sửa xong từng version) | Sửa tools.yaml + system_prompt v1→v2 | Điền version_log từng phần |
| 2:30 – 2:45 | Chạy v3 + group eval, test UI cuối | Sửa system_prompt v3, review lần cuối | Chạy group eval, ghi kết quả vào log |
| 2:45 – 3:20 | Chat live qua UI, lưu transcript | Review transcript, gợi ý cải thiện thêm | Viết REPORT.md từ log thật |
| 3:20 – 3:50 | Parse runs ra CSV, deploy thử Streamlit | Viết bonus tools nếu kịp | Hoàn thiện REPORT, điền version_log đầy đủ |
| 3:50 – 4:00 | Chạy checklist, commit, push | Final review code + TOOL.md | Final review toàn bộ, đảm bảo không nộp .env |

---

## 🚨 Lỗi phổ biến — Phải tránh

| Lỗi | Hậu quả | Cách tránh |
|---|---|---|
| Sửa `data/eval_base.json` | Mất điểm eval | Không bao giờ chạm file này |
| Đổi tên tool, chỉ sửa 1 trong 3 chỗ | Eval báo `not declared`, chấm sai toàn bộ | Sync: `tools.yaml` + `__init__.py` + `eval_base.json` |
| Nộp file `.env` | Lộ API key, vi phạm bảo mật | Kiểm tra `.gitignore` trước khi push |
| `version_log.csv` dùng hash tự đặt | Không thể verify, mất điểm | Copy hash từ output `run_eval.py` |
| `REPORT.md` viết theo cảm giác | Mất điểm report | Mọi số liệu lấy từ `runs/*.json` |
| Tool mới thiếu TOOL.md | Mất điểm tool documentation | Mỗi tool phải có TOOL.md đầy đủ |
| Quên chạy `chat.py` | Thiếu transcript → mất điểm | Ưu tiên làm sớm ở giai đoạn 2:45 |
| eval_group.json < 10 cases | Mất điểm team eval | Người 3 hoàn thành trước 2:30 |
| `send` gửi không hỏi xác nhận | Mất điểm bonus send | Luôn có bước confirmed=false trước |

---

*Commit thường xuyên để mỗi người có lịch sử đóng góp. Nếu gặp lỗi API, kiểm tra `.env` trước khi debug code.*