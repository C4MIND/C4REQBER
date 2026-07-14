from __future__ import annotations


"""HIL Pipeline phase modules package."""

from .phase_a_usp import PhaseA_USPCognitiveFraming
from .phase_b_knowledge import PhaseB_KnowledgeAcquisition
from .phase_c_gaps import PhaseC_GapAnalysis
from .phase_d_agents import PhaseD_CognitiveAgents
from .phase_e_simulation import PhaseE_SimulationVerification
from .phase_f_dissertation import PhaseF_DissertationGeneration
from .phase_g_quality import PhaseG_QualityControl


__all__ = [
    "PhaseA_USPCognitiveFraming",
    "PhaseB_KnowledgeAcquisition",
    "PhaseC_GapAnalysis",
    "PhaseD_CognitiveAgents",
    "PhaseE_SimulationVerification",
    "PhaseF_DissertationGeneration",
    "PhaseG_QualityControl",
]
