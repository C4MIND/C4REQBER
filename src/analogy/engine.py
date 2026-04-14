"""
TURBO-CDI: Analogy Engine v4.0
Cross-domain analogy discovery using multiple methods

Methods:
1. Semantic Similarity - Sentence-BERT embeddings
2. Structural Analogies - Word2Vec vector arithmetic (A:B::C:D)
3. Knowledge-Based - ConceptNet relations
4. Graph Isomorphism - NetworkX structure matching

Usage:
    engine = AnalogyEngine()
    analogies = engine.find_analogies("biology", "computer_science", "neuron")
"""

import re
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from pathlib import Path
import pickle
import json
from datetime import datetime

import numpy as np
from cachetools import LRUCache

# Optional imports with fallbacks
try:
    from sentence_transformers import SentenceTransformer

    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("⚠️  sentence-transformers not installed. Using TF-IDF fallback.")

try:
    import gensim
    from gensim.models import Word2Vec, KeyedVectors

    HAS_GENSIM = True
except ImportError:
    HAS_GENSIM = False
    print("⚠️  gensim not installed. Word2Vec analogies unavailable.")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠️  scikit-learn not installed. Using numpy for similarity.")

from src.models.pydantic_models import AnalogyMappingModel
from src.graph.knowledge_graph import get_knowledge_graph


@dataclass
class AnalogyResult:
    """Result of analogy discovery."""

    source_concept: str
    target_concept: str
    source_domain: str
    target_domain: str
    mapping_type: str
    confidence: float
    semantic_similarity: Optional[float] = None
    structural_similarity: Optional[float] = None
    reasoning: str = ""
    evidence: List[str] = None

    def to_model(self) -> AnalogyMappingModel:
        """Convert to pydantic model for storage."""
        return AnalogyMappingModel(
            source_domain=self.source_domain,
            target_domain=self.target_domain,
            mapping_type=self.mapping_type,
            source_concept=self.source_concept,
            target_concept=self.target_concept,
            confidence=self.confidence,
            semantic_similarity=self.semantic_similarity,
            structural_similarity=self.structural_similarity,
        )


