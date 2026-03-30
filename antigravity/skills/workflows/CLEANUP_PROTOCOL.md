# CLEANUP_PROTOCOL.md

> **Phiên bản:** 1.0.0
> **Mục đích:** Đảm bảo môi trường làm việc luôn sạch sẽ, tối ưu dung lượng và bảo mật bằng cách dọn dẹp các tệp tạm thời sau khi sử dụng.

---

## 🧹 QUY TRÌNH DỌN DẸP BẮT BUỘC

### 1. Phân loại Tệp (File Classification)
Agent phải tự động xác định vòng đời của tệp:
- **Tệp Vĩnh viễn (Permanent):** Source code gốc, `PROJECT_MAP.md`, `README.md`, `push.bat`, `.gitignore`. -> **GIỮ LẠI**.
- **Tệp Tạm thời (Transient/Temporary):**
  - Các script test nhanh (vd: `test_api.py`, `debug_db.sql`).
  - Các file log tạm (vd: `temp_status.txt`, `npm-debug.log`).
  - Các bản nháp hoặc file trung gian (vd: `transformed_data.json`).
  - Thư mục build/cache sinh ra trong quá trình test. -> **XÓA SAU KHI DÙNG**.

### 2. Thời điểm Dọn dẹp (Trigger points)
- **Sau khi Test thành công:** Nếu một script test được tạo ra để xác minh một tính năng, ngay sau khi nhận được kết quả "PASS" và báo cáo cho User, Agent PHẢI chủ động xóa script đó.
- **Trước khi Kết thúc Phiên (Turn End):** Trước khi gửi câu trả lời cuối cùng, Agent quét lại thư mục làm việc và dọn dẹp các tệp không nằm trong cấu trúc dự án chính.
- **Trước khi Đẩy code (Pre-push):** Đảm bảo không có tệp rác nào lọt vào staging area.

### 3. Lệnh thực thi an toàn
- Sử dụng `Remove-Item` (PowerShell) hoặc `os.remove` (Python) với sự cẩn trọng cao độ.
- **LUÔN** kiểm tra đường dẫn tuyệt đối trước khi xóa để tránh xóa nhầm dữ liệu quan trọng.
- Nếu không chắc chắn về tầm quan trọng của file, hãy hỏi User: *"Tôi đã xong việc với file X, tôi có thể dọn dẹp nó không?"*

---

## 🚨 RÀNG BUỘC ĐẠO ĐỨC (AGENTIC CLEANLINESS)
Một Agent chuyên nghiệp không để lại "vết chân" (footprints) rác sau khi rời đi. Việc dọn dẹp là một phần của definition of done (Định nghĩa về sự hoàn thành).
