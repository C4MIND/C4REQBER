# SPDX-License-Identifier: AGPL-3.0
"""FEniCSx bridge — high-level FEM PDE solver (dolfinx).

Install: conda install -c conda-forge fenics-dolfinx
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class FenicsxBridge(BaseSimulationAdapter):
    """Bridge to FEniCSx / DOLFINx for finite-element PDE solving."""

    _engine_name = "fenicsx"
    _package_checks = ["dolfinx"]
    _install_hint = "conda install -c conda-forge fenics-dolfinx"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected keys: mesh_resolution, element_degree, equation_type

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            import dolfinx
            import numpy as np
            from mpi4py import MPI
            from dolfinx import fem, mesh
            import ufl

            # Default: solve Poisson on unit square
            n = self._params.get("mesh_resolution", 32)
            degree = self._params.get("element_degree", 1)
            domain = mesh.create_unit_square(MPI.COMM_WORLD, n, n)
            V = fem.functionspace(domain, ("Lagrange", degree))

            u = ufl.TrialFunction(V)
            v = ufl.TestFunction(V)
            f = fem.Constant(domain, 1.0)
            a = ufl.dot(ufl.grad(u), ufl.grad(v)) * ufl.dx
            L = f * v * ufl.dx

            # Dirichlet BC u=0 on boundary
            tdim = domain.topology.dim
            fdim = tdim - 1
            domain.topology.create_entities(fdim)
            boundary_facets = dolfinx.mesh.locate_entities_boundary(
                domain, fdim, lambda x: np.full(x.shape[1], True)
            )
            bc = fem.dirichletbc(
                0.0,
                dolfinx.fem.locate_dofs_topological(V, fdim, boundary_facets),
                V,
            )

            problem = fem.petsc.LinearProblem(a, L, bcs=[bc])
            uh = problem.solve()

            # Extract L2 norm as scalar metric
            expr = fem.Expression(uh * uh, V.element.interpolation_points())
            uh2 = fem.Function(V)
            uh2.interpolate(expr)
            l2_norm = float(domain.comm.allreduce(
                fem.assemble_scalar(fem.form(uh2 * ufl.dx)), op=MPI.SUM
            ) ** 0.5)

            return {
                "l2_norm": l2_norm,
                "dofs": V.dofmap.index_map.size_global,
                "mesh_cells": domain.topology.index_map(tdim).size_global,
            }

        return self._run_wrapped(_run, input_data)
