from typing import Tuple, Dict
from modules import C4State, TimeAxis, ScaleAxis, AgencyAxis


class GapToC4Mapper:
    """Map discovered knowledge gaps to C4 transformation coordinates."""

    def map_gap(self, gap: Dict) -> Tuple[C4State, C4State]:
        text = gap.get("description", "").lower()

        # Time axis
        if any(w in text for w in ["history", "past", "origins", "evolution"]):
            time_from = TimeAxis.PAST
            time_to = TimeAxis.PRESENT
        elif any(
            w in text
            for w in [
                "future",
                "predict",
                "forecast",
                "potential",
                "will be",
                "next generation",
            ]
        ):
            time_from = TimeAxis.PRESENT
            time_to = TimeAxis.FUTURE
        else:
            time_from = TimeAxis.PRESENT
            time_to = TimeAxis.FUTURE

        # Scale axis
        if any(
            w in text
            for w in [
                "implement",
                "build",
                "engineer",
                "prototype",
                "hardware",
                "device",
                "experimental",
            ]
        ):
            scale_from = ScaleAxis.CONCRETE
            scale_to = ScaleAxis.ABSTRACT
        elif any(
            w in text
            for w in [
                "theory",
                "framework",
                "paradigm",
                "foundations",
                "fundamental",
                "unified",
            ]
        ):
            scale_from = ScaleAxis.ABSTRACT
            scale_to = ScaleAxis.META
        elif any(w in text for w in ["scale", "generalize", "abstract", "unify"]):
            scale_from = ScaleAxis.CONCRETE
            scale_to = ScaleAxis.ABSTRACT
        else:
            scale_from = ScaleAxis.CONCRETE
            scale_to = ScaleAxis.ABSTRACT

        # Agency axis
        if any(w in text for w in ["individual", "human", "cognitive", "personal", "agent"]):
            agency_from = AgencyAxis.SELF
            agency_to = AgencyAxis.OTHER
        elif any(
            w in text
            for w in [
                "system",
                "society",
                "global",
                "infrastructure",
                "collective",
                "ecosystem",
            ]
        ):
            agency_from = AgencyAxis.OTHER
            agency_to = AgencyAxis.SYSTEM
        else:
            agency_from = AgencyAxis.SELF
            agency_to = AgencyAxis.SYSTEM

        from_state = C4State(time_from, scale_from, agency_from)
        to_state = C4State(time_to, scale_to, agency_to)

        return from_state, to_state

    def explain_mapping(self, gap: Dict, from_state: C4State, to_state: C4State) -> str:
        """Provide structured reasoning for gap-to-C4 mapping"""
        text = gap.get("description", "").lower()
        reasoning_parts = []

        # Time reasoning
        if from_state.time != to_state.time:
            if to_state.time == TimeAxis.FUTURE:
                reasoning_parts.append(
                    "Detected future-oriented keywords → Time axis: Present→Future"
                )
            elif to_state.time == TimeAxis.PAST:
                reasoning_parts.append("Detected historical keywords → Time axis: Present→Past")

        # Scale reasoning
        if from_state.scale != to_state.scale:
            if to_state.scale == ScaleAxis.ABSTRACT:
                reasoning_parts.append(
                    "Detected theoretical/principle keywords → Scale axis: Concrete→Abstract"
                )
            elif to_state.scale == ScaleAxis.META:
                reasoning_parts.append(
                    "Detected meta/system-level keywords → Scale axis: Abstract→Meta"
                )

        # Agency reasoning
        if from_state.agency != to_state.agency:
            if to_state.agency == AgencyAxis.SYSTEM:
                reasoning_parts.append(
                    "Detected systemic/collective keywords → Agency axis: Self→System"
                )

        # Combine reasoning
        if reasoning_parts:
            reasoning = "\n".join(f"• {part}" for part in reasoning_parts)
        else:
            reasoning = "• Gap mapped using default heuristic (Present→Future, Self→System)"

        return f"""🌉 **Gap-to-C4 Mapping Reasoning**

Gap: "{gap.get("description", "")[:60]}{"..." if len(gap.get("description", "")) > 60 else ""}"

**Mapping:** {from_state} → {to_state}

**Reasoning:**
{reasoning}

**Override Option:** If this mapping doesn't feel right, you can manually specify different C4 coordinates.
"""
