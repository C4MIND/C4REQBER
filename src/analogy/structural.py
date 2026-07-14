"""
C4REQBER: Structural Analogy Engine v5.0
Cross-domain structural analogy discovery using LLM + graph matching.

Methods:
1. LLM-Powered Domain Graph Extraction - Extract entity/relation graphs from text
2. Graph Isomorphism Matching - NetworkX graph edit distance + subgraph isomorphism
3. Causal Chain Mapping - Find similar causal paths across domains
4. Semantic Similarity - Sentence-BERT embeddings (fallback)
5. Knowledge-Based - ConceptNet/conceptual metaphors (fallback)

Usage:
    engine = StructuralAnalogyEngine()
    analogies = engine.find_structural_analogies(
        "biology", "computer_science",
        "A virus infects a cell and replicates",
        top_k=5
    )
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.graph.knowledge_graph import get_knowledge_graph


try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class DomainGraph:
    """Structural representation of a domain."""

    domain: str
    source_text: str
    nodes: list[dict] = field(default_factory=list)  # type: ignore[type-arg]
    edges: list[dict] = field(default_factory=list)  # type: ignore[type-arg]

    def to_nx_graph(self) -> Any:
        """Convert to NetworkX graph."""
        if not HAS_NETWORKX:
            return None
        G = nx.DiGraph()
        for node in self.nodes:
            G.add_node(node["id"], **node.get("attrs", {}))
        for edge in self.edges:
            G.add_edge(edge["source"], edge["target"], **edge.get("attrs", {}))
        return G


@dataclass
class StructuralAnalogyResult:
    """Result of structural analogy discovery."""

    source_domain: str
    target_domain: str
    source_concept: str
    target_concept: str
    mapping_type: str  # "structural", "causal", "semantic", "llm_generated"
    confidence: float
    structural_similarity: float | None = None
    causal_similarity: float | None = None
    semantic_similarity: float | None = None
    graph_edit_distance: float | None = None
    reasoning: str = ""
    entity_mapping: dict[str, str] = field(default_factory=dict)
    relation_mapping: dict[str, str] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)


class DomainGraphExtractor:
    """Extract structural graphs from text using LLM."""

    def __init__(self, llm_client: Any=None) -> None:
        self.llm_client = llm_client
        self._cache: dict[str, DomainGraph] = {}

    async def extract_graph(self, text: str, domain: str) -> DomainGraph:
        """Extract entity-relation graph from text using LLM."""
        cache_key = f"{domain}:{hash(text) % 1000000}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # If no LLM client, use rule-based extraction
        if self.llm_client is None:
            graph = self._rule_based_extract(text, domain)
            self._cache[cache_key] = graph
            return graph

        # LLM-powered extraction

        prompt = f"""Extract entities and relations from the following text about {domain}.

Text: {text}

Return JSON with:
- entities: list of objects with id, name, type
- relations: list of objects with source, target, relation

