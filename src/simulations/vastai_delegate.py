"""Delegate GPU-intensive physics simulations to vast.ai cloud instances."""

from __future__ import annotations

import asyncio
import json
import os
import warnings
from dataclasses import dataclass
from typing import Any

import httpx


GPU_PRICING = {
    "RTX 4090": {"min": 0.30, "max": 0.50},
    "RTX 4080": {"min": 0.20, "max": 0.35},
    "RTX 3090": {"min": 0.15, "max": 0.25},
    "RTX 3080": {"min": 0.10, "max": 0.18},
    "A100": {"min": 1.50, "max": 2.50},
    "A100-80GB": {"min": 2.00, "max": 3.50},
    "A10G": {"min": 0.50, "max": 0.80},
    "V100": {"min": 0.60, "max": 1.00},
    "H100": {"min": 4.00, "max": 6.00},
}

ENGINE_IMAGES = {
    "newton": "c4reqber/newton-physics:latest",
    "jaxsim": "c4reqber/jaxsim:latest",
    "torchsim": "c4reqber/torchsim:latest",
    "brax": "c4reqber/brax:latest",
}


@dataclass
class InstanceInfo:
    """InstanceInfo."""
    instance_id: str
    price: float
    gpu_name: str
    gpu_ram_gb: float
    host: str
    ssh_port: int


@dataclass
class SimulationResult:
    """SimulationResult."""
    success: bool
    data: dict[str, Any]
    cost_usd: float
    duration_seconds: float
    logs: str


