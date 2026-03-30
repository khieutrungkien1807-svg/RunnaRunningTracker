# 🤖 CHUYÊN MỤC AC: AI AGENTS & AGENTIC SYSTEMS

*Autonomous Agents, ReAct Pattern, Planning Loops, Tool Use, Self-Correction*

**Tổng số sections: 18**

---

## 📋 Table of Contents
- [AC.1 — ĐỊNH NGHĨA & PHÂN LOẠI AGENT](#ac1)
- [AC.2 — REACT PATTERN (Reason + Act)](#ac2)
- [AC.3 — PLANNING AGENT](#ac3)
- [AC.4 — SELF-CORRECTION AGENT](#ac4)
- [AC.5 — CODE AGENT](#ac5)
- [AC.6 — RESEARCH AGENT](#ac6)
- [AC.7 — DATA ANALYST AGENT](#ac7)
- [AC.8 — DOCUMENT PROCESSING AGENT](#ac8)
- [AC.9 — CUSTOMER SUPPORT AGENT](#ac9)
- [AC.10 — WORKFLOW AUTOMATION AGENT](#ac10)
- [AD — MULTI-AGENT ORCHESTRATION](#ad)
- [AE — AI MEMORY & CONTEXT](#ae)
- [AF — TOOL USE & FUNCTION CALLING](#af)
- [AG — AGENTIC SAFETY & ALIGNMENT](#ag)

---

<a id="ac1"></a>
## AC.1 — ĐỊNH NGHĨA & PHÂN LOẠI AGENT

### Các loại Agent:
```
SIMPLE REFLEX AGENT
  Input → Condition-Action Rule → Output
  Dùng khi: task đơn giản, không cần lịch sử

GOAL-BASED AGENT
  Input + Goal → Planning → Action
  Dùng khi: cần đạt mục tiêu qua nhiều bước

UTILITY-BASED AGENT
  Input + Utility Function → Optimal Action
  Dùng khi: có nhiều lựa chọn, cần tối ưu hóa

LEARNING AGENT
  Input + Feedback → Improved Performance
  Dùng khi: môi trường thay đổi, cần adaptability

MULTI-AGENT SYSTEM
  Agent1 ↔ Agent2 ↔ Agent3 → Collective Intelligence
  Dùng khi: task quá phức tạp cho 1 agent
```

### RULES cho Agent Design:
```
RULE AC.1.1: Mỗi agent chỉ làm 1 việc tốt (Single Responsibility)
RULE AC.1.2: Agent phải có tool list rõ ràng — không dùng tool ngoài danh sách
RULE AC.1.3: Agent phải có stopping condition — tránh infinite loop
RULE AC.1.4: Agent phải log mọi action để audit
RULE AC.1.5: Agent phải handle failure gracefully — retry với backoff
RULE AC.1.6: Agent KHÔNG được tự cấp quyền cho chính nó
RULE AC.1.7: Human-in-the-loop cho action có side effects (xóa data, gửi email, payment)
```

---

<a id="ac2"></a>
## AC.2 — REACT PATTERN (Reason + Act)

```javascript
// ReAct Agent Core Loop
async function reactAgent(task, tools, maxIterations = 10) {
  const history = [];
  let iteration = 0;
  while (iteration < maxIterations) {
    iteration++;
    const thought = await llm.complete({
      system: AGENT_SYSTEM_PROMPT,
      messages: [...history, { role: "user", content: task }],
      tools: tools.map(t => t.schema)
    });
    history.push({ role: "assistant", content: thought });
    if (thought.stopReason === "end_turn" && !thought.toolUse) {
      return { result: thought.text, iterations: iteration, history };
    }
    if (thought.toolUse) {
      const tool = tools.find(t => t.name === thought.toolUse.name);
      if (!tool) {
        history.push({ role: "user", content: `[Tool Error] Tool "${thought.toolUse.name}" không tồn tại` });
        continue;
      }
      try {
        const result = await tool.execute(thought.toolUse.input);
        history.push({ role: "user", content: `[Tool Result] ${JSON.stringify(result)}` });
      } catch (err) {
        history.push({ role: "user", content: `[Tool Error] ${err.message} — retry nếu cần` });
      }
    }
  }
  return { result: "MAX_ITERATIONS_REACHED", iterations: iteration, history };
}
```

---

<a id="ac3"></a>
## AC.3 — PLANNING AGENT (Kế hoạch trước, thực thi sau)

```javascript
// Planning Agent: Plan → Execute → Verify
class PlanningAgent {
  constructor(llm, tools) {
    this.llm = llm;
    this.tools = tools;
    this.plan = [];
    this.results = [];
  }
  async plan(task) {
    const planResponse = await this.llm.complete({
      system: `Bạn là một planner. Nhận task và tạo danh sách các bước thực thi.`,
      messages: [{ role: "user", content: task }]
    });
    this.plan = JSON.parse(planResponse.text);
    return this.plan;
  }
}

---

<a id="ac4"></a>
## AC.4 — SELF-CORRECTION AGENT

```javascript
// Self-Correction Loop
async function selfCorrectAgent(task, tools, maxCorrections = 3) {
  let attempt = 0;
  let lastResult = null;
  let lastError = null;
  while (attempt < maxCorrections) {
    attempt++;
    try {
      const result = await reactAgent(task, tools);
      const evaluation = await evaluateResult(task, result, lastError);
      if (evaluation.isCorrect) {
        return { result, corrections: attempt - 1 };
      }
      lastError = evaluation.issues;
      task = enrichTaskWithFeedback(task, evaluation.issues);
    } catch (err) {
      lastError = err.message;
      task = `${task}\n\n[Lần trước lỗi: ${err.message}. Tránh lỗi này.]`;
    }
  }
  return { result: lastResult, corrections: maxCorrections, failed: true };
}
```

---

<a id="ac5"></a>
## AC.5 — CODE AGENT (Viết & Chạy Code)

```javascript
// Code Agent với sandbox execution
class CodeAgent {
  async solve(problem) {
    const plan = await this.llm.complete({ system: "Analyze problem.", messages: [{ role: "user", content: problem }] });
    const codeResp = await this.llm.complete({ system: "Write code.", messages: [{ role: "user", content: problem }] });
    const code = extractCode(codeResp.text);
    const execResult = await this.executor.run(code);
    if (execResult.error) return await this.debugAndRetry(problem, code, execResult.error);
    return { code, output: execResult.output, success: true };
  }
}
```

---

<a id="ac6"></a>
## AC.6 — RESEARCH AGENT (Tìm kiếm & Tổng hợp)

```javascript
// Research Agent với web search + synthesis
class ResearchAgent {
  async research(topic, depth = "medium") {
    const questionsRes = await this.llm.complete({ system: "Generate questions.", messages: [{ role: "user", content: topic }] });
    const questions = JSON.parse(questionsRes.text);
    const searchResults = await Promise.allSettled(questions.map(q => this.search.query(q)));
    const synthesis = await this.llm.complete({ system: "Synthesize research.", messages: [{ role: "user", content: JSON.stringify(searchResults) }] });
    return { topic, report: synthesis.text };
  }
}
```

---

<a id="ac7"></a>
## AC.7 — DATA ANALYST AGENT

```javascript
// Data Analyst Agent cho Supabase
class DataAnalystAgent {
  async analyze(question) {
    const { sql } = JSON.parse(await this.llm.complete({ system: "SQL gen.", messages: [{ role: "user", content: question }] }).text);
    const { data } = await this.db.rpc("execute_readonly_query", { query: sql });
    return { data, sql };
  }
}
```

---

<a id="ac10"></a>
## AC.10 — WORKFLOW AUTOMATION AGENT

```javascript
// Workflow Agent: tự động hóa chuỗi tasks
class WorkflowAutomationAgent {
  async runWorkflow(workflowName, context = {}) {
    // Workflow logic: Trigger -> Steps -> Results
    return { log: "Workflow completed", success: true };
  }
}

---

<a id="ad"></a>
# 🌐 CHUYÊN MỤC AD: MULTI-AGENT ORCHESTRATION

```javascript
class AgentOrchestrator {
  async orchestrate(complexTask) {
    const subtasks = await this.decomposeTask(complexTask);
    const assignments = await this.assignTasks(subtasks);
    const results = await this.executeAssignments(assignments);
    return await this.synthesize(complexTask, results);
  }
}
```

---

<a id="ae"></a>
# 🧠 CHUYÊN MỤC AE: AI MEMORY & CONTEXT MANAGEMENT

```javascript
class AgentMemory {
  constructor(supabase, embeddingModel) {
    this.shortTerm = [];
    this.workingMemory = {};
  }
  async storeLongTerm(content, metadata = {}) {
    const embedding = await this.embedder.embed(content);
    await this.db.from("agent_memories").insert({ content, embedding, metadata });
  }
}
```

---

<a id="af"></a>
# 🔧 CHUYÊN MỤC AF: TOOL USE & FUNCTION CALLING

```javascript
const supabaseQueryTool = {
  name: "query_database",
  description: "Query Supabase database.",
  execute: async ({ table, filters = {} }) => {
    let query = supabase.from(table).select("*");
    return await query;
  }
};
```

---

<a id="ag"></a>
# 🔒 CHUYÊN MỤC AG: AGENTIC SAFETY & ALIGNMENT

```javascript
class SafeAgent {
  async executeAction(action) {
    const risk = ACTION_RISK[action.type] || "high";
    if (risk === "critical") {
      const approved = await this.approval.request({ action });
      if (!approved) return { success: false, reason: "Rejected" };
    }
    return await this.agent.execute(action);
  }
}
```

```

```
