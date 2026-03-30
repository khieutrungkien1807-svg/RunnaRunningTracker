import os
import re
import json
import subprocess
from pathlib import Path
from core.schemas import ArtifactCheck, ErrorDelta
from core.id_utils import new_id
from core.ast_analyzer import ASTAnalyzer

PROJECT_ROOT = Path(r"c:\Users\<YOUR_USERNAME>\.gemini\antigravity").resolve()

class DeterministicChecker:
    """Implement Level 1 Check: Deterministic First"""

    def _safe_resolve(self, path_str: str, project_root: Path = None) -> Path:
        """Resolve path. Allow absolute paths from known safe roots."""
        if not path_str:
            return None
        try:
            p = Path(path_str)
            if p.is_absolute():
                return p.resolve()
            base = project_root if project_root else PROJECT_ROOT
            target = (base / path_str).resolve()
            return target
        except Exception:
            return None

    def _normalize_errors(self, errors: list[str]) -> list[str]:
        """Normalize error strings to remove volatile parts (paths, timestamps, addresses)."""
        normalized = []
        for err in errors:
            # Strip file paths (Windows and Unix style)
            s = re.sub(r'[A-Za-z]:\\(?:[^\s\\/:*?"<>|\r\n]+\\)*[^\s\\/:*?"<>|\r\n]*', '<path>', err)
            s = re.sub(r'/(?:[^\s/]+/)*[^\s/]+', '<path>', s)
            # Strip ISO timestamps (e.g. 2024-01-15T12:34:56.789Z or 2024-01-15 12:34:56)
            s = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?', '<timestamp>', s)
            # Strip epoch numbers (large integers that look like timestamps, 10+ digits)
            s = re.sub(r'\b\d{10,}\b', '<timestamp>', s)
            # Strip hex addresses (0x...)
            s = re.sub(r'0x[0-9a-fA-F]+', '<addr>', s)
            # Strip standalone numbers at end of lines
            s = re.sub(r'\s+\d+\s*$', '', s)
            normalized.append(s)
        return normalized

    def check_file_exists(self, check: ArtifactCheck, project_root: Path = None) -> str | None:
        target = self._safe_resolve(check.path, project_root)
        if not target or not target.exists():
            return f"Missing file: {check.path}"
        return None

    def check_file_not_empty(self, check: ArtifactCheck, project_root: Path = None) -> str | None:
        target = self._safe_resolve(check.path, project_root)
        if not target or not target.exists() or target.stat().st_size == 0:
            return f"Empty or missing file: {check.path}"
        return None

    def check_file_contains(self, check: ArtifactCheck, project_root: Path = None) -> str | None:
        target = self._safe_resolve(check.path, project_root)
        if not target or not target.exists():
            return f"Missing file for keyword check: {check.path}"
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            if check.keyword not in content:
                return f"Keyword '{check.keyword}' not found in {check.path}"
        except Exception as e:
            return f"Failed reading {check.path}: {e}"
        return None

    def check_cmd_exit_zero(self, check: ArtifactCheck, project_root: Path = None) -> str | None:
        try:
            res = subprocess.run(
                check.cmd, shell=True,
                cwd=project_root if project_root else PROJECT_ROOT,
                capture_output=True, timeout=60, text=True
            )
            if res.returncode != 0:
                err = (res.stderr or res.stdout or "Unknown error")[-400:]
                return f"Command '{check.cmd}' failed (exit {res.returncode}): {err}"
        except Exception as e:
            return f"Command '{check.cmd}' execution failed: {e}"
        return None

    def check_json_valid(self, check: ArtifactCheck, project_root: Path = None) -> str | None:
        target = self._safe_resolve(check.path, project_root)
        if not target or not target.exists():
            return f"Missing file for JSON check: {check.path}"
        try:
            with open(target, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            return f"Invalid JSON in {check.path}: {e}"
        except Exception as e:
            return f"Error reading {check.path}: {e}"
        return None

    def examine(
        self,
        checks: list[ArtifactCheck],
        previous_errors: list[str] | None = None,
        project_root: str | Path = None,
    ) -> ErrorDelta:
        """Run all checks and return an ErrorDelta.

        Backward compatible: callers using examine(checks, project_root=...) keyword arg
        still work. Callers passing project_root as second positional arg should migrate
        to keyword usage.
        """
        if project_root and isinstance(project_root, str):
            project_root = Path(project_root)

        mapping = {
            "file_exists": self.check_file_exists,
            "file_not_empty": self.check_file_not_empty,
            "file_contains": self.check_file_contains,
            "cmd_exit_zero": self.check_cmd_exit_zero,
            "json_valid": self.check_json_valid,
        }

        current_errors: list[str] = []
        for check in checks:
            handler = mapping.get(check.type)
            if handler:
                err = handler(check, project_root=project_root)
                if err:
                    current_errors.append(err)
            else:
                current_errors.append(f"Unknown check type: {check.type}")

        prev = previous_errors if previous_errors is not None else []

        norm_prev = self._normalize_errors(prev)
        norm_curr = self._normalize_errors(current_errors)

        old_error_score = ErrorDelta.compute_score(prev)
        new_error_score = ErrorDelta.compute_score(current_errors)

        norm_prev_set = set(norm_prev)
        norm_curr_set = set(norm_curr)

        errors_resolved = [e for e in norm_prev if e not in norm_curr_set]
        errors_introduced = [e for e in norm_curr if e not in norm_prev_set]

        net_improvement = new_error_score <= old_error_score

        return ErrorDelta(
            operation_id=new_id(),
            errors_resolved=errors_resolved,
            errors_introduced=errors_introduced,
            old_error_score=old_error_score,
            new_error_score=new_error_score,
            net_improvement=net_improvement,
        )

    def verify_python_ast(self, file_path: str, error_line: int = 1) -> dict:
        """
        Verify Python code using AST analysis.
        
        Args:
            file_path: Path to Python file
            error_line: Line number to analyze around (default: 1)
            
        Returns:
            Structured JSON output with AST analysis results
        """
        analyzer = ASTAnalyzer()
        contract = analyzer.analyze([(file_path, error_line)])
        
        result = {
            "file": file_path,
            "language": "python",
            "is_fallback": contract.is_fallback,
            "error_type": contract.error_type,
            "total_size_bytes": contract.total_size_bytes,
        }
        
        if contract.is_fallback:
            result["raw_excerpt"] = contract.raw_excerpt
        else:
            result["affected_nodes"] = [
                {
                    "node_id": node.node_id,
                    "function_name": node.function_name,
                    "class_name": node.class_name,
                    "start_line": node.start_line,
                    "end_line": node.end_line,
                    "scope_path": node.scope_path,
                    "signature": node.signature,
                }
                for node in contract.affected_nodes
            ]
            
            # Check for missing return types
            missing_return_types = []
            for node in contract.affected_nodes:
                if node.signature and node.function_name:
                    # Check if signature has return type annotation
                    if "->" not in node.signature:
                        missing_return_types.append({
                            "function": node.function_name,
                            "line": node.start_line,
                            "signature": node.signature,
                        })
            
            if missing_return_types:
                result["warnings"] = {
                    "missing_return_types": missing_return_types
                }
        
        return result

    def verify_js_ast(self, file_path: str, error_line: int = 1) -> dict:
        """
        Verify JavaScript/TypeScript code using AST analysis.
        
        Args:
            file_path: Path to JS/TS file
            error_line: Line number to analyze around (default: 1)
            
        Returns:
            Structured JSON output with AST analysis results
        """
        analyzer = ASTAnalyzer()
        contract = analyzer.analyze([(file_path, error_line)])
        
        # Determine language from file extension
        suffix = Path(file_path).suffix.lower()
        language = "typescript" if suffix in (".ts", ".tsx") else "javascript"
        
        result = {
            "file": file_path,
            "language": language,
            "is_fallback": contract.is_fallback,
            "error_type": contract.error_type,
            "total_size_bytes": contract.total_size_bytes,
        }
        
        if contract.is_fallback:
            result["raw_excerpt"] = contract.raw_excerpt
        else:
            result["affected_nodes"] = [
                {
                    "node_id": node.node_id,
                    "function_name": node.function_name,
                    "class_name": node.class_name,
                    "start_line": node.start_line,
                    "end_line": node.end_line,
                    "scope_path": node.scope_path,
                    "signature": node.signature,
                }
                for node in contract.affected_nodes
            ]
            
            # Check for missing type annotations (TypeScript)
            if language == "typescript":
                missing_types = []
                for node in contract.affected_nodes:
                    if node.signature and node.function_name:
                        # Check if signature has type annotations
                        if ":" not in node.signature or "=>" not in node.signature:
                            missing_types.append({
                                "function": node.function_name,
                                "line": node.start_line,
                                "signature": node.signature,
                            })
                
                if missing_types:
                    result["warnings"] = {
                        "missing_type_annotations": missing_types
                    }
        
        return result