class SemanticEmbedder:
    """
    Semantic embedding using Sentence-BERT or TF-IDF fallback.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.fallback_vectorizer = None
        self._embedding_cache: LRUCache = LRUCache(maxsize=1000)

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(model_name)
                print(f"✓ Loaded Sentence-BERT model: {model_name}")
            except Exception as e:
                print(f"⚠️  Failed to load Sentence-BERT: {e}")
                self.model = None

        if self.model is None and HAS_SKLEARN:
            self.fallback_vectorizer = TfidfVectorizer(
                max_features=1000, stop_words="english", ngram_range=(1, 2)
            )

    def embed(self, text: str) -> np.ndarray:
        """Get embedding vector for text."""
        # Check cache
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        if self.model is not None:
            # Use Sentence-BERT
            embedding = self.model.encode(text, convert_to_numpy=True)
        elif HAS_SKLEARN:
            # Use TF-IDF
            if not hasattr(self.fallback_vectorizer, "vocabulary_"):
                # Fit on single document (not ideal but works for fallback)
                self.fallback_vectorizer.fit([text])
            embedding = self.fallback_vectorizer.transform([text]).toarray()[0]
        else:
            # Last resort: simple word hash
            embedding = self._simple_hash_embedding(text)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        self._embedding_cache[text] = embedding
        return embedding

    def _simple_hash_embedding(self, text: str, dim: int = 128) -> np.ndarray:
        """Simple hash-based embedding as last resort."""
        words = text.lower().split()
        vec = np.zeros(dim)
        for word in words:
            # Simple hash-based encoding
            for i, char in enumerate(word):
                vec[i % dim] += ord(char)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        emb1 = self.embed(text1)
        emb2 = self.embed(text2)
        return float(np.dot(emb1, emb2))

    def batch_embed(self, texts: List[str]) -> np.ndarray:
        """Embed multiple texts efficiently."""
        if self.model is not None:
            return self.model.encode(texts, convert_to_numpy=True)
        return np.array([self.embed(t) for t in texts])


class Word2VecAnalogySolver:
    """
    Solve analogies using Word2Vec vector arithmetic.
    A:B::C:?  =>  D = C + (B - A)
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[KeyedVectors] = None
        self.model_path = model_path

        if HAS_GENSIM and model_path:
            try:
                self.model = KeyedVectors.load_word2vec_format(model_path, binary=True)
                print(f"✓ Loaded Word2Vec model: {model_path}")
            except Exception as e:
                print(f"⚠️  Failed to load Word2Vec: {e}")

    def solve(self, A: str, B: str, C: str, topn: int = 5) -> List[Tuple[str, float]]:
        """
        Solve A:B::C:? analogy.
        Returns list of (word, similarity) tuples.
        """
        if self.model is None:
            return []

        try:
            # Normalize terms
            A = A.lower().replace(" ", "_")
            B = B.lower().replace(" ", "_")
            C = C.lower().replace(" ", "_")

            # Vector arithmetic: D = C + (B - A)
            result = self.model.most_similar(positive=[B, C], negative=[A], topn=topn)
            return [(word.replace("_", " "), float(score)) for word, score in result]
        except KeyError as e:
            # Word not in vocabulary
            return []
        except Exception as e:
            print(f"⚠️  Word2Vec analogy error: {e}")
            return []

    def doesnt_match(self, words: List[str]) -> Optional[str]:
        """Find the word that doesn't match the others."""
        if self.model is None:
            return None

        try:
            normalized = [w.lower().replace(" ", "_") for w in words]
            return self.model.doesnt_match(normalized).replace("_", " ")
        except Exception:
            return None

    def similarity(self, word1: str, word2: str) -> float:
        """Get similarity between two words."""
        if self.model is None:
            return 0.0

        try:
            w1 = word1.lower().replace(" ", "_")
            w2 = word2.lower().replace(" ", "_")
            return float(self.model.similarity(w1, w2))
        except Exception:
            return 0.0


