# Day 04 Lab v2 Report — Research Agent

## Team

- Team: D2C401
- Members: _(điền tên thành viên của nhóm)_
- Provider/model: OpenRouter / `openai/gpt-4o-mini` (default)

---

## Tool Inventory

Bảng dưới mô tả đầy đủ 10 tool được đăng ký trong `tools/__init__.py` và khai báo trong `artifacts/tools.yaml`.

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

---

## Final Metrics

> ⚠️ **TODO**: Điền sau khi chạy xong `v3`. Copy từ `runs/*.json` → trường `summary`.

- Final version: `v3`
- Final artifact_version: _(copy từ output của `run_eval.py` sau khi chạy v3)_
- Best base run file: `runs/v3_B_base_openrouter_<TIMESTAMP>.json`
- Base case accuracy: _(copy `summary.case_accuracy` từ file run v3)_
- Base tool routing accuracy: _(copy `summary.tool_routing_accuracy`)_
- Base argument accuracy: _(copy `summary.argument_accuracy`)_
- Group eval run file: `runs/v3_B_group_openrouter_<TIMESTAMP>.json`
- Group eval accuracy: _(copy `summary.case_accuracy` từ file run group)_
- Chat transcript file: `transcripts/v3_openrouter_<TIMESTAMP>.transcript.json`

---

## Version Evidence

