# 🧭 MASTER SKILLS ROUTER - SIÊU ĐIỀU PHỐI (250+ SKILLS)

> **MỤC ĐÍCH:** Bộ não trung tâm điều phối và truy cập kho trí tuệ 250+ kỹ năng.
> **QUY TẮC:** AI PHẢI đọc file này TRƯỚC khi thực hiện bất kỳ task nào.
> **CẬP NHẬT:** 2024-03-24 (v4.0.0 - SUPER-ROUTER)

---

## 📋 CHIẾN LƯỢC TRUY XUẤT SIÊU TỐC
Với kho 250+ skills, AI cần tuân thủ quy trình truy xuất "2 Tầng":

1. **Tầng 1: Nhận diện Category & Master Inventory**
   - Xác định Domain (Frontend, Backend, Security, specialized, etc.)
   - Tải file `master-inventory.md` của category đó.

2. **Tầng 2: Truy vấn Chuyên sâu (Search-First)**
   - Nếu cần tìm skill cụ thể trong Master Inventory: **Sử dụng lệnh `grep_search`** hoặc đọc nhanh Mục lục (TOC) ở đầu file Master.
   - Nếu skill nằm trong **Heavy Folder** (có Scripts/Assets): Tải trực tiếp folder đó.

---

## 🏗️ MA TRẬN PHÂN TẦNG (TIER SYSTEM)

| Tier | Ý Nghĩa | Phạm Vi |
|------|---------|---------|
| **TIER 1** | Đơn giản | CRUD, UI, Boilerplate, Blog, Landing Page |
| **TIER 2** | Bắt buộc | Security, Auth, Performance, SEO, Compliance |
| **TIER 3** | Nâng cao | Scalability, Microservices, Real-time, Optimization |
| **TIER 4** | Chuyên sâu | OS, Firmware, Quant, Space, Life-Critical |

---

## 🗂️ BẢN ĐỒ SIÊU HỆ THỐNG (MAPPING)

### 1. FRONTEND & UI (20+ Skills)
- **Cẩm nang tổng hợp:** `frontend/frontend-master-inventory.md`
- **Heavy Folders:** `frontend-design/`, `react-best-practices/`, `ui-ux-pro-max/`, `vercel-react-best-practices/`
- **Common Tags:** `[React, CSS, Tailwind, UI, UX, CRO, Performance]`

### 2. BACKEND & API (25+ Skills)
- **Cẩm nang tổng hợp:** `backend/backend-master-inventory.md`
- **Heavy Folders:** `api-patterns/`, `typescript-expert/`, `algorithmic-art/`
- **Common Tags:** `[Nodejs, API, Database, Auth, Typescript, Python, GraphQL]`

### 3. SECURITY & PENTEST (40+ Skills)
- **Cẩm nang tổng hợp:** `security/security-master-inventory.md`
- **Heavy Folders:** `active-directory-attacks/`, `aws-penetration-testing/`, `cloud-penetration-testing/`, `vulnerability-scanner/`
- **Common Tags:** `[Pentest, XSS, SQLi, Cloud-Security, Red-Team, Audit]`

### 4. WORKFLOWS & DEBUG (50+ Skills)
- **Cẩm nang tổng hợp:** `workflows/workflows-master-inventory.md` (Gồm TDD, Planning, Git rules)
- **Heavy Folders:** `git-pushing/`, `lint-and-validate/`, `skill-creator/`, `performance-profiling/`
- **Công cụ Core:** `workflows/debug-protocol.md`, `workflows/advanced-testing.md`
- **Common Tags:** `[Debug, Testing, Git, Workflow, Automation, Root-Cause]`

### 5. AI, AGENTS & DEEP TECH (25+ Skills)
- **SIÊU CẨM NĂNG AGENT:** `deep-tech/ai-agents-master-inventory.md` (Gồm AC, AD, AE, AF, AG)
- **Cẩm nang tổng hợp:** `deep-tech/deep-tech-master-inventory.md` (Agents, MCP, Identity)
- **Heavy Folders:** `agent-identifier/`, `mcp-builder/`, `subagent-driven-development/`
- **Common Tags:** `[AI-Agent, Multi-Agent, RAG, MCP, LLM, Memory, Safety]`

### 6. SPECIALIZED & LEGACY DOMAINS (350+ Skills)
- **SIÊU CẨM NANG (750KB):** `specialized/specialized-master-inventory.md`
- **DI SẢN NGUYÊN BẢN (174 Rules):** `specialized/gemini-core-rules-inventory.md` (Chứa 100% kho tàng từ file GEMINI.md cũ: Quantum, Hardware, LSM-Tree, Compliance, Security Vectors...)
- **Heavy Folders:** `loki-mode/`, `shopify-development/`, `game-development/`, `app-builder/`
- **Common Tags:** `[Shopify, E-commerce, Legacy-Rules, Hardware, Audio, Payment, PDF, XLSX]`

