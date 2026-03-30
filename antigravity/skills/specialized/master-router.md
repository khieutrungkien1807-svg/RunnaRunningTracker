# 👑 THE ARCHITECT - MASTER ROUTER (MATRIX OF STANDARDS)

Đây là "Màng lọc Nhận thức" (Cognitive Filter) cao nhất để điều phối Agent.

## MA TRẬN PHÂN TẦNG (DEPTH-STRATIFICATION MATRIX)

### 1. NHÓM APP, WEB & HỆ THỐNG CỐT LÕI (Core Software Engineering)
- Tầng 1: Đơn giản & Hay gặp (Boilerplate/Common - MVC, DRY, SEO, UI responsive)
- Tầng 2: Bắt buộc (Mandatory/Security - OWASP, JWT, Rate Limiting, Backup)
- Tầng 3: Nâng cao (Advanced - Microservices, k8s, Redis, RabbitMQ, Zero-downtime)
- Tầng 4: Chuyên sâu cực độ (Deep/System - Custom GC, eBPF, Lock-free, Rust Engine)

### 2. NHÓM IOT & PHẦN CỨNG CHUYÊN SÂU (Hardware & Embedded)
- Tầng 1: Đơn giản (Sensors, I2C, SPI, MQTT)
- Tầng 2: Bắt buộc (Watchdog, OTA, TLS Hardware)
- Tầng 3: Nâng cao (Deep Sleep, FreeRTOS, Semaphores)
- Tầng 4: Chuyên sâu cực độ (Verilog FPGA, Clock Domain Crossing, MISRA-C)

### 3. NHÓM Y TẾ, NHÂN ĐẠO & NGƯỜI DÙNG (Human-Centric & Life-Critical)
- Tầng 1: Đơn giản (WCAG 2.1, i18n, Local Storage)
- Tầng 2: Bắt buộc (HIPAA/GDPR, Audit Logs, Encryption)
- Tầng 3: Nâng cao (HL7/FHIR, Mesh Network, CRDTs)
- Tầng 4: Chuyên sâu cực độ (IEC 62304 SaMD, Hard Fail-Safe, DSP BCI < 20ms)

### 4. NHÓM KINH TẾ, DỊCH VỤ & VẬN CHUYỂN (Economics & Logistics)
- Tầng 1: Đơn giản (Stripe integration, Cart management, Basic Booking)
- Tầng 2: Bắt buộc (Double-entry, Idempotency, ACID, Optimistic Locking)
- Tầng 3: Nâng cao (Dynamic Pricing, Route Optimization VRP, Event-driven inventory)
- Tầng 4: Chuyên sâu cực độ (HFT Zero-allocation, UTM 4D Trajectory)

---

## 🗂️ DIRECTORY TỔNG HỢP CÁC SKILLS HIỆN TẠI

