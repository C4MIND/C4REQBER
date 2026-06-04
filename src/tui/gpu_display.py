from __future__ import annotations


"""
TUI: GPU Display
GPU dashboard display methods for C4TUI.
"""

import os
import time
from typing import Any

from rich import box
from rich.panel import Panel
from rich.text import Text


def fetch_gpu_dashboard_data() -> dict[str, Any]:
    """Fetch and cache GPU dashboard data (local + cloud + NIM). Cached 30s."""
    _gpu_dashboard_data = getattr(fetch_gpu_dashboard_data, '_cache', None)
    _gpu_dashboard_time = getattr(fetch_gpu_dashboard_data, '_cache_time', 0)

    now = time.time()
    if _gpu_dashboard_data and (now - _gpu_dashboard_time) < 30:
        return _gpu_dashboard_data

    data: dict[str, Any] = {
        "local": None,
        "vastai_gpus": [],
        "cloud_providers": [],
        "nim_status": "not configured",
        "nim_models": 0,
        "overall": "red",
    }

    try:
        from compute.gpu_dashboard import GPUComputeDashboard
        local = GPUComputeDashboard().detect_local_gpu()
        data["local"] = local
        data["cloud_providers"] = GPUComputeDashboard().probe_cloud_providers()
    except (ImportError, KeyError):
        pass

    vastai_key = os.getenv("VASTAI_API_KEY", "")
    if vastai_key:
        try:
            import httpx
            with httpx.Client(timeout=5) as c:
                r = c.get(
                    "https://console.vast.ai/api/v0/bundles/",
                    headers={"Authorization": f"Bearer {vastai_key}", "Accept": "application/json"},
                )
                if r.status_code == 200:
                    offers = r.json().get("offers", [])
                    data["vastai_gpus"] = sorted(offers, key=lambda o: o.get("dph_total", 999))[:5]
        except (AttributeError, ImportError, KeyError):
            data["vastai_gpus"] = []

    nim_key = os.getenv("NVIDIA_API_KEY", "")
    if nim_key:
        try:
            import httpx
            with httpx.Client(timeout=5) as c:
                r = c.get(
                    "https://integrate.api.nvidia.com/v1/models",
                    headers={"Authorization": f"Bearer {nim_key}"},
                )
                if r.status_code == 200:
                    models = r.json().get("data", [])
                    data["nim_status"] = "online"
                    data["nim_models"] = len(models)
                else:
                    data["nim_status"] = f"error {r.status_code}"
        except (AttributeError, ImportError, KeyError):
            data["nim_status"] = "unreachable"

    has_local = data["local"] is not None
    has_cloud = bool(data["vastai_gpus"]) or bool(data["cloud_providers"])
    nim_online = data["nim_status"] == "online"

    if has_local and has_cloud and nim_online:
        data["overall"] = "green"
    elif has_local or has_cloud:
        data["overall"] = "yellow"
    else:
        data["overall"] = "red"

    fetch_gpu_dashboard_data._cache = data  # type: ignore[attr-defined]
    fetch_gpu_dashboard_data._cache_time = now  # type: ignore[attr-defined]
    return data


def get_gpu_header_text() -> str:
    """Build fast GPU status string for header."""
    try:
        data = fetch_gpu_dashboard_data()
    except (ImportError, AttributeError, OSError, ValueError):
        return "🖥️ GPU: — "

    local = data.get("local")
    cloud = data.get("cloud_providers", [])
    vastai = data.get("vastai_gpus", [])
    nim_status = data.get("nim_status", "unknown")
    overall = data.get("overall", "red")

    status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(overall, "⚙️")

    if local is not None:
        gpu_name = getattr(local, "gpu_name", "GPU")
        short_name = gpu_name[:18]
        return f"🖥️ {short_name} {status_icon}"
    elif cloud or vastai:
        return f"☁️ cloud {status_icon}"
    else:
        return f"�️ CPU {status_icon}"


