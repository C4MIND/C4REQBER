"""
TURBO-CDI v8.4 CLI Interface
Command Line Interface for TURBO-CDI system operations.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from turbo_cdi.infrastructure.config import Settings
from turbo_cdi.infrastructure.config.container import Container
from turbo_cdi.presentation.cli.commands import (
    corpus_commands,
    discovery_commands,
    system_commands,
)


# Global console for rich output
console = Console()


def create_container() -> Container:
    """Create dependency injection container"""
    settings = Settings()
    return Container(settings)


@click.group()
@click.option(
    "--config", "config_path", type=click.Path(exists=True), help="Path to configuration file"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.pass_context
def cli(ctx: click.Context, config_path: Optional[str], verbose: bool, debug: bool):
    """
    TURBO-CDI v8.4 - Cognitive Discovery Intelligence Platform

    A Clean Architecture enterprise system for automated knowledge discovery,
    cognitive transformation, and intelligent reasoning.

    Built with domain-driven design and CQRS patterns.
    """
    # Set up context
    ctx.ensure_object(dict)

    # Initialize settings
    if config_path:
        # TODO: Load custom config
        pass

    settings = Settings()
    if debug:
        settings.debug_mode = True

    # Create container
    container = create_container()
    ctx.obj["container"] = container
    ctx.obj["settings"] = settings
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug

    # Welcome message
    if not verbose:
        welcome_msg = Text("TURBO-CDI v8.4", style="bold magenta")
        welcome_msg.append(" - Cognitive Discovery Intelligence", style="cyan")
        console.print(Panel(welcome_msg, title="🚀 System Ready"))
        console.print()


# Add command groups
cli.add_command(corpus_commands)
cli.add_command(discovery_commands)
cli.add_command(system_commands)


@cli.command()
@click.pass_context
def status(ctx: click.Context):
    """Show system status and health information"""
    container = ctx.obj["container"]
    verbose = ctx.obj.get("verbose", False)

    console.print("\n🔍 Checking system status...\n", style="blue")

    # Create status table
    table = Table(title="System Status")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    try:
        # Check database
        from turbo_cdi.infrastructure.health import HealthChecker

        health_checker = HealthChecker(container)

        # Run quick checks
        health_data = asyncio.run(health_checker.check_all())

        # Database status
        db_status = health_data["services"].get("database", {})
        status_emoji = "✅" if db_status.get("status") == "healthy" else "❌"
        table.add_row(
            "Database",
            f"{status_emoji} {db_status.get('status', 'unknown').upper()}",
            db_status.get("message", "N/A"),
        )

        # Cache status
        cache_status = health_data["services"].get("cache", {})
        status_emoji = "✅" if cache_status.get("status") == "healthy" else "❌"
        table.add_row(
            "Cache",
            f"{status_emoji} {cache_status.get('status', 'unknown').upper()}",
            cache_status.get("message", "N/A"),
        )

        # System metrics
        system_status = health_data["services"].get("system_metrics", {})
        status_emoji = "✅" if system_status.get("status") == "healthy" else "⚠️"
        cpu_info = f"CPU: {system_status.get('cpu_percent', 'N/A')}%"
        mem_info = f"Memory: {system_status.get('memory_percent', 'N/A'):.1f}%"
        table.add_row(
            "System Metrics",
            f"{status_emoji} {system_status.get('status', 'unknown').upper()}",
            f"{cpu_info}, {mem_info}",
        )

        console.print(table)

        # Overall health
        overall = health_data.get("overall_health", "unknown")
        if overall == "healthy":
            console.print("\n🎉 System is fully operational!", style="green bold")
        elif overall == "warning":
            console.print("\n⚠️ System operational with minor warnings", style="yellow bold")
        else:
            console.print("\n❌ System has issues requiring attention", style="red bold")

        if verbose:
            console.print(f"\nOverall Health: {overall.upper()}")
            console.print(f"Services Checked: {health_data.get('total_checks', 0)}")
            console.print(f"Check Time: {health_data.get('total_check_time', 0):.2f}s")

    except Exception as e:
        console.print(f"\n❌ Failed to check system status: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--port", "-p", default=8000, help="Port to run API server on")
@click.option("--host", default="127.0.0.1", help="Host to bind API server to")
@click.option("--workers", "-w", default=1, help="Number of worker processes")
@click.option("--reload", "-r", is_flag=True, help="Enable auto-reload for development")
@click.pass_context
def serve(ctx: click.Context, port: int, host: str, workers: int, reload: bool):
    """Start the FastAPI server"""
    settings = ctx.obj["settings"]

    console.print(f"\n🚀 Starting TURBO-CDI API server on {host}:{port}", style="blue")

    if reload:
        console.print("🔄 Auto-reload enabled for development", style="yellow")

    try:
        import uvicorn

        # Override settings for this command
        settings.api_host = host
        settings.api_port = port

        uvicorn.run(
            "turbo_cdi.presentation.api.__init__:app",
            host=host,
            port=port,
            reload=reload and settings.debug_mode,
            log_level="info" if not ctx.obj.get("debug", False) else "debug",
            workers=workers,
        )

    except ImportError:
        console.print(
            "❌ FastAPI/uvicorn not installed. Install with: pip install fastapi uvicorn[standard]",
            style="red",
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Failed to start server: {e}", style="red")
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    version_info = """
TURBO-CDI v8.4.0
Cognitive Discovery Intelligence Platform

Built with Clean Architecture & CQRS
Python 3.9+ required

Enterprise Features:
• Automated knowledge discovery
• Cognitive transformation QZRF operators
• Real-time anomaly detection
• Multi-modal reasoning
• Production API & health monitoring
"""

    console.print(version_info)


def main():
    """Main CLI entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n\n⚠️ Interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="red")
        if "--debug" in sys.argv or "-v" in sys.argv:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
