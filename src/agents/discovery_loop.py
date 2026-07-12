from __future__ import annotations


"""Autonomous Discovery Agent — continuous loop mode."""
import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)


class DiscoveryAgent:
    """DiscoveryAgent."""
    def __init__(self) -> None:
        self.discoveries = []
        self.cycle_count = 0
        self.start_time = time.time()

    async def select_problem(self) -> str:
        """Select problem."""
        problems = [
            "catastrophic forgetting in continual learning",
            "improve solar panel efficiency beyond Shockley-Queisser limit",
            "novel antibiotic resistance mechanism",
            "reduce transformer inference cost by 10x",
            "room-temperature superconductivity",
            "CO2 capture at atmospheric concentration",
            "fusion energy plasma confinement",
            "Alzheimer disease early detection biomarker",
            "quantum error correction for noisy qubits",
            "biodegradable plastic that decomposes in seawater",
        ]
        return problems[self.cycle_count % len(problems)]

    async def run_cycle(self) -> dict[str, Any]:
        """Run cycle."""
        problem = await self.select_problem()
        self.cycle_count += 1
        try:
            import httpx
            import os
            headers: dict[str, str] = {}
            jwt_secret = os.getenv("JWT_SECRET", "")
            if jwt_secret:
                import jwt
                headers["Authorization"] = (
                    "Bearer " + jwt.encode({"sub": "discovery-agent"}, jwt_secret, algorithm="HS256")
                )
            async with httpx.AsyncClient(timeout=300) as c:
                r = await c.post(
                    "http://127.0.0.1:8000/v8/discover/one-click",
                    json={"problem": problem, "domain": "science"},
                    headers=headers,
                )
                return r.json()# type: ignore[no-any-return]
        except (TimeoutError, ImportError, TypeError, httpx.HTTPError, json.JSONDecodeError) as e:
            logger.warning("discovery request failed for problem=%r: %s", problem, e)
            return {"status": "error", "problem": problem}

    async def run_forever(self, max_cycles: int = 10) -> list[Any]:
        """Run forever."""
        for _ in range(max_cycles):
            result = await self.run_cycle()
            self.discoveries.append({"cycle": self.cycle_count, "problem": result.get("problem",""), "timestamp": datetime.now().isoformat(), "result": result})
            os.makedirs("discovery/agent_loop", exist_ok=True)
            with open(f"discovery/agent_loop/cycle_{self.cycle_count}.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            await asyncio.sleep(5)
        return self.discoveries

if __name__ == "__main__":
    agent = DiscoveryAgent()
    asyncio.run(agent.run_forever(max_cycles=3))