Focus on causal, functional, and structural relationships."""

        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt="You extract structured knowledge graphs from text. Respond ONLY with valid JSON.",
                temperature=0.3,
                max_tokens=1500,
            )
            data = json.loads(response.content)
            graph = DomainGraph(
                domain=domain,
                source_text=text,
                nodes=[
                    {"id": e["id"], "name": e["name"], "type": e.get("type", "entity")}
                    for e in data.get("entities", [])
                ],
                edges=[
                    {"source": r["source"], "target": r["target"], "relation": r["relation"]}
                    for r in data.get("relations", [])
                ],
            )
        except (json.JSONDecodeError, ValueError, RuntimeError):
            # Fallback to rule-based
            graph = self._rule_based_extract(text, domain)

        self._cache[cache_key] = graph
        return graph

    def _rule_based_extract(self, text: str, domain: str) -> DomainGraph:
        """Rule-based entity/relation extraction (fallback)."""
        # Simple noun phrase extraction
        words = text.lower().split()

        # Extract potential entities (nouns, capitalized words)
        entities = []
        entity_ids: Any = {}

        # Find capitalized words and noun phrases
        for word in words:
            clean = re.sub(r"[^\w]", "", word)
            if len(clean) > 3 and clean not in entity_ids:
                entity_ids[clean] = f"e{len(entity_ids)}"
                entities.append({"id": entity_ids[clean], "name": clean, "type": "entity"})

        # Find relation keywords
        relation_keywords = [
            "causes",
            "leads",
            "produces",
            "generates",
            "creates",
            "affects",
            "influences",
            "controls",
            "regulates",
            "contains",
            "includes",
            "part of",
            "depends on",
            "requires",
            "enables",
            "prevents",
            "inhibits",
        ]

        edges = []
        for i, word in enumerate(words):
            clean = re.sub(r"[^\w]", "", word.lower())
            if clean in relation_keywords and i > 0 and i < len(words) - 1:
                src = re.sub(r"[^\w]", "", words[i - 1].lower())
                tgt = re.sub(r"[^\w]", "", words[i + 1].lower())
                if src in entity_ids and tgt in entity_ids:
                    edges.append(
                        {"source": entity_ids[src], "target": entity_ids[tgt], "relation": clean}
                    )

        return DomainGraph(
            domain=domain,
            source_text=text,
            nodes=entities,
            edges=edges,
        )


class GraphMatcher:
    """Graph matching algorithms for structural analogy."""

    def __init__(self) -> None:
        self.use_networkx = HAS_NETWORKX

    def compute_similarity(self, g1: DomainGraph, g2: DomainGraph) -> dict[str, float]:
        """Compute multiple structural similarity metrics."""
        results = {}

        if not self.use_networkx:
            # Fallback: simple node/edge overlap
            nodes1 = {n["name"] for n in g1.nodes}
            nodes2 = {n["name"] for n in g2.nodes}
            overlap = len(nodes1 & nodes2)
            union = len(nodes1 | nodes2)
            results["node_jaccard"] = overlap / union if union > 0 else 0.0

            edges1 = {(e["source"], e["target"], e["relation"]) for e in g1.edges}
            edges2 = {(e["source"], e["target"], e["relation"]) for e in g2.edges}
            e_overlap = len(edges1 & edges2)
            e_union = len(edges1 | edges2)
            results["edge_jaccard"] = e_overlap / e_union if e_union > 0 else 0.0

            results["combined"] = 0.6 * results["node_jaccard"] + 0.4 * results["edge_jaccard"]
            return results

        nx1 = g1.to_nx_graph()
        nx2 = g2.to_nx_graph()

        if nx1 is None or nx2 is None or len(nx1.nodes) == 0 or len(nx2.nodes) == 0:
            results["combined"] = 0.0
            return results

        # Node degree distribution similarity
        degrees1 = sorted([d for _, d in nx1.degree()], reverse=True)
        degrees2 = sorted([d for _, d in nx2.degree()], reverse=True)
        results["degree_similarity"] = self._vector_similarity(degrees1, degrees2)

        # Graph edit distance approximation (normalized)
        try:
            ged = nx.graph_edit_distance(nx1, nx2)
            max_nodes = max(len(nx1.nodes), len(nx2.nodes))
            results["ged_normalized"] = 1.0 - (ged / max_nodes) if max_nodes > 0 and ged else 0.5
        except (RuntimeError, ValueError):
            results["ged_normalized"] = 0.5

        # Clustering coefficient
        try:
            cc1 = nx.average_clustering(nx1.to_undirected())
            cc2 = nx.average_clustering(nx2.to_undirected())
            results["clustering_similarity"] = 1.0 - abs(cc1 - cc2)
        except (RuntimeError, ValueError):
            results["clustering_similarity"] = 0.5

        # Combined structural score
        results["combined"] = (
            0.4 * results.get("degree_similarity", 0)
            + 0.3 * results.get("ged_normalized", 0.5)
            + 0.3 * results.get("clustering_similarity", 0.5)
        )

        return results

    def find_subgraph_isomorphism(self, g1: DomainGraph, g2: DomainGraph) -> list[dict]:  # type: ignore[type-arg]
        """Find subgraph isomorphisms between two graphs."""
        if not self.use_networkx:
            return []

        nx1 = g1.to_nx_graph()
        nx2 = g2.to_nx_graph()

        if nx1 is None or nx2 is None:
            return []

        matcher = nx.algorithms.isomorphism.DiGraphMatcher(nx2, nx1)
        mappings = []
        for mapping in matcher.subgraph_isomorphisms_iter():
            mappings.append(mapping)
            if len(mappings) >= 5:
                break

        return mappings

    def _vector_similarity(self, v1: list[Any], v2: list[Any]) -> float:
        """Compute cosine similarity between two vectors of different lengths."""
        max_len = max(len(v1), len(v2))
        a = np.zeros(max_len)
        b = np.zeros(max_len)
        a[: len(v1)] = v1
        b[: len(v2)] = v2

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class CausalChainMapper:
    """Map causal chains between domains."""

    def __init__(self) -> None:
        self.causal_keywords = [
            "causes",
            "leads",
            "produces",
            "generates",
            "creates",
            "results in",
            "gives rise to",
            "triggers",
            "induces",
        ]

    def extract_causal_chains(self, graph: DomainGraph) -> list[list[str]]:
        """Extract causal chains from a domain graph."""
        if not HAS_NETWORKX:
            # Simple chain extraction from edges
            chains = []
            for edge in graph.edges:
                if any(kw in edge["relation"] for kw in self.causal_keywords):
                    chains.append([edge["source"], edge["relation"], edge["target"]])
            return chains

        nxg = graph.to_nx_graph()
        if nxg is None:
            return []

        # Find all simple paths (causal chains)
        chains = []
        causal_edges = [
            (e["source"], e["target"])
            for e in graph.edges
            if any(kw in e["relation"] for kw in self.causal_keywords)
        ]

        for src, tgt in causal_edges:
            try:
                for path in nx.all_simple_paths(nxg, src, tgt, cutoff=4):
                    chains.append(path)
            except (RuntimeError, ValueError):
                chains.append([src, tgt])

        return chains

    def compare_causal_chains(self, chain1: list[Any], chain2: list[Any]) -> float:
        """Compare two causal chains for structural similarity."""
        if not chain1 or not chain2:
            return 0.0

        # Length similarity
        len_sim = 1.0 - abs(len(chain1) - len(chain2)) / max(len(chain1), len(chain2))

        # Node type similarity (if type info available)
        # For now, use simple overlap
        overlap = len(set(chain1) & set(chain2))
        union = len(set(chain1) | set(chain2))
        jaccard = overlap / union if union > 0 else 0.0

        return 0.5 * len_sim + 0.5 * jaccard


class LLMAnalogyGenerator:
    """Generate novel analogies using LLM."""

    def __init__(self, llm_client: Any=None) -> None:
        self.llm_client = llm_client

    async def generate_analogy(
        self,
        source_domain: str,
        target_domain: str,
        source_description: str,
    ) -> StructuralAnalogyResult | None:
        """Generate a novel cross-domain analogy using LLM."""
        if self.llm_client is None:
            return None

        prompt = f"""Given the following description from {source_domain}:

