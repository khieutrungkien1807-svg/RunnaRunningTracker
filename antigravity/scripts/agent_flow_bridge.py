"""
██████╗ ██████╗ ██╗██████╗  ██████╗ ███████╗
██╔══██╗██╔══██╗██║██╔══██╗██╔════╝ ██╔════╝
██████╔╝██████╔╝██║██║  ██║██║  ███╗█████╗  
██╔══██╗██╔══██╗██║██║  ██║██║   ██║██╔══╝  
██████╔╝██║  ██║██║██████╔╝╚██████╔╝███████╗
╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝ ╚══════╝

Antigravity → Agent Flow Bridge
================================
Real-time event bridge: converts Antigravity tool calls and agent actions
into JSONL events readable by the Agent Flow VS Code extension.

Usage:
    python agent_flow_bridge.py [--output PATH] [--watch] [--replay CONV_ID]

How it works:
    1. Intercepts tool_call events from Antigravity's internal mechanism
    2. Reads Antigravity daemon logs for session tracking  
    3. Emits AgentEvent JSONL format compatible with Agent Flow
    4. Agent Flow watches the output .jsonl file via 'agentVisualizer.eventLogPath'
    
Setup:
    In VS Code settings: "agentVisualizer.eventLogPath": "C:\\Users\\<USER_NAME>\\.gemini\\antigravity\\agent_flow_events.jsonl"
"""

import json
import os
import sys
import time
import uuid
import argparse
import threading
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── Config ──────────────────────────────────────────────────────────────────

Antigravity_DIR = Path(os.environ.get("Antigravity_DIR", r"C:\Users\<USER_NAME>\.gemini\antigravity"))
DAEMON_DIR = Antigravity_DIR / "daemon"

# Output path — MUST match VS Code setting "agentVisualizer.eventLogPath"
# The extension watches this file for live events.
OUTPUT_PATH = Antigravity_DIR / "agent_flow_events.jsonl"

# ─── AgentEvent Helpers ───────────────────────────────────────────────────────

