"""
C4REQBER System Dynamics DSL archetypes.

System archetypes defined in the Stock-Flow DSL format for direct
parsing and simulation via the DSL engine.
"""
from __future__ import annotations


LIMITS_TO_GROWTH_DSL = """
STOCK Population 100
STOCK CarryingCapacity 1000
FLOW Growth Stock Population "growth_rate * Population * (1 - Population / CarryingCapacity)"
PARAM growth_rate 0.1
TIME 0 50
"""

SHIFTING_THE_BURDEN_DSL = """
STOCK ProblemSymptoms 50
STOCK FundamentalSolution 0
FLOW QuickFix ProblemSymptoms Stock "5"
FLOW AddressingRootCause Stock FundamentalSolution "2"
PARAM fix_effectiveness 0.8
TIME 0 30
"""

TRAGEDY_OF_COMMONS_DSL = """
STOCK Resource 1000
STOCK Agent1Usage 100
STOCK Agent2Usage 100
FLOW Consumption Resource Stock "(Agent1Usage + Agent2Usage) * 0.5"
FLOW Regeneration Stock Resource "Resource * 0.03"
TIME 0 100
"""

ESCALATION_DSL = """
STOCK PartyA 50
STOCK PartyB 50
FLOW AEscalation Stock PartyA "max(0.1 * PartyB - 0.05 * PartyA, 0)"
FLOW BEscalation Stock PartyB "max(0.1 * PartyA - 0.05 * PartyB, 0)"
TIME 0 50
"""

FIXES_THAT_FAIL_DSL = """
STOCK Problem 100
STOCK UnintendedConsequence 0
FLOW QuickFix Problem Stock "0.2 * Problem"
FLOW SideEffect Stock UnintendedConsequence "0.05 * Problem"
FLOW Backlash Stock Problem "0.03 * UnintendedConsequence"
TIME 0 40
"""

DSL_ARCHETYPES: dict[str, str] = {
    "limits_to_growth": LIMITS_TO_GROWTH_DSL,
    "shifting_the_burden": SHIFTING_THE_BURDEN_DSL,
    "tragedy_of_commons": TRAGEDY_OF_COMMONS_DSL,
    "escalation": ESCALATION_DSL,
    "fixes_that_fail": FIXES_THAT_FAIL_DSL,
}