{source_description}

Find the most analogous concept or process in {target_domain}.

Explain the structural isomorphism: what entities map to what, what relations map to what, and why the analogy holds.

Return JSON:
{{
  "target_concept": "name of analogous concept",
  "entity_mapping": {{"source_entity": "target_entity"}},
  "relation_mapping": {{"source_relation": "target_relation"}},
  "reasoning": "explanation of the structural analogy",
  "confidence": 0.0-1.0
}}"""

        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are an expert in cross-domain analogy and structural mapping. Respond ONLY with valid JSON.",
                temperature=0.5,
                max_tokens=1500,
            )
            data = json.loads(response.content)

            return StructuralAnalogyResult(
                source_domain=source_domain,
                target_domain=target_domain,
                source_concept=source_description[:50],
                target_concept=data.get("target_concept", "unknown"),
                mapping_type="llm_generated",
                confidence=data.get("confidence", 0.7),
                reasoning=data.get("reasoning", ""),
                entity_mapping=data.get("entity_mapping", {}),
                relation_mapping=data.get("relation_mapping", {}),
            )
        except (json.JSONDecodeError, ValueError, RuntimeError):
            return None


class SemanticEmbedder:
    """Semantic embedding for fallback similarity."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model = None
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(model_name)
            except (OSError, RuntimeError, ValueError):
                pass

    def similarity(self, text1: str, text2: str) -> float:
        """Similarity."""
        if self.model is not None:
            emb1 = self.model.encode(text1, convert_to_numpy=True)
            emb2 = self.model.encode(text2, convert_to_numpy=True)
            return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
        return 0.5