class ConceptNetBridge:
    """
    Knowledge-based analogies using ConceptNet relations.
    Falls back to cached/local data if API unavailable.
    """

    # Domain-specific concept mappings
    DOMAIN_CONCEPTS: Dict[str, List[str]] = {
        "biology": [
            "cell",
            "organism",
            "evolution",
            "ecosystem",
            "gene",
            "protein",
            "metabolism",
            "neuron",
            "immune system",
            "homeostasis",
            "DNA",
            "photosynthesis",
            "mitochondria",
            "enzyme",
            "hormone",
            "tissue",
            "organ",
            "population",
            "species",
            "adaptation",
            "selection",
            "symbiosis",
            "predator",
            "prey",
            "parasite",
            "host",
            "virus",
            "bacteria",
            "fungi",
            "plant",
            "animal",
            "human",
            "brain",
            "heart",
            "blood",
            "muscle",
            "bone",
            "skin",
            "eye",
            "ear",
        ],
        "physics": [
            "force",
            "energy",
            "field",
            "wave",
            "particle",
            "entropy",
            "equilibrium",
            "resonance",
            "oscillation",
            "potential",
            "mass",
            "velocity",
            "acceleration",
            "momentum",
            "gravity",
            "electromagnetism",
            "quantum",
            "relativity",
            "thermodynamics",
            "pressure",
            "temperature",
            "volume",
            "density",
            "viscosity",
            "friction",
            "tension",
            "compression",
            "torque",
            "inertia",
            "light",
            "sound",
            "heat",
            "electricity",
            "magnetism",
            "atom",
            "molecule",
            "electron",
            "proton",
            "neutron",
            "quark",
        ],
        "computer_science": [
            "algorithm",
            "data structure",
            "network",
            "memory",
            "processor",
            "protocol",
            "interface",
            "queue",
            "stack",
            "recursion",
            "machine learning",
            "artificial intelligence",
            "neural network",
            "database",
            "cloud computing",
            "distributed system",
            "API",
            "function",
            "variable",
            "loop",
            "condition",
            "class",
            "object",
            "inheritance",
            "polymorphism",
            "encapsulation",
            "abstraction",
            "compiler",
            "interpreter",
            "operating system",
            "kernel",
            "security",
            "encryption",
            "hash",
            "blockchain",
            "container",
        ],
        "energy": [
            "battery",
            "solar panel",
            "wind turbine",
            "power plant",
            "electricity",
            "renewable energy",
            "fossil fuel",
            "nuclear",
            "energy storage",
            "grid",
            "transmission",
            "efficiency",
            "charging",
            "discharging",
            "capacity",
            "voltage",
            "current",
            "resistance",
            "power",
            "watt",
            "kilowatt",
            "megawatt",
            "photovoltaic",
            "thermal",
            "kinetic",
            "potential energy",
            "chemical energy",
            "nuclear energy",
            "fusion",
            "fission",
        ],
        "materials": [
            "metal",
            "polymer",
            "ceramic",
            "composite",
            "alloy",
            "semiconductor",
            "superconductor",
            "insulator",
            "conductor",
            "crystal",
            "amorphous",
            "nanomaterial",
            "graphene",
            "carbon fiber",
            "strength",
            "hardness",
            "ductility",
            "elasticity",
            "plasticity",
            "corrosion",
            "oxidation",
            "reduction",
            "catalysis",
            "synthesis",
        ],
        "mathematics": [
            "number",
            "equation",
            "function",
            "variable",
            "constant",
            "vector",
            "matrix",
            "tensor",
            "calculus",
            "algebra",
            "geometry",
            "topology",
            "statistics",
            "probability",
            "derivative",
            "integral",
            "differential equation",
            "linear algebra",
            "group theory",
            "set theory",
            "logic",
        ],
        "chemistry": [
            "atom",
            "molecule",
            "compound",
            "reaction",
            "catalyst",
            "acid",
            "base",
            "salt",
            "solvent",
            "solution",
            "organic",
            "inorganic",
            "polymer",
            "monomer",
            "bond",
            "ion",
            "radical",
            "isomer",
            "allotrope",
            "crystal",
        ],
        "general": [
            "system",
            "process",
            "structure",
            "function",
            "behavior",
            "pattern",
            "relationship",
            "interaction",
            "feedback",
            "control",
            "optimization",
            "efficiency",
            "performance",
            "reliability",
            "complexity",
            "simplicity",
            "flexibility",
            "robustness",
        ],
        "economics": [
            "market",
            "supply",
            "demand",
            "equilibrium",
            "inflation",
            "investment",
            "liquidity",
            "risk",
            "portfolio",
            "bubble",
        ],
        "chemistry": [
            "molecule",
            "reaction",
            "catalyst",
            "bond",
            "solution",
            "equilibrium",
            "concentration",
            "diffusion",
            "precipitation",
        ],
    }

    # Cross-domain mappings (derived from conceptual metaphors)
    CONCEPTUAL_METAPHORS: List[Tuple[str, str, str, str]] = [
        # (source_domain, source_concept, target_domain, target_concept)
        # Biology <-> Computer Science
        ("biology", "neuron", "computer_science", "node"),
        ("biology", "neural network", "computer_science", "artificial neural network"),
        ("biology", "evolution", "computer_science", "genetic algorithm"),
        ("biology", "immune system", "computer_science", "intrusion detection"),
        ("biology", "DNA", "computer_science", "code"),
        ("biology", "gene", "computer_science", "instruction"),
        ("biology", "cell", "computer_science", "unit"),
        ("biology", "tissue", "computer_science", "module"),
        ("biology", "organ", "computer_science", "component"),
        ("biology", "brain", "computer_science", "processor"),
        ("biology", "photosynthesis", "computer_science", "energy harvesting"),
        # Biology <-> Economics
        ("biology", "metabolism", "economics", "cash flow"),
        ("biology", "ecosystem", "economics", "market"),
        ("biology", "cell", "society", "individual"),
        ("biology", "population", "economics", "workforce"),
        ("biology", "predator", "economics", "competitor"),
        ("biology", "prey", "economics", "customer"),
        ("biology", "symbiosis", "economics", "partnership"),
        ("biology", "adaptation", "economics", "innovation"),
        ("biology", "selection", "economics", "competition"),
        ("biology", "homeostasis", "economics", "market equilibrium"),
        # Physics <-> Economics
        ("physics", "force", "economics", "incentive"),
        ("physics", "potential energy", "economics", "potential profit"),
        ("physics", "kinetic energy", "economics", "active revenue"),
        ("physics", "entropy", "information_theory", "information_entropy"),
        ("physics", "resonance", "sociology", "viral phenomenon"),
        ("physics", "wave", "sociology", "trend"),
        ("physics", "equilibrium", "economics", "market equilibrium"),
        ("physics", "friction", "economics", "transaction cost"),
        ("physics", "inertia", "economics", "market resistance"),
        ("physics", "momentum", "economics", "market trend"),
        ("physics", "pressure", "economics", "market pressure"),
        ("physics", "temperature", "economics", "market heat"),
        # Physics <-> Energy
        ("physics", "potential", "energy", "storage capacity"),
        ("physics", "flow", "energy", "current"),
        ("physics", "resistance", "energy", "internal resistance"),
        ("physics", "capacitor", "energy", "battery"),
        ("physics", "inductor", "energy", "flywheel"),
        # Chemistry <-> Economics/Society
        ("chemistry", "catalyst", "economics", "accelerator"),
        ("chemistry", "reaction", "sociology", "social change"),
        ("chemistry", "equilibrium", "economics", "market equilibrium"),
        ("chemistry", "bond", "society", "relationship"),
        ("chemistry", "solution", "society", "resolution"),
        ("chemistry", "compound", "society", "organization"),
        ("chemistry", "crystal", "society", "structure"),
        # Computer Science <-> Biology
        ("computer_science", "algorithm", "biology", "metabolic pathway"),
        ("computer_science", "memory", "biology", "memory"),
        ("computer_science", "protocol", "sociology", "ritual"),
        ("computer_science", "virus", "biology", "virus"),
        ("computer_science", "firewall", "biology", "immune system"),
        ("computer_science", "cache", "biology", "short-term memory"),
        ("computer_science", "database", "biology", "long-term memory"),
        ("computer_science", "network", "biology", "nervous system"),
        ("computer_science", "bandwidth", "biology", "nerve capacity"),
        # Computer Science <-> Energy
        ("computer_science", "load balancing", "energy", "grid management"),
        ("computer_science", "queue", "energy", "storage buffer"),
        ("computer_science", "scheduler", "energy", "load dispatcher"),
        ("computer_science", "optimization", "energy", "efficiency tuning"),
        # Mathematics <-> All domains
        ("mathematics", "optimization", "energy", "efficiency maximization"),
        ("mathematics", "gradient", "economics", "marginal change"),
        ("mathematics", "convergence", "physics", "equilibrium"),
        ("mathematics", "divergence", "physics", "instability"),
        ("mathematics", "graph", "computer_science", "network"),
        ("mathematics", "graph", "biology", "food web"),
        # Materials <-> Energy
        ("materials", "conductor", "energy", "electrode"),
        ("materials", "insulator", "energy", "separator"),
        ("materials", "crystal", "energy", "lattice structure"),
        ("materials", "composite", "energy", "hybrid system"),
        ("materials", "fatigue", "energy", "degradation"),
        ("materials", "corrosion", "energy", "electrolyte breakdown"),
        # Energy <-> Biology
        ("energy", "storage", "biology", "fat storage"),
        ("energy", "grid", "biology", "circulatory system"),
        ("energy", "peak load", "biology", "stress response"),
        ("energy", "baseload", "biology", "metabolic rate"),
        ("energy", "renewable", "biology", "sustainable resource"),
    ]

    def __init__(self):
        self.knowledge_graph = get_knowledge_graph()
        self._load_conceptual_metaphors()

    def _load_conceptual_metaphors(self):
        """Load conceptual metaphors into knowledge graph."""
        for (
            source_domain,
            source_concept,
            target_domain,
            target_concept,
        ) in self.CONCEPTUAL_METAPHORS:
            # Check if already exists
            existing = self.knowledge_graph.get_nodes_by_type("analogy")
            exists = any(
                a.get("metadata", {}).get("source_concept") == source_concept
                and a.get("metadata", {}).get("target_concept") == target_concept
                for a in existing
            )
            if not exists:
                self.knowledge_graph.add_analogy(
                    source_domain=source_domain,
                    target_domain=target_domain,
                    source_concept=source_concept,
                    target_concept=target_concept,
                    mapping_type="semantic",
                    confidence=0.8,
                    evidence=["conceptual_metaphor"],
                )

    def get_domain_concepts(self, domain: str) -> List[str]:
        """Get characteristic concepts for a domain."""
        return self.DOMAIN_CONCEPTS.get(domain, [])

    def find_conceptual_metaphors(
        self, source_domain: str, target_domain: str
    ) -> List[Tuple[str, str]]:
        """Find known conceptual metaphors between domains."""
        results = []
        for sd, sc, td, tc in self.CONCEPTUAL_METAPHORS:
            if sd == source_domain and td == target_domain:
                results.append((sc, tc))
            elif sd == target_domain and td == source_domain:
                results.append((tc, sc))  # Reverse
        return results

    # ═══════════════════════════════════════════════════════════════════
    # DYNAMIC CONCEPT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════

    def add_concept(self, domain: str, concept: str, auto_save: bool = True) -> bool:
        """
        Add a new concept to a domain.

        Args:
            domain: Domain name (creates new if doesn't exist)
            concept: Concept to add
            auto_save: Save to knowledge graph immediately

        Returns:
            True if added, False if already exists
        """
        if domain not in self.DOMAIN_CONCEPTS:
            self.DOMAIN_CONCEPTS[domain] = []
            print(f"✓ Created new domain: {domain}")

        if concept.lower() in [c.lower() for c in self.DOMAIN_CONCEPTS[domain]]:
            return False  # Already exists

        self.DOMAIN_CONCEPTS[domain].append(concept)

        if auto_save:
            self._save_concept_to_graph(domain, concept)

        return True

    def add_conceptual_metaphor(
        self,
        source_domain: str,
        source_concept: str,
        target_domain: str,
        target_concept: str,
        confidence: float = 0.8,
        auto_save: bool = True,
    ) -> bool:
        """
        Add a new conceptual metaphor.

        Args:
            source_domain: Source domain
            source_concept: Source concept
            target_domain: Target domain
            target_concept: Target concept
            confidence: Confidence level
            auto_save: Save to knowledge graph

        Returns:
            True if added, False if already exists
        """
        # Ensure domains and concepts exist
        self.add_concept(source_domain, source_concept, auto_save=False)
        self.add_concept(target_domain, target_concept, auto_save=False)

        # Check if already exists
        for sd, sc, td, tc in self.CONCEPTUAL_METAPHORS:
            if (
                sd == source_domain
                and sc == source_concept
                and td == target_domain
                and tc == target_concept
            ):
                return False

        self.CONCEPTUAL_METAPHORS.append(
            (source_domain, source_concept, target_domain, target_concept)
        )

        if auto_save:
            self.knowledge_graph.add_analogy(
                source_domain=source_domain,
                target_domain=target_domain,
                source_concept=source_concept,
                target_concept=target_concept,
                mapping_type="semantic",
                confidence=confidence,
                evidence=["user_added"],
            )
            self.knowledge_graph.save()

        return True

    def extract_concepts_from_text(
        self, text: str, domain: str, min_length: int = 4
    ) -> List[str]:
        """
        Auto-extract potential concepts from text.

        Uses simple heuristics:
        - Nouns and noun phrases
        - Technical terms
        - Capitalized terms

        Args:
            text: Text to analyze
            domain: Domain to assign concepts to
            min_length: Minimum concept length

        Returns:
            List of extracted concepts
        """
        import re

        # Simple extraction patterns
        patterns = [
            r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",  # Capitalized phrases
            r"\b[a-z]+(?:\s+[a-z]+){1,2}\b",  # Multi-word terms
        ]

        extracted = set()
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                if len(match) >= min_length and match not in [
                    "this",
                    "that",
                    "with",
                    "from",
                ]:
                    extracted.add(match)

        # Filter out common stop words
        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "man",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "its",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
        }

        extracted = {c for c in extracted if c not in stop_words}

        # Add to domain
        added = []
        for concept in extracted:
            if self.add_concept(domain, concept, auto_save=False):
                added.append(concept)

        if added:
            self.knowledge_graph.save()

        return added

    def auto_extract_from_hypothesis(
        self, hypothesis: str, domain: str
    ) -> Dict[str, List[str]]:
        """
        Auto-extract concepts and potential analogies from a hypothesis.

        This is the main auto-discovery method.

        Args:
            hypothesis: Hypothesis text
            domain: Domain of the hypothesis

        Returns:
            Dict with 'concepts' and 'potential_analogies'
        """
        # Extract concepts
        concepts = self.extract_concepts_from_text(hypothesis, domain)

        # Find potential cross-domain analogies
        potential_analogies = []

        for concept in concepts:
            # Check against all other domains
            for other_domain, other_concepts in self.DOMAIN_CONCEPTS.items():
                if other_domain == domain:
                    continue

                for other_concept in other_concepts:
                    # Simple string similarity check
                    if (
                        concept.lower() in other_concept.lower()
                        or other_concept.lower() in concept.lower()
                    ):
                        potential_analogies.append(
                            {
                                "source": (domain, concept),
                                "target": (other_domain, other_concept),
                                "match_type": "substring",
                            }
                        )

        return {
            "concepts": concepts,
            "potential_analogies": potential_analogies,
        }

    def _save_concept_to_graph(self, domain: str, concept: str):
        """Save concept node to knowledge graph."""
        node_id = f"concept_{domain}_{concept.replace(' ', '_')}"

        if not self.knowledge_graph.has_node(node_id):
            self.knowledge_graph.graph.add_node(
                node_id,
                node_type="concept",
                domain=domain,
                concept=concept,
                created_at=datetime.now().isoformat(),
            )

            # Link to domain
            domain_id = f"domain_{domain}"
            if not self.knowledge_graph.has_node(domain_id):
                self.knowledge_graph.graph.add_node(
                    domain_id,
                    node_type="domain",
                    name=domain,
                )

            self.knowledge_graph.add_edge(node_id, domain_id, edge_type="belongs_to")
            self.knowledge_graph.save()

    def list_domains(self) -> List[str]:
        """List all available domains."""
        return list(self.DOMAIN_CONCEPTS.keys())

    def get_concept_stats(self) -> Dict[str, int]:
        """Get concept counts by domain."""
        return {
            domain: len(concepts) for domain, concepts in self.DOMAIN_CONCEPTS.items()
        }


