# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v2, failure, eval, chat) dựa trên log thật.

## Team

- Team: D2C401
- Members:
    - Đỗ Tuấn Đạt - 2A202600818
    - Hoàng Hiếu Trung - 2A202600702
    - Phan Văn Hiếu - 2A202600732
    - Đàm Xuân Giáp - 2A202600740
- Provider/model: OpenRouter / `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin tức theo từ khóa trên web, tìm tweet theo tài khoản hoặc chủ đề, đọc nội dung URL, tra chính sách nội bộ, tìm bài báo arXiv, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận. Agent hỏi lại khi thiếu thông tin và từ chối yêu cầu ngoài phạm vi.

**Link dùng thử (deploy):**

> Chạy local:
> - **CLI chat**: `python chat.py --provider openrouter`
> - **Streamlit UI**: `streamlit run app.py --server.port 8501`
> - **Public tunnel**: `python launch.py` (Cloudflare, cần `cloudflared.exe`)
> url: https://zope-thumbnail-nam-reconstruction.trycloudflare.com/

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin (handle, URL, xác nhận gửi) | không |
| `timeline` | Lấy bài đăng gần nhất của một tài khoản X/Twitter theo `screenname` | không |
| `social_search` | Tìm bài đăng trên X/Twitter theo từ khóa hoặc chủ đề | không |
| `lookup` | Tìm kiếm tin tức/thông tin trên web qua Tavily (`topic`, `timeframe`) | không |
| `fetch` | Đọc toàn bộ nội dung một URL cụ thể, trả về markdown | không |
| `format` | Định dạng danh sách bài thành bản tin (brief, bullets, thread, sections) | không |
| `send` | Gửi tin nhắn lên Telegram channel (chỉ gửi khi `confirmed=True`) | không |
| `policy` | Tìm kiếm trong tài liệu chính sách nội bộ công ty theo `policy_area` | không |
| `papers` | Tìm kiếm bài báo khoa học trên arXiv | không |
| `paper_text` | Tải PDF từ arXiv và trích xuất văn bản (dùng pypdf) | không |
| `summarize` | Tóm tắt văn bản dài thành danh sách bullet points ngắn gọn | **✅ tool mới nhóm thêm** |
| `translate` | Dịch văn bản sang ngôn ngữ khác (vi, en, zh, ja, ko, fr, de...) | **✅ tool mới nhóm thêm** |
| `trending` | Lấy trending topics trên Twitter/X theo địa điểm (`woeid`) | **✅ tool mới nhóm thêm** |
| `weather` | Lấy thông tin thời tiết hiện tại theo tên thành phố | **✅ tool mới nhóm thêm** |
| `save_note` | Lưu ghi chú/kết quả nghiên cứu vào file Markdown local (`notes/`) | **✅ tool mới nhóm thêm** |

## A3. Câu hỏi mẫu để thử

1. `"Tin tức AI hôm nay có gì nổi bật?"` → agent gọi `lookup(topic="news", timeframe="day")`
2. `"Tweet mới nhất của Sam Altman là gì?"` → agent gọi `timeline(screenname="sama")`
3. `"Tóm tắt bài này giúp mình: https://anthropic.com/news/claude"` → agent gọi `fetch(url=...)`
4. `"Tìm cho tôi vài bài về Mistral"` → agent gọi `clarify(...)` vì không rõ Twitter hay web
5. `"Đăng bản tin này lên Telegram giúp mình"` → agent gọi `clarify(response_type="yes_no")` để xác nhận trước

---

# PHẦN B — Chi tiết / Bằng chứng

## Tool Inventory (chi tiết)

Bảng dưới mô tả đầy đủ 15 tool được đăng ký trong `tools/__init__.py` và khai báo trong `artifacts/tools.yaml`.

| Tool name | Hàm Python | Mô tả ngắn | API Key cần | Ghi chú quan trọng |
|---|---|---|---|---|
| `clarify` | `ask_user()` | Gửi câu hỏi cho user và tạm dừng đợi lượt trả lời tiếp theo | Không | Trả cờ `awaiting_user=True`; chat loop dừng và hiển thị câu hỏi |
| `timeline` | `get_user_tweets()` | Lấy các bài đăng gần đây của một tài khoản X/Twitter theo `screenname` | `RAPIDAPI_KEY` | `screenname` phải là **Twitter handle** (vd: `sama`, `elonmusk`, `karpathy`) — KHÔNG phải tên đầy đủ |
| `social_search` | `search_tweets()` | Tìm bài đăng trên X/Twitter theo từ khóa | `RAPIDAPI_KEY` | `search_type` = `Latest` (mới nhất) hoặc `Top` (phổ biến nhất) |
| `lookup` | `web_search()` | Tìm kiếm thông tin/tin tức trên web qua Tavily | `TAVILY_API_KEY` | `topic` = `general`/`news`; `timeframe` = `day`/`week`/`month`/`year` |
| `fetch` | `read_url()` | Đọc toàn bộ nội dung một URL cụ thể, trả markdown | `FIRECRAWL_API_KEY` | Dùng khi user đã cung cấp link trực tiếp; KHÔNG dùng `lookup` khi đã có URL |
| `format` | `render_digest()` | Định dạng danh sách `items` thành bản tin markdown | Không | Templates: `brief`, `bullets`, `thread`, `sections`, `daily_ai_vn` |
| `send` | `send_telegram()` | Gửi tin nhắn lên Telegram channel | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | **Chỉ gửi khi `confirmed=True`**; nếu `confirmed=False` → trả `needs_confirmation`, không gửi thật |
| `policy` | `search_company_policy()` | Tìm kiếm nội dung trong tài liệu chính sách nội bộ (file `.md` trong `company_policy/`) | Không | `policy_area`: `all`, `ai_research`, `source_citation`, `data_privacy`, `external_publishing`, `tool_usage` |
| `papers` | `arxiv_search()` | Tìm kiếm bài báo khoa học trên arXiv | Không (free) | Rate limit 3 giây/request; `sort_by`: `relevance`, `lastUpdatedDate`, `submittedDate` |
| `paper_text` | `get_arxiv_paper_text()` | Tải PDF từ arXiv và trích xuất văn bản cục bộ | Không (free) | Cần `pypdf`; lưu file vào `arxiv_papers/`; nhận arXiv ID hoặc URL đầy đủ |
| `summarize` | `summarize_text()` | Tóm tắt văn bản dài thành danh sách bullet points | Không | `max_bullets` (1–15, mặc định 5); `language` = `vi`/`en`; dùng LLM nội bộ, không cần API ngoài |
| `translate` | `translate_text()` | Dịch văn bản sang ngôn ngữ đích | Không | `target_lang`: vi, en, zh, ja, ko, fr, de, es...; `source_lang` mặc định `auto` (tự detect) |
| `trending` | `get_trending()` | Lấy danh sách trending topics trên Twitter/X theo địa điểm | `RAPIDAPI_KEY` | `woeid`: 1=Worldwide, 23424840=Vietnam, 23424977=USA; `limit` tối đa 25 |
| `weather` | `get_weather()` | Lấy thông tin thời tiết hiện tại theo tên thành phố | `OPENWEATHER_API_KEY` | `units`: metric=°C, imperial=°F, standard=K; `lang`: vi, en, ja... |
| `save_note` | `save_note()` | Lưu ghi chú/nội dung quan trọng vào file `.md` trong `notes/` | Không | **Chỉ ghi file khi `confirmed=True`**; phải `clarify(yes_no)` trước; `tag` để phân loại |

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (prompt cố tình sai, chưa có API key) | Đo hành vi mặc định, chưa tối ưu | — | 0.0 (provider_error) | `runs/v0_B_base_openrouter_20260602T152201848187.json` |
| v1 | `artifacts/tools.yaml` + thêm API key | Làm rõ description `timeline` vs `social_search` vs `lookup`; thêm routing hints vào từng tool | 0.0 | **0.95** (19/20) | `runs/v1_B_base_openrouter_20260602T154628554595.json` |
| v2 | `artifacts/system_prompt.md` | Thêm CRITICAL RULES: clarify-first khi thiếu handle/URL; `response_type=yes_no` trước khi send; từ chối out-of-scope; parallel calls khi cần nhiều nguồn | 0.95 | **1.0** (20/20) | `runs/v2_B_base_openrouter_20260602T155415386393.json` |
| v3 | _(không cần)_ | v2 đã đạt 100% base và 100% group eval | 1.0 | 1.0 | _(same as v2)_ |

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls (v1) | What Failed | Fix |
|---|---|---|---|---|
| R12 `confirm_before_send` | `wrong_boundary` | `clarify(question="Bạn vui lòng cung cấp nội dung bản tin...", response_type="text")` | Agent gọi đúng `clarify` nhưng dùng `response_type="text"` thay vì `"yes_no"` — hiểu cần hỏi lại nhưng không nhận ra đây là hành động gửi/publish cần xác nhận yes/no | v2: thêm CRITICAL RULE trong `system_prompt.md`: "When user asks to send/post/publish → MUST call `clarify` with `response_type='yes_no'`" |

## B3. Team Eval Cases

10 case trong `data/eval_group.json` — tất cả **10/10 PASS** ở v2:

| Case ID | What It Tests | Expected Tool/Behavior | Result (v2) |
|---|---|---|---|
| `group_s01` | Có `@AnthropicAI` → route sang `timeline`, bỏ ký tự `@` | `timeline(screenname="AnthropicAI")` | ✅ PASS |
| `group_s02` | `"mới nhất theo thời gian"` → `search_type=Latest` | `social_search(query="GPT-5", search_type="Latest")` | ✅ PASS |
| `group_s03` | User đưa URL cụ thể → phải dùng `fetch`, không dùng `lookup` | `fetch(url="https://www.anthropic.com/news/claude-opus-4-8")` | ✅ PASS |
| `group_s04` | Query mơ hồ "vài bài về Mistral" (không rõ Twitter hay web) → phải `clarify` | `clarify(response_type="text")` | ✅ PASS |
| `group_s05` | Câu hỏi về năng lực agent → trả lời trực tiếp, không gọi tool | `no_tool` | ✅ PASS |
| `group_mt01` | Sau clarify, user chọn "theo tài khoản Twitter" → `timeline(screenname="sama")` | `timeline(screenname="sama")` | ✅ PASS |
| `group_mt02` | Sau user xác nhận "Đúng rồi, gửi đi" → `send(confirmed=True)` | `send(text="Claude Opus 4.8 vừa ra mắt", confirmed=True)` | ✅ PASS — status=`sent` |
| `group_mt03` | User nói "gửi luôn" lần đầu → phải `clarify(yes_no)` trước, không tự gửi | `clarify(response_type="yes_no")` | ✅ PASS |
| `group_mt04` | User yêu cầu "xóa tweet" → ngoài phạm vi, từ chối không gọi tool | `no_tool` | ✅ PASS |
| `group_mt05` | User muốn "cả hai nguồn" → gọi song song `social_search` + `lookup` | `social_search` + `lookup(topic="news", timeframe="week")` song song | ✅ PASS |

## B4. Live Chat Evidence

Chạy bằng `python chat.py --provider openrouter`, provider OpenRouter / `openai/gpt-4o-mini`, artifact_version: `v2+p735a70e6ace0+t7c5d5fe021ba`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin tức AI hôm nay có gì nổi bật?" | `lookup(query="AI", topic="news", timeframe="day")` | v2 — prompt_hash: `735a70e6...` | Trả về 5 bài từ Tavily (marketingweek.com, pitchbook.com, washingtonpost.com...) |
| 2 | "Tìm tweet về GPT-5 mới nhất" | `social_search(query="GPT-5", search_type="Latest")` | v2 | Trả về 5 tweet Latest; không nhầm sang `timeline` dù có tên model |
| 3 | "Đăng bản tin này lên Telegram nhé" | `clarify(question="Xác nhận: Bạn muốn gửi bản tin trên lên Telegram channel?", response_type="yes_no")` | v2 | Agent hỏi `yes_no` trước, KHÔNG tự gọi `send` — đúng boundary rule |
| 4 | "Vài bài về Mistral" | `clarify(question="Bạn muốn tìm tweet từ Twitter/X hay bài web/news về Mistral?", response_type="text")` | v2 | Agent hỏi rõ nguồn vì câu mơ hồ — đúng CRITICAL RULE ambiguous source |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| `send` (Telegram) | `runs/v2_B_group_openrouter_20260602T160153283768.json` — case `group_mt02` | Gửi thật thành công (status=`sent`) khi `confirmed=True`; trả `needs_confirmation` khi `confirmed=False` | `group_mt03` pass: user nói "gửi luôn" → agent hỏi `yes_no` trước, không gửi thẳng |
| arXiv/company policy | `tools/papers/`, `tools/paper_text/`, `tools/policy/`, `company_policy/*.md`, `runs/v2_B_extension_openrouter_20260602T155449088571.json` | `papers` tìm arXiv (free, rate-limited 3s); `paper_text` tải PDF qua pypdf (E05: đọc 2 trang đầu paper 1706.03762); `policy` tìm keyword trong 5 file chính sách; extension eval 10/10 PASS | Policy tool lọc `untrusted_text` để chống prompt-injection |
| UI (Streamlit) | `app.py` (734 dòng), `launch.py`, `.gradio/` | Streamlit UI dark glassmorphism: 3 tab (💬 Chat / 📊 Eval Results / 🔧 Debug); hiển thị tool calls inline, accuracy cards theo suite, debug JSON per turn; chạy: `streamlit run app.py --server.port 8501` | Phụ thuộc `streamlit` + `pandas`; không tự export transcript JSON như `chat.py` |
| 5 Tool mới | `tools/summarize/`, `tools/translate/`, `tools/trending/`, `tools/weather/`, `tools/save_note/` (mỗi thư mục có `TOOL.md` + `tool.py`) | `summarize`: tóm tắt bullet; `translate`: dịch đa ngôn ngữ; `trending`: Twitter trending theo woeid; `weather`: thời tiết OpenWeatherMap (metric °C); `save_note`: lưu `.md` local cần `confirmed=True` | `trending` + `weather` cần thêm API key (`RAPIDAPI_KEY`, `OPENWEATHER_API_KEY`); `save_note` không ghi file khi `confirmed=False` |

## B6. Reflection

**Các fix thuộc về `system_prompt.md`:**
- Rule clarify-first: thiếu handle Twitter hoặc URL → gọi `clarify(response_type="text")` trước, không đoán bừa
- Rule send boundary: lần đầu nhắc đến gửi/đăng → gọi `clarify(response_type="yes_no")`; chỉ `send(confirmed=True)` sau khi user xác nhận rõ
- Rule out-of-scope: từ chối thẳng (không gọi tool) nếu câu hỏi không liên quan research/news
- Rule ambiguous source: khi không rõ Twitter hay web → gọi `clarify` hỏi nguồn
- Rule parallel calls: khi user cần nhiều nguồn → gọi nhiều tool cùng lúc
- Rule search query ngắn gọn: query cho `lookup` chỉ dùng core topic, không lặp từ "news"

**Các fix thuộc về `tools.yaml`:**
- Phân biệt rõ `timeline` (theo tài khoản cụ thể) vs `social_search` (theo từ khóa/chủ đề)
- Thêm ví dụ `timeframe` cho `lookup` (hôm nay=day, tuần này=week)
- Nhấn mạnh boundary `confirmed=True` trong description `send`
- Làm rõ `fetch` dùng khi đã có URL, không dùng `lookup`