class StructuralAnalogyEngine:
    """
    Main structural analogy discovery engine.

    Combines LLM-powered extraction, graph matching, causal chain mapping,
    and semantic similarity for robust cross-domain analogy discovery.
    """

    def __init__(self, llm_client: Any=None) -> None:
        self.llm_client = llm_client
        self.graph_extractor = DomainGraphExtractor(llm_client)
        self.graph_matcher = GraphMatcher()
        self.causal_mapper = CausalChainMapper()
        self.llm_generator = LLMAnalogyGenerator(llm_client)
        self.embedder = SemanticEmbedder()
        self.knowledge_graph = get_knowledge_graph()

    async def find_structural_analogies(
        self,
        source_domain: str,
        target_domain: str,
        source_description: str,
        top_k: int = 5,
    ) -> list[StructuralAnalogyResult]:
        """
        Find structural analogies between domains.

        Args:
            source_domain: Source domain name
            target_domain: Target domain name
            source_description: Text description of the source concept/process
            top_k: Number of top results to return

        Returns:
            List of StructuralAnalogyResult sorted by confidence
        """
        results = []

        # Step 1: Extract source domain graph
        source_graph = await self.graph_extractor.extract_graph(source_description, source_domain)

        # Step 2: LLM-generated analogy (if LLM available)
        if self.llm_client:
            llm_result = await self.llm_generator.generate_analogy(
                source_domain, target_domain, source_description
            )
            if llm_result:
                results.append(llm_result)

        # Step 3: Extract target domain concepts from knowledge graph
        target_concepts = self._get_target_concepts(target_domain)

        # Step 4: For each target concept, compute structural similarity
        for target_concept in target_concepts[:20]:  # Limit for performance
            # Build target graph (simplified)
            target_graph = await self._build_target_graph(target_domain, target_concept)

            # Graph matching
            struct_scores = self.graph_matcher.compute_similarity(source_graph, target_graph)
            struct_sim = struct_scores.get("combined", 0.0)

            # Causal chain comparison
            source_chains = self.causal_mapper.extract_causal_chains(source_graph)
            target_chains = self.causal_mapper.extract_causal_chains(target_graph)
            causal_sims = []
            for sc in source_chains:
                for tc in target_chains:
                    causal_sims.append(self.causal_mapper.compare_causal_chains(sc, tc))
            causal_sim = max(causal_sims) if causal_sims else 0.0

            # Semantic similarity
            sem_sim = self.embedder.similarity(
                f"{source_description} in {source_domain}", f"{target_concept} in {target_domain}"
            )

            # Combined score
            confidence = 0.4 * struct_sim + 0.3 * causal_sim + 0.3 * sem_sim

            if confidence > 0.3:  # Threshold
                results.append(
                    StructuralAnalogyResult(
                        source_domain=source_domain,
                        target_domain=target_domain,
                        source_concept=source_description[:50],
                        target_concept=target_concept,
                        mapping_type="structural",
                        confidence=confidence,
                        structural_similarity=struct_sim,
                        causal_similarity=causal_sim,
                        semantic_similarity=sem_sim,
                        reasoning=f"Structural: {struct_sim:.2f}, Causal: {causal_sim:.2f}, Semantic: {sem_sim:.2f}",
                    )
                )

        # Step 5: Deduplicate and sort
        seen = set()
        unique_results = []
        for r in sorted(results, key=lambda x: x.confidence, reverse=True):
            key = (r.source_concept.lower(), r.target_concept.lower())
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results[:top_k]

    async def _build_target_graph(self, domain: str, concept: str) -> DomainGraph:
        """Build a simple graph for a target concept."""
        # Try to get from knowledge graph first
        nodes = self.knowledge_graph.get_nodes_by_type("concept")
        related = [n for n in nodes if concept.lower() in n.get("concept", "").lower()]

        if related:
            # Build graph from knowledge graph data
            graph_nodes = [
                {"id": r["id"], "name": r.get("concept", ""), "type": "concept"} for r in related
            ]
            graph_edges = []
            for node in related:
                # Get neighbors
                neighbors = self.knowledge_graph.get_neighbors(node["id"])
                for neighbor in neighbors:
                    graph_edges.append(
                        {
                            "source": node["id"],
                            "target": neighbor["id"],  # type: ignore[index]
                            "relation": neighbor.get("relation", "related"),  # type: ignore[attr-defined]
                        }
                    )
            return DomainGraph(
                domain=domain, source_text=concept, nodes=graph_nodes, edges=graph_edges
            )

        # Fallback: minimal graph
        return DomainGraph(
            domain=domain,
            source_text=concept,
            nodes=[{"id": concept.replace(" ", "_"), "name": concept, "type": "concept"}],
            edges=[],
        )

    def _get_target_concepts(self, domain: str) -> list[str]:
        """Get concepts for a target domain."""
        # From knowledge graph
        nodes = self.knowledge_graph.get_nodes_by_type("concept")
        concepts = [n.get("concept", "") for n in nodes if n.get("domain") == domain]

        # From built-in domain lists
        from src.analogy.engine import ConceptNetBridge

        bridge = ConceptNetBridge()
        builtin = bridge.get_domain_concepts(domain)

        return list(set(concepts + builtin))

    def store_analogy(self, result: StructuralAnalogyResult) -> str:
        """Store analogy in knowledge graph."""
        return self.knowledge_graph.add_analogy(
            source_domain=result.source_domain,
            target_domain=result.target_domain,
            source_concept=result.source_concept,
            target_concept=result.target_concept,
            mapping_type=result.mapping_type,
            confidence=result.confidence,
            evidence=result.evidence,
        )


# Backward compatibility: keep old AnalogyEngine available
from src.analogy.engine import AnalogyEngine, get_analogy_engine


__all__ = [
    "StructuralAnalogyEngine",
    "StructuralAnalogyResult",
    "DomainGraph",
    "DomainGraphExtractor",
    "GraphMatcher",
    "CausalChainMapper",
    "LLMAnalogyGenerator",
    "AnalogyEngine",
    "get_analogy_engine",
]