class AgentFlowEmitter:
    """Writes AgentEvent JSONL lines compatible with Agent Flow extension."""

    def __init__(self, output_path: Path, session_id: Optional[str] = None, hook_url: Optional[str] = None):
        self.output_path = output_path
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.start_time = time.time()
        self.hook_url = hook_url
        self._lock = threading.Lock()
        
        # Initialize file and Claude Code structure
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        # Fake a Claude Code "cwd" line so the extension's SessionWatcher authenticates it
        init_event = {
            "type": "message",
            "cwd": str(Antigravity_DIR),
            "message": {"role": "user", "content": "Antigravity Bridge Init"}
        }
        with self._lock:
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(init_event) + "\n")
        
        if self.hook_url:
            self._send_to_hook(init_event)

    def _elapsed(self) -> float:
        return round(time.time() - self.start_time, 3)

    def _send_to_hook(self, event: dict):
        """Send event via HTTP POST to the Agent Flow hook server."""
        if not self.hook_url: return
        try:
            data = json.dumps(event).encode('utf-8')
            req = urllib.request.Request(self.hook_url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=1) as response:
                pass
        except Exception:
            pass

    def _emit(self, event_type: str, payload: dict):
        event = {
            "type": event_type,
            "payload": payload,
            "time": self._elapsed(),
            "sessionId": self.session_id,
        }
        with self._lock:
            with open(self.output_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                f.flush()
        
        if self.hook_url:
            self._send_to_hook(event)

    def session_start(self, task: str = "Antigravity Session"):
        """Emit session start and spawn orchestrator."""
        self._emit("agent_spawn", {
            "name": "Antigravity",
            "isMain": True,
            "task": task,
        })

    def _mask_secrets(self, text: str) -> str:
        """Loki Mode / PII Data Masking by Default: Redact sensitive information."""
        if not text: return text
        import re
        # Mask Bearer tokens
        text = re.sub(r'(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*', r'\1[MASKED_TOKEN]', text)
        # Mask API keys and secrets
        text = re.sub(r'([A-Za-z0-9_]*API[A-Za-z0-9_]*[Kk]ey\s*["\']?\s*:\s*["\']?)[A-Za-z0-9\-\._]+', r'\1[MASKED_API_KEY]', text)
        text = re.sub(r'([A-Za-z0-9_]*[Ss]ecret\s*["\']?\s*:\s*["\']?)[A-Za-z0-9\-\._]+', r'\1[MASKED_SECRET]', text)
        return text

    def tool_call_start(self, tool_name: str, args: str, agent: str = "Antigravity"):
        """Emit tool call start event with data masking."""
        safe_args = self._mask_secrets(args[:200])
        self._emit("tool_call_start", {
            "agent": agent,
            "tool": tool_name,
            "args": safe_args,
            "preview": f"{tool_name}: {safe_args[:80]}",
        })

    def tool_call_end(self, tool_name: str, result: str, agent: str = "Antigravity", token_cost: int = 0):
        """Emit tool call end event with data masking."""
        safe_result = self._mask_secrets(result[:500])
        self._emit("tool_call_end", {
            "agent": agent,
            "tool": tool_name,
            "result": safe_result,
            "tokenCost": token_cost,
        })

    def subagent_spawn(self, parent: str, child: str, task: str):
        """Emit subagent spawn (browser subagent, etc.)."""
        self._emit("subagent_dispatch", {"parent": parent, "child": child, "task": task})
        self._emit("agent_spawn", {"name": child, "parent": parent, "task": task})

    def subagent_return(self, parent: str, child: str, summary: str = ""):
        """Emit subagent return."""
        self._emit("subagent_return", {"parent": parent, "child": child, "summary": summary})
        self._emit("agent_complete", {"name": child})

    def agent_idle(self, agent: str = "Antigravity"):
        self._emit("agent_idle", {"name": agent})

    def agent_complete(self, task: str = "", session_end: bool = False):
        self._emit("agent_complete", {"name": "Antigravity", "task": task, "sessionEnd": session_end})

    def llm_request(self, model: str, messages: int, agent: str = "Antigravity"):
        """Emit a model inference event (mapped to tool_call_start)."""
        self._emit("tool_call_start", {
            "agent": agent,
            "tool": "🧠 LLM Inference",
            "args": f"model={model}, messages={messages}",
            "preview": f"Thinking... ({model}, {messages} msgs)",
        })

    def error(self, message: str, agent: str = "Antigravity"):
        self._emit("error", {"agent": agent, "message": message})


# ─── Daemon Log Watcher ───────────────────────────────────────────────────────

class AntigravityDaemonWatcher:
    """
    Watches Antigravity daemon logs and extracts agent events.
    
    Daemon log format:
      I0306 16:22:58.152371  2532 planner_generator.go:285] Requesting planner with 66 chat messages...
      I0306 16:23:04.979780  2532 http_helpers.go:123] URL: https://daily-cloudcode-pa.googleapis.com/...
      E0306 16:23:07.085220  2532 client.go:56] CEL: Sending error - type=LS_ERROR...
    """

    def __init__(self, daemon_dir: Path, emitter: AgentFlowEmitter):
        self.daemon_dir = daemon_dir
        self.emitter = emitter
        self._stop_event = threading.Event()
        self._file_positions: dict[str, int] = {}
        self._active_inference: dict[str, int] = {}  # file -> messages count

    def _find_latest_log(self) -> Optional[Path]:
        logs = sorted(self.daemon_dir.glob("ls_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        return logs[0] if logs else None

    def _parse_line(self, line: str):
        """Parse a daemon log line and emit relevant events."""
        # LLM inference start
        if "planner_generator.go" in line and "Requesting planner with" in line:
            try:
                parts = line.split("Requesting planner with")[1].strip()
                n_messages = int(parts.split(" chat messages")[0].strip())
                model_info = "gemini"
                # Try to detect model from recent context
                self.emitter._emit("tool_call_start", {
                    "agent": "Antigravity",
                    "tool": "🧠 LLM → Gemini",
                    "args": f"{n_messages} context messages",
                    "preview": f"Thinking... ({n_messages} msgs in context)",
                })
                self._active_inference["current"] = n_messages
            except (ValueError, IndexError):
                pass

        # HTTP call completed (means LLM responded)
        elif "http_helpers.go" in line and "URL:" in line and "streamGenerateContent" in line:
            msgs = self._active_inference.pop("current", 0)
            # Extract trace ID for uniqueness
            trace = ""
            if "Trace: " in line:
                trace = line.split("Trace: ")[1].strip()[:12]
            self.emitter._emit("tool_call_end", {
                "agent": "Antigravity",
                "tool": "🧠 LLM → Gemini",
                "result": f"Response received (trace: {trace})",
                "tokenCost": msgs * 4,  # rough estimate: 4 tokens per message ref
            })

        # Error events
        elif line.startswith("E") and "log.go:398]" in line:
            err_msg = line.split("log.go:398]")[1].strip() if "log.go:398]" in line else line[7:]
            if "internal error" in err_msg:
                self.emitter.error("Internal error occurred")
            elif "RESOURCE_EXHAUSTED" in err_msg:
                self.emitter.error("⚠️ Rate limit hit — waiting...")
            elif "UNAVAILABLE" in err_msg:
                self.emitter.error("⚠️ Model unavailable — retrying...")

        # MCP server events
        elif "MCP_SERVER_INIT_ERROR" in line:
            self.emitter.error("MCP server init error")

    def watch(self):
        """Continuously watch the latest daemon log."""
        print(f"[Bridge] Watching daemon logs in: {self.daemon_dir}")
        active_log = None

        while not self._stop_event.is_set():
            latest = self._find_latest_log()

            if latest != active_log:
                if latest:
                    print(f"[Bridge] Switched to log: {latest.name}")
                active_log = latest
                if active_log and active_log not in self._file_positions:
                    # Start from end of file for new logs
                    self._file_positions[str(active_log)] = active_log.stat().st_size

            if active_log and active_log.exists():
                key = str(active_log)
                current_size = active_log.stat().st_size
                pos = self._file_positions.get(key, current_size)

                if current_size > pos:
                    try:
                        with open(active_log, "r", encoding="utf-8", errors="ignore") as f:
                            f.seek(pos)
                            new_lines = f.read()
                            self._file_positions[key] = f.tell()

                        for line in new_lines.splitlines():
                            if line.strip():
                                self._parse_line(line)
                    except (OSError, IOError):
                        pass

            time.sleep(0.5)

    def stop(self):
        self._stop_event.set()


# ─── Tool Call Interceptor (stdin-based) ──────────────────────────────────────

class ToolCallInterceptor:
    """
    Reads tool call events from stdin (pipe from Antigravity hook).
    Format: JSON lines with {"tool": "...", "args": {...}, "result": "...", "phase": "start"|"end"}
    """

    def __init__(self, emitter: AgentFlowEmitter):
        self.emitter = emitter

    def run(self):
        """Read JSON event lines from stdin."""
        print("[Bridge] Waiting for tool call events on stdin...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                tool = event.get("tool", "unknown")
                phase = event.get("phase", "start")
                agent = event.get("agent", "Antigravity")
                
                if phase == "start":
                    args = event.get("args", "")
                    if isinstance(args, dict):
                        args = json.dumps(args)[:200]
                    self.emitter.tool_call_start(tool, str(args), agent)
                    
                elif phase == "end":
                    result = event.get("result", "")
                    if isinstance(result, dict):
                        result = json.dumps(result)[:300]
                    tokens = event.get("tokenCost", 0)
                    self.emitter.tool_call_end(tool, str(result), agent, tokens)
                    
                elif event.get("type") == "subagent_spawn":
                    self.emitter.subagent_spawn(
                        parent=event.get("parent", "Antigravity"),
                        child=event.get("child", "SubAgent"),
                        task=event.get("task", ""),
                    )
                elif event.get("type") == "subagent_return":
                    self.emitter.subagent_return(
                        parent=event.get("parent", "Antigravity"),
                        child=event.get("child", "SubAgent"),
                        summary=event.get("summary", ""),
                    )
                elif event.get("type") == "session_end":
                    self.emitter.agent_complete(session_end=True)
                    
            except json.JSONDecodeError:
                # Not JSON — treat as plain text message
                self.emitter._emit("message", {
                    "agent": "Antigravity",
                    "content": line[:200],
                })


# ─── Demo / Replay Mode ───────────────────────────────────────────────────────

def run_demo(emitter: AgentFlowEmitter):
    """Emit a realistic Antigravity demo scenario."""
    print("[Bridge] Running demo scenario...")
    
    emitter.session_start("Demo: Antigravity Skills System")
    time.sleep(0.3)
    
    # Load MASTER ROUTER
    emitter.tool_call_start("view_file", "MASTER_ROUTER.md")
    time.sleep(0.8)
    emitter.tool_call_end("view_file", "Loaded 128 lines — routing to Frontend + AI Agent domains")
    time.sleep(0.2)
    
    # LLM inference
    emitter.llm_request("gemini-3.1-pro", 12)
    time.sleep(1.5)
    emitter.tool_call_end("🧠 LLM → Gemini", "Analyzed user request: integrate Agent Flow into Antigravity")
    time.sleep(0.2)
    
    # Spawn browser subagent
    emitter.subagent_spawn("Antigravity", "BrowserAgent", "Explore agent-flow-main repo")
    time.sleep(0.5)
    
    emitter.tool_call_start("list_dir", "agent-flow-main/", "BrowserAgent")
    time.sleep(0.6)
    emitter.tool_call_end("list_dir", "Found: extension/, web/, README.md", "BrowserAgent")
    
    emitter.tool_call_start("view_file", "agent-flow-main/README.md", "BrowserAgent")
    time.sleep(0.7)
    emitter.tool_call_end("view_file", "Agent Flow: Real-time visualization of Claude Code agent orchestration", "BrowserAgent")
    
    emitter.subagent_return("Antigravity", "BrowserAgent", "Repo analysis complete")
    time.sleep(0.3)
    
    # Write bridge script
    emitter.tool_call_start("write_to_file", "C:/Users/<USER_NAME>/.gemini/antigravity/scripts/agent_flow_bridge.py")
    time.sleep(1.2)
    emitter.tool_call_end("write_to_file", "Created 250-line Python bridge script", token_cost=450)
    
    # LLM inference again
    emitter.llm_request("gemini-3.1-pro", 28)
    time.sleep(2.0)
    emitter.tool_call_end("🧠 LLM → Gemini", "Integration plan ready — building .vsix package")
    
    # Build extension
    emitter.tool_call_start("run_command", "npm install && npm run build:all")
    time.sleep(1.5)
    emitter.tool_call_end("run_command", "Build successful: agent-flow-0.4.9.vsix generated")
    
    emitter.agent_idle()
    time.sleep(0.5)
    emitter.agent_complete("Integration complete!", session_end=True)
    
    print("[Bridge] Demo complete! Check Agent Flow panel.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Antigravity → Agent Flow Event Bridge")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH), help="Output JSONL file path")
    parser.add_argument("--hook", type=str, help="HTTP Hook URL (e.g., http://localhost:3100)")
    parser.add_argument("--watch", action="store_true", help="Watch daemon logs (background mode)")
    parser.add_argument("--demo", action="store_true", help="Emit demo scenario")
    parser.add_argument("--stdin", action="store_true", help="Read tool events from stdin")
    parser.add_argument("--message", type=str, help="Emit a single message/event and exit")
    parser.add_argument("--session", type=str, help="Session ID (auto-generated if not set)")
    parser.add_argument("--clear", action="store_true", help="Clear output file before starting")
    args = parser.parse_args()

    output_path = Path(args.output)
    
    if args.clear and output_path.exists():
        output_path.unlink()
        print(f"[Bridge] Cleared: {output_path}")

    session_id = args.session or datetime.now().strftime("%H%M%S")
    emitter = AgentFlowEmitter(output_path, session_id=session_id, hook_url=args.hook)
    
    print(f"""
╔══════════════════════════════════════════════════╗
║     Antigravity → Agent Flow Bridge v1.0         ║
╠══════════════════════════════════════════════════╣
║  Output: {str(output_path)[:42]}
║  Session: {session_id}
╠══════════════════════════════════════════════════╣
║  VS Code setting to add:                         ║
║  "agentVisualizer.eventLogPath":                 ║
║  "{str(output_path)[:40]}"
╚══════════════════════════════════════════════════╝
""")

    if args.demo:
        emitter.session_start("Antigravity Demo")
        run_demo(emitter)
        return

    if args.message:
        emitter.tool_call_start("Loki System Event", args.message)
        emitter.tool_call_end("Loki System Event", "Event recorded")
        print(f"[Bridge] Message emitted: {args.message}")
        return

    # Start daemon watcher in background thread
    watcher = AntigravityDaemonWatcher(DAEMON_DIR, emitter)
    
    if args.watch or args.stdin:
        emitter.session_start(f"Antigravity Live Session — {datetime.now().strftime('%H:%M:%S')}")
        
        if args.watch:
            watcher_thread = threading.Thread(target=watcher.watch, daemon=True)
            watcher_thread.start()

        if args.stdin:
            interceptor = ToolCallInterceptor(emitter)
            try:
                interceptor.run()
            except KeyboardInterrupt:
                pass
        elif args.watch:
            try:
                print("[Bridge] Watching daemon logs. Press Ctrl+C to stop.")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        
        watcher.stop()
        emitter.agent_complete(session_end=True)
    else:
        parser.print_help()
        print("\nQuick start:")
        print(f"  python agent_flow_bridge.py --demo          # Emit demo scenario")
        print(f"  python agent_flow_bridge.py --watch         # Watch live daemon logs")
        print(f"  python agent_flow_bridge.py --watch --clear # Fresh session + watch")


if __name__ == "__main__":
    main()

