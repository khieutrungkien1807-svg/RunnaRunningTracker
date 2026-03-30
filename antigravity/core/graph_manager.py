"""
GraphManager — GraphRAG Ontology & Semantic Knowledge Graph
Version: 6.3.0 (Refined-State)

Manages relationships between Skills, Files, Errors, and Agents using a 
lightweight JSON-based triplet store (s, p, o).
Implements the GraphRAG strategy as defined in GEMINI.md NHÓM T.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any

logger = logging.getLogger(__name__)

class GraphManager:
    """
    Manages the Antigravity Knowledge Graph.
    Uses an adjacency list stored in a JSON file.
    
    Ontology:
    - Entities: Skill, File, Agent, Error, Domain, Task
    - Relations: FIXES, REQUIRES, BELONGS_TO, LOCATED_IN, TRIGGERED_BY
    """
    
    def __init__(self, graph_path: str | Path = None):
        if graph_path is None:
            # Default to antigravity/knowledge/knowledge_graph.json
            graph_path = Path(__file__).parent.parent / "knowledge" / "knowledge_graph.json"
        
        self.graph_path = Path(graph_path)
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage: {subject: {predicate: {objects...}}}
        self._triplets: Dict[str, Dict[str, Set[str]]] = {}
        self._load()
        
    def _load(self):
        """Load graph from JSON file."""
        if self.graph_path.exists():
            try:
                with open(self.graph_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert lists of objects back to sets
                    self._triplets = {
                        s: {p: set(o_list) for p, o_list in p_map.items()}
                        for s, p_map in data.items()
                    }
                logger.info(f"Loaded {self.count_triplets()} triplets from {self.graph_path}")
            except Exception as e:
                logger.error(f"Failed to load knowledge graph: {e}")
                self._triplets = {}
        else:
            self._triplets = {}
            
    def save(self):
        """Persist graph to JSON file."""
        try:
            # Convert sets to lists for JSON serialization
            data = {
                s: {p: list(o_set) for p, o_set in p_map.items()}
                for s, p_map in self._triplets.items()
            }
            with open(self.graph_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {self.count_triplets()} triplets to {self.graph_path}")
        except Exception as e:
            logger.error(f"Failed to save knowledge graph: {e}")

    def add_triplet(self, subject: str, predicate: str, obj: str):
        """Add a semantic relationship (s, p, o)."""
        if subject not in self._triplets:
            self._triplets[subject] = {}
        if predicate not in self._triplets[subject]:
            self._triplets[subject][predicate] = set()
        
        self._triplets[subject][predicate].add(obj)
        
    def get_related(self, subject: str, predicate: str = None) -> List[str] | Dict[str, List[str]]:
        """
        Query the graph for related objects.
        If predicate is None, returns all relationships for the subject.
        """
        if subject not in self._triplets:
            return [] if predicate else {}
            
        if predicate:
            return list(self._triplets[subject].get(predicate, []))
            
        return {p: list(o_set) for p, o_set in self._triplets[subject].items()}

    def find_path(self, start: str, end: str, max_depth: int = 3) -> List[List[Tuple[str, str]]]:
        """Simple BFS to find paths between two entities (e.g. Error -> Skill)."""
        # BFS implementation would go here for complex RAG queries
        # For now, return direct connections
        paths = []
        if start in self._triplets:
            for pred, objects in self._triplets[start].items():
                if end in objects:
                    paths.append([(pred, end)])
        return paths

    def count_triplets(self) -> int:
        count = 0
        for s in self._triplets:
            for p in self._triplets[s]:
                count += len(self._triplets[s][p])
        return count

    def ingest_skill(self, skill_name: str, errors_it_fixes: List[str], domains: List[str]):
        """Helper to batch ingest a skill's metadata into the graph."""
        for error in errors_it_fixes:
            self.add_triplet(skill_name, "FIXES", error)
            self.add_triplet(error, "FIXED_BY", skill_name)  # Bidirectional
        
        for domain in domains:
            self.add_triplet(skill_name, "BELONGS_TO", domain)
            self.add_triplet(domain, "CONTAINS", skill_name)

    def contextual_query(self, query_terms: List[str]) -> Dict[str, Any]:
        """
        Enhance a search query by pulling related entities from the graph.
        Useful for HybridRetriever.
        """
        context = {"skills": set(), "errors": set(), "domains": set()}
        
        for term in query_terms:
            # Look for matches in subjects
            if term in self._triplets:
                relations = self.get_related(term)
                if isinstance(relations, dict):
                    for p, objects in relations.items():
                        if p == "FIXES": context["errors"].update(objects)
                        elif p == "BELONGS_TO": context["domains"].update(objects)
                        elif p == "FIXED_BY": context["skills"].update(objects)
            
        return {k: list(v) for k, v in context.items()}

# ── Factory ──────────────────────────────────────────────────────────────────

def get_default_graph_manager() -> GraphManager:
    return GraphManager()
