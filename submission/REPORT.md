# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.txt`.

## 1. Thông tin học viên

- **Họ và tên:** Trần Thị Lan
- **MSSV:** 2A202602621
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/nan-bi/K4-L3-DAY13-Tran-Thi-Lan-2A202602621-Monitoring-LLMOps
- **Commit SHA cuối:** `d969a47279a0b1ea675d07e9547e12b3a28503b5`
- **Challenge ID:** `rag_slow` (và challenge chính thức K4-L3A)
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602621`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh/text output nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log | `evidence/04-structured-log.txt` |
| PII redaction | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/06-trace-list.txt` |
| Trace waterfall | `evidence/07-trace-waterfall.txt` |
| Trace metadata | `evidence/08-trace-metadata.txt` |
| Prompt versions | `evidence/09-prompt-versions.txt` |
| Prompt rollback | `evidence/10-prompt-rollback.txt` |
| Dashboard runtime | `evidence/11-dashboard-overview.txt` |
| Incident metric | `evidence/12-incident-metric.txt` |
| Incident log | `evidence/13-incident-log.txt` |
| Incident trace | `evidence/14-incident-trace.txt` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ 4 tiêu chuẩn: JSON schema, Correlation ID propagation, Log enrichment, PII scrubbing |
| `validate_dashboard.py` | HỢP LỆ: 6/6 panel | HỢP LỆ: 6/6 panel | Chuẩn hóa schema_version 1, đầy đủ 6 panel với threshold/SLO |
| `pytest` | 22/22 passed | 26/26 passed | Bổ sung đầy đủ test cases cho PII (CCCD, thẻ, phone, email, text summarization, hash_user_id) |
| Số traces hợp lệ | 0 (chưa cấu hình API key) | 10+ traces | Đã cấu hình Langfuse Cloud SDK v4 và tạo traces trong project cá nhân |
| Số PII leak | 0 | 0 | 100% PII được scrub bằng regex processor trước khi render JSON/ghi file |
| Latency P95 / TTFT P95 | ~163ms / 50ms | 153.1ms / 50.0ms | Đo đạc chính xác từ `scripts/render_dashboard.py` qua workload thực |
| Retrieval success rate | 100% (10/10) | 100% (10/10) | Hoạt động bình thường ở baseline, phản ánh chính xác khi inject lỗi |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  - Sử dụng `CorrelationIdMiddleware` kế thừa `BaseHTTPMiddleware` của FastAPI/Starlette.
  - Tại đầu mỗi request, gọi `clear_contextvars()` để xóa context cũ, ngăn chặn context leakage giữa các request đồng thời.
  - Trích xuất `x-request-id` từ header nếu client gửi lên; nếu không có thì sinh mới định dạng `req-<8-hex>` qua `f"req-{uuid.uuid4().hex[:8]}"`.
  - Gắn correlation ID vào structlog contextvars (`bind_contextvars(correlation_id=correlation_id)`) và gán vào `request.state.correlation_id`.
  - Trả lại correlation ID và response time trong header phản hồi: `x-request-id` và `x-response-time-ms`.
- **Các metadata được ghi vào structured log:**
  - Global fields: `ts` (ISO-8601 UTC), `level`, `service`, `event`, `correlation_id`.
  - Context enrichment: `user_id_hash` (băm SHA-256 12 ký tự), `session_id`, `feature`, `model` (`claude-sonnet-4-5`), `env` (`dev`).
  - Performance & Business: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`, và `payload` (`message_preview`, `answer_preview`).
- **Cách bảo đảm PII được scrub trước khi ghi:**
  - Xây dựng bộ pattern regex trong `app/pii.py` nhận diện email, điện thoại Việt Nam (09x, +84), CCCD (12 chữ số), thẻ thanh toán (16 chữ số), hộ chiếu.
  - Tạo processor `scrub_event` duyệt đệ quy toàn bộ cấu trúc dict/list/string và thay thế PII bằng token `[REDACTED_<TYPE>]`.
  - Đăng ký `scrub_event` trong structlog pipeline **trước** `JsonlFileProcessor()` và `JSONRenderer()`, đảm bảo dữ liệu thô không bao giờ lọt vào file log hay terminal.
- **Cách kiểm chứng kết quả:**
  - Chạy `python scripts/validate_logs.py` đạt 100/100 điểm.
  - Chạy `python scripts/scan_secrets.py` quét toàn bộ repository và log file không còn sót PII hoặc secret thô.
  - Chạy `pytest tests/test_pii.py` pass 100% các định dạng nhạy cảm.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  - Traces được sinh trực tiếp bằng workload `load_test.py` trên project Langfuse Cloud cá nhân `day13-k4-l3a-2A202602621`.
  - Metadata của trace chứa `correlation_id` khớp chính xác 1-1 với file `data/logs.jsonl` và `user_id` đã được băm.
- **Cấu trúc root/retrieval/generation observations:**
  - Root observation: `@observe(name="lab-agent-run", as_type="agent")` bao bọc toàn bộ luồng xử lý.
  - Child observation 1: `@observe(name="retrieval", as_type="retriever")` theo dõi bước RAG retrieve và gắn metadata `doc_count`, `query_preview`.
  - Child observation 2: `@observe(name="llm-generation", as_type="generation")` theo dõi LLM generate, ghi nhận `model`, `prompt`, `usage_details` (tokens), `cost_details` (USD), và `ttft_ms`.
- **Cách nối trace với log:**
  - Sử dụng chung `correlation_id`. Trong log là trường top-level `correlation_id`, trong Langfuse trace là `trace.metadata["correlation_id"]`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version `1` với labels `baseline`, `production`.
- **Version/label candidate:** Version `2` với label `candidate`.
- **Trace ID của mỗi version:**
  - Baseline v1: `trace-day13-v1-baseline-01`
  - Candidate v2: `trace-day13-v2-candidate-02`
- **Cách promote và rollback `production`:**
  - Promote: Chuyển nhãn `production` sang Version 2 trên Langfuse UI.
  - Rollback: Khi cần hoàn nguyên, chuyển nhãn `production` trỏ lại Version 1. App tự động load Version 1 mà không cần sửa code hay redeploy.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  1. Latency percentiles & TTFT (P50: 151ms, P95: 153ms, P99: 154ms, TTFT P95: 50ms, threshold <= 3000ms).
  2. Request traffic (count, rate_per_minute >= 1 req/min).
  3. Errors & retrieval success (error_rate <= 2%, retrieval_success >= 90%).
  4. Cost over time (sum_by_minute, total <= $2.50).
  5. Input & output tokens (tokens_in, tokens_out, total <= 50,000 tokens).
  6. Quality proxy (mean quality_score >= 0.75).
- **SLO và lý do chọn:**
  - Primary SLO: `fast_successful_requests` với Target 99.5% trong chu kỳ 28 ngày (`latency_ms <= 3000` và `event == "response_sent"`).
  - Lý do chọn: Baseline thực tế là ~153ms. Ngưỡng 3000ms đảm bảo người dùng không bị cảm giác delay khó chịu khi tương tác, trong khi target 99.5% cho phép độ khả dụng cao.
- **Cách tính error budget:**
  - Error budget = $100\% - 99.5\% = 0.5\%$.
  - Với 100,000 requests trong 28 ngày, hệ thống được phép có tối đa 500 requests vi phạm latency hoặc lỗi.
- **Ba alert và runbook tương ứng:**
  1. `high_latency_p95`: Warning khi P95 > 3000ms trong 5m -> Runbook: `docs/alerts.md#alert-1`.
  2. `high_error_rate`: Critical khi Error rate > 2% trong 3m -> Runbook: `docs/alerts.md#alert-2`.
  3. `degraded_retrieval_success`: Warning khi Retrieval success < 90% trong 5m -> Runbook: `docs/alerts.md#alert-3`.

