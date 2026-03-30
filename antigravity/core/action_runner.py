import os
import subprocess
from pathlib import Path
from core.llm_client import LLMClient
from core.schemas import GeneratedCodeResult

PROJECT_ROOT = Path(r"c:\Users\<YOUR_USERNAME>\.gemini\antigravity").resolve()

class ActionDispatcher:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def _safe_resolve(self, path_str: str) -> Path:
        """Thực thi Guardrails: Path Sandbox (Không cho ghi ra ngoài project root)"""
        # Nếu path là absolute, nó phải nằm trong PROJECT_ROOT
        # Nếu path là relative, nó sẽ được prepend PROJECT_ROOT
        try:
            target = (PROJECT_ROOT / path_str).resolve()
            if PROJECT_ROOT not in target.parents and target != PROJECT_ROOT:
                raise ValueError(f"Path Traversal Blocked: {path_str} is outside project root.")
            return target
        except Exception as e:
            raise ValueError(f"Invalid path {path_str}: {e}")

    def handle_read_file(self, input_args: dict, context: list) -> dict:
        """Đọc file thật từ disk"""
        path_str = input_args.get("file") or input_args.get("path")
        if not path_str:
            return {"error": "Missing 'file' or 'path' argument in input."}
            
        try:
            target = self._safe_resolve(path_str)
            if not target.exists():
                return {"exists": False, "content": None}
            
            # File size limit (Guardrail: avoid passing huge files into context)
            size_kb = target.stat().st_size / 1024
            if size_kb > 250: # max 250KB allowed to read
                return {"exists": True, "error": f"File too large ({size_kb:.1f}KB). Max allowed is 250KB."}

            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            return {"exists": True, "content": content}
        except Exception as e:
            return {"error": str(e)}

    def handle_write_file(self, input_args: dict, context: list) -> dict:
        """Ghi file thật xuống disk"""
        path_str = input_args.get("file") or input_args.get("path")
        content = input_args.get("content", "")
        mode = input_args.get("mode", "overwrite")
        
        if not path_str:
            return {"error": "Missing 'file' or 'path' argument in input."}
            
        try:
            target = self._safe_resolve(path_str)
            target.parent.mkdir(parents=True, exist_ok=True)
            
            flag = "a" if mode == "append" else "w"
            with open(target, flag, encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": str(target)}
        except Exception as e:
            return {"error": str(e)}

    def handle_generate_code(self, input_args: dict, context: list) -> dict:
        """Gọi LLMClient structured để sinh code và validate path"""
        requirements = input_args.get("requirements", str(input_args))
        
        # Build context string safely (pass relevant context downstream, not full logs)
        compiled_context = "\n".join([f"Step {c['step']} ({c['action']}): {str(c['result'])[:500]}" for c in context[-3:]])
        
        system_prompt = '''You are a deterministic code generator.
Based on the task requirements and context, generate the necessary files.
You MUST output fully functioning raw code. No placeholders.
Return exactly the GeneratedCodeResult schema with the specific files.'''
        messages = [
            {"role": "user", "content": f"Context/Previous outputs:\n{compiled_context}\n\nRequirements:\n{requirements}"}
        ]
        
        try:
            result: GeneratedCodeResult = self.llm.generate_structured(
                task_name="action_generate_code",
                model=os.getenv("AG_LLM_MODEL", "gemini-2.0-flash"),  # Use strong model for code gen
                system=system_prompt,
                messages=messages,
                response_model=GeneratedCodeResult
            )
            
            written_files = []
            errors = []
            for file_artifact in result.files:
                try:
                    # Validate path trước khi ghi
                    target = self._safe_resolve(file_artifact.path)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    flag = "a" if file_artifact.action == "modify" else "w"
                    with open(target, flag, encoding="utf-8") as f:
                        f.write(file_artifact.content)
                    written_files.append({"path": str(target), "action": file_artifact.action})
                except Exception as e:
                    errors.append(f"Failed to write {file_artifact.path}: {str(e)}")
                    
            return {"success": len(errors) == 0, "written_files": written_files, "errors": errors, "explanation": result.explanation}
        except Exception as e:
            return {"error": f"LLM Generation failed: {str(e)}"}

    def handle_run_cmd(self, input_args: dict, context: list) -> dict:
        """Run command local với Whitelist & Timeout"""
        cmd_str = input_args.get("command", "")
        if not cmd_str:
            return {"error": "Missing 'command' argument."}
            
        # Whitelist Guardrail
        allowed_prefixes = ["npm install", "npm run build", "pytest", "python -m pytest"]
        if not any(cmd_str.startswith(prefix) for prefix in allowed_prefixes):
            return {"error": f"Command blocked. Only allowed prefixes: {', '.join(allowed_prefixes)}"}
            
        try:
            # Chú ý timeout=30s
            result = subprocess.run(
                cmd_str,
                shell=True,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=30
            )
            # Truncate output to prevent huge context bloat downstream
            stdout = result.stdout[:1500] + ("..." if len(result.stdout) > 1500 else "")
            stderr = result.stderr[:1500] + ("..." if len(result.stderr) > 1500 else "")
            
            return {
                "exit_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command execution timed out after 30 seconds."}
        except Exception as e:
            return {"error": str(e)}

    def dispatch(self, action: str, input_args: dict, context: list) -> dict:
        """Nhận diện hành động và map tới function chuẩn"""
        ACTION_MAP = {
            "read_file": self.handle_read_file,
            "write_file": self.handle_write_file,
            "generate_code": self.handle_generate_code,
            "run_cmd": self.handle_run_cmd,
            "analyze": lambda inp, ctx: {"analysis_complete": True, "input": inp} # Dummy for fallback tests
        }
        
        handler = ACTION_MAP.get(action)
        if not handler:
            return {"error": f"Unsupported action: {action}"}
            
        print(f"[ACTION DISPATCHER] Executing {action}...")
        return handler(input_args, context)
