"""
Pattern Extractor - The Brain of Learning Loop

Extracts semantic patterns from raw failures.
Rule-based (no ML yet) - 10 core rules.

Philosophy: Structured learning, not log storage.
"""

from __future__ import annotations
import re
import hashlib
from dataclasses import dataclass
from typing import Literal
from datetime import datetime


# ── Data Models (3-Layer Abstraction) ────────────────────────────────────────

@dataclass
class FailureSurface:
    """Layer 1: Observable - what happened"""
    failure_id: str
    patch_diff: str
    error_text: str              # from ErrorDelta.errors_introduced[0]
    files_touched: list[str]
    timestamp: datetime
    session_id: str


@dataclass
class FailurePattern:
    """Layer 2: Semantic - why it failed (LLM-understandable)"""
    pattern_type: Literal[
        "syntax_error",
        "runtime_error",
        "no_op_patch",
        "import_missing",
        "type_mismatch",
        "logic_error"
    ]
    cause: str                   # e.g., "missing import"
    location: Literal[
        "top_of_file",
        "function_body",
        "class_definition",
        "end_of_file"
    ]
    action: str                  # e.g., "added function without import"
    symbols: list[str]           # e.g., ["foo", "bar"]
    signature: str               # hash for dedup
    confidence_score: float = 0.8  # v2: Default for legacy extractor (high enough to pass filter)


@dataclass
class FailureLesson:
    """Layer 3: Strategic - what to do differently (decision impact)"""
    avoid: str                   # What NOT to do
    prefer: str                  # What to do instead
    confidence: float            # 0.0-1.0 (based on frequency)
    applies_to: list[str]        # e.g., ["python", "import_statements"]


# ── Pattern Extractor ─────────────────────────────────────────────────────────