class AnalogyEngine:
    """
    Main analogy discovery engine combining multiple methods.

    Methods:
    - Semantic: Sentence-BERT cosine similarity
    - Structural: Word2Vec vector arithmetic
    - Knowledge-based: ConceptNet/conceptual metaphors
    - Graph-based: NetworkX structure matching
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        word2vec_path: Optional[str] = None,
        similarity_threshold: float = 0.6,
    ):
        self.embedder = SemanticEmbedder(embedding_model)
        self.word2vec = Word2VecAnalogySolver(word2vec_path)
        self.conceptnet = ConceptNetBridge()
        self.knowledge_graph = get_knowledge_graph()
        self.similarity_threshold = similarity_threshold

        print(f"✓ AnalogyEngine initialized")
        print(
            f"  - Semantic: {'Sentence-BERT' if HAS_SENTENCE_TRANSFORMERS else 'TF-IDF fallback'}"
        )
        print(f"  - Word2Vec: {'Available' if HAS_GENSIM else 'Unavailable'}")

    def find_analogies(
        self,
        source_domain: str,
        target_domain: str,
        source_concept: str,
        top_k: int = 5,
    ) -> List[AnalogyResult]:
        """
        Find analogies for a concept across domains.

        Example:
            engine.find_analogies("biology", "computer_science", "neuron")
            => Returns: [AnalogyResult("neuron", "node", ...), ...]
        """
        results: List[AnalogyResult] = []

        # Method 1: Check known conceptual metaphors
        metaphors = self.conceptnet.find_conceptual_metaphors(
            source_domain, target_domain
        )
        for sc, tc in metaphors:
            if sc.lower() == source_concept.lower():
                results.append(
                    AnalogyResult(
                        source_concept=source_concept,
                        target_concept=tc,
                        source_domain=source_domain,
                        target_domain=target_domain,
                        mapping_type="semantic",
                        confidence=0.85,
                        reasoning="Known conceptual metaphor",
                    )
                )

        # Method 2: Semantic similarity to target domain concepts
        target_concepts = self.conceptnet.get_domain_concepts(target_domain)
        if target_concepts:
            source_embedding = self.embedder.embed(
                f"{source_concept} in {source_domain}"
            )
            target_embeddings = self.embedder.batch_embed(
                [f"{tc} in {target_domain}" for tc in target_concepts]
            )

            similarities = np.dot(target_embeddings, source_embedding)
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            for idx in top_indices:
                if similarities[idx] >= self.similarity_threshold:
                    results.append(
                        AnalogyResult(
                            source_concept=source_concept,
                            target_concept=target_concepts[idx],
                            source_domain=source_domain,
                            target_domain=target_domain,
                            mapping_type="semantic",
                            confidence=float(similarities[idx]),
                            semantic_similarity=float(similarities[idx]),
                            reasoning=f"Semantic similarity: {similarities[idx]:.3f}",
                        )
                    )

        # Method 3: Word2Vec analogies if available
        if self.word2vec.model is not None:
            # Try to find analogical mappings
            # For "neuron in biology", look for "X in computer_science"
            # where the relationship matches
            w2v_results = self._word2vec_domain_analogy(
                source_domain, target_domain, source_concept
            )
            results.extend(w2v_results)

        # Method 4: Graph-based analogy discovery
        graph_results = self._graph_analogy_search(
            source_domain, target_domain, source_concept
        )
        results.extend(graph_results)

        # Deduplicate and sort by confidence
        seen = set()
        unique_results = []
        for r in results:
            key = (r.source_concept.lower(), r.target_concept.lower())
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        unique_results.sort(key=lambda x: x.confidence, reverse=True)
        return unique_results[:top_k]

    def _word2vec_domain_analogy(
        self,
        source_domain: str,
        target_domain: str,
        source_concept: str,
    ) -> List[AnalogyResult]:
        """Use Word2Vec to find domain analogies."""
        results = []

        # Find anchor pairs from conceptual metaphors
        anchors = self.conceptnet.find_conceptual_metaphors(
            source_domain, target_domain
        )

        for A, B in anchors[:3]:  # Use top 3 anchors
            # Solve A:B::source_concept:?
            solutions = self.word2vec.solve(A, B, source_concept, topn=3)
            for target_concept, score in solutions:
                if score >= 0.5:  # Threshold for Word2Vec
                    results.append(
                        AnalogyResult(
                            source_concept=source_concept,
                            target_concept=target_concept,
                            source_domain=source_domain,
                            target_domain=target_domain,
                            mapping_type="structural",
                            confidence=score,
                            structural_similarity=score,
                            reasoning=f"Word2Vec analogy {A}:{B}::{source_concept}:{target_concept}",
                        )
                    )

        return results

    def _graph_analogy_search(
        self,
        source_domain: str,
        target_domain: str,
        source_concept: str,
    ) -> List[AnalogyResult]:
        """Find analogies using knowledge graph structure."""
        results = []

        # Get analogy nodes connecting these domains
        analogies = self.knowledge_graph.get_nodes_by_type("analogy")

        for analogy in analogies:
            meta = analogy.get("metadata", {})
            if (
                meta.get("source_domain") == source_domain
                and meta.get("target_domain") == target_domain
            ):
                # Found a bridge - use it to suggest new analogies
                if meta.get("verified", False):
                    results.append(
                        AnalogyResult(
                            source_concept=source_concept,
                            target_concept=meta.get("target_concept", "unknown"),
                            source_domain=source_domain,
                            target_domain=target_domain,
                            mapping_type="graph_based",
                            confidence=meta.get("confidence", 0.5) * 0.9,
                            reasoning="Verified analogy from knowledge graph",
                        )
                    )

        return results

    def discover_cross_domain_analogies(
        self,
        domain1: str,
        domain2: str,
        max_analogies: int = 10,
    ) -> List[AnalogyResult]:
        """
        Systematically discover analogies between two domains.

        This is the main method for cross-domain innovation.
        """
        results = []

        # Get concepts from both domains
        concepts1 = self.conceptnet.get_domain_concepts(domain1)
        concepts2 = self.conceptnet.get_domain_concepts(domain2)

        if not concepts1 or not concepts2:
            print(f"⚠️  No predefined concepts for {domain1} or {domain2}")
            return results

        # Compute all pairwise semantic similarities
        embeddings1 = self.embedder.batch_embed(
            [f"{c} in {domain1}" for c in concepts1]
        )
        embeddings2 = self.embedder.batch_embed(
            [f"{c} in {domain2}" for c in concepts2]
        )

        # Compute similarity matrix
        similarity_matrix = np.dot(embeddings1, embeddings2.T)

        # Find best matches
        pairs = []
        for i, c1 in enumerate(concepts1):
            for j, c2 in enumerate(concepts2):
                pairs.append((similarity_matrix[i, j], c1, c2))

        pairs.sort(reverse=True)

        for score, c1, c2 in pairs[:max_analogies]:
            if score >= self.similarity_threshold:
                results.append(
                    AnalogyResult(
                        source_concept=c1,
                        target_concept=c2,
                        source_domain=domain1,
                        target_domain=domain2,
                        mapping_type="semantic",
                        confidence=float(score),
                        semantic_similarity=float(score),
                        reasoning=f"Cross-domain semantic match: {score:.3f}",
                    )
                )

        return results

    def solve_proportional_analogy(
        self,
        A: str,
        B: str,
        C: str,
    ) -> Optional[AnalogyResult]:
        """
        Solve A:B::C:? using Word2Vec.

        Example:
            solve_proportional_analogy("king", "queen", "man")
            => "woman"
        """
        if self.word2vec.model is None:
            return None

        solutions = self.word2vec.solve(A, B, C, topn=1)
        if solutions:
            D, score = solutions[0]
            return AnalogyResult(
                source_concept=f"{A}:{B}",
                target_concept=f"{C}:{D}",
                source_domain="proportional",
                target_domain="proportional",
                mapping_type="structural",
                confidence=score,
                structural_similarity=score,
                reasoning=f"Word2Vec: {A}:{B}::{C}:{D}",
            )
        return None

    def store_analogy(self, result: AnalogyResult) -> str:
        """Store analogy in knowledge graph."""
        analogy_id = self.knowledge_graph.add_analogy(
            source_domain=result.source_domain,
            target_domain=result.target_domain,
            source_concept=result.source_concept,
            target_concept=result.target_concept,
            mapping_type=result.mapping_type,
            confidence=result.confidence,
            semantic_similarity=result.semantic_similarity,
            structural_similarity=result.structural_similarity,
            evidence=result.evidence or [],
        )
        self.knowledge_graph.save()
        return analogy_id

    def get_analogy_chain(
        self,
        source_domain: str,
        target_domain: str,
        max_length: int = 3,
    ) -> List[List[str]]:
        """
        Find chains of analogies connecting domains.

        Example chain:
        biology:neuron -> cs:node -> cs:network -> biology:neural_network
        """
        return self.knowledge_graph.find_analogy_chains(
            source_domain, target_domain, max_length
        )


# ═══════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════

_analogy_engine: Optional[AnalogyEngine] = None


def get_analogy_engine() -> AnalogyEngine:
    """Get singleton analogy engine instance."""
    global _analogy_engine
    if _analogy_engine is None:
        _analogy_engine = AnalogyEngine()
    return _analogy_engine