---

## 🎯 LOGIC ĐIỀU PHỐI TỰ ĐỘNG

```javascript
// Case: "Fix bug bảo mật cho hệ thống Shopify"
→ Tags: [Debug, Security, Shopify]
→ Load:
  1. workflows/debug-protocol.md (Rule số 1)
  2. security/security-master-inventory.md (Để tìm lỗi tương ứng)
  3. specialized/specialized-master-inventory.md (Tìm section "Shopify")
  4. specialized/shopify-development/ (Nếu cần script test)

// Case: "Tạo hệ thống RAG dùng MCP"
→ Tags: [AI, RAG, MCP, Backend]
→ Load:
  1. deep-tech/deep-tech-master-inventory.md (Agentic patterns)
  2. deep-tech/mcp-builder/ (Tools xây dựng MCP)
  3. backend/backend-master-inventory.md (Database & API)
```

---

## 🚨 QUY TẮC SIÊU TỐI ƯU (TOKEN SAVING)

1. **CHỈ đọc phần cần thiết:** Khi dùng Master Inventory, hãy dùng `view_content_chunk` hoặc `grep_search` để lấy đúng section cần dùng. Tránh nạp toàn bộ 750KB vào context một lúc trừ khi thực sự cần tổng phổ kiến thức.
2. **Context Pruning:** Xoá bỏ skills cũ khi đổi task.
3. **Always Load Workflows First:** Nếu gặp lỗi, quay lại đọc `debug-protocol.md`.

---

**Version:** 4.0.0 (Super-Router)
**Last Updated:** 2024-03-24
**Maintained by:** Antigravity AI Skills Brain

### 🚨 QUY TẮC DỌN DẸP (CLEANUP-BY-DEFAULT)
**MỆNH LỆNH TỐI CAO:** {Antigravity_ROOT}/skills/workflows/CLEANUP_PROTOCOL.md

Một Agent chuyên nghiệp không để lại file rác. Agent PHẢI chủ động dọn dẹp các tệp tạm, script test, và log trung gian ngay sau khi xác nhận task thành công. "Xong việc là phải Sạch".

### 7. ENTERPRISE GOVERNANCE & OPERATIONS (12 Domains)
- **SIÊU CẨM NANG (EA-EL):** specialized/enterprise-ops-master-inventory.md
  - Plugin Sandboxing, Webhook HMAC, API Versioning (EA)
  - Zero Trust, Secrets Rotation, Strict CSP (EB)
  - OpenTelemetry, Chaos Engineering, FinOps Tagging (EC)
  - ABAC, Maker-Checker, PII Masking (ED)
  - Strangler Fig, Anti-Corruption Layer, CDC Read-Only (EE)
  - XAI, Bias Mitigation, IP Sanitization (EF)
  - Hick Law, Error Recovery, Fitts Law (EG)
  - WORM Backups, Active-Active Failover, Air-Gapped Recovery (EH)
  - Streaming UI/SSE, Headless CMS, RAG State (EI)
  - TinyML, Wake-on-Event, FOTA Delta (EJ)
  - DePIN, PoPW, Micro-Transactions (EK)
  - Digital Twins, Graph Routing, Multi-Agent Orchestration (EL)
- **Common Tags:** [Enterprise, Governance, Platform, Legacy, AI-Ethics, IoT, Logistics]

### 8. AUTONOMOUS COGNITION & EVOLUTION (16 Domains)
- **SIÊU CẨM NĂNG (EM-FB):** deep-tech/autonomous-cognition-inventory.md
  - Long-Term Memory, Vectorized State, ADRs, User Prefs (EM, EY)
  - Swarm Orchestration, Peer Review, Conflict Resolution, P2P (EN, EW)
  - Meta-Cognition, Skill Auto-Evolution, Distillation, Fine-Tuning (EO, EU, EZ)
  - HITL Safety, Permission Rings, Kill-Switch, Threat Defense (EP, ES)
  - Computer Use, Visual QA, OS Navigation, Hardware-in-the-loop (EQ, EX)
  - Financial Autonomy, Price Arbitrage, Predictive Cache (ER, FA, EV, FB)
- **Common Tags:** [Cognition, Evolution, Swarm, Memory, Safety, Economics, Predictive]
