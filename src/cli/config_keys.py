"""CLI handlers for `blast config keys`."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table

from src.config.key_registry import CATEGORY_LABELS, categories
from src.config.secrets_store import (
    category_summary,
    is_registered_env_name,
    list_key_status,
    set_secret,
)


console = Console()


def _filter_rows(category: str) -> list[dict[str, Any]]:
    rows = list_key_status()
    if category:
        cat = category.lower().strip()
        rows = [r for r in rows if str(r["category"]) == cat]
    return rows


def handle_keys_command(
    *,
    json_out: bool = False,
    category: str = "",
    assign: str = "",
    health: bool = False,
) -> None:
    """Dispatch blast config keys sub-operations."""
    if assign:
        if "=" not in assign:
            console.print("[red]Use --assign ENV_NAME=value[/]")
            raise SystemExit(1)
        name, value = assign.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            console.print("[red]Empty env name[/]")
            raise SystemExit(1)
        if not is_registered_env_name(name):
            console.print(f"[red]Unknown key: {name} (see docs/API_KEYS.md)[/]")
            raise SystemExit(1)
        try:
            path = set_secret(name, value)
        except ValueError as exc:
            console.print(f"[red]{exc}[/]")
            raise SystemExit(1) from exc
        console.print(f"[green]Saved {name} → {path}[/]")
        return

    if health:
        _print_health()
        return

    if json_out:
        from src.cli.config_models import print_json

        payload = {
            "categories": [
                {
                    "id": cat,
                    "label": CATEGORY_LABELS.get(cat, cat),
                    **category_summary().get(cat, {"configured": 0, "total": 0}),
                }
                for cat in categories()
            ],
            "keys": _filter_rows(category),
        }
        print_json(payload)
        return

    summary = category_summary()
    console.print("\n[bold]API keys & secrets[/bold]  [dim](~/.c4reqber/secrets.env + env)[/]\n")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Category")
    table.add_column("Configured", justify="right")
    table.add_column("Total", justify="right")
    for cat in categories():
        counts = summary.get(cat, {"configured": 0, "total": 0})
        label = CATEGORY_LABELS.get(cat, cat)
        table.add_row(label, str(counts["configured"]), str(counts["total"]))
    console.print(table)

    rows = _filter_rows(category)
    if category or len(rows) <= 30:
        console.print()
        for row in rows:
            icon = "[green]●[/]" if row["configured"] else "[dim]○[/]"
            masked = row["masked"] or "(not set)"
            req = " [yellow]required[/]" if row.get("required") else ""
            console.print(f"  {icon} {row['env_name']:<28} {masked}{req}")
    else:
        console.print(
            "\n[dim]Tip: blast config keys --category social  |  --json  |  --assign KEY=value[/]"
        )
    console.print(
        "\n[dim]Wizard: blast init  |  Docs: docs/API_KEYS.md  |  Social: docs/SOCIAL_PUBLISHING.md[/]"
    )


def _print_health() -> None:
    rows = list_key_status()
    console.print("\n[bold]Key health (essentials)[/bold]\n")
    ok = True
    openrouter = next((r for r in rows if r["env_name"] == "OPENROUTER_API_KEY"), None)
    if openrouter and not openrouter["configured"]:
        ok = False
        console.print("  [red]✗[/] OPENROUTER_API_KEY (recommended for all LLM routes)")
    elif openrouter and openrouter["configured"]:
        console.print("  [green]✓[/] OPENROUTER_API_KEY")
    for row in rows:
        if not row.get("required"):
            continue
        if row["env_name"] == "OPENROUTER_API_KEY":
            continue
        configured = bool(row["configured"])
        icon = "[green]✓[/]" if configured else "[red]✗[/]"
        if not configured:
            ok = False
        console.print(f"  {icon} {row['env_name']}")
    social_rows = [r for r in rows if r["category"] == "social" and r["configured"]]
    console.print(f"\n  Social channels configured: {len(social_rows)}")
    console.print("\n[dim]Full platform check: blast social health[/]")
    if not ok:
        raise SystemExit(1)
