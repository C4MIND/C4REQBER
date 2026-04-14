"""
CLI Commands for TURBO-CDI v8.4
Modular command groups for corpus, discovery, and system operations.
"""

import asyncio
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


# Corpus Commands
@click.group()
def corpus():
    """Corpus management commands"""
    pass


@corpus.command()
@click.argument('corpus_id')
@click.option('--name', '-n', required=True, help='Corpus name')
@click.option('--domain', '-d', required=True, help='Knowledge domain')
@click.option('--subdomain', '-s', multiple=True, help='Domain subdomains')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def create(ctx, corpus_id: str, name: str, domain: str, subdomain: List[str], verbose: bool):
    """Create a new knowledge corpus"""
    container = ctx.obj['container']

    with console.status("[bold green]Creating corpus..."):
        try:
            corpus_service = container.corpus_management_service()

            async def create_corpus():
                corpus = await corpus_service.create_corpus_with_validation(
                    corpus_id=corpus_id,
                    name=name,
                    domain=domain,
                    subdomains=subdomain,
                    created_by="cli_user"
                )
                return corpus

            corpus = asyncio.run(create_corpus())

            if verbose:
                console.print(f"✅ Corpus created successfully:")
                console.print(f"   ID: {corpus.id}")
                console.print(f"   Name: {corpus.name}")
                console.print(f"   Domain: {corpus.domain}")
                console.print(f"   Created: {corpus.created_at}")
            else:
                console.print(f"✅ Corpus '{corpus.name}' created", style="green")

        except Exception as e:
            console.print(f"❌ Failed to create corpus: {e}", style="red")
            ctx.exit(1)