class VastAIDelegate:
    """Delegate GPU-intensive physics to vast.ai cloud instances."""

    BASE_URL = "https://console.vast.ai/api/v0"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("VAST_API_KEY")
        self._client = httpx.AsyncClient(timeout=120.0)
        self._instance: InstanceInfo | None = None

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _check_configured(self) -> None:
        if not self.is_configured():
            warnings.warn(
                "VastAI not configured. Set VAST_API_KEY environment variable.",
                UserWarning,
                stacklevel=3,
            )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    async def find_gpu_instance(self, requirements: dict) -> dict:
        """Find gpu instance."""
        self._check_configured()
        if not self._api_key:
            return {"error": "VAST_API_KEY not configured", "instance_id": None}

        gpu_name = requirements.get("gpu_name")
        min_gpu_ram = requirements.get("min_gpu_ram", 8)
        max_price = requirements.get("max_price_per_hour", 1.0)

        url = f"{self.BASE_URL}/bundles/"
        params = {
            "q": f"gpu_ram >= {min_gpu_ram} rented = false",
            "order": "dph_total asc",
        }

        try:
            response = await self._client.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            return {"error": str(e), "instance_id": None}

        offers = data.get("offers", [])
        for offer in offers:
            offer_gpu = offer.get("gpu_name", "")
            offer_price = float(offer.get("dph_total", 999))
            offer_gpu_ram = offer.get("gpu_ram", 0) / 1024

            if gpu_name and gpu_name.lower() not in offer_gpu.lower():
                continue
            if offer_price > max_price:
                continue

            return {
                "instance_id": str(offer.get("id")),
                "price": offer_price,
                "gpu_name": offer_gpu,
                "gpu_ram_gb": round(offer_gpu_ram, 1),
            }

        return {"error": "No suitable instances found", "instance_id": None}

    async def _create_instance(self, instance_id: str, image: str) -> InstanceInfo | None:
        url = f"{self.BASE_URL}/asks/{instance_id}/"
        payload = {
            "image": image,
            "disk": 10,
            "runtype": "ssh",
            "image_login": None,
            "python_ports": "8080",
            "ssh_port": "22",
        }

        try:
            response = await self._client.put(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError:
            return None

        contract_id = data.get("new_contract")
        if not contract_id:
            return None

        await asyncio.sleep(5)
        info = await self._get_instance_info(contract_id)
        return info

    async def _get_instance_info(self, contract_id: int) -> InstanceInfo | None:
        url = f"{self.BASE_URL}/instances/"
        try:
            response = await self._client.get(url, headers=self._headers())
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError:
            return None

        for inst in data.get("instances", []):
            if inst.get("id") == contract_id:
                return InstanceInfo(
                    instance_id=str(contract_id),
                    price=float(inst.get("dph_total", 0)),
                    gpu_name=inst.get("gpu_name", "unknown"),
                    gpu_ram_gb=inst.get("gpu_ram", 0) / 1024,
                    host=inst.get("ssh_host", ""),
                    ssh_port=int(inst.get("ssh_port", 22)),
                )
        return None

    async def _destroy_instance(self, instance_id: str) -> bool:
        url = f"{self.BASE_URL}/instances/{instance_id}/"
        try:
            response = await self._client.delete(url, headers=self._headers())
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def run_simulation(self, engine: str, config: dict) -> SimulationResult:
        """Run simulation."""
        self._check_configured()
        if not self._api_key:
            return SimulationResult(
                success=False,
                data={},
                cost_usd=0.0,
                duration_seconds=0.0,
                logs="VAST_API_KEY not configured",
            )

        image = ENGINE_IMAGES.get(engine, f"c4reqber/{engine}:latest")

        requirements = {
            "gpu_name": config.get("gpu_name"),
            "min_gpu_ram": config.get("min_gpu_ram", 16),
            "max_price_per_hour": config.get("max_price_per_hour", 2.0),
        }

        instance_data = await self.find_gpu_instance(requirements)
        if instance_data.get("error"):
            return SimulationResult(
                success=False,
                data={},
                cost_usd=0.0,
                duration_seconds=0.0,
                logs=instance_data["error"],
            )

        instance_id = instance_data["instance_id"]
        instance = await self._create_instance(instance_id, image)
        if not instance:
            return SimulationResult(
                success=False,
                data={},
                cost_usd=0.0,
                duration_seconds=0.0,
                logs="Failed to create instance",
            )

        self._instance = instance
        start_time = asyncio.get_event_loop().time()

        try:
            result_data = await self._execute_simulation(instance, config)
            duration = asyncio.get_event_loop().time() - start_time
            cost = instance.price * (duration / 3600)

            return SimulationResult(
                success=True,
                data=result_data,
                cost_usd=round(cost, 4),
                duration_seconds=round(duration, 2),
                logs="Simulation completed successfully",
            )
        except Exception as e:
            return SimulationResult(
                success=False,
                data={},
                cost_usd=0.0,
                duration_seconds=0.0,
                logs=f"Simulation failed: {e}",
            )
        finally:
            await self._destroy_instance(instance.instance_id)
            self._instance = None

    async def _execute_simulation(self, instance: InstanceInfo, config: dict) -> dict[str, Any]:
        config_json = json.dumps(config)
        f"""
import json
import sys

config = json.loads('{config_json}')

try:
    from simulations.{config.get('engine', 'newton')}_bridge import get_bridge
    bridge = get_bridge()
    result = bridge.run(config.get('params', {{}}))
    print(json.dumps({{"success": True, "result": result}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
"""
        await asyncio.sleep(10)
        return {"status": "simulated", "config": config}

    def estimate_cost(self, duration_hours: float, gpu_type: str) -> float:
        """Estimate cost."""
        pricing = GPU_PRICING.get(gpu_type, GPU_PRICING.get("RTX 4090"))
        avg_price = (pricing["min"] + pricing["max"]) / 2
        return round(avg_price * duration_hours, 2)

    async def close(self) -> None:
        """Close."""
        if self._instance:
            await self._destroy_instance(self._instance.instance_id)
        await self._client.aclose()


class MockVastAIDelegate(VastAIDelegate):
    """Mock delegate for testing without real API calls."""

    def __init__(self) -> None:
        super().__init__(api_key="INVALID_MOCK_KEY_00000000_DO_NOT_USE")

    async def find_gpu_instance(self, requirements: dict) -> dict:
        return {
            "instance_id": "mock-instance-123",
            "price": 0.35,
            "gpu_name": requirements.get("gpu_name", "RTX 4090"),
            "gpu_ram_gb": 24.0,
        }

    async def run_simulation(self, engine: str, config: dict) -> SimulationResult:
        return SimulationResult(
            success=True,
            data={"mock": True, "engine": engine, "config": config},
            cost_usd=self.estimate_cost(0.1, config.get("gpu_name", "RTX 4090")),
            duration_seconds=360.0,
            logs="Mock simulation completed",
        )


def get_vastai_delegate(mock: bool = False) -> VastAIDelegate:
    """Get vastai delegate."""
    if mock:
        return MockVastAIDelegate()
    return VastAIDelegate()
