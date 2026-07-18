"""Delegate GPU-intensive physics simulations to vast.ai cloud instances."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
import warnings
from dataclasses import dataclass
from typing import Any

import httpx


logger = logging.getLogger(__name__)


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
    "newton": "c4reqber/vast-sim-runner:latest",
    "jaxsim": "c4reqber/vast-sim-runner:latest",
    "torchsim": "c4reqber/vast-sim-runner:latest",
    "brax": "c4reqber/vast-sim-runner:latest",
    "amuse": "c4reqber/vast-sim-runner:latest",
    "rebound": "c4reqber/vast-sim-runner:latest",
}

# Default remote argv when config omits remote_argv (image must provide these).
_DEFAULT_REMOTE_ARGV: dict[str, list[str]] = {
    "newton": ["python3", "/app/vast_remote_runner.py", "--config", "/tmp/c4_sim_config.json"],
    "jaxsim": ["python3", "/app/vast_remote_runner.py", "--config", "/tmp/c4_sim_config.json"],
    "torchsim": ["python3", "/app/vast_remote_runner.py", "--config", "/tmp/c4_sim_config.json"],
    "amuse": ["python3", "/app/vast_remote_runner.py", "--config", "/tmp/c4_sim_config.json"],
    "rebound": ["python3", "/app/vast_remote_runner.py", "--config", "/tmp/c4_sim_config.json"],
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

        # Poll until SSH host appears (up to ~60s); no fake sleep-as-success.
        for _ in range(12):
            info = await self._get_instance_info(contract_id)
            if info and info.host:
                return info
            await asyncio.sleep(5)
        return await self._get_instance_info(contract_id)

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
                    host=inst.get("ssh_host", "") or "",
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

    def _ssh_base_cmd(self, instance: InstanceInfo) -> list[str]:
        """Build OpenSSH client argv for this instance."""
        user = os.environ.get("VAST_SSH_USER", "root")
        key = os.environ.get("VAST_SSH_KEY") or os.path.expanduser(
            os.environ.get("VAST_SSH_IDENTITY", "~/.ssh/id_rsa")
        )
        cmd = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "ConnectTimeout=20",
            "-p",
            str(instance.ssh_port or 22),
        ]
        if key and os.path.isfile(os.path.expanduser(key)):
            cmd.extend(["-i", os.path.expanduser(key)])
        cmd.append(f"{user}@{instance.host}")
        return cmd

    async def _ssh_run(
        self,
        instance: InstanceInfo,
        remote_command: str,
        *,
        stdin: bytes | None = None,
        timeout: float = 600.0,
    ) -> tuple[int, str, str]:
        """Run ``remote_command`` on the instance via OpenSSH. Returns (rc, stdout, stderr)."""
        argv = self._ssh_base_cmd(instance) + [remote_command]
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE if stdin is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out_b, err_b = await asyncio.wait_for(proc.communicate(stdin), timeout=timeout)
        except TimeoutError:
            proc.kill()
            await proc.wait()
            raise TimeoutError(f"SSH timed out after {timeout}s: {remote_command[:80]}") from None
        return (
            int(proc.returncode or 0),
            out_b.decode("utf-8", errors="replace"),
            err_b.decode("utf-8", errors="replace"),
        )

    async def run_simulation(self, engine: str, config: dict) -> SimulationResult:
        """Rent instance, SSH-exec remote runner, destroy instance."""
        self._check_configured()
        if not self._api_key:
            return SimulationResult(
                success=False,
                data={"stub": True, "executed": False},
                cost_usd=0.0,
                duration_seconds=0.0,
                logs="VAST_API_KEY not configured",
            )

        image = ENGINE_IMAGES.get(engine, f"c4reqber/{engine}:latest")
        cfg = {**config, "engine": engine}

        requirements = {
            "gpu_name": cfg.get("gpu_name"),
            "min_gpu_ram": cfg.get("min_gpu_ram", 16),
            "max_price_per_hour": cfg.get("max_price_per_hour", 2.0),
        }

        instance_data = await self.find_gpu_instance(requirements)
        if instance_data.get("error"):
            return SimulationResult(
                success=False,
                data={"stub": True, "executed": False},
                cost_usd=0.0,
                duration_seconds=0.0,
                logs=instance_data["error"],
            )

        instance_id = instance_data["instance_id"]
        instance = await self._create_instance(instance_id, image)
        if not instance:
            return SimulationResult(
                success=False,
                data={"stub": True, "executed": False},
                cost_usd=0.0,
                duration_seconds=0.0,
                logs="Failed to create instance",
            )

        self._instance = instance
        start_time = asyncio.get_event_loop().time()

        try:
            result_data = await self._execute_simulation(instance, cfg)
            duration = asyncio.get_event_loop().time() - start_time
            cost = instance.price * (duration / 3600)
            ok = (
                bool(result_data.get("executed"))
                and not result_data.get("stub")
                and str(result_data.get("status", "")).lower() in {"completed", "success", "ok"}
            )
            return SimulationResult(
                success=ok,
                data=result_data,
                cost_usd=round(cost, 4) if ok else 0.0,
                duration_seconds=round(duration, 2),
                logs=str(
                    result_data.get("error")
                    or result_data.get("logs")
                    or ("ok" if ok else "failed")
                ),
            )
        except Exception as e:
            return SimulationResult(
                success=False,
                data={"stub": True, "executed": False, "error": str(e)},
                cost_usd=0.0,
                duration_seconds=0.0,
                logs=f"Simulation failed: {e}",
            )
        finally:
            await self._destroy_instance(instance.instance_id)
            self._instance = None

    async def _execute_simulation(self, instance: InstanceInfo, config: dict) -> dict[str, Any]:
        """SSH into the instance, upload config, run remote_argv, return parsed JSON."""
        host = getattr(instance, "host", "") or ""
        if not host:
            logger.error(
                "Vast.ai SSH host missing (instance=%s)",
                getattr(instance, "instance_id", "?"),
            )
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "config": config,
                "instance_id": getattr(instance, "instance_id", None),
                "error": "No SSH host on instance — cannot execute remote simulation.",
            }

        engine = str(config.get("engine") or "newton")
        remote_argv = config.get("remote_argv")
        if remote_argv is None:
            remote_argv = list(_DEFAULT_REMOTE_ARGV.get(engine, []))
        if not remote_argv:
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "error": (
                    f"No remote_argv for engine={engine!r}. "
                    "Pass config['remote_argv'] = ['python3', 'runner.py', ...] "
                    "or use a known ENGINE_IMAGES engine."
                ),
                "instance_id": getattr(instance, "instance_id", None),
            }
        if not isinstance(remote_argv, (list, tuple)) or not all(
            isinstance(x, str) for x in remote_argv
        ):
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "error": "remote_argv must be a list[str]",
            }

        timeout = float(config.get("ssh_timeout", config.get("timeout", 600)))
        cfg_json = json.dumps(config, default=str).encode("utf-8")

        # Upload config over SSH stdin.
        rc_up, _, err_up = await self._ssh_run(
            instance,
            "cat > /tmp/c4_sim_config.json",
            stdin=cfg_json,
            timeout=min(60.0, timeout),
        )
        if rc_up != 0:
            return {
                "status": "unavailable",
                "stub": True,
                "executed": False,
                "error": f"Failed to upload config via SSH (rc={rc_up}): {err_up[:500]}",
                "instance_id": getattr(instance, "instance_id", None),
            }

        remote_cmd = " ".join(shlex.quote(a) for a in remote_argv)
        # Run the user command only — never invent physics JSON on failure.
        rc, stdout, stderr = await self._ssh_run(instance, remote_cmd, timeout=timeout)

        parsed: dict[str, Any] | None = None
        text = (stdout or "").strip()
        if text:
            # Last JSON object in stdout wins (runners often log then print JSON).
            for line in reversed(text.splitlines()):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        candidate = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(candidate, dict):
                        parsed = candidate
                        break
            if parsed is None:
                try:
                    candidate = json.loads(text)
                    if isinstance(candidate, dict):
                        parsed = candidate
                except json.JSONDecodeError:
                    parsed = None

        if parsed is not None:
            parsed.setdefault("executed", True)
            parsed.setdefault("stub", False)
            if rc != 0 and str(parsed.get("status", "")).lower() in {
                "",
                "completed",
                "success",
                "ok",
            }:
                parsed["status"] = "failed"
            parsed["returncode"] = rc
            parsed["instance_id"] = getattr(instance, "instance_id", None)
            parsed["ssh_host"] = host
            if stderr:
                parsed["stderr_tail"] = stderr[-2000:]
            return parsed

        # No JSON from runner — do not treat empty ssh success as physics.
        if rc == 0:
            return {
                "status": "unavailable",
                "executed": False,
                "stub": True,
                "returncode": 0,
                "stdout_tail": text[-2000:],
                "stderr_tail": (stderr or "")[-2000:],
                "instance_id": getattr(instance, "instance_id", None),
                "ssh_host": host,
                "error": (
                    "Remote command exited 0 but produced no JSON payload — "
                    "refusing to claim simulation completed"
                ),
            }

        logger.error(
            "Vast.ai SSH exec failed instance=%s rc=%s err=%s",
            getattr(instance, "instance_id", "?"),
            rc,
            (stderr or "")[:300],
        )
        return {
            "status": "unavailable",
            "stub": True,
            "executed": False,
            "returncode": rc,
            "error": f"Remote command failed (rc={rc}): {(stderr or stdout)[:500]}",
            "instance_id": getattr(instance, "instance_id", None),
            "ssh_host": host,
        }

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
        # Explicit mock only — never claim real GPU success without mock flag.
        return SimulationResult(
            success=False,
            data={"mock": True, "engine": engine, "config": config, "stub": True},
            cost_usd=0.0,
            duration_seconds=0.0,
            logs="MockVastAIDelegate: not a real run (success=False)",
        )


def get_vastai_delegate(mock: bool = False) -> VastAIDelegate:
    """Get vastai delegate. ``mock=True`` is for unit tests only."""
    if mock:
        return MockVastAIDelegate()
    return VastAIDelegate()