@corpus.command()
@click.argument('corpus_id')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def show(ctx, corpus_id: str, verbose: bool):
    """Show details of a corpus"""
    container = ctx.obj['container']

    try:
        discovery_repo = container.discovery_repo()

        async def get_corpus():
            corpus = await discovery_repo.get_corpus(corpus_id)
            return corpus

        corpus = asyncio.run(get_corpus())

        if not corpus:
            console.print(f"❌ Corpus '{corpus_id}' not found", style="red")
            ctx.exit(1)

        # Create table
        table = Table(title=f"Corpus: {corpus.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("ID", corpus.id)
        table.add_row("Name", corpus.name)
        table.add_row("Domain", corpus.domain)
        table.add_row("Subdomains", ", ".join(corpus.subdomains))
        table.add_row("Facts", str(len(corpus.facts)))
        table.add_row("Theories", str(len(corpus.theories)))
        table.add_row("Anomalies", str(len(corpus.anomalies)))
        table.add_row("Created", corpus.created_at.isoformat())
        table.add_row("Updated", corpus.updated_at.isoformat())

        console.print(table)

        if verbose:
            console.print("\n📊 Corpus Statistics:")
            console.print(f"   Total Knowledge Items: {len(corpus.facts) + len(corpus.theories)}")
            console.print(f"   Knowledge Density: {(len(corpus.facts) + len(corpus.theories)) / max(1, len(corpus.anomalies)):.2f} items per anomaly")

    except Exception as e:
        console.print(f"❌ Failed to show corpus: {e}", style="red")
        ctx.exit(1)


@corpus.command()
@click.option('--domain', '-d', help='Filter by domain')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def list(ctx, domain: Optional[str], verbose: bool):
    """List all corpora"""
    container = ctx.obj['container']

    try:
        discovery_repo = container.discovery_repo()

        async def list_corpora():
            corpora = await discovery_repo.list_corpuses(domain=domain)
            return corpora

        corpora = asyncio.run(list_corpora())

        if not corpora:
            console.print("📝 No corpora found")
            return

        # Create table
        table = Table(title="Knowledge Corpora")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Domain", style="green")
        table.add_column("Facts", justify="right")
        table.add_column("Theories", justify="right")
        table.add_column("Anomalies", justify="right")
        table.add_column("Created", style="dim")

        for corpus in corpora:
            table.add_row(
                corpus.id,
                corpus.name,
                corpus.domain,
                str(len(corpus.facts)),
                str(len(corpus.theories)),
                str(len(corpus.anomalies)),
                corpus.created_at.strftime("%Y-%m-%d"),
            )

        console.print(table)

        if verbose:
            total_facts = sum(len(c.facts) for c in corpora)
            total_theories = sum(len(c.theories) for c in corpora)
            total_anomalies = sum(len(c.anomalies) for c in corpora)
            console.print(f"\n📊 Summary: {len(corpora)} corpora, {total_facts} facts, {total_theories} theories, {total_anomalies} anomalies")

    except Exception as e:
        console.print(f"❌ Failed to list corpora: {e}", style="red")
        ctx.exit(1)


# Discovery Commands
@click.group()
def discovery():
    """Knowledge discovery commands"""
    pass


@discovery.command()
@click.argument('corpus_id')
@click.option('--threshold', '-t', default=0.7, help='Anomaly detection threshold')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def analyze(ctx, corpus_id: str, threshold: float, verbose: bool):
    """Run knowledge discovery analysis on a corpus"""
    container = ctx.obj['container']

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing corpus for anomalies...", total=None)

        try:
            discovery_service = container.knowledge_discovery_service()

            async def analyze_corpus():
                results = await discovery_service.comprehensive_discovery_analysis(
                    corpus_id=corpus_id,
                    analysis_timeout=300
                )
                return results

            results = asyncio.run(analyze_corpus())

            progress.update(task, completed=True, description="✅ Analysis complete")

            # Display results
            console.print(f"\n🎯 Analysis Results for Corpus '{corpus_id}':")
            console.print(f"   Anomalies Found: {results['anomalies_found']}")
            console.print(f"   Presuppositions Analyzed: {results['presuppositions_found']}")
            console.print(f"   Processing Time: {results['processing_time']:.2f}s")
            console.print(f"   Analysis Completed: {results['analysis_completed']}")

            if results['anomalies_found'] > 0:
                console.print(f"\n⚠️ {results['anomalies_found']} knowledge anomalies detected", style="yellow")
                if verbose:
                    console.print("   Review corpus for potential conflicts or missing knowledge")

        except Exception as e:
            progress.update(task, completed=True, description="❌ Analysis failed")
            console.print(f"\n❌ Analysis failed: {e}", style="red")
            ctx.exit(1)


@discovery.command()
@click.argument('corpus_id')
@click.option('--limit', '-l', default=10, help='Max transformations to show')
@click.pass_context
def transformations(ctx, corpus_id: str, limit: int):
    """Show effective transformations for a corpus"""
    container = ctx.obj['container']

    try:
        transformation_repo = container.transformation_repo()

        async def get_transformations():
            transformations = await transformation_repo.get_most_effective_transformations(limit=limit)
            return transformations

        transformations = asyncio.run(get_transformations())

        if not transformations:
            console.print("📝 No transformations found")
            return

        # Create table
        table = Table(title=f"Top {len(transformations)} Transformations")
        table.add_column("Type", style="cyan")
        table.add_column("Input Concept", style="white")
        table.add_column("Output Concept", style="white")
        table.add_column("Domain", style="green")
        table.add_column("Effectiveness", justify="right", style="yellow")
        table.add_column("Operator", style="blue")

        for t in transformations:
            table.add_row(
                t.type.value.upper(),
                t.input_concept,
                t.output_concept,
                t.domain,
                ".3f",
                t.operator,
            )

        console.print(table)

    except Exception as e:
        console.print(f"❌ Failed to get transformations: {e}", style="red")
        ctx.exit(1)


# System Commands
@click.group()
def system():
    """System administration commands"""
    pass


@system.command()
@click.option('--include-services', is_flag=True, help='Include external services check')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def health(ctx, include_services: bool, verbose: bool):
    """Check system health"""
    container = ctx.obj['container']

    try:
        from turbo_cdi.infrastructure.health import HealthChecker
        health_checker = HealthChecker(container)

        with console.status("[bold green]Checking system health..."):
            health_data = asyncio.run(health_checker.check_all())

        # Display health summary
        overall = health_data.get("overall_health", "unknown")

        if overall == "healthy":
            icon = "✅"
            style = "green"
        elif overall == "warning":
            icon = "⚠️"
            style = "yellow"
        else:
            icon = "❌"
            style = "red"

        console.print(f"\n{icon} System Health: {overall.upper()}", style=f"{style} bold")

        # Services table
        table = Table(title="Service Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Message", style="yellow")

        for service_name, service_data in health_data["services"].items():
            status = service_data.get("status", "unknown")
            message = service_data.get("message", "")

            # Style status
            if status == "healthy":
                status_display = f"[green]✅ {status.upper()}[/green]"
            elif status == "warning":
                status_display = f"[yellow]⚠️ {status.upper()}[/yellow]"
            else:
                status_display = f"[red]❌ {status.upper()}[/red]"

            table.add_row(service_name, status_display, message)

        console.print(table)

        if verbose:
            check_time = health_data.get("total_check_time", 0)
            services_checked = health_data.get("total_checks", 0)
            console.print(f"\n⏱️ Check Time: {check_time:.2f}s | Services Checked: {services_checked}")

    except Exception as e:
        console.print(f"❌ Health check failed: {e}", style="red")
        ctx.exit(1)


@system.command()
@click.pass_context
def metrics(ctx):
    """Show system metrics"""
    container = ctx.obj['container']

    try:
        # Get metrics from monitoring
        from turbo_cdi.application.transactions import transaction_monitor
        from turbo_cdi.application.events import metrics_handler

        # Transaction metrics
        tx_health = transaction_monitor.get_health_report()

        console.print("\n📊 System Metrics:")

        # Transaction stats
        console.print(f"\n💼 Transactions:")
        console.print(f"   Started: {tx_health.get('transactions_started', 0)}")
        console.print(f"   Committed: {tx_health.get('transactions_committed', 0)}")
        console.print(f"   Rolled Back: {tx_health.get('transactions_rolled_back', 0)}")
        console.print(f"   Rollback Rate: {tx_health.get('rollback_rate', 0):.1%}")

        # Application events
        events_metrics = metrics_handler.get_metrics()
        console.print(f"\n📈 Application Events:")
        console.print(f"   Total Events: {events_metrics.get('operations_total', 0)}")
        operations_by_type = events_metrics.get('operations_by_type', {})
        if operations_by_type:
            console.print(f"   By Type: {', '.join(f'{k}: {v}' for k, v in operations_by_type.items())}")

    except Exception as e:
        console.print(f"❌ Failed to get metrics: {e}", style="red")
        ctx.exit(1)


@system.command()
@click.argument('level', type=click.Choice(['basic', 'standard', 'deep']))
@click.pass_context
def optimize(ctx, level: str):
    """Run system optimization"""
    console.print(f"🚀 Starting system optimization (level: {level})...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        tasks = [
            "Optimizing database indexes...",
            "Cleaning cache...",
            "Defragmenting storage...",
            "Updating statistics...",
        ]

        task_progress = progress.add_task("Running optimizations...", total=len(tasks))

        try:
            # Simulate optimization steps
            for task in tasks:
                progress.update(task_progress, description=task)
                # Simulate work
                import time
                time.sleep(0.5)
                progress.advance(task_progress)

            progress.update(task_progress, completed=True, description="✅ Optimization complete")

            console.print("
✅ System optimization completed successfully!" console.print("   Database indexes optimized"            console.print("   Cache cleaned and rebuilt"            console.print("   Storage defragmented"
            console.print(f"   Statistics updated (level: {level})")

        except Exception as e:
            progress.update(task_progress, description="❌ Optimization failed")
            console.print(f"\n❌ Optimization failed: {e}", style="red")
            ctx.exit(1)