class PatternExtractor:
    """
    Extract semantic patterns from raw failures.
    
    Pipeline:
        FailureSurface → FailurePattern → FailureLesson
    
    Uses 10 rule-based patterns (no ML yet).
    """
    
    def extract(self, surface: FailureSurface) -> tuple[FailurePattern, FailureLesson]:
        """
        Main extraction pipeline.
        
        Returns: (pattern, lesson)
        """
        # Try each rule in priority order
        rules = [
            self._rule_no_op_patch,
            self._rule_missing_import,
            self._rule_unmatched_bracket,
            self._rule_incorrect_indentation,
            self._rule_missing_colon,
            self._rule_type_mismatch,
            self._rule_undefined_variable,
            self._rule_attribute_error,
            self._rule_index_out_of_range,
            self._rule_division_by_zero,
        ]
        
        for rule in rules:
            result = rule(surface)
            if result:
                pattern, lesson = result
                return pattern, lesson
        
        # Fallback: generic pattern
        return self._rule_generic(surface)
    
    # ── Rule 1: No-Op Patch ───────────────────────────────────────────────────
    
    def _rule_no_op_patch(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Patch doesn't change anything
        Cause: Identical content before/after
        """
        # Check if patch is empty or only whitespace
        if not surface.patch_diff.strip():
            pattern = FailurePattern(
                pattern_type="no_op_patch",
                cause="identical content",
                location="function_body",
                action="generated patch with no semantic changes",
                symbols=[],
                signature=self._hash_pattern("no_op_patch", "identical_content", "function_body")
            )
            
            lesson = FailureLesson(
                avoid="generating patches that don't change logic",
                prefer="analyze error carefully before suggesting changes",
                confidence=0.5,  # will be updated by frequency
                applies_to=["all_languages"]
            )
            
            return pattern, lesson
        
        return None
    
    # ── Rule 2: Missing Import ────────────────────────────────────────────────
    
    def _rule_missing_import(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Added code uses undefined name
        Cause: Missing import statement
        """
        error = surface.error_text
        
        if "NameError" in error or "is not defined" in error:
            # Extract symbol name
            match = re.search(r"name '(\w+)' is not defined", error)
            if match:
                symbol = match.group(1)
                
                # Check if symbol appears in patch but no import added
                if symbol in surface.patch_diff and "import" not in surface.patch_diff:
                    pattern = FailurePattern(
                        pattern_type="import_missing",
                        cause="missing import",
                        location="top_of_file",
                        action=f"added code using '{symbol}' without import",
                        symbols=[symbol],
                        signature=self._hash_pattern("import_missing", "missing_import", "top_of_file")
                    )
                    
                    lesson = FailureLesson(
                        avoid="adding new symbol without checking imports",
                        prefer="add import statement before using new symbol",
                        confidence=0.5,
                        applies_to=["python", "import_statements"]
                    )
                    
                    return pattern, lesson
        
        return None
    
    # ── Rule 3: Unmatched Bracket ─────────────────────────────────────────────
    
    def _rule_unmatched_bracket(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: Syntax error with unmatched bracket
        Cause: Missing closing bracket
        """
        error = surface.error_text
        
        if "SyntaxError" in error and any(kw in error for kw in ["unmatched", "expected ']'", "expected ')'"]):
            # Determine bracket type
            if "']'" in error or "'['" in error:
                bracket_type = "square_bracket"
            elif "')'" in error or "'('" in error:
                bracket_type = "parenthesis"
            else:
                bracket_type = "bracket"
            
            pattern = FailurePattern(
                pattern_type="syntax_error",
                cause=f"unmatched {bracket_type}",
                location="function_body",
                action=f"added code with unmatched {bracket_type}",
                symbols=[],
                signature=self._hash_pattern("syntax_error", f"unmatched_{bracket_type}", "function_body")
            )
            
            lesson = FailureLesson(
                avoid="writing complex expressions without bracket matching",
                prefer="use simpler expressions or verify bracket pairs",
                confidence=0.5,
                applies_to=["python", "syntax"]
            )
            
            return pattern, lesson
        
        return None
    
    # ── Rule 4: Incorrect Indentation ─────────────────────────────────────────
    
    def _rule_incorrect_indentation(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: IndentationError
        Cause: Wrong indentation level
        """
        error = surface.error_text
        
        if "IndentationError" in error or "unexpected indent" in error:
            pattern = FailurePattern(
                pattern_type="syntax_error",
                cause="incorrect indentation",
                location="function_body",
                action="added code with wrong indentation level",
                symbols=[],
                signature=self._hash_pattern("syntax_error", "incorrect_indentation", "function_body")
            )
            
            lesson = FailureLesson(
                avoid="mixing tabs and spaces or wrong indent level",
                prefer="match existing indentation style (4 spaces for Python)",
                confidence=0.5,
                applies_to=["python", "indentation"]
            )
            
            return pattern, lesson
        
        return None
    
    # ── Rule 5: Missing Colon ─────────────────────────────────────────────────
    
    def _rule_missing_colon(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: SyntaxError with missing colon
        Cause: Forgot colon after if/for/def/class
        """
        error = surface.error_text
        
        if "SyntaxError" in error and "expected ':'" in error:
            # Determine statement type
            stmt_type = "statement"
            for stmt in ["if", "for", "while", "def", "class"]:
                if stmt in surface.patch_diff:
                    stmt_type = stmt
                    break
            
            pattern = FailurePattern(
                pattern_type="syntax_error",
                cause="missing colon",
                location="function_body",
                action=f"added {stmt_type} statement without colon",
                symbols=[],
                signature=self._hash_pattern("syntax_error", "missing_colon", "function_body")
            )
            
            lesson = FailureLesson(
                avoid="forgetting colon after control flow statements",
                prefer="always add colon after if/for/while/def/class",
                confidence=0.5,
                applies_to=["python", "syntax"]
            )
            
            return pattern, lesson
        
        return None
    
    # ── Rule 6: Type Mismatch ─────────────────────────────────────────────────
    
    def _rule_type_mismatch(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: TypeError
        Cause: Wrong type passed to function
        """
        error = surface.error_text
        
        if "TypeError" in error:
            # Extract expected vs actual types
            match = re.search(r"expected (\w+), got (\w+)", error)
            if match:
                expected, actual = match.groups()
                
                pattern = FailurePattern(
                    pattern_type="type_mismatch",
                    cause=f"passed {actual} instead of {expected}",
                    location="function_body",
                    action="called function with wrong type",
                    symbols=[],
                    signature=self._hash_pattern("type_mismatch", f"{actual}_to_{expected}", "function_body")
                )
                
                lesson = FailureLesson(
                    avoid="passing wrong types without checking function signature",
                    prefer="verify parameter types before calling functions",
                    confidence=0.5,
                    applies_to=["python", "type_checking"]
                )
                
                return pattern, lesson
        
        return None
    
    # ── Rule 7: Undefined Variable ────────────────────────────────────────────
    
    def _rule_undefined_variable(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: NameError for local variable
        Cause: Used variable before assignment
        """
        error = surface.error_text
        
        if "NameError" in error and "local variable" in error:
            match = re.search(r"local variable '(\w+)'", error)
            if match:
                var_name = match.group(1)
                
                pattern = FailurePattern(
                    pattern_type="runtime_error",
                    cause="used before assignment",
                    location="function_body",
                    action=f"used variable '{var_name}' before defining it",
                    symbols=[var_name],
                    signature=self._hash_pattern("runtime_error", "undefined_variable", "function_body")
                )
                
                lesson = FailureLesson(
                    avoid="using variables before assigning values",
                    prefer="initialize variables before use",
                    confidence=0.5,
                    applies_to=["python", "variables"]
                )
                
                return pattern, lesson
        
        return None
    
    # ── Rule 8: Attribute Error ───────────────────────────────────────────────
    
    def _rule_attribute_error(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: AttributeError
        Cause: Object doesn't have attribute
        """
        error = surface.error_text
        
        if "AttributeError" in error:
            match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error)
            if match:
                obj_type, attr_name = match.groups()
                
                pattern = FailurePattern(
                    pattern_type="runtime_error",
                    cause=f"attribute '{attr_name}' doesn't exist on {obj_type}",
                    location="function_body",
                    action="accessed non-existent attribute",
                    symbols=[attr_name],
                    signature=self._hash_pattern("runtime_error", "attribute_error", "function_body")
                )
                
                lesson = FailureLesson(
                    avoid="accessing attributes without checking object type",
                    prefer="verify object has attribute before accessing",
                    confidence=0.5,
                    applies_to=["python", "attributes"]
                )
                
                return pattern, lesson
        
        return None
    
    # ── Rule 9: Index Out of Range ────────────────────────────────────────────
    
    def _rule_index_out_of_range(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: IndexError
        Cause: Accessed list index that doesn't exist
        """
        error = surface.error_text
        
        if "IndexError" in error and "out of range" in error:
            pattern = FailurePattern(
                pattern_type="runtime_error",
                cause="index out of range",
                location="function_body",
                action="accessed list index without bounds check",
                symbols=[],
                signature=self._hash_pattern("runtime_error", "index_out_of_range", "function_body")
            )
            
            lesson = FailureLesson(
                avoid="accessing list indices without checking length",
                prefer="check list length before accessing or use try/except",
                confidence=0.5,
                applies_to=["python", "lists"]
            )
            
            return pattern, lesson
        
        return None
    
    # ── Rule 10: Division by Zero ─────────────────────────────────────────────
    
    def _rule_division_by_zero(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson] | None:
        """
        Pattern: ZeroDivisionError
        Cause: Divided by zero
        """
        error = surface.error_text
        
        if "ZeroDivisionError" in error:
            pattern = FailurePattern(
                pattern_type="runtime_error",
                cause="division by zero",
                location="function_body",
                action="performed division without zero check",
                symbols=[],
                signature=self._hash_pattern("runtime_error", "division_by_zero", "function_body")
            )
            
            lesson = FailureLesson(
                avoid="dividing without checking denominator is non-zero",
                prefer="add zero check before division or use try/except",
                confidence=0.5,
                applies_to=["python", "arithmetic"]
            )
            
            return pattern, lesson
        
        return None
    
    # ── Fallback: Generic Pattern ─────────────────────────────────────────────
    
    def _rule_generic(
        self,
        surface: FailureSurface
    ) -> tuple[FailurePattern, FailureLesson]:
        """
        Fallback pattern when no specific rule matches.
        """
        # Classify as syntax or runtime based on error text
        if "SyntaxError" in surface.error_text or "IndentationError" in surface.error_text:
            pattern_type = "syntax_error"
            cause = "syntax error"
        elif any(kw in surface.error_text for kw in ["Error", "Exception"]):
            pattern_type = "runtime_error"
            cause = "runtime error"
        else:
            pattern_type = "logic_error"
            cause = "logic error"
        
        pattern = FailurePattern(
            pattern_type=pattern_type,  # type: ignore
            cause=cause,
            location="function_body",
            action="generated patch that caused error",
            symbols=[],
            signature=self._hash_pattern(pattern_type, cause, "function_body")
        )
        
        lesson = FailureLesson(
            avoid="making changes without understanding error context",
            prefer="analyze error message carefully before suggesting fix",
            confidence=0.3,  # low confidence for generic
            applies_to=["all_languages"]
        )
        
        return pattern, lesson
    
    # ── Helper: Hash Pattern ──────────────────────────────────────────────────
    
    def _hash_pattern(
        self,
        pattern_type: str,
        cause: str,
        location: str
    ) -> str:
        """
        Compute signature for pattern deduplication.
        
        Signature = SHA-256(pattern_type + cause + location)
        """
        content = f"{pattern_type}:{cause}:{location}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
