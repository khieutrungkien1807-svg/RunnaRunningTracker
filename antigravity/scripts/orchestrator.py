import os
import sys
import uuid
import json
import hashlib
import logging

from collections import deque
import subprocess
from pathlib import Path
import re

# Thêm antigravity root vào path để import
PROJECT_ROOT = Path(r"c:\Users\<USER_NAME>\.gemini\antigravity")
sys.path.insert(0, str(PROJECT_ROOT))

# Import Adapter & Schema
from core.tracing import TracingService
from core.llm_client import LLMClient
from core.schemas import RouteDecision, ExecutionPlan, PlanStep
from core.schemas import TaskCompletionSpec, ArtifactCheck, ErrorDelta

# Phase 3 (Skill/Memory Hub)
from core.skill_store import SkillStore

# Architecture Upgrade Components (Task 13)
from core.id_utils import new_id, is_valid_time_sortable_id
from core.budget_guard import BudgetGuard, BudgetExceededError
from core.backup_manager import BackupManager
from core.slm_router import SLMRouter
from core.ast_analyzer import ASTAnalyzer

# v6.2 Learning Loop (Phase 1)
from core.failure_memory import FailureMemory

logger = logging.getLogger(__name__)

# --- CATEGORIES ---
AGENTS = {
    "architect": "Architect_Agent (System Design & Schema)",
    "developer": "Dev_Agent (Code Implementation)",
    "reviewer": "Reviewer_Agent (Code Review & Linting)",
    "security": "Security_Agent (Vulnerability Scan)",
    "debug": "Debugger_Agent (Root Cause Analysis)",
    "general": "General_Agent (Q&A & Support)",
    "frontend": "Frontend_Agent (React, CSS, UI)",
    "backend": "Backend_Agent (Node.js, Postgres)",
    "infra": "Infra_Agent (Docker, DevOps)"
}

