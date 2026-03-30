"""
FailureMemory - Learning Loop Storage & Retrieval

Structured learning system, NOT log storage.
Implements 3-layer abstraction: Surface → Pattern → Lesson

Requirements: v6.2 Phase 1 (Learning Loop)
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, asdict

from core.schemas import FailureSurface, FailurePattern, FailureLesson
from core.pattern_extractor_v2 import PatternExtractorV2

logger = logging.getLogger(__name__)


@dataclass
class FailureEntry:
    """Complete failure record with all 3 layers"""
    surface: FailureSurface
    pattern: FailurePattern
    lesson: FailureLesson
    frequency: int = 1  # How many times this pattern occurred
    
    # v2: Effectiveness tracking (measurement)
    times_injected: int = 0  # How many times this lesson was shown to LLM
    times_helped: float = 0.0  # v4: Changed to float for fractional credit (Phase 1d.2)
    effectiveness: float = 0.0  # times_helped / times_injected (computed)


class FailureMemoryStore:
    """
    Persistent storage with TTL, dedup, and frequency tracking.
    
    Storage strategy:
    - TTL: 7 days (configurable)
    - Dedup: by pattern signature
    - Max entries: 1000 (LRU eviction)
    - Format: JSON lines (one entry per line)
    """
    
    def __init__(
        self,
        storage_path: Path | str,
        ttl_days: int = 7,
        max_entries: int = 1000
    ):
        self._storage_path = Path(storage_path)
        self._ttl = timedelta(days=ttl_days)
        self._max_entries = max_entries
        
        # In-memory index for fast lookup
        self._by_signature: dict[str, FailureEntry] = {}
        self._by_frequency: dict[str, int] = {}
        
        # Ensure storage directory exists
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing entries
        self._load_from_disk()
    
    def _load_from_disk(self) -> None:
        """Load entries from disk into memory"""
        if not self._storage_path.exists():
            logger.info(f"No existing failure memory at {self._storage_path}")
            return
        
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        # Reconstruct entry
                        surface = FailureSurface(**data['surface'])
                        pattern = FailurePattern(**data['pattern'])
                        lesson = FailureLesson(**data['lesson'])
                        frequency = data.get('frequency', 1)
                        
                        # v2: Load effectiveness tracking fields
                        times_injected = data.get('times_injected', 0)
                        times_helped = data.get('times_helped', 0)
                        effectiveness = data.get('effectiveness', 0.0)
                        
                        entry = FailureEntry(
                            surface=surface,
                            pattern=pattern,
                            lesson=lesson,
                            frequency=frequency,
                            times_injected=times_injected,
                            times_helped=times_helped,
                            effectiveness=effectiveness
                        )
                        
                        self._by_signature[pattern.signature] = entry
                        self._by_frequency[pattern.signature] = frequency
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse failure entry: {e}")
                        continue
            
            logger.info(f"Loaded {len(self._by_signature)} failure patterns from disk")
            
        except Exception as e:
            logger.error(f"Failed to load failure memory: {e}")
    
    def _save_to_disk(self) -> None:
        """Save all entries to disk (overwrites file)"""
        try:
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                for entry in self._by_signature.values():
                    data = {
                        'surface': entry.surface.model_dump(),
                        'pattern': entry.pattern.model_dump(),
                        'lesson': entry.lesson.model_dump(),
                        'frequency': entry.frequency,
                        # v2: Save effectiveness tracking fields
                        'times_injected': entry.times_injected,
                        'times_helped': entry.times_helped,
                        'effectiveness': entry.effectiveness
                    }
                    f.write(json.dumps(data) + '\n')
            
            logger.debug(f"Saved {len(self._by_signature)} entries to disk")
            
        except Exception as e:
            logger.error(f"Failed to save failure memory: {e}")
    
    def store(
        self,
        surface: FailureSurface,
        pattern: FailurePattern,
        lesson: FailureLesson
    ) -> None:
        """
        Store failure with dedup and frequency tracking.
        
        If pattern already exists:
        - Increment frequency
        - Update lesson confidence based on frequency
        
        If new pattern:
        - Add to index
        - Initialize frequency to 1
        """
        # Check if pattern already exists (dedup)
        if pattern.signature in self._by_signature:
            # Increment frequency
            self._by_frequency[pattern.signature] += 1
            
            # Update existing entry
            existing = self._by_signature[pattern.signature]
            existing.frequency = self._by_frequency[pattern.signature]
            
            # Update lesson confidence based on frequency
            # Formula: confidence = min(1.0, frequency / 10.0)
            # 10 occurrences = 100% confidence
            existing.lesson.confidence = min(
                1.0,
                self._by_frequency[pattern.signature] / 10.0
            )
            
            logger.info(
                f"Pattern {pattern.signature[:8]} seen {existing.frequency} times, "
                f"confidence now {existing.lesson.confidence:.2f}"
            )
        else:
            # New pattern
            entry = FailureEntry(
                surface=surface,
                pattern=pattern,
                lesson=lesson,
                frequency=1
            )
            self._by_signature[pattern.signature] = entry
            self._by_frequency[pattern.signature] = 1
            
            logger.info(f"New failure pattern stored: {pattern.pattern_type} - {pattern.cause}")
        
        # Enforce max entries (LRU eviction)
        if len(self._by_signature) > self._max_entries:
            self._evict_oldest()
        
        # Save to disk
        self._save_to_disk()
    
    def _evict_oldest(self) -> None:
        """Evict oldest entry (by timestamp) to maintain max_entries limit"""
        if not self._by_signature:
            return
        
        # Find oldest entry
        oldest_sig = None
        oldest_time = None
        
        for sig, entry in self._by_signature.items():
            timestamp = datetime.fromisoformat(entry.surface.timestamp)
            if oldest_time is None or timestamp < oldest_time:
                oldest_time = timestamp
                oldest_sig = sig
        
        if oldest_sig:
            del self._by_signature[oldest_sig]
            del self._by_frequency[oldest_sig]
            logger.debug(f"Evicted oldest pattern: {oldest_sig[:8]}")
    
    def purge_expired(self) -> int:
        """
        Remove entries older than TTL.
        
        Returns: number of entries purged
        """
        now = datetime.now()
        expired = []
        
        for sig, entry in self._by_signature.items():
            timestamp = datetime.fromisoformat(entry.surface.timestamp)
            if now - timestamp > self._ttl:
                expired.append(sig)
        
        for sig in expired:
            del self._by_signature[sig]
            del self._by_frequency[sig]
        
        if expired:
            logger.info(f"Purged {len(expired)} expired patterns")
            self._save_to_disk()
        
        return len(expired)
    
    def get_all_entries(self) -> list[FailureEntry]:
        """Get all stored entries (for retrieval)"""
        return list(self._by_signature.values())
    
    def get_stats(self) -> dict:
        """Get memory statistics"""
        return {
            "total_patterns": len(self._by_signature),
            "total_occurrences": sum(self._by_frequency.values()),
            "most_common": sorted(
                self._by_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def _increment_injection_count(self, signature: str) -> None:
        """Increment times_injected for a pattern (v2: effectiveness tracking)"""
        if signature in self._by_signature:
            entry = self._by_signature[signature]
            entry.times_injected += 1
            self._save_to_disk()
            logger.debug(f"Pattern {signature[:8]} injected {entry.times_injected} times")
    
    def _increment_helped_count(self, signature: str) -> None:
        """Increment times_helped for a pattern (v2: effectiveness tracking)"""
        if signature in self._by_signature:
            entry = self._by_signature[signature]
            entry.times_helped += 1
            
            # Recompute effectiveness
            if entry.times_injected > 0:
                entry.effectiveness = entry.times_helped / entry.times_injected
            
            self._save_to_disk()
            logger.info(
                f"Pattern {signature[:8]} helped! Effectiveness: {entry.effectiveness:.2%} "
                f"({entry.times_helped}/{entry.times_injected})"
            )
    
    def _increment_helped_count_split(
        self,
        signature: str,
        credit: float = 1.0  # v4: fractional credit (Phase 1d.2)
    ) -> None:
        """
        v4: Increment with fractional credit to handle co-occurrence (Phase 1d.2).
        
        When multiple patterns are injected together, split credit
        to avoid over-crediting weak patterns.
        """
        if signature in self._by_signature:
            entry = self._by_signature[signature]
            entry.times_helped += credit  # Fractional increment
            
            # Recompute effectiveness
            if entry.times_injected > 0:
                entry.effectiveness = entry.times_helped / entry.times_injected
            
            self._save_to_disk()
            logger.info(
                f"Pattern {signature[:8]} helped (credit={credit:.2f})! "
                f"Effectiveness: {entry.effectiveness:.2%} "
                f"({entry.times_helped:.1f}/{entry.times_injected})"
            )
    
    def _check_pattern_usage(self, pattern: FailurePattern, patch_diff: str) -> bool:
        """
        Check if pattern's guidance was actually followed in the patch (v3: attribution fix).
        
        Returns True if patch shows evidence of following pattern's correct_direction.
        This prevents false attribution where pattern was injected but not used.
        """
        if not pattern.correct_direction:
            return False
        
        patch_lower = patch_diff.lower()
        direction_lower = pattern.correct_direction.lower()
        
        # Extract key action words from correct_direction
        action_keywords = []
        
        if "import" in direction_lower:
            action_keywords.append("import")
        
        if "check" in direction_lower and "type" in direction_lower:
            action_keywords.extend(["isinstance", "type(", "array.isarray"])
        
        if "loading" in direction_lower or "state" in direction_lower:
            action_keywords.extend(["loading", "isloading", "usestate"])
        
        if "data flow" in direction_lower or "fetch" in direction_lower:
            action_keywords.extend(["fetch", "async", "await", "useeffect"])
        
        if "parent" in direction_lower or "component" in direction_lower:
            # Check if modified correct file
            if pattern.context and "error_file" in pattern.context:
                error_file = pattern.context["error_file"].lower()
                if error_file in patch_lower:
                    return True
        
        # Check if ANY action keyword appears in patch
        if action_keywords:
            return any(kw in patch_lower for kw in action_keywords)
        
        # Fallback: if no specific keywords, assume pattern was considered
        return True
    
    def _check_pattern_usage_v2(self, pattern: FailurePattern, patch_diff: str) -> bool:
        """
        v4: Intent signature detection (Phase 1d.1) - more precise than keyword matching.
        
        Checks for structured signals rather than surface keywords.
        Falls back to v3 keyword detection if no usage_signals defined.
        """
        if not pattern.usage_signals:
            # Fallback to v3 keyword detection
            return self._check_pattern_usage(pattern, patch_diff)
        
        patch_lower = patch_diff.lower()
        
        # Check each signal
        for signal in pattern.usage_signals:
            # Simple regex support
            if signal.startswith("regex:"):
                import re
                regex_pattern = signal[6:]  # Remove "regex:" prefix
                try:
                    if re.search(regex_pattern, patch_lower, re.IGNORECASE):
                        return True
                except re.error:
                    logger.warning(f"Invalid regex pattern: {regex_pattern}")
                    continue
            else:
                # Structured signal detection
                if signal == "added import":
                    # Look for "+ import" or "+import" (diff format)
                    if "+ import" in patch_lower or "+import" in patch_lower:
                        return True
                elif signal == "modified import":
                    # Look for "- import" followed by "+ import"
                    if "- import" in patch_lower and "+ import" in patch_lower:
                        return True
                elif signal == "fixed module reference":
                    # Look for changes to module paths
                    if "from " in patch_lower and ("." in patch_lower or "/" in patch_lower):
                        return True
                elif signal in patch_lower:
                    # Direct match
                    return True
        
        return False


class FailureMemoryRetriever:
    """
    Intelligent retrieval of relevant failures.
    
    Similar to HybridRetriever but for patterns.
    Uses keyword matching + recency + frequency.
    """
    
    def __init__(self, store: FailureMemoryStore):
        self._store = store
    
    def search_relevant(
        self,
        current_task: str,
        current_error: str,
        top_k: int = 3
    ) -> list[tuple[FailurePattern, FailureLesson, float]]:
        """
        Search for relevant past failures.
        
        Ranking factors (v2 - effectiveness-weighted):
        1. Effectiveness (times_helped / times_injected) - 40%
        2. Context match (file_type, framework, error_type) - 30%
        3. Pattern type match - 20%
        4. Recency + Frequency - 10%
        
        Only inject patterns with confidence_score > 0.6
        
        Returns: [(pattern, lesson, relevance_score)]
        """
        entries = self._store.get_all_entries()
        
        if not entries:
            return []
        
        candidates = []
        
        for entry in entries:
            # Filter: only consider high-confidence patterns
            if entry.pattern.confidence_score <= 0.6:
                continue
            
            score = self._compute_relevance(
                entry.pattern,
                entry.surface.timestamp,
                entry.frequency,
                entry.effectiveness,  # v2: pass effectiveness
                current_task,
                current_error
            )
            candidates.append((entry.pattern, entry.lesson, score))
        
        # Sort by relevance score descending
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        return candidates[:top_k]
    
    def _compute_relevance(
        self,
        pattern: FailurePattern,
        timestamp: str,
        frequency: int,
        effectiveness: float,  # v2: effectiveness parameter
        task: str,
        error: str
    ) -> float:
        """
        Compute relevance score (0.0-1.0) - v2 with effectiveness weighting.
        
        Factors:
        - Effectiveness (times_helped / times_injected): +0.4 (MOST IMPORTANT)
        - Context match (file_type, framework, error_type): +0.3
        - Pattern type match: +0.2
        - Recency + Frequency: +0.1
        
        v3: Uses Bayesian smoothing for effectiveness to handle cold start.
        """
        score = 0.0
        
        # 1. Effectiveness (40%) - v3: WITH BAYESIAN SMOOTHING
        # Get the entry to check times_injected
        entry = None
        for e in self._store.get_all_entries():
            if e.pattern.signature == pattern.signature:
                entry = e
                break
        
        if entry and entry.times_injected < 5:
            # Cold start: use low weight + frequency as proxy
            effective_score = 0.1 * min(1.0, frequency / 10)
        elif entry:
            # Bayesian smoothing: (successes + 1) / (attempts + 2)
            # Prevents 1/1 = 100% and 0/1 = 0% extremes
            smoothed = (entry.times_helped + 1) / (entry.times_injected + 2)
            effective_score = smoothed
        else:
            # No entry found, use raw effectiveness
            effective_score = effectiveness
        
        score += 0.4 * effective_score
        
        # 2. Context match (30%) - v2: Check context dict
        error_lower = error.lower()
        task_lower = task.lower()
        
        if pattern.context:
            context_matches = 0
            context_total = len(pattern.context)
            
            for key, value in pattern.context.items():
                value_str = str(value).lower()
                if value_str in error_lower or value_str in task_lower:
                    context_matches += 1
            
            if context_total > 0:
                score += 0.3 * (context_matches / context_total)
        
        # 3. Pattern type match (20%)
        if pattern.pattern_type in error_lower:
            score += 0.2
        elif pattern.pattern_type == "syntax_error" and any(
            kw in error_lower for kw in ["syntax", "indentation", "unexpected"]
        ):
            score += 0.2
        elif pattern.pattern_type == "runtime_error" and any(
            kw in error_lower for kw in ["error", "exception", "traceback"]
        ):
            score += 0.2
        elif pattern.pattern_type == "import_missing" and any(
            kw in error_lower for kw in ["import", "not defined", "nameerror"]
        ):
            score += 0.2
        elif pattern.pattern_type == "wrong_fix_strategy" and any(
            kw in error_lower for kw in ["is not a function", "not a function"]
        ):
            score += 0.2
        elif pattern.pattern_type == "fix_symptom_not_root" and any(
            kw in error_lower for kw in ["undefined", "cannot read property", "null"]
        ):
            score += 0.2
        
        # 4. Recency + Frequency (10%)
        try:
            ts = datetime.fromisoformat(timestamp)
            age_days = (datetime.now() - ts).days
            recency_score = max(0, 1 - (age_days / 7))  # Decay over 7 days
        except:
            recency_score = 0.5
        
        frequency_score = min(1.0, frequency / 10)  # Cap at 10 occurrences
        
        score += 0.05 * recency_score + 0.05 * frequency_score
        
        return min(score, 1.0)


class FailureMemory:
    """
    Main interface for failure learning loop.
    
    Combines PatternExtractor, Store, and Retriever.
    """
    
    def __init__(
        self,
        storage_path: Path | str,
        ttl_days: int = 7,
        max_entries: int = 1000
    ):
        self._extractor = PatternExtractorV2()
        self._store = FailureMemoryStore(storage_path, ttl_days, max_entries)
        self._retriever = FailureMemoryRetriever(self._store)
    
    def record_failure(
        self,
        failure_id: str,
        patch_diff: str,
        error_text: str,
        files_touched: list[str],
        session_id: str
    ) -> tuple[FailurePattern, FailureLesson]:
        """
        Record a failure and extract pattern + lesson.
        
        Returns: (pattern, lesson) for immediate use
        """
        # Create surface layer
        surface = FailureSurface(
            failure_id=failure_id,
            patch_diff=patch_diff,
            error_text=error_text,
            files_touched=files_touched,
            timestamp=datetime.now().isoformat(),
            session_id=session_id
        )
        
        # Extract pattern and lesson
        pattern, lesson = self._extractor.extract(surface)
        
        # Store for future retrieval
        self._store.store(surface, pattern, lesson)
        
        return pattern, lesson
    
    def retrieve_lessons(
        self,
        current_task: str,
        current_error: str,
        top_k: int = 3
    ) -> list[tuple[FailurePattern, FailureLesson, float]]:
        """
        Retrieve relevant lessons for current failure.
        
        Returns: [(pattern, lesson, relevance_score)]
        """
        return self._retriever.search_relevant(current_task, current_error, top_k)
    
    def format_for_prompt(
        self,
        relevant_failures: list[tuple[FailurePattern, FailureLesson, float]]
    ) -> str:
        """
        Format failures for LLM prompt injection (v4: Final alignment pass - Phase 1d.3).
        
        Focus on CONSTRAINTS and DIRECTIVES, not just advice.
        v3: Add forced reasoning to ensure LLM acknowledges constraints.
        v4: Add final verification step to prevent generation drift.
        """
        if not relevant_failures:
            return ""
        
        lines = ["[FAILURE MEMORY - CRITICAL CONSTRAINTS]"]
        lines.append("You are making a repair to code that previously failed.")
        lines.append("Known failure patterns (high confidence):\n")
        
        for i, (pattern, lesson, score) in enumerate(relevant_failures, 1):
            # Build context string
            context_str = ""
            if pattern.context:
                context_items = [f"{k}={v}" for k, v in pattern.context.items()]
                context_str = f" [{', '.join(context_items)}]"
            
            # Pattern description with attempted fix
            lines.append(f"{i}. {pattern.cause.upper()}{context_str}")
            
            if pattern.attempted_fix:
                lines.append(f"   Previous attempt: {pattern.attempted_fix}")
            
            if pattern.correct_direction:
                lines.append(f"   Why it failed: {pattern.correct_direction}")
            
            lines.append(f"   Confidence: {lesson.confidence:.0%} (seen {int(lesson.confidence * 10)} times) | Relevance: {score:.0%}\n")
        
        # v4: FORCED REASONING HOOK WITH FINAL ALIGNMENT (Phase 1d.3)
        lines.append("BEFORE WRITING THE FIX, YOU MUST:")
        lines.append("1. Identify which failure pattern(s) apply to this error")
        lines.append("2. Explain why the previous fix approach failed")
        lines.append("3. State what you will do differently this time")
        lines.append("4. Write the patch")
        lines.append("5. Verify the fix explicitly satisfies the constraints above\n")
        
        # Add strict rules section
        lines.append("STRICT RULES:")
        for i, (pattern, lesson, score) in enumerate(relevant_failures, 1):
            lines.append(f"  {i}. {lesson.avoid}")
            lines.append(f"     → MUST: {lesson.prefer}")
        
        lines.append("\nIf you skip the reasoning, drift during generation, or violate these rules,")
        lines.append("the patch will fail again. Final verification is mandatory.")
        
        return "\n".join(lines)
    
    def purge_expired(self) -> int:
        """Purge expired entries"""
        return self._store.purge_expired()
    
    def get_stats(self) -> dict:
        """Get memory statistics"""
        return self._store.get_stats()
