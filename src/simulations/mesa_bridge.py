# SPDX-License-Identifier: AGPL-3.0
"""Mesa bridge — agent-based modeling framework.

Install: pip install mesa
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseSimulationAdapter, SimulationResult

logger = logging.getLogger(__name__)


class MesaBridge(BaseSimulationAdapter):
    """Bridge to Mesa for agent-based model simulations."""

    _engine_name = "mesa"
    _package_checks = ["mesa"]
    _install_hint = "pip install mesa"

    def configure(self, params: dict[str, Any]) -> None:
        super().configure(params)
        # Expected: n_agents, width, height, steps

    def run(self, input_data: dict[str, Any] | None = None) -> SimulationResult:
        def _run(data: dict[str, Any]) -> dict[str, Any]:
            from mesa import Agent, Model
            from mesa.space import MultiGrid
            from mesa.time import RandomActivation

            class SimpleAgent(Agent):
                def __init__(self, unique_id, model):
                    super().__init__(unique_id, model)
                    self.wealth = 1

                def step(self):
                    self.move()
                    if self.wealth > 0:
                        self.give_money()

                def move(self):
                    possible_steps = self.model.grid.get_neighborhood(
                        self.pos, moore=True, include_center=False
                    )
                    new_position = self.random.choice(possible_steps)
                    self.model.grid.move_agent(self, new_position)

                def give_money(self):
                    cellmates = self.model.grid.get_cell_list_contents([self.pos])
                    if len(cellmates) > 1:
                        other = self.random.choice(cellmates)
                        other.wealth += 1
                        self.wealth -= 1

            class SimpleModel(Model):
                def __init__(self, n, width, height):
                    super().__init__()
                    self.num_agents = n
                    self.grid = MultiGrid(width, height, True)
                    self.schedule = RandomActivation(self)
                    for i in range(self.num_agents):
                        a = SimpleAgent(i, self)
                        self.schedule.add(a)
                        x = self.random.randrange(self.grid.width)
                        y = self.random.randrange(self.grid.height)
                        self.grid.place_agent(a, (x, y))

                def step(self):
                    self.schedule.step()

            n = self._params.get("n_agents", 100)
            w = self._params.get("width", 10)
            h = self._params.get("height", 10)
            steps = self._params.get("steps", 20)
            model = SimpleModel(n, w, h)
            for _ in range(steps):
                model.step()

            gini = self._gini([a.wealth for a in model.schedule.agents])
            return {
                "n_agents": n,
                "grid": f"{w}x{h}",
                "steps": steps,
                "gini_coefficient": round(gini, 4),
                "note": "Mesa ABM simulation completed",
            }

        return self._run_wrapped(_run, input_data)

    @staticmethod
    def _gini(x: list[float]) -> float:
        x = sorted(x)
        n = len(x)
        cumsum = sum((i + 1) * v for i, v in enumerate(x))
        return (2 * cumsum) / (n * sum(x)) - (n + 1) / n if sum(x) else 0.0
