"""
PatternExtractor v2 - Context-Aware with Signal Pairing

Key upgrade: Extract patterns based on COMBO signals:
(error_type + patch_diff_signal + file_context)

This transforms patterns from "labels" to "diagnostic insights"
"""

from __future__ import annotations
import re
import hashlib
from dataclasses import dataclass
from typing import Literal
from datetime import datetime

from core.schemas import FailureSurface, FailurePattern, FailureLesson


class PatternExtractorV2:
    """
    v2: Context-aware pattern extraction with signal pairing.
    
    Philosophy: Pattern = (error + attempted_fix + context)
    Not just: Pattern = error_type
    """
    
    def extract(self, surface: FailureSurface) -> tuple[FailurePattern, FailureLesson]:
        """
        Main extraction with signal pairing.
        
        Pipeline:
        1. Detect error type
        2. Detect code signals in patch
        3. Detect file context
        4. Pair signals → pattern
        5. Generate lesson
        """
        error = surface.error_text.lower()
        patch = surface.patch_diff.lower()
        files = surface.files_touched
        
        # Try high-signal patterns first (context-aware)
        rules = [
            self._rule_fix_symptom_not_root,
            self._rule_wrong_fix_strategy,
            self._rule_wrong_file_modified,
            self._rule_test_breaking_change,
            self._rule_incomplete_fix,
            self._rule_overfix,
            self._rule_wrong_assumption,
            self._rule_dependency_not_updated,
            self._rule_incorrect_refactor_scope,
            self._rule_no_op_patch_v2,
            # Fallback to basic patterns
            self._rule_missing_import,
            self._rule_syntax_error,
        ]
        
        for rule in rules:
            result = rule(surface, error, patch, files)
            if result:
                return result
        
        # Ultimate fallback
        return self._rule_generic(surface)
    
    # ── HIGH-SIGNAL PATTERNS (Context-Aware) ──────────────────────────────────
    
    def _rule_fix_symptom_not_root(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Used optional chaining/null check for undefined error
        Signal pairing: (undefined error + defensive code added)
        """
        # Signal 1: Error about undefined/null
        has_undefined_error = any(kw in error for kw in [
            "undefined", "cannot read property", "null"
        ])
        
        # Signal 2: Added defensive code
        has_defensive_code = any(kw in patch for kw in [
            "?.", "?.?", "null check", "if (", "&&"
        ])
        
        if has_undefined_error and has_defensive_code:
            # Extract what was accessed
            prop_match = re.search(r"property '(\w+)'", surface.error_text)
            prop_name = prop_match.group(1) if prop_match else "property"
            
            pattern = FailurePattern(
                pattern_type="fix_symptom_not_root",
                cause=f"added defensive code for undefined {prop_name}",
                location="function_body",
                action="added optional chaining or null check",
                symbols=[prop_name],
                signature=self._hash_pattern("fix_symptom_not_root", "defensive_code", "function_body"),
                context={
                    "error_type": "undefined_access",
                    "defensive_pattern": "optional_chaining"
                },
                attempted_fix="added optional chaining (?.) or null check",
                correct_direction="fix data flow - ensure data exists before render/access",
                confidence_score=0.7,
                anti_pattern_signature={
                    "error_regex": ["undefined", "cannot read property", "null"],
                    "code_signal": ["?.", "null check", "if (.*&&"]
                },
                usage_signals=[
                    "regex:useeffect",
                    "regex:usestate.*loading",
                    "regex:fetch|async|await",
                    "added loading state",
                    "fixed data flow"
                ]
            )
            
            lesson = FailureLesson(
                avoid="Using optional chaining (?.) to hide undefined errors without fixing root cause",
                prefer="Fix data flow: add loading state, ensure data fetched before access, or fix parent component state",
                confidence=0.7,
                applies_to=["javascript", "typescript", "react"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_wrong_fix_strategy(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Added null check for "is not a function" error
        Signal pairing: (function error + null check added)
        """
        # Signal 1: Function error
        has_function_error = any(kw in error for kw in [
            "is not a function", "not a function", "undefined is not"
        ])
        
        # Signal 2: Added null/undefined check
        has_null_check = any(kw in patch for kw in [
            "if (", "null", "undefined", "typeof"
        ])
        
        if has_function_error and has_null_check:
            # Extract function name
            func_match = re.search(r"(\w+) is not a function", surface.error_text)
            func_name = func_match.group(1) if func_match else "function"
            
            pattern = FailurePattern(
                pattern_type="wrong_fix_strategy",
                cause=f"added null check for '{func_name} is not a function' error",
                location="function_body",
                action="added conditional check before function call",
                symbols=[func_name],
                signature=self._hash_pattern("wrong_fix_strategy", "null_check_for_function", "function_body"),
                context={
                    "error_type": "not_a_function",
                    "wrong_strategy": "null_check"
                },
                attempted_fix=f"added null/undefined check before calling {func_name}",
                correct_direction="check imports - function likely not imported or imported incorrectly",
                confidence_score=0.8,
                anti_pattern_signature={
                    "error_regex": ["is not a function", "not a function"],
                    "code_signal": ["if (", "null", "undefined", "typeof"]
                },
                usage_signals=[
                    "added import",
                    "modified import",
                    "fixed module reference",
                    "regex:import.*react",
                    "regex:from ['\"].*['\"]"
                ]
            )
            
            lesson = FailureLesson(
                avoid="Adding null checks when error is 'X is not a function' - root cause is usually wrong import",
                prefer="Check import statements first: verify function is imported, check for typos, verify package version",
                confidence=0.8,
                applies_to=["javascript", "typescript", "react", "node"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_wrong_file_modified(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Modified child component when error in parent
        Signal pairing: (error mentions parent + modified child file)
        """
        if not files:
            return None
        
        # Extract file from error (simple heuristic)
        error_file_match = re.search(r'at (\w+Component)', surface.error_text)
        if not error_file_match:
            return None
        
        error_component = error_file_match.group(1)
        
        # Check if modified different file
        modified_files = [f.lower() for f in files]
        error_in_different_file = not any(error_component.lower() in f for f in modified_files)
        
        if error_in_different_file and len(files) > 0:
            pattern = FailurePattern(
                pattern_type="wrong_file_modified",
                cause=f"modified {files[0]} when error was in {error_component}",
                location="function_body",
                action="changed wrong component",
                symbols=[error_component],
                signature=self._hash_pattern("wrong_file_modified", "wrong_component", "function_body"),
                context={
                    "error_file": error_component,
                    "modified_file": files[0]
                },
                attempted_fix=f"modified {files[0]}",
                correct_direction=f"modify {error_component} where error actually occurred",
                confidence_score=0.6,
                anti_pattern_signature={
                    "error_regex": [r"at \w+Component"],
                    "code_signal": ["different_file_modified"]
                }
            )
            
            lesson = FailureLesson(
                avoid="Modifying child/sibling components when stack trace points to different component",
                prefer="Follow stack trace to actual error location - modify the component mentioned in error",
                confidence=0.6,
                applies_to=["react", "vue", "angular"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_test_breaking_change(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Changed function signature without updating tests
        Signal pairing: (test error + signature change in patch)
        """
        # Signal 1: Test error
        has_test_error = any(kw in error for kw in [
            "test", "expect", "assertion", "jest", "mocha"
        ])
        
        # Signal 2: Function signature change
        has_signature_change = any(kw in patch for kw in [
            "function", "def ", "const ", "=>"
        ])
        
        if has_test_error and has_signature_change:
            pattern = FailurePattern(
                pattern_type="test_breaking_change",
                cause="changed function signature without updating test calls",
                location="function_body",
                action="modified function parameters",
                symbols=[],
                signature=self._hash_pattern("test_breaking_change", "signature_change", "function_body"),
                context={
                    "error_type": "test_failure",
                    "change_type": "signature"
                },
                attempted_fix="changed function signature",
                correct_direction="update all test files that call this function with new signature",
                confidence_score=0.7,
                anti_pattern_signature={
                    "error_regex": ["test", "expect", "assertion"],
                    "code_signal": ["function", "def ", "=>"]
                }
            )
            
            lesson = FailureLesson(
                avoid="Changing function signatures without searching for all usages in tests",
                prefer="Before changing signature: search for function name in test files, update all calls",
                confidence=0.7,
                applies_to=["all_languages"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_incomplete_fix(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Fixed one occurrence but error still exists
        Signal pairing: (same error + small patch)
        """
        # Signal: Very small patch (likely only fixed one place)
        patch_lines = surface.patch_diff.count('\n')
        is_small_patch = patch_lines < 5
        
        # Signal: Error mentions multiple occurrences or "still"
        suggests_multiple = any(kw in error for kw in [
            "still", "another", "also", "multiple"
        ])
        
        if is_small_patch and suggests_multiple:
            pattern = FailurePattern(
                pattern_type="incomplete_fix",
                cause="fixed one occurrence but missed others",
                location="function_body",
                action="partial fix applied",
                symbols=[],
                signature=self._hash_pattern("incomplete_fix", "partial", "function_body"),
                context={
                    "patch_size": "small",
                    "error_suggests": "multiple_occurrences"
                },
                attempted_fix="fixed only first occurrence found",
                correct_direction="use global search (grep/find-all) to find ALL occurrences before fixing",
                confidence_score=0.6,
                anti_pattern_signature={
                    "error_regex": ["still", "another", "also"],
                    "code_signal": ["small_patch"]
                }
            )
            
            lesson = FailureLesson(
                avoid="Fixing only the first occurrence without checking for others",
                prefer="Use find-all-references or global search to locate ALL occurrences, fix them all",
                confidence=0.6,
                applies_to=["all_languages"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_overfix(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Changed too many things for one error
        Signal pairing: (simple error + large patch)
        """
        # Signal 1: Simple error (one line)
        error_lines = surface.error_text.count('\n')
        is_simple_error = error_lines < 3
        
        # Signal 2: Large patch
        patch_lines = surface.patch_diff.count('\n')
        is_large_patch = patch_lines > 20
        
        if is_simple_error and is_large_patch:
            pattern = FailurePattern(
                pattern_type="overfix",
                cause="changed multiple things for single error",
                location="function_body",
                action="made extensive changes",
                symbols=[],
                signature=self._hash_pattern("overfix", "too_many_changes", "function_body"),
                context={
                    "error_complexity": "simple",
                    "patch_size": "large"
                },
                attempted_fix="made large refactor or multiple changes",
                correct_direction="minimal fix - change ONLY what's needed to resolve the specific error",
                confidence_score=0.7,
                anti_pattern_signature={
                    "error_regex": ["simple_single_line"],
                    "code_signal": ["large_patch"]
                }
            )
            
            lesson = FailureLesson(
                avoid="Making large refactors or multiple unrelated changes when fixing single error",
                prefer="Surgical fix: change minimum code needed, refactor separately after bug is fixed",
                confidence=0.7,
                applies_to=["all_languages"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_wrong_assumption(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Assumed array but got object (or vice versa)
        Signal pairing: (type error + array method in patch)
        """
        # Signal 1: Type error
        has_type_error = "typeerror" in error
        
        # Signal 2: Array method used
        has_array_method = any(kw in patch for kw in [
            ".map", ".filter", ".reduce", ".foreach"
        ])
        
        if has_type_error and has_array_method:
            pattern = FailurePattern(
                pattern_type="wrong_assumption",
                cause="assumed array but got object or null",
                location="function_body",
                action="called array method on non-array",
                symbols=[],
                signature=self._hash_pattern("wrong_assumption", "array_vs_object", "function_body"),
                context={
                    "error_type": "type_mismatch",
                    "assumed_type": "array"
                },
                attempted_fix="called .map/.filter on data without checking type",
                correct_direction="check API response structure or use Object.values() if data is object",
                confidence_score=0.7,
                anti_pattern_signature={
                    "error_regex": ["typeerror"],
                    "code_signal": [".map", ".filter", ".reduce"]
                }
            )
            
            lesson = FailureLesson(
                avoid="Assuming data types without checking API documentation or actual response",
                prefer="Add type guards (Array.isArray) or check API docs for actual return type",
                confidence=0.7,
                applies_to=["javascript", "typescript"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_dependency_not_updated(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Used new API without upgrading package
        Signal pairing: (import error + new API name)
        """
        # Signal: Import or module error
        has_import_error = any(kw in error for kw in [
            "cannot find", "does not exist", "is not exported"
        ])
        
        # Signal: Patch adds import
        has_new_import = "import" in patch
        
        if has_import_error and has_new_import:
            # Extract what was imported
            import_match = re.search(r'import.*{([^}]+)}', surface.patch_diff)
            imported = import_match.group(1).strip() if import_match else "API"
            
            pattern = FailurePattern(
                pattern_type="dependency_not_updated",
                cause=f"used {imported} without checking package version",
                location="top_of_file",
                action="imported new API",
                symbols=[imported],
                signature=self._hash_pattern("dependency_not_updated", "version_mismatch", "top_of_file"),
                context={
                    "error_type": "import_not_found",
                    "api_name": imported
                },
                attempted_fix=f"imported {imported}",
                correct_direction="check package.json - may need to upgrade package version",
                confidence_score=0.6,
                anti_pattern_signature={
                    "error_regex": ["cannot find", "does not exist", "not exported"],
                    "code_signal": ["import"]
                }
            )
            
            lesson = FailureLesson(
                avoid="Using new APIs without verifying package version supports them",
                prefer="Check package docs for version requirements, upgrade if needed before importing",
                confidence=0.6,
                applies_to=["javascript", "typescript", "python"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_incorrect_refactor_scope(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Refactored too much at once
        Signal pairing: (multiple files changed + error)
        """
        # Signal: Multiple files modified
        multiple_files = len(files) > 2
        
        # Signal: Large changes
        patch_lines = surface.patch_diff.count('\n')
        large_changes = patch_lines > 30
        
        if multiple_files and large_changes:
            pattern = FailurePattern(
                pattern_type="incorrect_refactor_scope",
                cause="refactored multiple files for single bug",
                location="function_body",
                action="large multi-file refactor",
                symbols=[],
                signature=self._hash_pattern("incorrect_refactor_scope", "too_broad", "function_body"),
                context={
                    "files_changed": len(files),
                    "scope": "too_broad"
                },
                attempted_fix=f"refactored {len(files)} files",
                correct_direction="fix bug first with minimal changes, refactor separately",
                confidence_score=0.6,
                anti_pattern_signature={
                    "error_regex": ["single_error"],
                    "code_signal": ["multiple_files", "large_patch"]
                }
            )
            
            lesson = FailureLesson(
                avoid="Large multi-file refactors when fixing small bugs - introduces new errors",
                prefer="Surgical bug fix first, then refactor in separate commit after tests pass",
                confidence=0.6,
                applies_to=["all_languages"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_no_op_patch_v2(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Generated identical code (v2 with context)
        Signal: Empty or whitespace-only patch
        """
        if not surface.patch_diff.strip():
            pattern = FailurePattern(
                pattern_type="no_op_patch",
                cause="generated identical code",
                location="function_body",
                action="no semantic changes made",
                symbols=[],
                signature=self._hash_pattern("no_op_patch", "identical", "function_body"),
                context={
                    "error_type": error.split(':')[0] if ':' in error else "unknown",
                    "strategy_failed": "regeneration"
                },
                attempted_fix="regenerated same code",
                correct_direction="change strategy completely - try different approach or ask for clarification",
                confidence_score=0.8,
                anti_pattern_signature={
                    "error_regex": [".*"],
                    "code_signal": ["empty_patch"]
                }
            )
            
            lesson = FailureLesson(
                avoid="Regenerating same code when first attempt failed - indicates wrong strategy",
                prefer="Change approach: analyze error differently, try alternative solution, or request more context",
                confidence=0.8,
                applies_to=["all_languages"]
            )
            
            return pattern, lesson
        
        return None
    
    # ── BASIC PATTERNS (Fallback) ─────────────────────────────────────────────
    
    def _rule_missing_import(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """Basic: Missing import (kept for coverage)"""
        if "is not defined" in error and "import" not in patch:
            match = re.search(r"name '(\w+)' is not defined", surface.error_text)
            symbol = match.group(1) if match else "symbol"
            
            pattern = FailurePattern(
                pattern_type="import_missing",
                cause="missing import",
                location="top_of_file",
                action=f"used {symbol} without import",
                symbols=[symbol],
                signature=self._hash_pattern("import_missing", "basic", "top_of_file"),
                context={"symbol": symbol},
                confidence_score=0.7  # v2: Increased to pass filter (>0.6)
            )
            
            lesson = FailureLesson(
                avoid="Using symbols without importing them",
                prefer="Add import statement at top of file",
                confidence=0.5,
                applies_to=["python", "javascript"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_syntax_error(
        self,
        surface: FailureSurface,
        error: str,
        patch: str,
        files: list[str]
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """Basic: Syntax error (kept for coverage)"""
        if "syntaxerror" in error:
            pattern = FailurePattern(
                pattern_type="syntax_error",
                cause="syntax error",
                location="function_body",
                action="introduced syntax error",
                symbols=[],
                signature=self._hash_pattern("syntax_error", "basic", "function_body"),
                confidence_score=0.7  # v2: Increased to pass filter
            )
            
            lesson = FailureLesson(
                avoid="Introducing syntax errors",
                prefer="Check syntax before submitting",
                confidence=0.4,
                applies_to=["all_languages"]
            )
            
            return pattern, lesson
        
        return None
    
    def _rule_generic(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson]:
        """Ultimate fallback"""
        pattern = FailurePattern(
            pattern_type="logic_error",
            cause="unclassified error",
            location="function_body",
            action="made changes that caused error",
            symbols=[],
            signature=self._hash_pattern("logic_error", "generic", "function_body"),
            confidence_score=0.7  # v2: Increased to pass filter
        )
        
        lesson = FailureLesson(
            avoid="Making changes without understanding error context",
            prefer="Analyze error carefully before suggesting fix",
            confidence=0.2,
            applies_to=["all_languages"]
        )
        
        return pattern, lesson
    
    # ── Helper ─────────────────────────────────────────────────────────────────
    
    def _hash_pattern(self, pattern_type: str, cause: str, location: str) -> str:
        """Compute signature for deduplication"""
        content = f"{pattern_type}:{cause}:{location}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
