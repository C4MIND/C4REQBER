# C44TCDI: Cross-Domain Structural Isomorphism Database
# 50+ known isomorphisms for analogical discovery

ISOMORPHISM_SEED = [
    # Fluid Dynamics ↔ Neural Networks
    {"id":"iso-001","source":"fluid_dynamics","target":"neural_networks",
     "mapping":"Navier-Stokes vortex ↔ gradient flow in weight space",
     "confidence":0.82,"triz":[1,7,15],"applications":"continual_learning,catastrophic_forgetting"},

    {"id":"iso-002","source":"fluid_dynamics","target":"neural_networks",
     "mapping":"turbulence cascade ↔ hierarchical feature learning",
     "confidence":0.78,"triz":[1,7],"applications":"deep_learning_architecture"},

    {"id":"iso-003","source":"fluid_dynamics","target":"optimization",
     "mapping":"Reynolds stress ↔ momentum in SGD",
     "confidence":0.75,"triz":[15,35],"applications":"optimizer_design"},

    # Thermodynamics ↔ Information Theory
    {"id":"iso-004","source":"thermodynamics","target":"information_theory",
     "mapping":"entropy ↔ uncertainty (Shannon)",
     "confidence":0.95,"triz":[35],"applications":"compression,coding_theory"},

    {"id":"iso-005","source":"thermodynamics","target":"machine_learning",
     "mapping":"free energy minimization ↔ variational inference (ELBO)",
     "confidence":0.90,"triz":[28,35],"applications":"VAE,Bayesian_inference"},

    {"id":"iso-006","source":"thermodynamics","target":"machine_learning",
     "mapping":"temperature ↔ inverse regularization strength",
     "confidence":0.85,"triz":[35],"applications":"simulated_annealing,distillation"},

    {"id":"iso-007","source":"thermodynamics","target":"neural_networks",
     "mapping":"heat diffusion ↔ activation propagation",
     "confidence":0.80,"triz":[1,7],"applications":"graph_neural_networks"},

    # Quantum Mechanics ↔ Machine Learning
    {"id":"iso-008","source":"quantum_mechanics","target":"machine_learning",
     "mapping":"wavefunction collapse ↔ decision boundary",
     "confidence":0.72,"triz":[28,35],"applications":"classification,uncertainty"},

    {"id":"iso-009","source":"quantum_mechanics","target":"optimization",
     "mapping":"tunneling ↔ escaping local minima",
     "confidence":0.78,"triz":[15,17],"applications":"global_optimization"},

    {"id":"iso-010","source":"quantum_mechanics","target":"neural_networks",
     "mapping":"superposition ↔ ensemble methods",
     "confidence":0.80,"triz":[5,6],"applications":"dropout,bootstrap"},

    # Biology ↔ Computing
    {"id":"iso-011","source":"biology","target":"computing",
     "mapping":"neuron ↔ perceptron",
     "confidence":0.95,"triz":[26],"applications":"deep_learning"},

    {"id":"iso-012","source":"biology","target":"computing",
     "mapping":"immune system ↔ anomaly detection",
     "confidence":0.85,"triz":[24],"applications":"cybersecurity"},

    {"id":"iso-013","source":"biology","target":"optimization",
     "mapping":"evolution ↔ genetic algorithms",
     "confidence":0.90,"triz":[2,15],"applications":"hyperparameter_tuning"},

    {"id":"iso-014","source":"biology","target":"machine_learning",
     "mapping":"synaptic pruning ↔ network sparsification",
     "confidence":0.82,"triz":[2,34],"applications":"model_compression"},

    # Neuroscience ↔ Continual Learning
    {"id":"iso-015","source":"neuroscience","target":"continual_learning",
     "mapping":"synaptic consolidation ↔ EWC (elastic weight consolidation)",
     "confidence":0.88,"triz":[7,15],"applications":"catastrophic_forgetting"},

    {"id":"iso-016","source":"neuroscience","target":"continual_learning",
     "mapping":"hippocampal replay ↔ experience replay buffer",
     "confidence":0.85,"triz":[10,24],"applications":"reinforcement_learning"},

    {"id":"iso-017","source":"neuroscience","target":"continual_learning",
     "mapping":"dendritic gating ↔ task-specific subnetworks",
     "confidence":0.80,"triz":[1,2],"applications":"continual_learning"},

    {"id":"iso-018","source":"neuroscience","target":"continual_learning",
     "mapping":"sleep consolidation ↔ offline replay training",
     "confidence":0.75,"triz":[19,21],"applications":"lifelong_learning"},

    # Physics ↔ Economics
    {"id":"iso-019","source":"physics","target":"economics",
     "mapping":"potential field ↔ market equilibrium",
     "confidence":0.70,"triz":[28],"applications":"market_modeling"},

    {"id":"iso-020","source":"physics","target":"economics",
     "mapping":"phase transition ↔ market crash",
     "confidence":0.75,"triz":[36],"applications":"risk_analysis"},

    # Network Science ↔ All
    {"id":"iso-021","source":"network_science","target":"neuroscience",
     "mapping":"small-world networks ↔ brain connectome",
     "confidence":0.85,"triz":[1,5],"applications":"brain_mapping"},

    {"id":"iso-022","source":"network_science","target":"machine_learning",
     "mapping":"scale-free degree distribution ↔ attention distribution",
     "confidence":0.78,"triz":[2],"applications":"transformer_architecture"},

    {"id":"iso-023","source":"network_science","target":"neural_networks",
     "mapping":"modularity ↔ layer-wise specialization",
     "confidence":0.82,"triz":[1,7],"applications":"architecture_design"},

    # Materials ↔ ML
    {"id":"iso-024","source":"materials_science","target":"machine_learning",
     "mapping":"crystal lattice ↔ weight matrix structure",
     "confidence":0.72,"triz":[30,31],"applications":"structured_pruning"},

    {"id":"iso-025","source":"materials_science","target":"optimization",
     "mapping":"annealing ↔ learning rate scheduling",
     "confidence":0.88,"triz":[35],"applications":"training_schedules"},

    {"id":"iso-026","source":"materials_science","target":"machine_learning",
     "mapping":"dislocation motion ↔ gradient descent path",
     "confidence":0.70,"triz":[15],"applications":"optimization_landscape"},

    # Control Theory ↔ ML
    {"id":"iso-027","source":"control_theory","target":"machine_learning",
     "mapping":"PID controller ↔ momentum optimizer (Adam)",
     "confidence":0.85,"triz":[23],"applications":"optimization"},

    {"id":"iso-028","source":"control_theory","target":"neural_networks",
     "mapping":"feedback loop ↔ backpropagation",
     "confidence":0.90,"triz":[23],"applications":"training"},

    {"id":"iso-029","source":"control_theory","target":"reinforcement_learning",
     "mapping":"optimal control ↔ policy gradient",
     "confidence":0.88,"triz":[23,15],"applications":"RL,robotics"},

    # Information Theory ↔ ML
    {"id":"iso-030","source":"information_theory","target":"machine_learning",
     "mapping":"channel capacity ↔ model capacity",
     "confidence":0.82,"triz":[28],"applications":"overfitting"},

    {"id":"iso-031","source":"information_theory","target":"continual_learning",
     "mapping":"mutual information ↔ knowledge retention",
     "confidence":0.85,"triz":[24],"applications":"catastrophic_forgetting"},

    {"id":"iso-032","source":"information_theory","target":"machine_learning",
     "mapping":"rate-distortion ↔ VAE latent space",
     "confidence":0.80,"triz":[35],"applications":"generative_models"},

    # Ecology ↔ Computing
    {"id":"iso-033","source":"ecology","target":"distributed_systems",
     "mapping":"niche partitioning ↔ resource allocation",
     "confidence":0.75,"triz":[1,2],"applications":"cloud_computing"},

    {"id":"iso-034","source":"ecology","target":"machine_learning",
     "mapping":"predator-prey dynamics ↔ adversarial training",
     "confidence":0.82,"triz":[15],"applications":"GANs"},

    {"id":"iso-035","source":"ecology","target":"optimization",
     "mapping":"biodiversity ↔ ensemble diversity",
     "confidence":0.78,"triz":[5,6],"applications":"ensemble_methods"},

    # Mechanics ↔ ML
    {"id":"iso-036","source":"mechanics","target":"optimization",
     "mapping":"potential energy ↔ loss function",
     "confidence":0.90,"triz":[28],"applications":"gradients"},

    {"id":"iso-037","source":"mechanics","target":"neural_networks",
     "mapping":"elastic deformation ↔ adversarial perturbation",
     "confidence":0.78,"triz":[14],"applications":"robustness"},

    {"id":"iso-038","source":"mechanics","target":"machine_learning",
     "mapping":"fracture mechanics ↔ catastrophic forgetting",
     "confidence":0.80,"triz":[2,15],"applications":"continual_learning"},

    # Linguistics ↔ ML
    {"id":"iso-039","source":"linguistics","target":"machine_learning",
     "mapping":"grammar ↔ architecture constraints",
     "confidence":0.72,"triz":[1],"applications":"neural_architecture_search"},

    {"id":"iso-040","source":"linguistics","target":"machine_learning",
     "mapping":"semantic shift ↔ concept drift",
     "confidence":0.80,"triz":[15],"applications":"continual_learning"},

    # Mathematics ↔ ML
    {"id":"iso-041","source":"mathematics","target":"machine_learning",
     "mapping":"manifold hypothesis ↔ dimensionality reduction",
     "confidence":0.88,"triz":[17],"applications":"representation_learning"},

    {"id":"iso-042","source":"mathematics","target":"optimization",
     "mapping":"convex duality ↔ primal-dual optimization",
     "confidence":0.85,"triz":[13],"applications":"constrained_optimization"},

    {"id":"iso-043","source":"mathematics","target":"machine_learning",
     "mapping":"Fourier transform ↔ convolution theorem ↔ CNN",
     "confidence":0.90,"triz":[28],"applications":"computer_vision"},

    {"id":"iso-044","source":"mathematics","target":"neural_networks",
     "mapping":"fixed point theorem ↔ equilibrium states ↔ RNN convergence",
     "confidence":0.82,"triz":[25],"applications":"recurrent_networks"},

    # Electromagnetics ↔ ML
    {"id":"iso-045","source":"electromagnetics","target":"machine_learning",
     "mapping":"field theory ↔ attention mechanism",
     "confidence":0.78,"triz":[28],"applications":"transformers"},

    {"id":"iso-046","source":"electromagnetics","target":"optimization",
     "mapping":"Maxwell's equations ↔ information flow in graphs",
     "confidence":0.75,"triz":[7,28],"applications":"graph_networks"},

    # Complex Systems ↔ ML
    {"id":"iso-047","source":"complex_systems","target":"machine_learning",
     "mapping":"emergence ↔ deep feature hierarchies",
     "confidence":0.82,"triz":[1,7],"applications":"deep_learning"},

    {"id":"iso-048","source":"complex_systems","target":"machine_learning",
     "mapping":"self-organized criticality ↔ critical learning regime",
     "confidence":0.78,"triz":[15,35],"applications":"training_dynamics"},

    {"id":"iso-049","source":"complex_systems","target":"neural_networks",
     "mapping":"bifurcation ↔ phase transition in learning",
     "confidence":0.80,"triz":[36],"applications":"grokking,double_descent"},

    {"id":"iso-050","source":"complex_systems","target":"continual_learning",
     "mapping":"attractor states ↔ task-specific minima",
     "confidence":0.85,"triz":[15,25],"applications":"task_switching"},

    # Additional specific isomorphisms for continual learning
    {"id":"iso-051","source":"ecology","target":"continual_learning",
     "mapping":"invasive species ↔ catastrophic interference",
     "confidence":0.82,"triz":[2,15],"applications":"task_isolation"},

    {"id":"iso-052","source":"immunology","target":"continual_learning",
     "mapping":"antibody memory ↔ weight importance",
     "confidence":0.80,"triz":[24,25],"applications":"importance_sampling"},
]
