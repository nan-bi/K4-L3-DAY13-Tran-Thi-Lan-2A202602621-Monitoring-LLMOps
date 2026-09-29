# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `high_latency_p95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack (`#ai-ops-alerts`)
- SLI/SLO liên quan: `fast_successful_requests` (SLO Target 99.5%, latency <= 3000ms)
- Điều kiện và thời gian duy trì: Latency P95 vượt ngưỡng 3000ms kéo dài liên tục trên 5 phút.
- Ảnh hưởng tới người dùng: Người dùng phải chờ đợi lâu khi chat hoặc hỏi đáp, trải nghiệm phản hồi chậm trễ, nguy cơ timeout ở client.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard kiểm tra panel Latency (P50, P95, P99, TTFT) để xác định thời điểm bắt đầu tăng đột biến.
  2. Lọc `data/logs.jsonl` tìm các log có `latency_ms > 3000` để lấy `correlation_id` của request bị chậm.
  3. Mở Langfuse trace tương ứng với `correlation_id` đó để xem span nào đang chiếm nhiều thời gian nhất (Retrieval RAG hay LLM generation).
- Mitigation tạm thời:
  - Nếu RAG chậm: Bật cache cho retrieval hoặc tạm thời giảm số lượng tài liệu `top_k`, bypass vector search chậm nếu có fallback.
  - Nếu LLM generation chậm: Chuyển hướng traffic sang model backup hoặc hạ bớt `max_tokens`.
- Owner: `oncall-llmops`

## Alert 2

- Tên: `high_error_rate`
- Severity: `critical`
- Duration: `3m`
- Kênh thông báo: Slack (`#ai-ops-alerts`)
- SLI/SLO liên quan: Guardrail `error_rate_pct_max` (<= 2%) và SLO `fast_successful_requests`
- Điều kiện và thời gian duy trì: Tỷ lệ request thất bại (`event == "request_failed"`) vượt quá 2% trong cửa sổ 3 phút liên tiếp.
- Ảnh hưởng tới người dùng: Người dùng nhận phản hồi HTTP 500 hoặc thông báo lỗi hệ thống, không thể tiếp tục phiên chat.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Errors trên dashboard để phân loại `error_type` (ví dụ `RuntimeError`, `Timeout`, `HTTPException`).
  2. Lấy `correlation_id` từ các dòng `request_failed` trong `data/logs.jsonl` và xem stack trace / error detail trong payload.
  3. Tìm trace trên Langfuse để xác định span ném ra exception và input payload liên quan.
- Mitigation tạm thời:
  - Bật cơ chế circuit breaker / fallback trả câu trả lời an toàn mặc định cho người dùng.
  - Rollback prompt hoặc cấu hình vừa deploy nếu lỗi xuất hiện ngay sau đợt phát hành mới.
- Owner: `oncall-llmops`

## Alert 3

- Tên: `degraded_retrieval_success`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack (`#ai-ops-alerts`)
- SLI/SLO liên quan: Guardrail `retrieval_success_rate_pct_min` (>= 90%)
- Điều kiện và thời gian duy trì: Tỷ lệ truy xuất dữ liệu RAG thành công (`tool_success == true`) tụt xuống dưới 90% trong 5 phút.
- Ảnh hưởng tới người dùng: Chatbot không lấy được dữ liệu ngữ cảnh phù hợp, trả lời bằng câu fallback chung chung hoặc giảm độ chính xác của câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Errors và tỷ lệ `tool_success_rate_pct` trên dashboard.
  2. Lọc log có `tool_name == "retrieval"` và `tool_success == false` để kiểm tra thông điệp lỗi của Vector DB / RAG service.
  3. Mở trace span `retrieval` trên Langfuse để phân tích query đầu vào và trạng thái kết nối tới kho tri thức.
- Mitigation tạm thời:
  - Khởi động lại service RAG / Vector store instance hoặc chuyển sang search replica.
  - Tạm thời chuyển sang chế độ hybrid search hoặc sử dụng fallback knowledge base tĩnh.
- Owner: `oncall-rag`
