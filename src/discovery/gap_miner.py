from __future__ import annotations


"""Gap & Contradiction Miner — finds research opportunities in literature."""
import datetime
import logging
import re
from typing import Any

from src.discovery.gap_analyzer_base import GAP_INDICATORS, GapAnalyzer


logger = logging.getLogger(__name__)


class GapMiner(GapAnalyzer):
    """GapMiner."""
    CONTRADICTION_PATTERNS = [
        r"(however|but|although|conversely|in contrast)",
        r"(remains unclear|remains unknown|controversial)",
        r"(further research|future work|needs to be)",
        r"(limitation|drawback|shortcoming|gap)",
        r"(contradicts|challenges|conflicts with|inconsistent)",
    ]

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize GapMiner with optional LLM client for cross-paper synthesis."""
        self._llm_client = llm_client

    def analyze(self, sources: list[dict], topic: str) -> list[dict]:
        """Analyze."""
        result = getattr(self, 'mine_for_discovery', self.analyze_papers)(topic, sources)  # type: ignore[call-arg,arg-type]
        if isinstance(result, dict):
            return result.get('gaps', [])
        return result if isinstance(result, list) else []

    async def analyze_papers(self, papers: list[Any]) -> dict[str, Any]:
        """Analyze papers."""
        " ".join(
            (p.get("abstract") or "") + " " + (p.get("title") or "") + " " +
            (p.get("description") or "") + " " + (p.get("snippet") or "")
            for p in papers if isinstance(p, dict)
        )

        # Multi-layer gap detection
        gaps = []
        contradictions = []

        for p in papers:
            if not isinstance(p, dict):
                continue
            abstract = str(p.get("abstract", "") or p.get("description", "") or p.get("snippet", ""))
            title = str(p.get("title", ""))
            text = (abstract + " " + title).lower()
            year = p.get("year") or p.get("publication_year") or 0
            citation_marker = f"{title[:120]} ({year})" if year else title[:120]

            # Layer 1: Explicit gap indicators
            for indicator in GAP_INDICATORS:
                if indicator in text:
                    sentences = re.split(r'[.!?]', abstract)
                    for s in sentences:
                        if indicator in s.lower():
                            gaps.append({
                                "indicator": indicator,
                                "paper": title[:120],
                                "sentence": s.strip()[:200],
                                "opportunity_score": self._score_gap(indicator, year),
                                "year": year,
                                "supporting_papers": [citation_marker],
                            })
                            break

            # Layer 2: Contradiction/conflict detection
            for pattern in self.CONTRADICTION_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    contradictions.append({
                        "pattern": pattern,
                        "paper": title[:120],
                        "abstract_preview": abstract[:200]
                    })
                    break

            # Layer 3: Low-citation detection (understudied area)
            citations = p.get("citation_count") or p.get("cited_by_count") or p.get("citations") or 0
            if isinstance(citations, (int, float)) and citations < 5 and len(abstract) > 100:
                gaps.append({
                    "indicator": "low_citation",
                    "paper": title[:120],
                    "sentence": f"Only {int(citations)} citations — potentially understudied area",
                    "opportunity_score": self._score_gap("low_citation", year),
                    "year": year,
                    "supporting_papers": [citation_marker],
                })

        # Deduplicate gaps before sorting
        gaps = self._deduplicate_gaps(gaps)
        gaps.sort(key=lambda g: g["opportunity_score"], reverse=True)

        # Build hypothesis_citations from deduplicated gaps
        hypothesis_citations: dict[str, list[str]] = {}
        for gap in gaps:
            sentence = gap.get("sentence", "")
            hypothesis_citations[sentence] = gap.get("supporting_papers", [])

        result = {
            "gaps_found": len(gaps),
            "contradictions_found": len(contradictions),
            "top_gaps": gaps[:15],
            "top_contradictions": contradictions[:10],
            "research_opportunity": len(gaps) >= 3 or len(contradictions) >= 2,
            "analysis_layers": 3,
            "hypothesis_citations": hypothesis_citations,
        }

        # Layer 4: Cross-paper analysis
        if len(papers) >= 2:
            cross_contradictions = await self.detect_cross_paper_contradictions(papers)
            result["cross_paper_contradictions"] = cross_contradictions
            result["cross_paper_contradictions_found"] = len(cross_contradictions)
            result["analysis_layers"] = 4
        else:
            result["cross_paper_contradictions"] = []
            result["cross_paper_contradictions_found"] = 0

        # Layer 5: LLM-based cross-paper synthesis
        if self._llm_client and len(papers) >= 2:
            synthesis = await self._synthesize_gaps_with_llm(papers)
            if synthesis:
                result["llm_synthesis"] = synthesis
                result["analysis_layers"] = 5

        return result

    def _score_gap(self, indicator: str, year: int | None = None, supporting_papers: int = 1) -> float:
        """Score a research gap indicator with optional recency and citation bonuses."""
        base_score = {
            "no study has":0.95, "has not been investigated":0.90,
            "remains unexplored":0.90, "few studies":0.75,
            "limited research":0.70, "open question":0.85,
            "unknown whether":0.80, "poorly understood":0.85,
            "understudied":0.80, "overlooked":0.85, "neglected":0.90,
            "surprisingly little":0.85, "scarcely investigated":0.90,
            "remains to be":0.75, "still unclear":0.80,
            "yet to be determined":0.75, "uncharacterized":0.85,
            "missing piece":0.90, "critical gap":0.95,
            "major gap":0.90, "knowledge gap":0.80,
            "not yet":0.75, "low_citation":0.40,
        }.get(indicator, 0.5)

        # Recency bonus: gaps from papers < 2 years old get +0.1
        if year is not None and year > 0:
            current_year = datetime.datetime.now().year
            if current_year - year < 2:
                base_score = min(1.0, base_score + 0.1)

        # Citation bonus: gaps mentioned in multiple papers get +0.1 per extra paper
        if supporting_papers > 1:
            base_score = min(1.0, base_score + 0.1 * (supporting_papers - 1))

        return base_score

    def _normalize_gap_text(self, text: str) -> str:
        """Normalize gap sentence for deduplication comparison."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        words = text.split()
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                      "have", "has", "had", "do", "does", "did", "will", "would",
                      "could", "should", "may", "might", "must", "shall", "can",
                      "need", "needs", "this", "that", "these", "those", "it",
                      "its", "our", "we", "us", "they", "them", "their", "to",
                      "of", "in", "on", "at", "by", "for", "with", "about",
                      "against", "between", "into", "through", "during", "before",
                      "after", "above", "below", "from", "up", "down", "out",
                      "off", "over", "under", "again", "further", "then", "once",
                      "only", "own", "same", "so", "than", "too", "very", "just",
                      "and", "but", "if", "or", "because", "as", "until", "while",
                      "here", "there", "when", "where", "why", "how", "all", "any",
                      "both", "each", "few", "more", "most", "other", "some", "such",
                      "no", "nor", "not", "now"}
        words = [w for w in words if w not in stop_words and len(w) > 2]
        return " ".join(sorted(words))

    def _gap_text_overlap(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two normalized gap texts."""
        norm1 = self._normalize_gap_text(text1)
        norm2 = self._normalize_gap_text(text2)
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def _deduplicate_gaps(self, gaps: list[dict]) -> list[dict]:
        """Deduplicate gaps using normalized text + keyword overlap.

        Compares gap sentences using Jaccard similarity on normalized keywords.
        Keeps the highest-scoring duplicate and merges supporting paper citations.
        """
        if not gaps:
            return []

        unique_gaps: list[dict] = []
        for gap in gaps:
            sentence = gap.get("sentence", "")
            is_duplicate = False

            for existing in unique_gaps:
                overlap = self._gap_text_overlap(sentence, existing.get("sentence", ""))
                if overlap >= 0.6:
                    is_duplicate = True
                    # Keep the highest score and freshest metadata
                    if gap.get("opportunity_score", 0) > existing.get("opportunity_score", 0):
                        existing["opportunity_score"] = gap["opportunity_score"]
                        existing["sentence"] = gap["sentence"]
                        existing["indicator"] = gap.get("indicator", existing.get("indicator"))
                        existing["year"] = gap.get("year", existing.get("year"))
                    # Merge supporting papers
                    existing_papers = set(existing.get("supporting_papers", []))
                    gap_papers = set(gap.get("supporting_papers", []))
                    existing["supporting_papers"] = sorted(existing_papers | gap_papers)
                    # Recompute score with merged citation count
                    existing["opportunity_score"] = self._score_gap(
                        existing.get("indicator", ""),
                        existing.get("year"),
                        len(existing.get("supporting_papers", [])),
                    )
                    break

            if not is_duplicate:
                gap.setdefault("supporting_papers", [gap.get("paper", "")])
                unique_gaps.append(gap)

        return unique_gaps

    def _extract_numerical_claims(self, text: str) -> list[dict]:
        """Extract numerical claims from text using regex.

        Looks for patterns like:
        - "achieved 85% accuracy"
        - "efficiency of 92.3%"
        - "error rate decreased by 15%"
        - "temperature increased to 300K"

        Returns list of {"value": float, "unit": str, "metric": str, "context": str}
        """
        claims = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        metric_words = r'efficiency|accuracy|precision|recall|f1|score|rate|error rate|temperature|pressure|speed|velocity|density|concentration|performance|throughput|latency'
        unit_pattern = r'%|percent|K|°C|°F|mm|cm|m|km|mg|g|kg|ml|l|s|ms|min|hr|Hz|GHz|MPa|GPa|eV|J|W|dB|fold|x'

        patterns = [
            # metric before value: "accuracy of 92.3%"
            (rf'({metric_words})\s+(?:of|was|is|achieved|reached|at|to)\s+([\d]+(?:\.\d+)?)\s*({unit_pattern})?', 1, 2, 3),
            # value unit metric after: "achieved 85.5% accuracy"
            (rf'(?:achieved|reached|was|is|at|report)\s+([\d]+(?:\.\d+)?)\s*({unit_pattern})?\s+({metric_words})', 3, 1, 2),
            # metric changed by/to value: "error rate decreased by 15%"
            (rf'({metric_words})\s+(?:decreased|increased|reduced|improved|dropped|rose|fell)\s+(?:by|to)\s+([\d]+(?:\.\d+)?)\s*({unit_pattern})?', 1, 2, 3),
        ]

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            for pattern, metric_group, value_group, unit_group in patterns:
                for match in re.finditer(pattern, sentence, re.IGNORECASE):
                    groups = match.groups()
                    try:
                        metric = groups[metric_group - 1].strip().lower() if groups[metric_group - 1] else "unknown"
                        value = float(groups[value_group - 1])
                        unit = groups[unit_group - 1] if unit_group <= len(groups) and groups[unit_group - 1] else ""
                        if metric and value is not None:
                            claims.append({
                                "value": value,
                                "unit": unit,
                                "metric": metric[:80],
                                "context": sentence[:200],
                            })
                    except (ValueError, IndexError):
                        continue
        return claims

    def _extract_factual_claims(self, text: str) -> list[dict]:
        """Extract factual/causal claims.

        Looks for patterns like:
        - "X causes Y"
        - "X leads to Y"
        - "X prevents Y"
        - "X is associated with Y"

        Returns list of {"subject": str, "relation": str, "object": str, "context": str}
        """
        claims = []
        sentences = re.split(r'(?<=[.!?])\s+', text)

        negative_patterns = [
            (r'([\w\s]{2,40}?)\s+does\s+not\s+cause\s+([\w\s]+)', "does_not_cause"),
            (r'([\w\s]{2,40}?)\s+is\s+independent\s+of\s+([\w\s]+)', "independent_of"),
            (r'([\w\s]{2,40}?)\s+has\s+no\s+effect\s+on\s+([\w\s]+)', "no_effect"),
        ]
        positive_patterns = [
            (r'([\w\s]{2,40}?)\s+causes?\s+([\w\s]+)', "causes"),
            (r'([\w\s]{2,40}?)\s+leads?\s+to\s+([\w\s]+)', "leads_to"),
            (r'([\w\s]{2,40}?)\s+prevents?\s+([\w\s]+)', "prevents"),
            (r'([\w\s]{2,40}?)\s+is\s+associated\s+with\s+([\w\s]+)', "associated_with"),
            (r'([\w\s]{2,40}?)\s+increases?\s+([\w\s]+)', "increases"),
            (r'([\w\s]{2,40}?)\s+decreases?\s+([\w\s]+)', "decreases"),
        ]

        _FILLER_WORDS = {
            "our", "we", "the", "these", "those", "this", "that", "a", "an",
            "findings", "show", "shows", "showed", "shown", "conclude",
            "concludes", "concluded", "results", "indicate", "indicates",
            "suggest", "suggests", "demonstrate", "demonstrates", "demonstrated",
            "prove", "proves", "proved", "observed", "reported", "study",
            "analysis", "data", "evidence", "thus", "therefore", "hence",
        }

        def _clean_subject(subject: str) -> str:
            subject = subject.strip().lower()
            words = subject.split()
            # Strip leading filler words
            while words and words[0] in _FILLER_WORDS:
                words.pop(0)
            if not words:
                return subject[:80]
            # Keep last 3 meaningful words at most
            if len(words) > 3:
                words = words[-3:]
            return " ".join(words)[:80]

        def _clean_object(obj: str) -> str:
            obj = obj.strip().lower()
            words = obj.split()
            if len(words) > 6:
                obj = " ".join(words[:6])
            return obj[:80]

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            had_negative = False
            for pattern, relation in negative_patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    subject = _clean_subject(match.group(1))
                    obj = _clean_object(match.group(2))
                    if subject and obj and len(subject) > 2 and len(obj) > 2:
                        claims.append({
                            "subject": subject,
                            "relation": relation,
                            "object": obj,
                            "context": sentence[:200],
                        })
                        had_negative = True
            if had_negative:
                continue
            for pattern, relation in positive_patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    subject = _clean_subject(match.group(1))
                    obj = _clean_object(match.group(2))
                    if subject and obj and len(subject) > 2 and len(obj) > 2:
                        claims.append({
                            "subject": subject,
                            "relation": relation,
                            "object": obj,
                            "context": sentence[:200],
                        })
        return claims

    def _claims_contradictory(self, claim1: dict, claim2: dict) -> bool:
        """Check if two claims contradict each other.

        Types of contradiction:
        1. Numerical: same metric, different values beyond margin
        2. Causal: "X causes Y" vs "X does not cause Y"
        3. Directional: "increases" vs "decreases" for same metric
        4. Temporal: "impossible" vs "demonstrated" (older vs newer)
        """
        if not claim1 or not claim2:
            return False

        # Numerical contradiction
        if "value" in claim1 and "value" in claim2:
            metric1 = claim1.get("metric", "").lower()
            metric2 = claim2.get("metric", "").lower()
            if metric1 and metric2 and metric1 == metric2:
                val1 = claim1["value"]
                val2 = claim2["value"]
                unit1 = claim1.get("unit", "")
                unit2 = claim2.get("unit", "")
                if unit1 == unit2 or (not unit1 and not unit2):
                    margin = max(abs(val1), abs(val2), 1.0) * 0.15
                    if abs(val1 - val2) > margin:
                        return True

        # Causal / directional contradiction
        if "subject" in claim1 and "subject" in claim2:
            subj1 = claim1.get("subject", "").lower()
            subj2 = claim2.get("subject", "").lower()
            obj1 = claim1.get("object", "").lower()
            obj2 = claim2.get("object", "").lower()
            rel1 = claim1.get("relation", "")
            rel2 = claim2.get("relation", "")

            if subj1 and subj2 and obj1 and obj2:
                same_subjects = subj1 == subj2 or subj1 in subj2 or subj2 in subj1
                same_objects = obj1 == obj2 or obj1 in obj2 or obj2 in obj1

                if same_subjects and same_objects:
                    contradictory_pairs = [
                        ("causes", "does_not_cause"),
                        ("causes", "no_effect"),
                        ("causes", "independent_of"),
                        ("leads_to", "does_not_cause"),
                        ("leads_to", "no_effect"),
                        ("increases", "decreases"),
                        ("prevents", "causes"),
                        ("prevents", "leads_to"),
                        ("prevents", "increases"),
                        ("associated_with", "independent_of"),
                        ("associated_with", "no_effect"),
                    ]
                    for r1, r2 in contradictory_pairs:
                        if (rel1 == r1 and rel2 == r2) or (rel1 == r2 and rel2 == r1):
                            return True

        return False

    async def detect_cross_paper_contradictions(self, papers: list[dict]) -> list[dict]:
        """Layer 4: Find contradictions between different papers."""
        all_claims = []
        for paper in papers:
            text = " ".join(filter(None, [
                str(paper.get("abstract", "")),
                str(paper.get("description", "")),
                str(paper.get("snippet", "")),
                str(paper.get("title", "")),
            ]))
            title = str(paper.get("title", ""))[:120]
            year = paper.get("year") or paper.get("publication_year") or 0
            numerical = self._extract_numerical_claims(text)
            factual = self._extract_factual_claims(text)
            for claim in numerical:
                claim["paper"] = title
                claim["year"] = year
                claim["claim_type"] = "numerical"
                all_claims.append(claim)
            for claim in factual:
                claim["paper"] = title
                claim["year"] = year
                claim["claim_type"] = "factual"
                all_claims.append(claim)

        contradictions = []
        for i in range(len(all_claims)):
            for j in range(i + 1, len(all_claims)):
                c1 = all_claims[i]
                c2 = all_claims[j]
                if c1.get("paper") == c2.get("paper"):
                    continue
                if self._claims_contradictory(c1, c2):
                    contradictions.append({
                        "paper_a": c1.get("paper", ""),
                        "paper_b": c2.get("paper", ""),
                        "claim_a": c1,
                        "claim_b": c2,
                        "contradiction_type": c1.get("claim_type", "unknown"),
                        "year_a": c1.get("year", 0),
                        "year_b": c2.get("year", 0),
                    })
        return contradictions

    async def _synthesize_gaps_with_llm(self, papers: list[Any]) -> dict[str, Any] | None:
        """Use LLM to perform cross-paper synthesis of research gaps.

        Collects keyword-based gaps and contradictions, then prompts an LLM to:
        1. Identify the most significant unresolved contradiction
        2. Propose a novel research direction addressing multiple gaps
        3. Find the paper combination suggesting the strongest discovery opportunity

        Falls back to None if LLM is unavailable or fails.
        """
        if not self._llm_client:
            return None

        # Avoid recursion: temporarily disable LLM for inner analysis
        saved_client = self._llm_client
        self._llm_client = None
        try:
            text_analysis = await self.analyze_papers(papers)
        finally:
            self._llm_client = saved_client

        gaps = text_analysis.get("top_gaps", [])
        contradictions = text_analysis.get("top_contradictions", [])
        cross_paper = text_analysis.get("cross_paper_contradictions", [])

        if not gaps and not contradictions:
            return None

        prompt = self._build_synthesis_prompt(gaps, contradictions, cross_paper, len(papers))

        try:
            response = await self._llm_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a research synthesis expert. Analyze gaps across papers and output structured JSON only.",
                max_tokens=1200,
            )
            return self._parse_synthesis_response(response)
        except Exception as e:
            logger.warning("LLM cross-paper synthesis failed: %s", e)
            return None

    def _build_synthesis_prompt(self, gaps: list[dict], contradictions: list[dict], cross_paper: list[dict], paper_count: int) -> str:
        """Build the synthesis prompt for the LLM."""
        gap_count = len(gaps)
        gap_texts = "\n".join(
            f"{i+1}. {g.get('sentence', '')} (score: {g.get('opportunity_score', 0):.2f}, papers: {', '.join(g.get('supporting_papers', [])[:2])})"
            for i, g in enumerate(gaps[:10])
        )
        contra_texts = "\n".join(
            f"{i+1}. Pattern '{c.get('pattern', '')}' in {c.get('paper', '')}"
            for i, c in enumerate(contradictions[:5])
        )
        cross_texts = "\n".join(
            f"{i+1}. {c.get('paper_a', '')} vs {c.get('paper_b', '')}: {c.get('contradiction_type', '')} contradiction"
            for i, c in enumerate(cross_paper[:5])
        )

        return (
            f"Given these {gap_count} research gaps across {paper_count} papers, analyze the following and respond with structured JSON:\n\n"
            f"GAPS:\n{gap_texts or 'None'}\n\n"
            f"SINGLE-PAPER CONTRADICTIONS:\n{contra_texts or 'None'}\n\n"
            f"CROSS-PAPER CONTRADICTIONS:\n{cross_texts or 'None'}\n\n"
            "Identify:\n"
            "1. The most significant unresolved contradiction\n"
            "2. A novel research direction that addresses multiple gaps\n"
            "3. The paper combination that most strongly suggests a discovery opportunity\n\n"
            "Output JSON with exactly these keys:\n"
            '- "most_significant_contradiction": string describing the contradiction and why it matters\n'
            '- "novel_direction": string describing a concrete research direction\n'
            '- "discovery_opportunity_papers": list of paper titles that together suggest the best opportunity'
        )

    def _parse_synthesis_response(self, response: Any) -> dict[str, Any] | None:
        """Parse and normalize the LLM synthesis response."""
        if not isinstance(response, dict):
            return None

        papers = response.get("discovery_opportunity_papers", [])
        if not isinstance(papers, list):
            papers = []

        return {
            "most_significant_contradiction": response.get("most_significant_contradiction", ""),
            "novel_direction": response.get("novel_direction", ""),
            "discovery_opportunity_papers": papers,
        }

    async def mine_with_llm(self, problem, papers) -> list | dict[str, Any]:
        """Use unified LLM provider to find research gaps.

        Attempts LLM-based gap discovery and falls back to text-based analysis.
        Logs errors instead of silently swallowing exceptions. Returns partial
        results even if some papers fail processing.
        """
        llm_gaps = []

        try:
            from src.llm.gateway import get_gateway
            paper_titles = "; ".join(p.get("title", "")[:80] for p in papers[:10])
            result = await get_gateway().chat_json(
                messages=[{
                    "role": "user",
                    "content": (
                        f"Problem: {problem}. Existing papers: {paper_titles}. "
                        "Find 5-10 SPECIFIC research gaps that no existing paper addresses. "
                        "Output a JSON object with key 'gaps' containing array of "
                        '{"gap_description":"...","opportunity_score":0.8,"why_unexplored":"..."}'
                    )
                }],
                system_prompt="You analyze scientific literature for research gaps.",
                max_tokens=800,
            )
            if isinstance(result, dict) and result.get("gaps"):
                llm_gaps = result["gaps"]
            elif isinstance(result, list):
                llm_gaps = result
        except Exception as e:
            logger.warning("LLM gap mining failed for problem %r: %s", problem, e)

        if llm_gaps:
            return llm_gaps

        # Fallback: analyze papers textually
        try:
            return await self.analyze_papers(papers)
        except Exception as e:
            logger.error("Fallback text analysis failed in mine_with_llm: %s", e)
            return {
                "gaps_found": 0,
                "contradictions_found": 0,
                "top_gaps": [],
                "top_contradictions": [],
                "research_opportunity": False,
                "analysis_layers": 0,
                "cross_paper_contradictions": [],
                "cross_paper_contradictions_found": 0,
                "hypothesis_citations": {},
                "errors": [str(e)],
            }

    async def mine_for_discovery(self, problem, papers) -> dict[str, Any]:
        # Primary: LLM-based gap analysis
        """Mine for discovery."""
        llm_result = await self.mine_with_llm(problem, papers)

        # Fallback: text-based analysis
        text_analysis = await self.analyze_papers(papers)

        # Compute potential from LLM results if available
        if isinstance(llm_result, list) and llm_result:
            scores = [g.get("opportunity_score", 0) for g in llm_result]
            potential = sum(scores) / max(len(scores), 1) if scores else 0.0
            gap_count = len(llm_result)
        elif isinstance(llm_result, dict) and llm_result.get("llm_gaps"):
            potential = 0.3  # LLM returned text, assume moderate potential
            gap_count = 1
        else:
            potential = min(1.0, text_analysis["gaps_found"] * 0.05)
            gap_count = text_analysis["gaps_found"]

        return {
            "problem": problem,
            "discovery_potential": round(potential, 2),
            "analysis": text_analysis,
            "llm_analysis": llm_result if isinstance(llm_result, list) else {},
            "gaps_found": gap_count,
            "recommendation": "HIGH" if potential > 0.5 else "MODERATE" if potential > 0.3 else "LOW",
        }
