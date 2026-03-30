# 🤖 AUTONOMOUS COGNITION & EVOLUTION — MASTER INVENTORY (v5.0.0)

*Long-Term Memory, Multi-Agent Swarms, Self-Healing, Economic Autonomy & Predictive Intelligence*

---

## 📋 Table of Contents

- [NHÓM 1: MEMORY & CONTINUITY (EM, EY)](#memory)
- [NHÓM 2: SWARM ORCHESTRATION (EN, ET)](#swarm)
- [NHÓM 3: COGNITION & EVOLUTION (EO, EU, EZ)](#cognition)
- [NHÓM 4: SAFETY & HITL (EP, ES)](#safety)
- [NHÓM 5: PHYSICAL & COMPUTER USE (EQ, EX)](#physical)
- [NHÓM 6: ECONOMICS & PREDICTION (ER, FA, EV, FB)](#economics)

---

<a id="memory"></a>
## 🧠 NHÓM 1: MEMORY & CONTINUITY

### EM — LONG-TERM MEMORY & CONTEXT CONTINUITY
- **Rule 1: Vectorized Project State:** Bắt buộc sử dụng Vector DB (ChromaDB/Milvus). Khi kết thúc task, Agent phải nhúng (embed) các quyết định quan trọng thành Memory Chunks.
- **Rule 2: Automated Architecture Decision Records (ADR):** Tự động tạo file `ADR-00X.md` trong `/.docs/architecture/` khi có thay đổi cấu trúc lớn.
- **Rule 3: User Preference Sync:** Tự động thu thập thói quen code của người dùng vào `user-preferences.md`.

### EY — TIME-TRAVEL DEBUGGING
- **Rule 1: OS-Level Recording:** Sử dụng công cụ ghi lại thanh ghi/RAM (như `rr`) để tái tạo lỗi.
- **Rule 2: Shadow DOM & State Snapshotting:** Chụp ảnh (snapshot) trạng thái UI/Redux để mô phỏng 100% môi trường lúc crash.
- **Rule 3: Quantum-State Rollback:** Proxy database cho phép hoàn tác trạng thái DB về đúng 1 giây trước lỗi.

---

<a id="swarm"></a>
## 🐝 NHÓM 2: SWARM ORCHESTRATION

### EN — MULTI-AGENT SWARM ORCHESTRATION
- **Rule 1: Role-Based Agent Spawning:** Master Router tự động gọi `Architect_Agent`, `Dev_Agent`, và `Security_Agent` cho task lớn.
- **Rule 2: Asynchronous Peer Review:** Code phải pass qua `Reviewer_Agent` trước khi báo cáo hoàn thành.
- **Rule 3: Conflict Resolution:** `Lead_Agent` đưa ra quyết định cuối cùng khi các đặc vụ tranh cãi.

### ET — CROSS-PLATFORM SYMBIOSIS
- **Rule 1: Jira/Linear Mind-Meld:** Tự động hóa workflow: Jira Step -> Git Branch -> Scaffolding.
- **Rule 2: Figma-to-Code:** Quét thiết kế Figma và tự sinh React/Tailwind components.
- **Rule 3: Slack/Discord Persona:** Agent trực kênh báo lỗi, tự vá lỗi và tag kỹ sư liên quan.

---

<a id="cognition"></a>
## 🧬 NHÓM 3: COGNITION & EVOLUTION

### EO — META-COGNITION & SKILL AUTO-EVOLUTION
- **Rule 1: Document Ingestion Pipeline:** Tự động cào Doc mới từ Internet và cập nhật file `SKILL.md`.
- **Rule 2: Post-Mortem Auto-Correction:** Phân tích Stack Trace và tự tạo rule ngăn chặn lỗi tái diễn.
- **Rule 3: Dead Code & Skill Pruning:** Định kỳ đánh giá và cắt bỏ quy tắc/kỹ năng rác.

### EU — KNOWLEDGE DISTILLATION & FINE-TUNING
- **Rule 1: Automated Dataset Generation:** Trích xuất cặp [Lỗi + Giải pháp] thành JSONL.
- **Rule 2: Local LoRA Spawning:** Tự train model nhỏ (Llama/Qwen) qua Ollama khi dataset đủ lớn.
- **Rule 3: Self-Hosted Fallback:** Ưu tiên dùng model local để giảm chi phí API.

### EZ — SEMANTIC AST MORPHING
- **Rule 1: AST Manipulation:** Thao tác trực tiếp trên Cây cú pháp thay vì text.
- **Rule 2: Logic-Proof Isomorphism:** Một logic meta sinh code đồng nhất cho cả Backend và Frontend.
- **Rule 3: Auto-Transpilation Fallback:** Tự viết lại module bằng Rust/WASM nếu thư viện cũ dính mã độc.

---

<a id="safety"></a>
## 🚦 NHÓM 4: SAFETY & HITL

### EP — HUMAN-IN-THE-LOOP (HITL) & SAFETY
- **Rule 1: Tiered Permission Rings:** Phân cấp quyền (Xanh/Vàng/Đỏ) cho các hành động.
- **Rule 2: Blast Radius Containment:** Ép chạy mọi code thử nghiệm trong Docker cô lập.
- **Rule 3: Algorithmic Kill-Switch:** Nút ngắt khẩn cấp khi Agent rơi vào vòng lặp vô hạn.

### ES — ACTIVE THREAT NEUTRALIZATION
- **Rule 1: Zero-Day Auto-Patching:** Tự vá lỗi thư viện dựa trên tin bảo mật mới nhất API.
- **Rule 2: Dynamic Honeypots:** Tạo bẫy file/API để bắt hacker.
- **Rule 3: Code Deobfuscation:** Tự giải mã mã độc chèn vào hệ thống.

---

<a id="physical"></a>
## 🖥️ NHÓM 5: PHYSICAL & COMPUTER USE

### EQ — COMPUTER USE & VISUAL COGNITION
- **Rule 1: Visual QA Testing:** Dùng Screenshot so sánh chính xác với Figma.
- **Rule 2: Autonomous OS Navigation:** Điều khiển Terminal/GUI Desktop để cấu hình.
- **Rule 3: OCR & Unstructured Ingestion:** Bóc tách kiến trúc từ ảnh chụp mờ.

### EX — HARDWARE-IN-THE-LOOP (HITL)
- **Rule 1: Automated Firmware Flashing:** Nạp code trực tiếp xuống ESP32/Arduino.
- **Rule 2: Hardware Telemetry Loop:** Lắng nghe Serial, tự reset và sửa code phần cứng.
- **Rule 3: Physical Kill-Switch:** Ngắt điện nguồn khi thiết bị quá nhiệt qua rơ-le.

---

<a id="economics"></a>
## 💸 NHÓM 6: ECONOMICS & PREDICTION

### ER — FINANCIAL AUTONOMY & LLM ROUTING
- **Rule 1: Dynamic Model Routing:** Chọn model rẻ cho task dễ, đắt cho task khó.
- **Rule 2: Token Budget Burn-Down:** Circuit breaker khi vượt ngân sách hàng ngày.
- **Rule 3: Prompt Caching Maximization:** Tối ưu cache context lớn để giảm 90% chi phí.

### FA — AUTONOMOUS ECONOMIC ENTITIES (AEE)
- **Rule 1: Cloud Resource Arbitrage:** Tự di tản hệ thống sang Cloud rẻ nhất.
- **Rule 2: Freelancer Bounties:** Tự thuê người sửa bug nếu AI fail quá 5 lần.
- **Rule 3: Self-Sustaining Budgeting:** Quản lý ví API để duy trì sự tồn tại.

### EV — PREDICTIVE CHAOS & SHADOW SIMULATION
- **Rule 1: Shadow Workspace Instantiation:** Clone dự án ra môi trường bóng tối để stress test liên tục.
- **Rule 2: Automated Mutation Testing:** Cố tình phá code để kiểm thử độ chặt chẽ của bài Test.
- **Rule 3: Memory Leak Accelerated Aging:** Giả lập chạy 1 năm trong 5 phút tìm rò rỉ bộ nhớ.

### FB — PREDICTIVE COGNITION & ZERO-LATENCY
- **Rule 1: Cursor Trajectory Prediction:** Tải dữ liệu trước khi người dùng kịp click.
- **Rule 2: Speculative Database Execution:** Query ngầm dựa trên dự đoán hành vi.
- **Rule 3: Zero-Downtime Offline Fallback:** Tự đồng bộ ngầm khi có mạng.

---

<a id="safety-advanced"></a>
## 🛡️ NHÓM 7: AI SAFETY & BOUNDARIES (FC, FD)

### FC — AI HALLUCINATION & CONTEXT DECAY
- **Rule 1: Deterministic Grounding:** Cấm đoán mò; mọi hàm thư viện phải được xác thực qua Doc hoặc AST.
- **Rule 2: Context Pruning:** Tự động tóm tắt (Summarize) và dọn dẹp lịch sử chat sau mỗi 5 turns.
- **Rule 3: Confidence Mandate:** Trả lời "Tôi không biết" nếu độ tự tin dưới 90%.

### FD — PROMPT INJECTION & LLM SECURITY
- **Rule 1: Delimiter Fencing:** Bọc dữ liệu thô trong thẻ `<data_randomID>`.
- **Rule 2: Security Firewall Agent:** Mọi input thô phải qua Security_Agent quét Jailbreak.
- **Rule 3: Egress Sandboxing:** Chặn Internet trong môi trường Docker chạy code thử nghiệm.

---

<a id="alignment"></a>
## 🚀 NHÓM 8: ALIGNMENT & ROBUSTNESS (FE, FF)

### FE — MODEL COLLAPSE & DATA POISONING
- **Rule 1: Human Anchor Dataset:** Giữ 20% dữ liệu mỏ neo do người viết.
- **Rule 2: Entropy Monitoring:** Script chạy ngầm đo độ đa dạng của code; cảnh báo AI Slop.
- **Rule 3: Cross-Model Validation:** Dùng mô hình này code, mô hình kia review.

### FF — REWARD HACKING & MISALIGNMENT
- **Rule 1: Multi-Dimensional Constraints:** Tối ưu hiệu năng nhưng KHÔNG giảm bảo mật.
- **Rule 2: Constitutional AI:** Đối chiếu thay đổi với CONSTITUTION.md.
- **Rule 3: Blast Radius Limits:** Cấm thay đổi > 50 dòng hoặc xóa > 3 file mà không có confirm.
