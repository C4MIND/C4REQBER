from __future__ import annotations


"""Phase A: USP Cognitive Framing — IMPACT, C4, MP, QZRF, Isomorphism, MatrixDream."""

import logging
from typing import Any

from src.c4.engine import C4Space, C4State
from src.c4.transformer import DomainTransformer
from src.metamodels.impact import ImpactEngine
from src.metamodels.matrix_dream import MatrixDreamLibrary
from src.metamodels.mp.library import MPLibrary
from src.metamodels.mp.profiles import MPRotationEngine
from src.metamodels.qzrf.operators import QzrfLibrary


logger = logging.getLogger(__name__)


class PhaseA_USPCognitiveFraming:
    """Run USP metamodel analysis: IMPACT, C4, MP, QZRF, Isomorphism, MatrixDream."""

    def __init__(self) -> None:
        self.c4_space = C4Space()
        self.impact = ImpactEngine()
        self.mp_lib = MPLibrary()
        self.mp_rotation = MPRotationEngine(self.mp_lib)
        self.qzrf = QzrfLibrary()
        self.matrix_dream = MatrixDreamLibrary()
        self.transformer = DomainTransformer(self.c4_space)

    def run(self, topic: str) -> dict[str, Any]:
        """Execute all USP framing steps and return combined context."""
        print("\n[Phase A] USP Cognitive Framing...")

        # Step A1: IMPACT Analysis
        print("\n[A1/7] Running IMPACT analysis...")
        impact_result = self._run_impact_analysis(topic)

        # Step A2: C4 Fingerprint
        print("\n[A2/7] Running C4 fingerprint...")
        c4_state = self._run_c4_fingerprint(topic)

        # Step A3: MP Rotation
        print("\n[A3/7] Running MP Rotation...")
        mp_perspectives = self._run_mp_rotation(topic, c4_state)

        # Step A4: QZRF Select
        print("\n[A4/7] Running QZRF operator selection...")
        qzrf_operators = self._run_qzrf_select(c4_state)

        # Step A5: Isomorphism Search
        print("\n[A5/7] Running isomorphism search...")
        iso_mappings = self._run_isomorphism_search(topic, c4_state)

        # Step A6: MatrixDream
        print("\n[A6/7] Running MatrixDream pattern matching...")
        matrix_patterns = self._run_matrix_dream(topic)

        return {
            "impact": impact_result,
            "c4_state": c4_state,
            "mp_perspectives": mp_perspectives,
            "qzrf_operators": qzrf_operators,
            "iso_mappings": iso_mappings,
            "matrix_patterns": matrix_patterns,
        }

    def _run_impact_analysis(self, topic: str) -> dict[str, Any]:
        try:
            result = self.impact.solve(topic)
            entities: list[str] = []
            stakeholders: list[str] = []
            for step in result.steps:
                outputs = getattr(step, "outputs", {}) or {}
                entities.extend(outputs.get("entities", []))
                stakeholders.extend(outputs.get("stakeholders", []))
            if not entities:
                entities = [topic]
            if not stakeholders:
                stakeholders = ["Researchers", "Practitioners"]
            print(f"      IMPACT: {len(entities)} entities, {len(stakeholders)} stakeholders")
            return {"entities": entities, "stakeholders": stakeholders}
        except Exception as e:
            logger.warning("IMPACT analysis failed: %s", e)
            return {"entities": [], "stakeholders": []}

    def _run_c4_fingerprint(self, topic: str) -> str:
        try:
            fp = self.transformer.fingerprint(domain=topic, entities=[], relations=[], constraints=[])
            if fp.c4_state:
                state = fp.c4_state
                result_str = f"{state}"
            else:
                result_str = "C4(1,1,1)"
            print(f"      C4 Fingerprint: {result_str}")
            return result_str
        except Exception as e:
            logger.warning("C4 fingerprint failed: %s", e)
            return "unknown"

    def _run_mp_rotation(self, topic: str, c4_state: str) -> list[dict[str, Any]]:
        try:
            rotation = self.mp_rotation.analyze(topic, n_profiles=3)
            perspectives = [
                {
                    "agent_id": p.agent_id,
                    "profile_name": p.profile_name,
                    "c4_state": str(p.c4_state),
                    "confidence": p.confidence,
                    "key_insights": p.key_insights,
                    "blind_spots": p.blind_spots,
                }
                for p in rotation.perspectives
            ]
            print(f"      MP Rotation: {len(perspectives)} perspectives")
            return perspectives
        except Exception as e:
            logger.warning("MP rotation failed: %s", e)
            return []

    def _run_qzrf_select(self, c4_state: str) -> list[str]:
        try:
            parsed = C4State(T=1, S=1, A=1)
            if c4_state != "unknown":
                import re
                nums = re.findall(r'\d+', c4_state)
                if len(nums) >= 3:
                    parsed = C4State(T=int(nums[0]) % 3, S=int(nums[1]) % 3, A=int(nums[2]) % 3)
            operators = self.qzrf.applicable_to(parsed)
            op_ids = [op.id for op in operators]
            print(f"      QZRF Select: {', '.join(op_ids[:5])}")
            return op_ids
        except Exception as e:
            logger.warning("QZRF select failed: %s", e)
            return []

    def _run_isomorphism_search(self, topic: str, c4_state: str) -> list[dict[str, Any]]:
        try:
            source_fp = self.transformer.fingerprint(domain=topic, entities=[topic], relations=[], constraints=[])
            memory_entries = self.transformer.search_memory(source_fp, min_confidence=0.1)
            candidates = [entry.fingerprint for entry in memory_entries[:10] if hasattr(entry, "fingerprint")]
            if not candidates:
                print("      Isomorphism Search: no candidates in memory")
                return []
            best: dict[str, Any] | None = None
            for candidate in candidates:
                result = self.transformer.find_isomorphism(source_fp, candidate.domain, [candidate, source_fp])
                if best is None or result.confidence > float(best.get("confidence", 0.0)):
                    best = {
                        "source_domain": result.source_domain,
                        "target_domain": result.target_domain,
                        "confidence": result.confidence,
                        "isomorphism_type": str(result.isomorphism_type),
                        "description": result.description,
                    }
            if best and float(best.get("confidence", 0.0)) > 0.3:
                print(f"      Isomorphism Search: found (confidence={best['confidence']:.2f})")
                return [best]
            print("      Isomorphism Search: none above threshold")
            return []
        except Exception as e:
            logger.warning("Isomorphism search failed: %s", e)
            return []

    def _run_matrix_dream(self, topic: str) -> list[dict[str, Any]]:
        try:
            patterns = self.matrix_dream.match(topic)
            print(f"      MatrixDream: {len(patterns)} pattern matches")
            return [{"pattern": str(p[0]), "score": p[1]} for p in patterns]
        except Exception as e:
            logger.warning("MatrixDream failed: %s", e)
            return []