class AntigravityOrchestrator:
    """
    Core Engine for Loki-mode (v6.0.0-SOLID-STATE).
    Phase 1: Observability & Structured Outputs
    Phase 2A: Vertical Slice Execution Planning
    Phase 2B: Deterministic Verification & Self-Healing Loop
    Phase 3: Actionable Intelligence & Skill Memory Routing
    Phase 4: Architecture Upgrade Integration (Task 13)
    """
    def __init__(self, notebook_id=None):
        self.notebook_id = notebook_id
        self.CONTEXT_WINDOW_SIZE = int(os.getenv("AG_CONTEXT_WINDOW", "5"))
        
        # Core components
        self.tracer = TracingService()
        self.llm = LLMClient(tracer=self.tracer)
        self.skill_store = SkillStore()
        
        # Architecture Upgrade Components (Task 13)
        self.budget_guard = BudgetGuard(
            max_steps=int(os.getenv("AG_MAX_STEPS", "50")),
            max_tokens=int(os.getenv("AG_MAX_TOKENS", "100000")),
            max_repair_attempts=int(os.getenv("AG_MAX_REPAIR_ATTEMPTS", "5")),
        )
        self.backup_manager = BackupManager()
        self.ast_analyzer = ASTAnalyzer()
        
        # v6.2 Learning Loop (Phase 1)
        failure_memory_path = PROJECT_ROOT / "brain" / "failure_memory.jsonl"
        self.failure_memory = FailureMemory(
            storage_path=failure_memory_path,
            ttl_days=int(os.getenv("AG_FAILURE_MEMORY_TTL_DAYS", "7")),
            max_entries=int(os.getenv("AG_FAILURE_MEMORY_MAX_ENTRIES", "1000"))
        )
        
        # Initialize SLMRouter if prototypes file exists
        prototypes_path = PROJECT_ROOT / "config" / "slm_prototypes.json"
        if prototypes_path.exists():
            self.slm_router = SLMRouter(prototypes_path=prototypes_path)
        else:
            logger.warning(f"SLM prototypes not found at {prototypes_path}, SLMRouter disabled")
            self.slm_router = None
        
        # Load constitution and master router for static prefix
        self._load_static_prefix()
    
    def _load_static_prefix(self):
        """Load CONSTITUTION and MASTER_ROUTER content for LLM prefix caching."""
        constitution_path = PROJECT_ROOT / "skills" / "CONSTITUTION.md"
        master_router_path = PROJECT_ROOT / "skills" / "MASTER_ROUTER.md"
        
        static_content = []
        
        if constitution_path.exists():
            static_content.append(constitution_path.read_text(encoding="utf-8"))
        else:
            logger.warning(f"CONSTITUTION.md not found at {constitution_path}")
        
        if master_router_path.exists():
            static_content.append(master_router_path.read_text(encoding="utf-8"))
        else:
            logger.warning(f"MASTER_ROUTER.md not found at {master_router_path}")
        
        if static_content:
            combined = "\n\n".join(static_content)
            self.llm.set_static_prefix(combined)
            logger.info("Static prefix loaded for LLM prefix caching")

    def _deterministic_router_fallback(self, query: str, err: Exception) -> RouteDecision:
        q = query.lower()
        domain = "general"
        intent = "analyze"
        
        if any(w in q for w in ["error", "bug", "exception", "fails", "trace", "lỗi"]): intent = "debug"
        elif any(w in q for w in ["create", "build", "generate", "add", "tạo"]): intent = "generate"
        elif any(w in q for w in ["edit", "update", "modify", "sửa"]): intent = "edit"
            
        if any(w in q for w in ["react", "next", "component", "css", "ui"]): domain = "frontend"
        elif any(w in q for w in ["api", "database", "endpoint", "sql", "node", "redis"]): domain = "backend"
        elif any(w in q for w in ["docker", "deploy", "nginx"]): domain = "infra"
            
        return RouteDecision(
            domain=domain, intent=intent, requires_retrieval=True, confidence=0.1,
            candidate_skills=[], reasoning_summary=f"Heuristic Fallback: {str(err)[:50]}"
        )

    def route_task(self, task_description, span) -> RouteDecision:
        """
        Route task using SLMRouter first, fall through to LLM if needed.
        Enforces budget before LLM call.
        
        Requirements: 4.2, 4.3, 7.7
        """
        # Try SLM router first (Requirement 4.2, 4.3)
        if self.slm_router:
            try:
                slm_decision = self.slm_router.classify(task_description)
                if slm_decision is not None:
                    # SLM confidence >= threshold, use it directly
                    logger.info(f"SLMRouter classified with confidence {slm_decision.confidence:.3f}")
                    span.update(slm_used=True, slm_confidence=slm_decision.confidence)
                    
                    # Convert SLMRouteDecision to RouteDecision
                    return RouteDecision(
                        domain=slm_decision.chosen,
                        intent="analyze",  # Default intent
                        requires_retrieval=True,
                        confidence=slm_decision.confidence,
                        candidate_skills=[],
                        reasoning_summary=f"SLM classification: {slm_decision.chosen}"
                    )
            except Exception as e:
                logger.warning(f"SLMRouter failed: {e}, falling through to LLM")
                span.update(slm_error=str(e))
        
        # Fall through to LLM routing (Requirement 4.3)
        system_prompt = '''You are a routing engine for the Antigravity orchestrator.
Classify the request into: domain, intent, whether retrieval is required, candidate skills.
Rules:
- Prefer "debug" when user includes errors, stack traces, failing behavior.
- Prefer "generate" when user asks to create new code.
- Prefer "edit" when modifying existing code.
- Set requires_retrieval=true when domain-specific project knowledge is needed.
- Keep reasoning_summary under 300 characters.
Return only data matching the schema.'''

        messages = [{"role": "user", "content": f"User Request: {task_description}"}]
        
        # Estimate token cost for budget check (Requirement 7.7)
        estimated_input = len(system_prompt) // 4 + len(task_description) // 4  # Rough estimate
        max_output = 200  # RouteDecision is small
        
        try:
            # Check budget BEFORE LLM call (Requirement 7.7)
            self.budget_guard.check_pre_call(estimated_input, max_output)
            
            result = self.llm.generate_structured(
                task_name="router_primary",
                model=os.getenv("AG_LLM_MODEL", "gemini-2.5-flash"),
                system=system_prompt,
                messages=messages,
                response_model=RouteDecision
            )
            
            # Record actual usage
            actual_tokens = estimated_input + max_output  # Approximate
            self.budget_guard.record_call(actual_tokens)
            self.budget_guard.record_step()
            
            return result
            
        except BudgetExceededError as e:
            logger.critical(f"Budget exceeded during routing: {e.termination_reason}")
            span.update(budget_exceeded=True, termination_reason=e.termination_reason)
            raise
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Routing failed, Safe Deterministic Fallback. Error: {e}")
            span.log_error(str(e))
            span.update(fallback_used=True, fallback_reason=str(e))
            return self._deterministic_router_fallback(task_description, e)

    def _deterministic_planner_fallback(self, task_desc: str, err: Exception, domain: str, completion_spec: TaskCompletionSpec = None) -> ExecutionPlan:
        safe_desc = str(task_desc)[:50]
        if not completion_spec:
            completion_spec = TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="file_exists", path=f"fallback_{domain}.log")],
                semantic_goal="Analyze task and output fallback log."
            )
        return ExecutionPlan(
            objective=f"Fallback Execution for: {safe_desc}",
            steps=[PlanStep(step_id=1, action="analyze", agent=domain, input={"query": str(task_desc), "fallback": True})],
            completion_criteria=completion_spec,
            risk_flags=[f"Planner Failed: {str(err)}", "Using single-step fallback execution"]
        )


    def plan_execution(self, task_description: str, route: RouteDecision, span) -> ExecutionPlan:
        
        # Phase 3: Planner Augmentation (Mode 1 - Intent Retrieval)
        skill = self.skill_store.retrieve(task_description)
        skill_injector = ""
        if skill:
            skill_injector = f"""
[SKILL MEMORY HIT - OVERRIDE INSTRUCTION]
You MUST follow this proven macro skill template:
- Name: {skill.name}
- Blueprint Steps: {skill.plan_template}
- Success Constraints: {skill.success_criteria}
Adapt the placeholder variables (like {{PACKAGE_NAME}} or {{DYNAMIC_PATH}}) based on user context.
"""

        system_prompt = f'''You are the Lead Execution Planner. 
Break down the task into minimal executable steps AND define strict deterministic completion criteria.
Domain={route.domain}, Intent={route.intent}.

RULES:
- Actions MUST be one of: ["generate_code", "analyze", "write_file", "read_file", "run_cmd"].
- MUST generate completion_criteria defining exact artifacts expected ("file_exists", "cmd_exit_zero", etc).
{skill_injector}'''

        messages = [{"role": "user", "content": f"User Request: {task_description}"}]
        
        try:
            return self.llm.generate_structured(
                task_name="planner_primary",
                model=os.getenv("AG_LLM_MODEL", "gemini-2.5-flash"),
                system=system_prompt,
                messages=messages,
                response_model=ExecutionPlan
            )
        except Exception as e:
            print(f"[ORCHESTRATOR] Planner failed. Single-step heuristic fallback.")
            span.log_error(str(e))
            span.update(fallback_used=True, fallback_strategy="single_step_fallback")
            # Pull criteria from description if we can find it, otherwise it stays None
            return self._deterministic_planner_fallback(task_description, e, route.domain)


    def replan_repair(self, task_description: str, failed_plan: ExecutionPlan, error_delta: ErrorDelta, span) -> ExecutionPlan:
        """
        Generate repair plan using ASTAnalyzer and ErrorDelta context.
        
        Requirements: 2.6, 3.2, 3.4
        """
        # --- MOCK LLM MODE ---
        if os.getenv("AG_FORCE_REPAIR_PATCH") == "true":
            print("[ORCHESTRATOR][MOCK] AG_FORCE_REPAIR_PATCH is set. Injecting deterministic React fix.")
            # Hardcoded fix for the specific React useState lint error
            return ExecutionPlan(
                objective="Targeted Mock Repair: Fix React useState missing import",
                steps=[
                    PlanStep(
                        step_id=1,
                        agent="developer",
                        action="write_file",
                        input={
                            "path": "test-react-app/src/App.jsx",
                            "content": "import { useState } from 'react'\nimport reactLogo from './assets/react.svg'\nimport viteLogo from './assets/vite.svg'\nimport heroImg from './assets/hero.png'\nimport './App.css'\n\nfunction App() {\n  const [count, setCount] = useState(0)\n\n  return (\n    <>\n      <section id=\"center\">\n        <div className=\"hero\">\n          <img src={heroImg} className=\"base\" width=\"170\" height=\"179\" alt=\"\" />\n          <img src={reactLogo} className=\"framework\" alt=\"React logo\" />\n          <img src={viteLogo} className=\"vite\" alt=\"Vite logo\" />\n        </div>\n        <div>\n          <h1>Get started</h1>\n          <p>\n            Edit <code>src/App.jsx</code> and save to test <code>HMR</code>\n          </p>\n        </div>\n        <button\n          className=\"counter\"\n          onClick={() => setCount((count) => count + 1)}\n        >\n          Count is {count}\n        </button>\n      </section>\n\n      <div className=\"ticks\"></div>\n\n      <section id=\"next-steps\">\n        <div id=\"docs\">\n          <svg className=\"icon\" role=\"presentation\" aria-hidden=\"true\">\n            <use href=\"/icons.svg#documentation-icon\"></use>\n          </svg>\n          <h2>Documentation</h2>\n          <p>Your questions, answered</p>\n          <ul>\n            <li>\n              <a href=\"https://vite.dev/\" target=\"_blank\">\n                <img className=\"logo\" src={viteLogo} alt=\"\" />\n                Explore Vite\n              </a>\n            </li>\n            <li>\n              <a href=\"https://react.dev/\" target=\"_blank\">\n                <img className=\"button-icon\" src={reactLogo} alt=\"\" />\n                Learn more\n              </a>\n            </li>\n          </ul>\n        </div>\n        <div id=\"social\">\n          <svg className=\"icon\" role=\"presentation\" aria-hidden=\"true\">\n            <use href=\"/icons.svg#social-icon\"></use>\n          </svg>\n          <h2>Connect with us</h2>\n          <p>Join the Vite community</p>\n          <ul>\n            <li>\n              <a href=\"https://github.com/vitejs/vite\" target=\"_blank\">\n                <svg\n                  className=\"button-icon\"\n                  role=\"presentation\"\n                  aria-hidden=\"true\"\n                >\n                  <use href=\"/icons.svg#github-icon\"></use>\n                </svg>\n                GitHub\n              </a>\n            </li>\n            <li>\n              <a href=\"https://chat.vite.dev/\" target=\"_blank\">\n                <svg\n                  className=\"button-icon\"\n                  role=\"presentation\"\n                  aria-hidden=\"true\"\n                >\n                  <use href=\"/icons.svg#discord-icon\"></use>\n                </svg>\n                Discord\n              </a>\n            </li>\n            <li>\n              <a href=\"https://x.com/vite_js\" target=\"_blank\">\n                <svg\n                  className=\"button-icon\"\n                  role=\"presentation\"\n                  aria-hidden=\"true\"\n                >\n                  <use href=\"/icons.svg#x-icon\"></use>\n                </svg>\n                X.com\n              </a>\n            </li>\n            <li>\n              <a href=\"https://bsky.app/profile/vite.dev\" target=\"_blank\">\n                <svg\n                  className=\"button-icon\"\n                  role=\"presentation\"\n                  aria-hidden=\"true\"\n                >\n                  <use href=\"/icons.svg#bluesky-icon\"></use>\n                </svg>\n                Bluesky\n              </a>\n            </li>\n          </ul>\n        </div>\n      </section>\n\n      <div className=\"ticks\"></div>\n      <section id=\"spacer\"></section>\n    </>\n  )\n}\n\nexport default App\n"
                        }
                    )
                ],
                completion_criteria=failed_plan.completion_criteria
            )

        # Phase 3: Hard Override for Failure Patterns (Mode 2 - Repair Macro Retrieval)
        errors_list = error_delta.errors_introduced + error_delta.errors_resolved
        skill = self.skill_store.retrieve(task_description, errors_list)
        skill_injector = ""
        if skill:
            skill_injector = f"""
[CRITICAL REPAIR MACRO MATCHED]
Error matches known failure: '{skill.name}'.
Use EXACTLY this blueprint: {skill.plan_template}
Adapt dynamic fields. Keep original completion criteria.
"""

        # Use ASTAnalyzer for repair context (Requirement 2.6)
        ast_context = ""
        if error_delta.errors_introduced:
            # Extract file paths from errors (simple heuristic)
            error_files = []
            for err in error_delta.errors_introduced:
                # Look for file paths in error messages
                import re
                file_matches = re.findall(r'[\w/\\.-]+\.(?:py|js|jsx|ts|tsx)', err)
                for match in file_matches:
                    if match not in error_files:
                        error_files.append(match)
            
            if error_files:
                try:
                    # Analyze first file with error line 1 (we don't have exact line from error string)
                    targets = [(f, 1) for f in error_files[:3]]  # Limit to 3 files
                    ast_contract = self.ast_analyzer.analyze(targets)
                    ast_context = f"\n[AST ANALYSIS]\n{ast_contract.model_dump_json(indent=2)}\n"
                except Exception as e:
                    logger.warning(f"AST analysis failed: {e}")
        
        # v6.2: Retrieve relevant failure lessons (Learning Loop)
        failure_memory_context = ""
        try:
            err_str = '\n'.join(error_delta.errors_introduced)
            relevant_failures = self.failure_memory.retrieve_lessons(
                current_task=task_description,
                current_error=err_str,
                top_k=3
            )
            
            if relevant_failures:
                failure_memory_context = "\n" + self.failure_memory.format_for_prompt(relevant_failures) + "\n"
                logger.info(f"Retrieved {len(relevant_failures)} relevant failure lessons")
                span.update(failure_lessons_retrieved=len(relevant_failures))
        except Exception as e:
            logger.warning(f"FailureMemory retrieval failed: {e}")

        # Build repair prompt with ErrorDelta context (Requirement 3.4)
        system_prompt = f'''You are the Targeted Repair Planner.
The execution failed deterministic checks.

[ERROR DELTA ANALYSIS]
Operation ID: {error_delta.operation_id}
Old Error Score: {error_delta.old_error_score}
New Error Score: {error_delta.new_error_score}
Net Improvement: {error_delta.net_improvement}
Errors Resolved: {error_delta.errors_resolved}
Errors Introduced: {error_delta.errors_introduced}

{ast_context}
{failure_memory_context}

Generate a MINIMAL plan to fix ONLY the failed step.
{skill_injector}'''

        err_str = '\n'.join(error_delta.errors_introduced)
        messages = [
            {"role": "user", "content": f"Original task: {task_description}\nFailed checks:\n{err_str}\n\nRe-plan specific minimal fix."}
        ]
        
        # Estimate token cost
        estimated_input = len(system_prompt) // 4 + len(err_str) // 4
        max_output = 1000
        
        try:
            # Check budget before repair LLM call
            self.budget_guard.check_pre_call(estimated_input, max_output)
            
            plan = self.llm.generate_structured(
                task_name="replan_repair",
                model=os.getenv("AG_LLM_MODEL", "gemini-2.5-flash"),
                system=system_prompt,
                messages=messages,
                response_model=ExecutionPlan
            )
            
            # Record usage
            actual_tokens = estimated_input + max_output
            self.budget_guard.record_call(actual_tokens)
            self.budget_guard.record_repair()
            
            plan.completion_criteria = failed_plan.completion_criteria
            return plan
            
        except BudgetExceededError as e:
            logger.critical(f"Budget exceeded during repair: {e.termination_reason}")
            span.update(budget_exceeded=True, termination_reason=e.termination_reason)
            raise
            
        except Exception as e:
            print(f"[ORCHESTRATOR] Repair Replan failed. Applying fallback.")
            return self._deterministic_planner_fallback(task_description, e, "debug", completion_spec=failed_plan.completion_criteria)


    def execute(self, task):
        """
        Main execution loop with full architecture upgrade integration.
        
        Requirements: 1.6, 2.6, 3.2, 3.3, 3.4, 3.6, 3.9, 4.2, 4.3, 5.1, 6.3, 6.8, 7.1, 7.2, 7.4, 7.7, 8.2
        """
        session_id = None
        current_trace = None
        try:
            # Accept task as dict or JSON string
            if isinstance(task, str):
                try:
                    task = json.loads(task)
                except json.JSONDecodeError:
                    pass  # treat as plain description string
            if isinstance(task, dict):
                task_description = task.get("description", str(task))
                project_path = task.get("project_path", None)
                user_criteria = task.get("completion_criteria", {})
            else:
                task_description = str(task)
                project_path = None
                user_criteria = {}
            
            # Generate session_id using time-sortable ID (Requirement 8.2)
            session_id = new_id()
            
            # Validate externally-provided IDs (Requirement 8.2)
            if isinstance(task, dict) and "session_id" in task:
                provided_id = task["session_id"]
                if not is_valid_time_sortable_id(provided_id):
                    logger.warning(f"Invalid session_id format: {provided_id}, generating compliant replacement")
                    self.tracer.log_event("invalid_id_format", {"provided_id": provided_id, "replacement": session_id})
                else:
                    session_id = provided_id
            
            # Build ArtifactCheck list from user-supplied criteria dict
            from core.schemas import ArtifactCheck, TaskCompletionSpec
            user_checks = []
            if isinstance(user_criteria, dict):
                for check_type, value in user_criteria.items():
                    if check_type == "file_exists":
                        user_checks.append(ArtifactCheck(type="file_exists", path=value))
                    elif check_type == "cmd_exit_zero":
                        user_checks.append(ArtifactCheck(type="cmd_exit_zero", cmd=value))
                    elif check_type == "file_contains":
                        user_checks.append(ArtifactCheck(type="file_contains", path=value.get("path"), keyword=value.get("keyword")))
            user_completion_spec = TaskCompletionSpec(
                deterministic_checks=user_checks,
                semantic_goal=f"Complete: {task_description[:100]}"
            ) if user_checks else None
            
            with self.tracer.trace_session(name="orchestrator_request", session_id=session_id) as trace:
                current_trace = trace  # Store reference for exception handlers
                with trace.span(name="route_task") as route_span:
                    print(f"\n[{session_id}][ORCHESTRATOR] Analyzing task...")
                    decision = self.route_task(task_description, route_span)
                    
                with trace.span(name="plan_execution") as plan_span:
                    print(f"[{session_id}][ORCHESTRATOR] Formulating Plan Blueprint...")
                    active_plan = self.plan_execution(task_description, decision, plan_span)
                    # Override with user-supplied completion criteria if present
                    if user_completion_spec:
                        active_plan.completion_criteria = user_completion_spec
                    print(f"[EXECUTION PLAN] Steps: {len(active_plan.steps)} | Checks: {len(active_plan.completion_criteria.deterministic_checks)}")


                from core.action_runner import ActionDispatcher
                from core.checker import DeterministicChecker
                
                dispatcher = ActionDispatcher(self.llm)
                checker = DeterministicChecker()
                accumulated_context = deque(maxlen=self.CONTEXT_WINDOW_SIZE) if hasattr(self, 'CONTEXT_WINDOW_SIZE') else deque(maxlen=5)
                MAX_REPAIR_ATTEMPTS = self.budget_guard._max_repair_attempts
                repair_count = 0
                stagnation_count = 0
                previous_error_delta = None
                
                with trace.span(name="execution_and_healing_loop") as exec_span:
                    while repair_count <= MAX_REPAIR_ATTEMPTS:
                        print(f"\n[{session_id}][ORCHESTRATOR] Executor Loop (Attempt {repair_count}):")
                        
                        # Generate operation_id for this attempt (Requirement 3.3)
                        operation_id = new_id()
                        
                        # Collect files that will be modified for backup (Requirement 3.3)
                        modified_files = []
                        for step in active_plan.steps:
                            if step.action in ["write_file", "generate_code"]:
                                if "path" in step.input:
                                    modified_files.append(step.input["path"])
                                elif "files" in step.input:
                                    for f in step.input["files"]:
                                        if isinstance(f, dict) and "path" in f:
                                            modified_files.append(f["path"])
                        
                        # Create backup before dispatch (Requirement 3.3)
                        if modified_files:
                            try:
                                self.backup_manager.create_backup(session_id, operation_id, modified_files)
                                logger.info(f"Created backup for operation {operation_id}: {len(modified_files)} files")
                            except Exception as e:
                                logger.warning(f"Backup creation failed: {e}")
                        
                        # Compute pre-patch hashes for no-op detection (Requirement 3.9)
                        pre_patch_hashes = {}
                        for file_path in modified_files:
                            try:
                                path = Path(file_path)
                                if path.exists():
                                    content = path.read_bytes()
                                    pre_patch_hashes[file_path] = hashlib.sha256(content).hexdigest()
                            except Exception as e:
                                logger.warning(f"Failed to hash {file_path}: {e}")
                        
                        # Execute steps
                        for step in active_plan.steps:
                            with exec_span.span(name=f"step_{step.step_id}_{step.action}") as step_span:
                                print(f"  [EXEC] Step {step.step_id} via {step.agent}: {step.action} ...")
                                try:
                                    result = dispatcher.dispatch(step.action, step.input, list(accumulated_context))
                                    useful_result = {k: (str(v)[:300] + "...") if isinstance(v, str) and len(v) > 300 else v for k, v in result.items()}
                                    accumulated_context.append({"step": step.step_id, "action": step.action, "result": useful_result})
                                    if hasattr(step_span, "update"):
                                        step_span.update(agent=step.agent, action=step.action, output=str(useful_result))
                                except Exception as e:
                                    print(f"  [ERROR] Step {step.step_id}: {e}")
                                    if hasattr(step_span, "log_error"):
                                        step_span.log_error(str(e))
                                    accumulated_context.append({"step": step.step_id, "action": step.action, "result": {"error": str(e)}})
                        
                        # Check for no-op patches (Requirement 3.9)
                        post_patch_hashes = {}
                        no_op_detected = False
                        for file_path in modified_files:
                            try:
                                path = Path(file_path)
                                if path.exists():
                                    content = path.read_bytes()
                                    post_patch_hashes[file_path] = hashlib.sha256(content).hexdigest()
                            except Exception as e:
                                logger.warning(f"Failed to hash {file_path}: {e}")
                        
                        if pre_patch_hashes == post_patch_hashes and pre_patch_hashes:
                            no_op_detected = True
                            logger.warning(f"No-op patch detected for operation {operation_id}")
                            exec_span.log_event("no_op_patch_detected", {"operation_id": operation_id})
                            
                            # Skip checker and request replan
                            print(f"[{session_id}][ORCHESTRATOR] No-op patch detected, requesting replan...")
                            repair_count += 1
                            
                            if repair_count > MAX_REPAIR_ATTEMPTS:
                                print(f"[{session_id}][ORCHESTRATOR] MAX_REPAIR_ATTEMPTS reached after no-op. Yielding.")
                                if hasattr(exec_span, "update"):
                                    exec_span.update(status="partial", reason="max_repair_reached_no_op")
                                return {"status": "failure", "reason": "max_repair_attempts_no_op", "session_id": session_id}
                            
                            # Create fake error delta for replan
                            fake_error_delta = ErrorDelta(
                                operation_id=operation_id,
                                errors_introduced=["No-op patch: no semantic changes detected"],
                                old_error_score=0.0,
                                new_error_score=1.0,
                                net_improvement=False
                            )
                            active_plan = self.replan_repair(task_description, active_plan, fake_error_delta, exec_span)
                            continue
                                    
                        print(f"\n[{session_id}][CHECKER] Running Deterministic Hardware Verification...")
                        
                        # Get previous errors for ErrorDelta computation
                        prev_errors = previous_error_delta.errors_introduced if previous_error_delta else []
                        
                        # Run checker and get ErrorDelta (Requirement 3.1, 3.2)
                        error_delta = checker.examine(
                            active_plan.completion_criteria.deterministic_checks,
                            previous_errors=prev_errors,
                            project_root=project_path
                        )
                        
                        # Link patch metadata to trace (Requirement 6.3)
                        exec_span.link_patch_metadata(
                            patch_id=operation_id,
                            error_delta=error_delta,
                            rollback_triggered=False
                        )
                        
                        if error_delta.net_improvement and error_delta.new_error_score == 0.0:
                            print(f"[{session_id}][CHECKER] All checks PASS. ✅ Task Fully Complete.")
                            if hasattr(exec_span, "update"):
                                exec_span.update(status="success", repair_count=repair_count)
                            
                            # Score trace as success (Requirement 6.6)
                            trace.score(1.0)
                            break
                        
                        # Check for regression (Requirement 3.2, 3.4)
                        if not error_delta.net_improvement:
                            print(f"[{session_id}][CHECKER] REGRESSION DETECTED ❌")
                            print(f"  Old Score: {error_delta.old_error_score}, New Score: {error_delta.new_error_score}")
                            print(f"  Errors Introduced: {error_delta.errors_introduced}")
                            
                            # Trigger rollback (Requirement 3.2, 3.6)
                            try:
                                self.backup_manager.rollback(session_id, operation_id)
                                logger.info(f"Rolled back operation {operation_id}")
                                
                                # v6.2: Record failure for learning loop
                                try:
                                    # Get patch diff from modified files
                                    patch_diff = f"Operation {operation_id}: {len(modified_files)} files modified"
                                    if modified_files:
                                        patch_diff = "\n".join(f"- {f}" for f in modified_files)
                                    
                                    # Record failure
                                    pattern, lesson = self.failure_memory.record_failure(
                                        failure_id=operation_id,
                                        patch_diff=patch_diff,
                                        error_text='\n'.join(error_delta.errors_introduced),
                                        files_touched=modified_files,
                                        session_id=session_id
                                    )
                                    
                                    logger.info(
                                        f"Recorded failure pattern: {pattern.pattern_type} - {pattern.cause}"
                                    )
                                    exec_span.log_event("failure_recorded", {
                                        "pattern_type": pattern.pattern_type,
                                        "cause": pattern.cause,
                                        "confidence": lesson.confidence
                                    })
                                except Exception as e:
                                    logger.warning(f"Failed to record failure: {e}")
                                
                                # Update trace metadata
                                exec_span.link_patch_metadata(
                                    patch_id=operation_id,
                                    error_delta=error_delta,
                                    rollback_triggered=True
                                )
                            except Exception as e:
                                logger.critical(f"Rollback failed: {e}")
                        else:
                            print(f"[{session_id}][CHECKER] Partial progress: {error_delta.errors_resolved} resolved, {error_delta.errors_introduced} new")
                        
                        # Check for stagnation
                        if previous_error_delta and error_delta.new_error_score == previous_error_delta.new_error_score:
                            stagnation_count += 1
                            if stagnation_count >= 2:
                                print(f"[{session_id}][SAFETY] No-Progress loop. Hard Exit.")
                                if hasattr(exec_span, "update"):
                                    exec_span.update(status="partial", reason="stagnation_looping")
                                
                                # Score trace as failure (Requirement 6.6)
                                trace.score(0.0)
                                break
                        else:
                            stagnation_count = 0
                            
                        previous_error_delta = error_delta
                        repair_count += 1
                        
                        if repair_count > MAX_REPAIR_ATTEMPTS:
                            print(f"[{session_id}][ORCHESTRATOR] MAX_REPAIR_ATTEMPTS reached. Yielding.")
                            if hasattr(exec_span, "update"):
                                exec_span.update(status="partial", reason="max_repair_reached")
                            
                            # Score trace as failure (Requirement 6.6)
                            trace.score(0.0)
                            return {"status": "failure", "reason": "max_repair_attempts", "session_id": session_id}
                            
                        print(f"\n[{session_id}][AGENT-MEMORY] Initiating Targeted Self-Heal Protocol...")
                        
                        # Log replan event (Requirement 6.4)
                        exec_span.log_replan_triggered(error_delta)
                        
                        # Replan with ErrorDelta context (Requirement 3.4)
                        active_plan = self.replan_repair(task_description, active_plan, error_delta, exec_span)

            return {"status": "success", "session_id": session_id}
            
        except BudgetExceededError as e:
            logger.critical(f"Budget exceeded: {e.termination_reason}")
            if current_trace:
                current_trace.score(0.0)
            return {
                "status": "budget_exceeded",
                "reason": e.termination_reason,
                "dimension": e.dimension,
                "session_id": session_id if session_id else ""
            }
            
        except Exception as e:
            logger.error(f"Orchestrator execution failed: {e}", exc_info=True)
            if current_trace:
                current_trace.score(0.0)
            return {"status": "error", "error": str(e), "session_id": session_id if session_id else ""}
            
        finally:
            # Flush traces (Requirement 6.8)
            try:
                self.tracer.flush()
            except Exception as e:
                logger.error(f"Failed to flush traces: {e}")
            
            # Finalize budget (Requirement 7.2)
            try:
                self.budget_guard.finalize()
            except Exception as e:
                logger.error(f"Failed to finalize budget: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py 'query'")
        sys.exit(1)
    engine = AntigravityOrchestrator()
    engine.execute(sys.argv[1])