def make_gpu_dashboard_panel() -> Panel:
    """Full GPU dashboard panel: local + cloud + NIM + status indicator."""
    text = Text()

    data = fetch_gpu_dashboard_data()
    local = data.get("local")
    vastai_gpus = data.get("vastai_gpus", [])
    cloud_providers = data.get("cloud_providers", [])
    nim_status = data.get("nim_status", "unknown")
    nim_models = data.get("nim_models", 0)
    overall = data.get("overall", "red")

    status_style = {"green": "bold #4ADE80", "yellow": "bold #FFD93D", "red": "bold #FF6B6B"}
    status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    overall_label = {"green": "ALL SYSTEMS GO", "yellow": "DEGRADED", "red": "OFFLINE"}

    text.append(
        f"GPU COMPUTE STATUS: {status_icon.get(overall, '⚙️')} {overall_label.get(overall, 'UNKNOWN')}\n",
        style=status_style.get(overall, "bold"),
    )

    text.append("─" * 50 + "\n", style="dim")

    text.append("\n�️  LOCAL GPU\n", style="bold #4ECDC4")
    if local is not None:
        provider_icon = {
            "nvidia_cuda": "🟢", "apple_metal": "🔵", "amd_rocm": "🟣",
        }.get(getattr(local, "provider", ""), "�️")
        text.append(f"   {provider_icon} {getattr(local, 'gpu_name', 'Unknown')}\n")
        text.append(f"   Provider: {getattr(local, 'provider', 'unknown')}\n")
        mem_total = getattr(local, "memory_total_mb", 0)
        mem_used = getattr(local, "memory_used_mb", 0)
        if mem_total > 0:
            mem_pct = (mem_used / mem_total * 100) if mem_total else 0
            text.append(f"   VRAM: {mem_used}MB / {mem_total}MB ({mem_pct:.0f}%)\n")
        util = getattr(local, "utilization_pct", 0)
        if util > 0:
            text.append(f"   Utilization: {util:.1f}%\n")
    else:
        text.append("   No local GPU detected\n", style="dim red")

    text.append("\n☁️  CLOUD GPU INSTANCES\n", style="bold #FFD93D")
    if vastai_gpus:
        text.append(f"   Vast.ai: {len(vastai_gpus)} instances under $0.05/hr\n")
        for g in vastai_gpus[:5]:
            name = g.get("gpu_name", "unknown")[:22]
            price = g.get("dph_total", 0)
            dlperf = g.get("dlperf", 0)
            text.append(f"     {name} ${price:.3f}/hr (dlperf: {dlperf:.1f})\n", style="dim")
    else:
        vastai_key = os.getenv("VASTAI_API_KEY", "")
        if vastai_key:
            text.append("   Vast.ai: No instances under $0.05/hr or API unreachable\n", style="dim yellow")
        else:
            text.append("   Vast.ai: Not configured (set VASTAI_API_KEY)\n", style="dim")

    if cloud_providers:
        for c in cloud_providers:
            text.append(f"   {getattr(c, 'provider', 'cloud')}: {getattr(c, 'gpu_name', 'N/A')} ${getattr(c, 'price_per_hr', 0):.2f}/hr\n", style="dim")

    text.append("\n🤖  NVIDIA NIM\n", style="bold #4ADE80")
    nim_icon = {"online": "🟢", "not configured": "⚙️"}.get(nim_status, "🔴")
    if nim_status == "online":
        text.append(f"   {nim_icon} Status: online — {nim_models} models available\n", style="green")
    elif nim_status == "not configured":
        text.append(f"   {nim_icon} Status: not configured (set NVIDIA_API_KEY)\n", style="dim")
    else:
        text.append(f"   {nim_icon} Status: {nim_status}\n", style="dim red")

    return Panel(
        text,
        title=f"[bold]{status_icon.get(overall, '⚙️')} GPU COMPUTE DASHBOARD[/]",
        border_style=status_style.get(overall, "bold"),
        box=box.ROUNDED,
        padding=(1, 2),
    )