- **[agent-identifier](./agent-identifier/SKILL.md)**: This skill should be used when the user asks to "create an agent", "add an agent", "write a subagent", "agent frontmatter", "when to use description", "agent examples", "agent tools", "agent colors", "autonomous agent", or needs guidance on agent structure, system prompts, triggering conditions, or agent development best practices for Claude Code plugins.
- **[brainstorming](./brainstorming/SKILL.md)**: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."
- **[claude-opus-4-5-migration](./claude-opus-4-5-migration/SKILL.md)**: Migrate prompts and code from Claude Sonnet 4.0, Sonnet 4.5, or Opus 4.1 to Opus 4.5. Use when the user wants to update their codebase, prompts, or API calls to use Opus 4.5. Handles model string updates and prompt adjustments for known Opus 4.5 behavioral differences. Does NOT migrate Haiku 4.5.
- **[create-pr](./create-pr/SKILL.md)**: Creates GitHub pull requests with properly formatted titles that pass the check-pr-title CI validation. Use when creating PRs, submitting changes for review, or when the user says /pr or asks to create a pull request.
- **[dispatching-parallel-agents](./dispatching-parallel-agents/SKILL.md)**: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies
- **[executing-plans](./executing-plans/SKILL.md)**: Use when you have a written implementation plan to execute in a separate session with review checkpoints
- **[finishing-a-development-branch](./finishing-a-development-branch/SKILL.md)**: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
- **[frontend-code-review](./frontend-code-review/SKILL.md)**: "Trigger when the user requests a review of frontend files (e.g., `.tsx`, `.ts`, `.js`). Support both pending-change reviews and focused file reviews while applying the checklist rules."
- **[frontend-design](./frontend-design/SKILL.md)**: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
- **[frontend-testing](./frontend-testing/SKILL.md)**: Generate Vitest + React Testing Library tests for Dify frontend components, hooks, and utilities. Triggers on testing, spec files, coverage, Vitest, RTL, unit tests, integration tests, or write/review test requests.
- **[receiving-code-review](./receiving-code-review/SKILL.md)**: Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation
- **[requesting-code-review](./requesting-code-review/SKILL.md)**: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
- **[seo-review](./seo-review/SKILL.md)**: Perform a focused SEO audit on JavaScript concept pages to maximize search visibility, featured snippet optimization, and ranking potential
- **[skill-creator](./skill-creator/SKILL.md)**: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Gemini CLI's capabilities with specialized knowledge, workflows, or tool integrations.
- **[skill-creator-1](./skill-creator-1/SKILL.md)**: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.
- **[skill-lookup](./skill-lookup/SKILL.md)**: Activates when the user asks about Agent Skills, wants to find reusable AI capabilities, needs to install skills, or mentions skills for Claude. Use for discovering, retrieving, and installing skills.
- **[subagent-driven-development](./subagent-driven-development/SKILL.md)**: Use when executing implementation plans with independent tasks in the current session
- **[systematic-debugging](./systematic-debugging/SKILL.md)**: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
- **[test-driven-development](./test-driven-development/SKILL.md)**: Use when implementing any feature or bugfix, before writing implementation code
- **[using-git-worktrees](./using-git-worktrees/SKILL.md)**: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
- **[using-superpowers](./using-superpowers/SKILL.md)**: Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions
- **[vercel-react-best-practices](./vercel-react-best-practices/SKILL.md)**: React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js code to ensure optimal performance patterns. Triggers on tasks involving React components, Next.js pages, data fetching, bundle optimization, or performance improvements.
- **[verification-before-completion](./verification-before-completion/SKILL.md)**: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
- **[web-design-guidelines](./web-design-guidelines/SKILL.md)**: Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices".
- **[writing-plans](./writing-plans/SKILL.md)**: Use when you have a spec or requirements for a multi-step task, before touching code
- **[writing-skills](./writing-skills/SKILL.md)**: Use when creating new skills, editing existing skills, or verifying skills work before deployment
- **[workflow-testing](./workflow-testing/SKILL.md)**: Workflow: Testing standards, Unit, E2E, UI, and Cypress/Vitest patterns.
- **[workflow-git](./workflow-git/SKILL.md)**: Workflow: Git conventions, branch management, release process, and push routines.
- **[workflow-debug](./workflow-debug/SKILL.md)**: Workflow: Systematic debugging, root cause analysis, error tracing.
- **[exascale-computing](./exascale-computing/SKILL.md)**: CJ: Exascale Computing & Supercomputing. MPI, NUMA, Job Scheduling, AI Leverage.
- **[green-computing](./green-computing/SKILL.md)**: CK: Green Computing & Carbon-Aware Scheduling.
- **[spatial-os](./spatial-os/SKILL.md)**: CL: Spatial OS Kernels & XR Compositors.
- **[agentic-protocols](./agentic-protocols/SKILL.md)**: CM: Meta-Rules & Agentic Protocols.
- **[astrodynamics-orbital](./astrodynamics-orbital/SKILL.md)**: CN: Astrodynamics & Orbital Mesh Networks.
- **[fully-homomorphic-encryption](./fully-homomorphic-encryption/SKILL.md)**: CO: Fully Homomorphic Encryption (FHE).
- **[neuromorphic-snn](./neuromorphic-snn/SKILL.md)**: CP: Neuromorphic Engineering & SNNs.
- **[topological-data-analysis](./topological-data-analysis/SKILL.md)**: CQ: Topological Data Analysis (TDA).
- **[compiler-mlir](./compiler-mlir/SKILL.md)**: CR: Compiler Infrastructure & MLIR.
- **[zero-knowledge-proofs](./zero-knowledge-proofs/SKILL.md)**: CS: Zero-Knowledge Proofs & Verifiable Computation.
- **[stochastic-superoptimization](./stochastic-superoptimization/SKILL.md)**: CT: Stochastic Superoptimization.
- **[photonic-computing](./photonic-computing/SKILL.md)**: CU: Photonic Computing & Optical Networks.
- **[legaltech-compliance](./legaltech-compliance/SKILL.md)**: CV: LegalTech & Automated Compliance.
- **[proptech-facility](./proptech-facility/SKILL.md)**: CW: PropTech & Smart Facility Management.
- **[omnichannel-retail](./omnichannel-retail/SKILL.md)**: CX: Omnichannel Retail & Supply Chain.
- **[govtech-civic](./govtech-civic/SKILL.md)**: CY: GovTech & Civic Infrastructure.
- **[generative-media](./generative-media/SKILL.md)**: CZ: Generative Media & Autonomous Studios.
- **[neuro-symbolic-ai](./neuro-symbolic-ai/SKILL.md)**: DA: Neuro-Symbolic AI & Automated Discovery.
- **[macro-economics-cbdc](./macro-economics-cbdc/SKILL.md)**: DB: Macro-Economics & CBDC Infrastructure.
- **[deep-space-networking](./deep-space-networking/SKILL.md)**: DC: Deep Space Networking & Off-World Infrastructure.
- **[internet-of-medical-things](./internet-of-medical-things/SKILL.md)**: DD: Internet of Medical Things (IoMT).
- **[humanitarian-resilience](./humanitarian-resilience/SKILL.md)**: DE: Humanitarian Tech & Disaster Resilience.
- **[autonomous-hyper-logistics](./autonomous-hyper-logistics/SKILL.md)**: DF: Autonomous Hyper-Logistics & UTM.
- **[algorithmic-economics](./algorithmic-economics/SKILL.md)**: DG: Algorithmic Economics & Tokenized Societies.
- **[materials-informatics](./materials-informatics/SKILL.md)**: DH: Materials Informatics & Metamaterials.
- **[plasma-physics-fusion](./plasma-physics-fusion/SKILL.md)**: DI: Plasma Physics & Fusion Reactor Control.
- **[cognitive-security](./cognitive-security/SKILL.md)**: DJ: Cognitive Security & Memetic Warfare.
- **[planetary-geoengineering](./planetary-geoengineering/SKILL.md)**: DK: Planetary Geoengineering & Biosphere Orchestration.
