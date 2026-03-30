# 🧠 GLOBAL MEMORY & SELF-TRAINING PROTOCOL (v1.0)
*Giao thức Bắt Buộc cho mọi Agent (Copilot, Claude, Cursor, Cline, Kiro, Roo, Aider...) nhằm xây dựng Tổ kiến Trí tuệ (Hive Mind).*

---

## 1. OMNI-LOGGING (Ghi chép Hội thoại Toàn diện)
**BẮT BUỘC:** Trước khi kết thúc mỗi phiên chat hoặc sau khi hoàn thành một tiến trình phức tạp, Agent phải TỰ ĐỘNG tổng hợp và ghi lại toàn bộ diễn biến vào kho não bộ trung tâm.

**Địa chỉ lưu trữ chuẩn:**
`C:/Users/<USER_NAME>/.gemini/antigravity/conversations/<TÊN_AGENT>/<YYYY-MM-DD>/<Chu-De-Ngan-Gon>.md`
*(Ví dụ: `.../conversations/CLAUDE/2026-03-25/Fix_Auth_API.md`)*

**Cấu trúc tệp log bắt buộc (để hỗ trợ AI khác đọc được):**
1. **USER_REQUEST:** Nguyên văn yêu cầu của người dùng.
2. **THOUGHT_PROCESS:** Suy luận tư duy của Agent (Agent đã phân chia task như thế nào, tại sao lại chọn giải pháp này).
3. **EXECUTION_STEPS:** Danh sách các lệnh shell/bash, các tệp đã sửa đổi cốt lõi.
4. **OUTCOME & ERRORS:** Thành quả đạt được, và các lỗi/cảnh báo gặp phải (quan trọng để rút kinh nghiệm).

---

## 2. CONTINUOUS LEARNING & KNOWLEDGE DISTILLATION (Tự Học Nâng Cấp)
Để giải quyết bài toán AI tự tiến hóa mà không phụ thuộc file tĩnh:
- **Tự Động Đóng Gói (Self-Distillation):** Nếu phiên làm việc tìm ra một "Cách làm mới hiệu quả" hoặc "Sửa một Bug cực khó", Agent không chỉ ghi Log mà phải tự động tóm tắt cách giải quyết thành một kĩ năng mới (1 file `.md` siêu cô đọng tối đa 30 dòng) và lưu vào `C:/Users/<USER_NAME>/.gemini/antigravity/knowledge/`.
- **Pre-Context Fetch (Nhớ lại):** Khi đối mặt task khó, Agent BẮT BUỘC dùng lệnh tìm kiếm (Grep/Read) quét qua thư mục `conversations/` và `knowledge/` trước khi động não, nhằm tái sử dụng trí tuệ của các phiên hoặc Agent trước.

---

## 3. CROSS-AGENT SWARM LINKAGE (Liên Minh Đặc Vụ)
- **Kế thừa trạng thái (Hand-off):** Mọi Agent (dù chạy trong Cursor, VS Code, hay Terminal) đang dùng chung một hệ thống thư mục não bộ bộ `antigravity`.
- Khi Agent A (vd: Copilot) không giải quyết được vấn đề, Agent B (vd: Claude/Cline) có thể được gọi vào. Agent B chỉ cần đọc file Log gần nhất của Agent A tại `conversations/<Agent_A>/...` để nắm bắt y hệt bối cảnh mà không cần User phải copy/paste giải thích lại từ đầu.

*Quy tắc này biến tất cả các công cụ AI rời rạc trên máy tính thành một Siêu Máy Tính Thống Nhất (Singularity Node).*