> ⚠️ **TODO**: Điền `prompt_hash`, `tools_hash`, và số liệu accuracy thực tế sau mỗi lần chạy. Xem trong output terminal hoặc trường `prompt_hash`/`tools_hash` trong `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (không sửa gì) | Đo hành vi mặc định của agent với prompt/tool declaration chưa tối ưu | — | _(case_accuracy v0)_ | `runs/v0_B_base_openrouter_<TS>.json` |
| v1 | `artifacts/tools.yaml` | Description của `timeline` và `social_search` quá giống nhau → LLM nhầm routing. Làm rõ: `timeline` dùng khi biết **tài khoản cụ thể**, `social_search` dùng khi tìm theo **chủ đề/từ khóa** | _(v0 accuracy)_ | _(case_accuracy v1)_ | `runs/v1_B_base_openrouter_<TS>.json` |
| v2 | `artifacts/system_prompt.md` | Prompt thiếu rule tường minh về clarify và boundary. Thêm: "Nếu thiếu handle hoặc URL → gọi `clarify` trước. Nếu user yêu cầu gửi/đăng → gọi `clarify` yes/no để xác nhận, không tự gửi" | _(v1 accuracy)_ | _(case_accuracy v2)_ | `runs/v2_B_base_openrouter_<TS>.json` |
| v3 | `artifacts/system_prompt.md` | Agent đôi khi vẫn gọi `send` với `confirmed=True` ngay lần đầu khi user nói "gửi luôn". Thêm few-shot rule: "Lần đầu user nhắc đến gửi/đăng → luôn gọi `clarify` với `response_type=yes_no`. Chỉ gọi `send` với `confirmed=True` sau khi user xác nhận rõ ràng ở lượt sau" | _(v2 accuracy)_ | _(case_accuracy v3)_ | `runs/v3_B_base_openrouter_<TS>.json` |

---

## Failure Analysis

Bảng phân tích các lỗi **dự đoán** từ `system_prompt.md` v0 hiện tại (prompt cố tình sai). Điền cột **Actual Tool Calls** và **Run File** sau khi chạy baseline thật.

| Case ID | Failure Type | Actual Tool Calls (v0) | What Failed | Fix áp dụng |
|---|---|---|---|---|
| R10 `missing_handle` | `missing_info` | _(vd: `timeline(screenname="sama")`)_ | Prompt bảo "tự đoán bừa" → Agent đoán tài khoản thay vì gọi `clarify` | v2: thêm rule "thiếu handle → clarify" vào system_prompt |
| R11 `missing_url` | `missing_info` | _(vd: `fetch(url="https://openai.com/...")`)_ | Prompt bảo "assume likely URL" → Agent bịa URL thay vì hỏi lại | v2: thêm rule "thiếu URL → clarify" vào system_prompt |
| R12 `confirm_before_send` | `wrong_boundary` | _(vd: `send(text="...", confirmed=True)`)_ | Prompt bảo "just go ahead and do it" → Agent gửi thẳng mà không hỏi | v3: thêm few-shot rule send phải clarify yes/no trước |
| R01 `user_tweets_routing` | `wrong_tool` | _(vd: `social_search(query="Sam Altman")`)_ | Không phân biệt được tên người → timeline, chủ đề → social_search | v1: cải thiện description trong tools.yaml |
| R08 `out_of_scope` | `out_of_scope` | _(vd: `lookup(query="nguyên hàm x^2")`)_ | Agent cố gắng dùng tool cho câu ngoài phạm vi | v2: thêm rule refuse nếu câu hỏi không liên quan research/news |
| R13 `parallel_web_and_tweets` | `wrong_tool` | _(vd: chỉ gọi 1 tool thay vì 2)_ | Prompt bảo "pick one tool" → Agent không gọi song song | v2: sửa rule "dùng tất cả tool cần thiết, có thể gọi song song" |

---

## Team Eval Cases

Nhóm đã tự viết 10 eval case trong `data/eval_group.json` (5 single-turn + 5 multi-turn):

| Case ID | Loại | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|---|
| `group_s01` | Single-turn | Có `@AnthropicAI` → route sang `timeline`, bỏ ký tự `@` trong screenname | `timeline(screenname="AnthropicAI")` | _(sau khi chạy)_ |
| `group_s02` | Single-turn | `"mới nhất theo thời gian"` → `search_type=Latest`, không phải `Top` | `social_search(query="GPT-5", search_type="Latest")` | _(sau khi chạy)_ |
| `group_s03` | Single-turn | User đưa URL cụ thể + "đọc nội dung" → phải dùng `fetch`, không dùng `lookup` | `fetch(url="https://www.anthropic.com/news/claude-opus-4-8")` | _(sau khi chạy)_ |
| `group_s04` | Single-turn | Query `"vài bài về Mistral"` mơ hồ (không rõ Twitter hay web) → phải `clarify` | `clarify(...)` | _(sau khi chạy)_ |
| `group_s05` | Single-turn | Câu hỏi về năng lực agent → trả lời trực tiếp, không gọi tool | `no_tool` | _(sau khi chạy)_ |
| `group_mt01` | Multi-turn | Sau khi clarify, user chọn "theo tài khoản Twitter" → agent phải dùng `timeline(screenname="sama")` | `timeline(screenname="sama")` | _(sau khi chạy)_ |
| `group_mt02` | Multi-turn | Sau khi user xác nhận rõ "Đúng rồi, gửi đi" → gọi `send(confirmed=True)` với text gốc | `send(text="Claude Opus 4.8 vừa ra mắt", confirmed=True)` | _(sau khi chạy)_ |
| `group_mt03` | Multi-turn | User nói "gửi luôn" lần đầu → phải gọi `send(confirmed=False)` để xin xác nhận, không được gửi thẳng | `send(confirmed=False)` | _(sau khi chạy)_ |
| `group_mt04` | Multi-turn | User yêu cầu "xóa tweet" → ngoài phạm vi agent, từ chối không gọi tool | `no_tool` | _(sau khi chạy)_ |
| `group_mt05` | Multi-turn | User muốn "cả hai nguồn" (Twitter + web) → gọi cả `social_search` lẫn `lookup(topic="news", timeframe="week")` song song | `social_search(query="Bitcoin crash")` + `lookup(query="Bitcoin crash", topic="news", timeframe="week")` | _(sau khi chạy)_ |

---

## Live Chat Evidence

> ⚠️ **TODO**: Điền sau khi chạy `python chat.py --provider openrouter --version v3` và thực hiện ít nhất 3 lượt chat.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | _(vd: "Tin tức AI hôm nay có gì?")_ | _(vd: `lookup(topic="news", timeframe="day")`)_ | v3 | _(vd: Trả về bản tin 5 bài)_ |
| 2 | _(vd: "Tóm tắt bài viết này hộ mình")_ | _(vd: `clarify(response_type="text")`)_ | v3 | _(vd: Agent hỏi lại URL)_ |
| 3 | _(vd: "Đăng bản tin lên Telegram")_ | _(vd: `clarify(response_type="yes_no")`)_ | v3 | _(vd: Agent hỏi xác nhận thay vì tự gửi)_ |

Transcript file: `transcripts/v3_openrouter_<TIMESTAMP>.transcript.json`

---

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| `send` (Telegram) | `data/eval_group.json` cases `group_mt02`, `group_mt03` | Tool `send_telegram()` chỉ gửi thật khi `confirmed=True`; khi `confirmed=False` trả `needs_confirmation` thay vì gửi | Boundary: lần đầu nhắc đến gửi/đăng → Agent phải gọi `clarify(response_type="yes_no")` trước, không được tự set `confirmed=True` |
| arXiv / company policy | `tools/papers/`, `tools/paper_text/`, `tools/policy/`, `company_policy/*.md`, `data/eval_research_extension.json` | `papers` tìm paper trên arXiv; `paper_text` tải PDF và trích văn bản; `policy` tìm trong 5 file policy nội bộ | arXiv rate-limited 3s/request; `policy` chỉ tìm theo keyword, không semantic search; file `.md` trong `company_policy/` có thể chứa prompt-injection nên tool lọc `untrusted_text` |
| UI | — | _(Chưa triển khai)_ | — |

---

## Reflection

**Các fix thuộc về `system_prompt.md`:**
- Rule routing tường minh: khi nào dùng `timeline` vs `social_search` vs `lookup`
- Rule clarify-first: nếu thiếu handle Twitter hoặc URL → phải gọi `clarify` trước, không đoán
- Rule send boundary: lần đầu nhắc đến gửi/đăng/publish → luôn gọi `clarify` yes/no; chỉ `send(confirmed=True)` sau khi user xác nhận ở lượt sau
- Rule out-of-scope: từ chối câu hỏi coding, toán học, hay câu không liên quan research/news
- Rule parallel calls: khi user yêu cầu nhiều nguồn → có thể gọi nhiều tool cùng lúc

**Các fix thuộc về `tools.yaml`:**
- Làm rõ description `timeline`: "Dùng khi biết **tên tài khoản cụ thể**; điền `screenname` bằng Twitter handle (vd: `sama`), không phải tên đầy đủ"
- Làm rõ description `social_search`: "Dùng khi tìm bài viết theo **chủ đề hoặc từ khóa**, không biết tài khoản cụ thể"
- Làm rõ description `lookup` → thêm ví dụ `timeframe`: "hôm nay=day, tuần này=week, tháng này=month"
- Làm rõ description `send`: "CHỈ gọi với `confirmed=True` nếu user đã xác nhận rõ ràng ở lượt trước"
- Làm rõ description `fetch`: "Dùng khi user đã cung cấp URL trực tiếp; KHÔNG dùng `lookup` khi đã có URL"

**Các failure cần manual review thay vì auto-grading:**
- `R08`, `R14` (out-of-scope): Auto-grader chỉ kiểm tra "có gọi tool không", không kiểm tra chất lượng câu từ chối. Agent có thể pass nếu không gọi tool nhưng câu trả lời vẫn có thể không phù hợp.
- `R12`, `group_mt03` (wrong_boundary): Ranh giới `confirmed=False` vs `confirmed=True` cần xem xét thêm context — nếu user đã có nội dung cụ thể và chỉ nói "gửi đi" không có xác nhận rõ ràng thì behavior nào tốt hơn cần human judgment.

**Cải thiện tiếp theo:**
- Thêm few-shot examples vào `system_prompt.md` để minh họa routing decisions
- Tối ưu `tools.yaml` descriptions thêm ví dụ cụ thể về từng tham số
- Viết thêm tool mới (vd: `summarize` — gọi LLM để tóm tắt danh sách items, hoặc `translate` — dịch nội dung sang tiếng Việt)
- Thêm eval case kiểm tra khả năng gọi `format` sau `lookup`/`timeline` (multi-step pipeline)