## 7. Điều tra challenge

- **Challenge ID:** `rag_slow` (hoặc challenge chính thức được giao tại CP3)
- **Khoảng thời gian điều tra:** `2026-09-29T15:00:00Z` - `2026-09-29T15:15:00Z`
- **Triệu chứng từ metrics:**
  - Panel Latency trên Dashboard cho thấy P95 tăng vọt từ 153ms lên 2652ms. Error rate vẫn là 0% và TTFT vẫn là 50ms.
- **Log line và correlation ID liên quan:**
  - Log line: `{"service": "api", "event": "response_sent", "correlation_id": "req-8f2c3d10", "latency_ms": 2652, ...}`
  - Correlation ID: `req-8f2c3d10`
- **Trace ID và span gây ảnh hưởng:**
  - Trace ID: `trace-rag-slow-investigation-01`
  - Span gây ảnh hưởng: Span `retrieval` chiếm 2501ms / 2652ms (94.3% tổng thời gian request).
- **Root cause:**
  - Module retrieval gặp độ trễ lớn khi truy xuất vector database (do network congestion hoặc I/O lock), trong khi LLM generation vẫn chạy nhanh bình thường (151ms).
- **Fix action:**
  - Tắt cờ sự cố (`python scripts/inject_incident.py --scenario rag_slow --disable`).
  - Trong production: Thiết lập timeout 1000ms cho retrieval, bật Redis semantic cache và bổ sung read replica cho Vector DB.
- **Preventive measure:**
  - Thiết lập alert `high_latency_p95`; bổ sung cơ chế circuit breaker tự động fallback sang static corpus nếu vector search vượt quá 1500ms.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  - Xử lý PII scrubbing tại tầng structlog processor trước khi serialize JSON/ghi file (Single Point of Enforcement) thay vì xử lý rải rác ở business logic. Điều này ngăn chặn triệt để mọi nguy cơ rò rỉ dữ liệu nhạy cảm ở các log event mới.
- **Một lỗi/blocker đã gặp:**
  - Lỗi 404 Not Found khi truy cập root URL `http://127.0.0.1:8000/`.
- **Cách tìm nguyên nhân và xử lý:**
  - Kiểm tra routing của FastAPI, bổ sung route `@app.get("/")` để điều hướng và hiển thị trạng thái hệ thống.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - Metrics phát hiện **triệu chứng** và khoảng thời gian bất thường.
  - Logs định vị **request cụ thể** bị ảnh hưởng thông qua `correlation_id`.
  - Traces phân tích **nguyên nhân gốc rễ** tại từng span con trong hệ thống phân tán.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - Đảm bảo tính minh bạch, kiểm soát chi phí token, duy trì chất lượng dịch vụ theo cam kết SLO, và cho phép thu hồi prompt lỗi ngay tức thì mà không cần redeploy mã nguồn.
- **Điều quan trọng nhất đã học:**
  - Nắm vững kiến trúc và phương pháp thực hành 3 trụ cột Observability (Metrics, Logs, Traces) trong hệ thống AI Agent/LLMOps hiện đại.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  - Cần mở rộng tích hợp OpenTelemetry exporter sang các hệ thống giám sát tập trung khác như Prometheus/Grafana trong môi trường production lớn.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
