DOMAIN_SIMULATION_MAP = {
    'materials': ['cfd','phase_field','thermal','atomistic_deposition','composite_mechanics','crystal_growth','dft','elasticity_3d'],
    'biology': ['agent_based','epidemic_sir','hodgkin_huxley','enzyme_kinetics','population_genetics','predator_prey','gene_regulatory','protein_folding'],
    'climate': ['climate_gcm','advection_diffusion','air_quality','thermal','boundary_layer','reaction_diffusion','forest_gap','cellular_automata'],
    'physics': ['n_body','double_pendulum','wave_equation','quantum_harmonic_oscillator','spring_mass','acoustic_wave','maxwell_fdtd','black_hole_accretion'],
    'medicine': ['epidemic_seir','pharmacokinetics','enzyme_kinetics','signal_transduction','age_structured','hodgkin_huxley','neural_mass','agent_based'],
    'neuroscience': ['neural_mass','hodgkin_huxley','connectome','synaptic_plasticity','agent_based','ising_model','cellular_automata','wave_equation'],
    'computer_science': ['neural_network','cellular_automata','game_theory','markov_chain','monte_carlo_pi','bootstrap','optimization_lp','social_network'],
}


def get_domain_simulations(domain: str, count: int = 8) -> list[str]:
    return DOMAIN_SIMULATION_MAP.get(domain, DOMAIN_SIMULATION_MAP['physics'])[:count]
