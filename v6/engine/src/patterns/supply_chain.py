"""
Supply Chain Pattern
Inventory and logistics optimization

Based on:
- Inventory theory (EOQ, newsvendor)
- Bullwhip effect
- Multi-echelon systems
"""

import asyncio
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
import logging

from ..core import (
    SimulationPattern, SimulationResult, SimulationStatus,
    Hypothesis, SimulationParameter, ValidationLevel, simulation_pattern
)

logger = logging.getLogger(__name__)


@simulation_pattern(
    id="supply_chain",
    name="Supply Chain Simulation",
    category="operations",
    description="Inventory management and supply chain optimization",
)
class SupplyChainPattern(SimulationPattern):
    """
    Supply chain simulation for logistics
    
    Implements:
    - Inventory dynamics
    - Bullwhip effect
    - EOQ optimization
    - Multi-echelon supply chain
    """
    
    parameters = [
        SimulationParameter(
            name="num_echelons",
            type="int",
            default=3,
            min=1,
            max=10,
            description="Number of supply chain levels",
        ),
        SimulationParameter(
            name="periods",
            type="int",
            default=100,
            min=10,
            max=1000,
            description="Simulation periods",
        ),
        SimulationParameter(
            name="demand_mean",
            type="float",
            default=100.0,
            min=1.0,
            max=1000.0,
            description="Average demand",
        ),
        SimulationParameter(
            name="demand_std",
            type="float",
            default=20.0,
            min=0.0,
            max=200.0,
            description="Demand standard deviation",
        ),
        SimulationParameter(
            name="lead_time",
            type="int",
            default=2,
            min=1,
            max=10,
            description="Lead time (periods)",
        ),
        SimulationParameter(
            name="holding_cost",
            type="float",
            default=1.0,
            min=0.1,
            max=10.0,
            description="Holding cost per unit per period",
        ),
        SimulationParameter(
            name="shortage_cost",
            type="float",
            default=10.0,
            min=1.0,
            max=100.0,
            description="Shortage cost per unit",
        ),
    ]
    
    def can_simulate(self, hypothesis: Hypothesis) -> bool:
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()
        keywords = [
            "supply chain", "inventory", "logistics",
            "bullwhip", "eoq", "newsvendor",
            "reorder point", "safety stock",
            "demand forecasting", "multi-echelon",
        ]
        return any(kw in title or kw in desc for kw in keywords)
    
    async def run(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> SimulationResult:
        start_time = datetime.now()
        simulation_id = f"sc_{start_time.timestamp()}"
        
        try:
            results = await self._simulate_supply_chain(hypothesis, config)
            
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=datetime.now(),
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )
        except Exception as e:
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
    
    async def _simulate_supply_chain(self, hypothesis: Hypothesis, config: Dict[str, Any]) -> Dict[str, Any]:
        N = config.get("num_echelons", 3)  # Retailer, Distributor, Manufacturer
        T = config.get("periods", 100)
        demand_mean = config.get("demand_mean", 100)
        demand_std = config.get("demand_std", 20)
        lead_time = config.get("lead_time", 2)
        h_cost = config.get("holding_cost", 1.0)
        s_cost = config.get("shortage_cost", 10.0)
        
        # Initialize
        inventory = [100.0] * N  # Inventory at each echelon
        pipeline = [[] for _ in range(N)]  # Orders in transit
        orders = np.zeros((T, N))  # Order history
        demand_hist = np.zeros(T)
        
        total_holding_cost = 0
        total_shortage_cost = 0
        
        # Policy: (R, Q) - reorder point, order quantity
        # EOQ approximation
        D = demand_mean
        S = 50  # Fixed ordering cost
        Q_opt = np.sqrt(2 * D * S / h_cost)  # EOQ
        R_opt = demand_mean * lead_time + 1.65 * demand_std * np.sqrt(lead_time)  # Service level 95%
        
        for t in range(T):
            # Generate demand at retailer
            demand = max(0, demand_mean + demand_std * np.random.randn())
            demand_hist[t] = demand
            
            # Process each echelon (backwards: retailer first)
            for echelon in range(N):
                # Receive orders from upstream (pipeline)
                if pipeline[echelon] and pipeline[echelon][0][0] <= t:
                    _, qty = pipeline[echelon].pop(0)
                    inventory[echelon] += qty
                
                # Demand (from downstream or external)
                if echelon == 0:
                    echelon_demand = demand
                else:
                    # Demand from downstream echelon's order
                    echelon_demand = orders[t-1, echelon-1] if t > 0 else demand
                
                # Fulfill demand
                fulfilled = min(inventory[echelon], echelon_demand)
                inventory[echelon] -= fulfilled
                shortage = echelon_demand - fulfilled
                
                # Costs
                total_holding_cost += inventory[echelon] * h_cost
                total_shortage_cost += shortage * s_cost
                
                # Place order (upstream)
                if inventory[echelon] < R_opt or t == 0:
                    order_qty = Q_opt if echelon < N - 1 else max(0, demand_mean * 3 - inventory[echelon])
                    orders[t, echelon] = order_qty
                    
                    # Add to pipeline of upstream echelon
                    if echelon < N - 1:
                        arrival = t + lead_time
                        pipeline[echelon + 1].append((arrival, order_qty))
            
            if t % 10 == 0:
                await asyncio.sleep(0)
        
        # Calculate metrics
        order_variance = [np.var(orders[:, i]) for i in range(N)]
        
        # Bullwhip effect: variance amplification upstream
        bullwhip = []
        for i in range(1, N):
            if order_variance[i-1] > 0:
                bullwhip.append(order_variance[i] / order_variance[i-1])
        
        metrics = {
            "num_echelons": N,
            "total_holding_cost": float(total_holding_cost),
            "total_shortage_cost": float(total_shortage_cost),
            "total_cost": float(total_holding_cost + total_shortage_cost),
            "avg_inventory": float(np.mean([inv for inv in inventory])),
            "eoq": float(Q_opt),
            "reorder_point": float(R_opt),
            "bullwhip_ratios": [float(b) for b in bullwhip],
            "avg_bullwhip": float(np.mean(bullwhip)) if bullwhip else 1.0,
        }
        
        logs = [
            f"Supply chain: {N} echelons, {T} periods",
            f"EOQ: {Q_opt:.1f}, Reorder point: {R_opt:.1f}",
            f"Total cost: ${metrics['total_cost']:.2f}",
            f"Bullwhip effect: {metrics['avg_bullwhip']:.2f}x variance amplification",
        ]
        
        return {"metrics": metrics, "logs": logs}
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        metrics = results["metrics"]
        factors = []
        
        if metrics.get("eoq", 0) > 0:
            factors.append(0.3)
        
        if metrics.get("total_cost", 0) > 0:
            factors.append(0.3)
        
        if 0 < metrics.get("avg_bullwhip", 0) < 10:
            factors.append(0.2)
        
        return min(0.9, sum(factors) + 0.2)
    
    def estimate_resources(self, hypothesis: Hypothesis) -> Dict[str, Any]:
        N = hypothesis.parameters.get("num_echelons", 3)
        T = hypothesis.parameters.get("periods", 100)
        return {
            "cpu_cores": 1,
            "memory_gb": 0.5,
            "gpu_required": False,
            "estimated_time_seconds": N * T / 1000,
        }
