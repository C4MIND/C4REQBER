"""
C4 Analysis — application/analysis layer built ON TOP of the pure C4 kernel.

These modules use the C4 kernel (src/c4) plus outward dependencies (LLM, plugins,
memory) to classify problems into C4 states, route prompts, analyze/synthesize
systems, and transfer structure across domains. They are deliberately kept OUT of
src/c4 so that the kernel (src/c4) depends on nothing and stays a clean leaf.

Dependency direction: c4_analysis -> c4 (kernel) -> nothing.  Never the reverse.
"""
