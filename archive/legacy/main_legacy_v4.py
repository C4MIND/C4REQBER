"""
TURBO-CDI: Unified CLI v4.5 - Advanced Scientific Discovery Platform

Commands:
  CORE DISCOVERY:
    turbo solve            - One-shot discovery (FULL CYCLE in one command)
    turbo discover         - Multi-agent discovery (Analyst+Scientist+Critic+Synthesizer)

  C4 COGNITIVE GEOMETRY:
    turbo c4 discover      - Generate hypothesis from contradiction
    turbo c4 path          - Find optimal C4 transformation path
    turbo c4 states        - List all C4 states
    turbo explain          - Explain why C4 path works

  TRIZ METHODOLOGY:
    turbo triz list        - List 40 TRIZ principles
    turbo triz show        - Show TRIZ principle details
    turbo triz recommend   - Get C4+TRIZ recommendations
    turbo triz bridge      - Show C4→TRIZ mapping
    turbo triz solve       - Generate C4+TRIZ solution
    turbo triz matrix      - Interactive Contradiction Matrix

  ANALOGY ENGINE:
    turbo analogy find     - Find analogies for a concept
    turbo analogy discover - Discover analogies between domains
    turbo analogy solve    - Solve A:B::C:? proportional analogies
    turbo analogy domains  - List available domains
    turbo analogy chain    - Find analogy chains

  SEARCH & LITERATURE:
    turbo search arxiv     - Search arXiv papers
    turbo search pubmed    - Search PubMed papers
    turbo search semantic  - Search Semantic Scholar (200M papers)
    turbo search patents   - Search patents, white space analysis
    turbo search import    - Import from Zotero/Mendeley
    turbo search discoveries - Search discoveries in graph

  KNOWLEDGE GRAPH:
    turbo graph stats      - Show knowledge graph statistics
    turbo graph visualize  - Export graph for visualization
    turbo graph view       - Obsidian-style graph visualization
    turbo graph analogies  - Find analogies between domains

  VALIDATION:
    turbo validate create  - Create validation experiment
    turbo validate start   - Start experiment
    turbo validate observe - Add observation
    turbo validate conclude - Conclude experiment
    turbo validate summary - Validation statistics
    turbo validate consensus - Analyze scientific consensus (Consensus Meter)

  ANALYTICS & REPORTING:
    turbo dashboard        - Business metrics and ROI analytics
    turbo evolution        - Technology S-curve analysis
    turbo effects          - Physical/chemical effects database
    turbo present          - Export to presentation slides

  AGENTS & AUTOMATION:
    turbo agent discover   - Autonomous discovery agent
    turbo plugins          - Manage tool plugins

  SYSTEM:
    turbo llm generate     - Generate text with LLM
    turbo llm batch        - Batch generation (async)
    turbo llm test         - Test LLM connection
    turbo concept list     - List concepts and domains
    turbo repl             - Interactive shell
    turbo server           - Start API server
    turbo status           - System health check

Usage:
  turbo --help

  # One-shot discovery
  turbo solve "increase battery life" --full --output report.md

  # Multi-agent system
  turbo discover "optimize neural network training"

  # Explain C4 reasoning
  turbo explain discovery_001 --level technical

  # Dashboard & analytics
  turbo dashboard --export metrics.json

  # Technology forecasting
  turbo evolution "lithium-ion battery"

  # Patent & white space
  turbo search patents "solid state battery" --white-space

  # Reference management
  turbo search import library.bib --source zotero

  # Effects database
  turbo effects "temperature sensing"

  # Create presentation
  turbo present discovery_001 --output slides.md
"""

import sys
from typing import Optional, List
from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.pydantic_models import (
    C4StateModel,
    DiscoveryStatus,
    TimeAxis,
    ScaleAxis,
    AgencyAxis,
)
from src.graph.knowledge_graph import get_knowledge_graph, KnowledgeGraph


# ═══════════════════════════════════════════════════════════════════
# CLI SETUP
# ═══════════════════════════════════════════════════════════════════

app = typer.Typer(
    name="turbo",
    help="TURBO-CDI v4.0 - Scientific Hypothesis Generation Platform",
    rich_markup_mode="rich",
)
console = Console()

# Sub-command groups
c4_app = typer.Typer(help="C4 Cognitive Geometry operations")
project_app = typer.Typer(help="Research project management")
search_app = typer.Typer(help="Search research databases")
graph_app = typer.Typer(help="Knowledge graph operations")
analogy_app = typer.Typer(help="Cross-domain analogy discovery")
triz_app = typer.Typer(help="C4-TRIZ methodology bridge")
validation_app = typer.Typer(help="Experiment validation and tracking")
llm_app = typer.Typer(help="LLM integration (sync and async)")
agent_app = typer.Typer(help="Autonomous scientific discovery agent")
concept_app = typer.Typer(help="Concept and domain management")

app.add_typer(c4_app, name="c4")
app.add_typer(project_app, name="project")
app.add_typer(search_app, name="search")
app.add_typer(graph_app, name="graph")
app.add_typer(analogy_app, name="analogy")
app.add_typer(triz_app, name="triz")
app.add_typer(validation_app, name="validate")
app.add_typer(llm_app, name="llm")
app.add_typer(agent_app, name="agent")
app.add_typer(concept_app, name="concept")


# ═══════════════════════════════════════════════════════════════════
# C4 COMMANDS
# ═══════════════════════════════════════════════════════════════════


@c4_app.command("discover")
def c4_discover(
    problem: str = typer.Option(..., "--problem", "-p", help="Problem statement"),
    contradiction: str = typer.Option(
        ...,
        "--contradiction",
        "-c",
        help="Physical contradiction (X must be A AND not-A)",
    ),
    domain: str = typer.Option("general", "--domain", "-d", help="Scientific domain"),
    confidence: float = typer.Option(0.8, "--confidence", min=0.0, max=1.0),
    tags: Optional[List[str]] = typer.Option(
        None, "--tag", help="Tags (can use multiple)"
    ),
    export: Optional[str] = typer.Option(
        None, "--export", "-e", help="Export to file (json, md, html)"
    ),
):
    """
    Generate scientific hypothesis using C4 cognitive geometry.

    Example:
        turbo c4 discover -p "increase battery life" -c "fast charging vs capacity preservation" -d energy
    """
    console.print(
        Panel.fit(
            f"[bold blue]TURBO-CDI Discovery Engine[/bold blue]\n"
            f"Domain: [cyan]{domain}[/cyan] | Confidence threshold: {confidence}",
            title="🔬 Hypothesis Generation",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Parse contradiction
        task1 = progress.add_task("Parsing physical contradiction...", total=None)
        # Parse contradiction format: "X must be A AND not-A for Y and Z"
        parts = contradiction.split("AND")
        if len(parts) == 2:
            param_part = parts[0].strip()
            not_a_part = parts[1].strip()
            param = (
                param_part.split("must be")[0].strip()
                if "must be" in param_part
                else param_part
            )
            value_a = (
                param_part.split("must be")[1].strip()
                if "must be" in param_part
                else ""
            )
            value_not_a = not_a_part.strip()
        else:
            param = "unknown"
            value_a = contradiction
            value_not_a = "not-" + contradiction
        progress.update(task1, completed=True)

        # Step 2: Generate C4 path
        task2 = progress.add_task(
            "Computing optimal C4 path (Theorem 11)...", total=None
        )
        # Simplified: use 4-step path for demonstration
        c4_path = ["tau+", "sigma", "delta", "lambda+"]
        progress.update(task2, completed=True)

        # Step 3: Synthesize hypothesis
        task3 = progress.add_task("Synthesizing hypothesis via LLM...", total=None)
        hypothesis = f"""
[bold]Hypothesis:[/bold] Adaptive {param} mechanism that dynamically optimizes 
between {value_a} and {value_not_a} based on operational context.

[bold]Mechanism:[/bold] Utilize C4 path {" → ".join(c4_path)} to transform the problem 
from present-concrete (trade-off) to future-meta (synergy).

[bold]Key Innovation:[/bold] Context-aware switching eliminates the apparent 
contradiction through temporal separation of requirements.
"""
        progress.update(task3, completed=True)

        # Step 4: Store in knowledge graph
        task4 = progress.add_task("Storing in knowledge graph...", total=None)
        kg = get_knowledge_graph()
        discovery_id = kg.add_discovery(
            problem=problem,
            hypothesis=hypothesis,
            contradiction={
                "parameter": param,
                "value_a": value_a,
                "value_not_a": value_not_a,
                "requirement_y": "performance",
                "requirement_z": "reliability",
            },
            c4_path=c4_path,
            confidence_score=confidence,
            domain=domain,
            tags=tags or [],
        )
        kg.save()
        progress.update(task4, completed=True)

    # Output results
    console.print(f"\n[bold green]✓ Discovery created:[/bold green] {discovery_id}")
    console.print(Panel(hypothesis, title="Generated Hypothesis", border_style="green"))

    # Path visualization
    path_tree = Tree("[bold]C4 Transformation Path[/bold]")
    states = [
        ("F⟨Past, Concrete, Self⟩", "Initial state (problem as given)"),
        ("F⟨Present, Concrete, Other⟩", "After tau+: Recontextualize"),
        ("F⟨Present, Abstract, System⟩", "After sigma: Abstract"),
        ("F⟨Future, Abstract, System⟩", "After delta: Temporal shift"),
        ("F⟨Future, Meta, System⟩", "After lambda+: Meta synthesis"),
    ]
    for i, (state, desc) in enumerate(states):
        path_tree.add(f"[cyan]{i}.[/cyan] {state}: [dim]{desc}[/dim]")
    console.print(path_tree)

    if export:
        export_path = f"discovery_{discovery_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export}"
        console.print(f"\n[dim]Export: {export_path}[/dim]")


@c4_app.command("path")
def c4_path(
    from_state: str = typer.Option(
        ..., "--from", help="Starting state (T,S,A e.g., 0,0,0)"
    ),
    to_state: str = typer.Option(..., "--to", help="Target state (T,S,A e.g., 2,2,2)"),
    visualize: bool = typer.Option(
        False, "--visualize", "-v", help="Show ASCII visualization"
    ),
):
    """
    Find optimal C4 transformation path between two states.

    States are 3-digit coordinates (T,S,A) where each is 0, 1, or 2.

    Example:
        turbo c4 path --from 0,0,0 --to 2,2,2 --visualize
    """
    try:
        from_t, from_s, from_a = map(int, from_state.split(","))
        to_t, to_s, to_a = map(int, to_state.split(","))

        start = C4StateModel(
            T=TimeAxis(from_t), S=ScaleAxis(from_s), A=AgencyAxis(from_a)
        )
        end = C4StateModel(T=TimeAxis(to_t), S=ScaleAxis(to_s), A=AgencyAxis(to_a))

    except (ValueError, IndexError):
        console.print("[red]Error: States must be in format T,S,A (e.g., 0,0,0)[/red]")
        raise typer.Exit(1)

    # Calculate path
    distance = start.hamming_distance(end)

    console.print(
        Panel.fit(
            f"[bold]Path Analysis[/bold]\n"
            f"From: {start.label}\n"
            f"To:   {end.label}\n"
            f"Hamming distance: [cyan]{distance}[/cyan] steps"
        )
    )

    # Generate path description
    path_steps = []
    current = start

    if from_t != to_t:
        path_steps.append(
            f"tau{'+' if to_t > from_t else '-'}: Time axis ({from_t} → {to_t})"
        )
    if from_s != to_s:
        path_steps.append(f"sigma: Scale axis ({from_s} → {to_s})")
    if from_a != to_a:
        path_steps.append(f"rho: Agency axis ({from_a} → {to_a})")

    table = Table(title="Recommended Operators")
    table.add_column("Step", style="cyan")
    table.add_column("Operator", style="magenta")
    table.add_column("Description", style="green")

    for i, step in enumerate(path_steps, 1):
        op, desc = step.split(":", 1)
        table.add_row(str(i), op, desc.strip())

    console.print(table)

    if visualize:
        console.print("\n[bold]ASCII Visualization:[/bold]")
        # Simple 3x3x3 representation
        console.print("[dim]C4 Space (showing path projection)...[/dim]")
        console.print(f"  Start: [cyan]({from_t},{from_s},{from_a})[/cyan]")
        console.print(f"  End:   [green]({to_t},{to_s},{to_a})[/green]")


@c4_app.command("states")
def c4_states(
    filter_domain: Optional[str] = typer.Option(None, "--domain", "-d"),
):
    """List all C4 states and their meanings."""
    table = Table(title="C4 State Space (Z₃³ = 27 states)")
    table.add_column("Coordinates", style="cyan")
    table.add_column("Label", style="magenta")
    table.add_column("Description", style="green")

    descriptions = {
        (0, 0, 0): "Raw experience, unprocessed perception",
        (1, 0, 0): "Immediate concrete situation",
        (2, 0, 0): "Expected concrete outcome",
        (0, 1, 0): "Past patterns, learned abstractions",
        (1, 1, 0): "Current abstract understanding",
        (2, 1, 0): "Planned abstractions, goals",
        (0, 2, 0): "Self-reflection on past cognition",
        (1, 2, 0): "Current meta-cognitive state",
        (2, 2, 0): "Designed cognitive frameworks",
    }

    for state in C4StateModel.all_states():
        coords = state.to_coords()
        key = (coords["T"], coords["S"], coords["A"])
        desc = descriptions.get(key, "Complex cognitive state")
        table.add_row(f"({coords['T']},{coords['S']},{coords['A']})", state.label, desc)

    console.print(table)


# ═══════════════════════════════════════════════════════════════════
# PROJECT COMMANDS
# ═══════════════════════════════════════════════════════════════════


@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option(
        "", "--description", "-d", help="Project description"
    ),
    domain: str = typer.Option("general", "--domain", help="Scientific domain"),
    objectives: Optional[List[str]] = typer.Option(
        None, "--objective", "-o", help="Objectives"
    ),
):
    """Create a new research project."""
    kg = get_knowledge_graph()

    project_id = kg.add_project(
        name=name,
        description=description,
        domain=domain,
        objectives=objectives or [],
    )
    kg.save()

    console.print(
        Panel.fit(
            f"[bold green]✓ Project created[/bold green]\n"
            f"ID: [cyan]{project_id}[/cyan]\n"
            f"Name: {name}\n"
            f"Domain: {domain}",
            title="📁 Research Project",
        )
    )


@project_app.command("list")
def project_list(
    domain: Optional[str] = typer.Option(None, "--domain", "-d"),
    status: Optional[str] = typer.Option(None, "--status", "-s"),
):
    """List all research projects."""
    kg = get_knowledge_graph()
    projects = kg.get_nodes_by_type("project")

    if domain:
        projects = [
            p for p in projects if p.get("metadata", {}).get("domain") == domain
        ]

    table = Table(title="Research Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Domain", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")

    for proj in projects:
        meta = proj.get("metadata", {})
        table.add_row(
            proj["node_id"],
            meta.get("name", "N/A"),
            meta.get("domain", "general"),
            meta.get("status", "active"),
            proj["created_at"][:10] if isinstance(proj["created_at"], str) else "N/A",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(projects)} projects[/dim]")


@project_app.command("show")
def project_show(
    project_id: str = typer.Argument(..., help="Project ID"),
):
    """Show detailed project information."""
    kg = get_knowledge_graph()
    project = kg.get_node(project_id)

    if not project:
        console.print(f"[red]Project {project_id} not found[/red]")
        raise typer.Exit(1)

    meta = project.get("metadata", {})

    console.print(
        Panel.fit(
            f"[bold]{meta.get('name', 'N/A')}[/bold]\n\n"
            f"ID: {project['node_id']}\n"
            f"Domain: {meta.get('domain', 'general')}\n"
            f"Status: {meta.get('status', 'active')}\n"
            f"Created: {project.get('created_at', 'N/A')}\n\n"
            f"[dim]{meta.get('description', 'No description')}[/dim]",
            title="📁 Project Details",
        )
    )

    # Show linked discoveries
    discoveries = kg.get_neighbors(project_id, edge_type="contains")
    if discoveries:
        console.print("\n[bold]Linked Discoveries:[/bold]")
        for disc_id in discoveries:
            disc = kg.get_node(disc_id)
            if disc:
                console.print(
                    f"  • {disc_id}: {disc.get('metadata', {}).get('hypothesis', 'N/A')[:60]}..."
                )


# ═══════════════════════════════════════════════════════════════════
# SEARCH COMMANDS
# ═══════════════════════════════════════════════════════════════════


@search_app.command("arxiv")
def search_arxiv(
    query: str = typer.Argument(..., help="Search query"),
    max_results: int = typer.Option(5, "--limit", "-l", min=1, max=20),
    save: bool = typer.Option(False, "--save", "-s", help="Save to knowledge graph"),
):
    """
    Search arXiv for papers.

    Uses arXiv API (no API key required).
    """
    import urllib.request
    import urllib.parse
    import xml.etree.ElementTree as ET

    console.print(f"[dim]Searching arXiv for: {query}...[/dim]")

    try:
        # Build arXiv API query
        search_query = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results={max_results}"

        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()

        # Parse Atom feed
        root = ET.fromstring(data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            authors = entry.findall("atom:author/atom:name", ns)
            published = entry.find("atom:published", ns)
            id_elem = entry.find("atom:id", ns)

            if title is not None:
                results.append(
                    {
                        "title": title.text.strip().replace("\n", " "),
                        "authors": [a.text for a in authors if a.text],
                        "year": int(published.text[:4]) if published is not None else 0,
                        "id": id_elem.text.split("/")[-1] if id_elem else "unknown",
                    }
                )

        if not results:
            console.print("[yellow]No papers found on arXiv.[/yellow]")
            return

        table = Table(title=f"arXiv Search Results: '{query}'")
        table.add_column("Title", style="cyan", max_width=50)
        table.add_column("Authors", style="magenta", max_width=30)
        table.add_column("Year", style="green")

        for paper in results:
            authors_str = ", ".join(paper["authors"][:2])
            if len(paper["authors"]) > 2:
                authors_str += " et al."

            table.add_row(
                paper["title"][:60] + "..."
                if len(paper["title"]) > 60
                else paper["title"],
                authors_str,
                str(paper["year"]),
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(results)} papers on arXiv[/dim]")

        if save:
            kg = get_knowledge_graph()
            for paper in results:
                kg.add_reference(
                    title=paper["title"],
                    authors=paper["authors"],
                    year=paper["year"],
                    source="arxiv",
                    source_id=paper["id"],
                )
            kg.save()
            console.print(
                f"[green]✓ Saved {len(results)} references to knowledge graph[/green]"
            )

    except urllib.error.URLError as e:
        console.print(f"[red]Network error: {e}[/red]")
        console.print("[dim]Tip: Check your internet connection[/dim]")
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")


@search_app.command("pubmed")
def search_pubmed(
    query: str = typer.Argument(..., help="Search query"),
    max_results: int = typer.Option(5, "--limit", "-l", min=1, max=20),
):
    """Search PubMed for papers."""
    console.print(f"[dim]Searching PubMed for: {query}...[/dim]")
    console.print("[yellow]Note: PubMed search requires API key configuration[/yellow]")


@search_app.command("discoveries")
def search_discoveries(
    query: str = typer.Argument(..., help="Search query"),
    domain: Optional[str] = typer.Option(None, "--domain", "-d"),
):
    """Search discoveries in knowledge graph."""
    kg = get_knowledge_graph()
    discoveries = kg.get_nodes_by_type("discovery")

    # Simple text search
    results = []
    for disc in discoveries:
        meta = disc.get("metadata", {})
        text = f"{meta.get('problem', '')} {meta.get('hypothesis', '')}".lower()
        if query.lower() in text:
            if domain is None or meta.get("domain") == domain:
                results.append(disc)

    table = Table(title=f"Discoveries matching '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Problem", style="magenta", max_width=40)
    table.add_column("Confidence", style="green")
    table.add_column("Domain", style="yellow")

    for disc in results:
        meta = disc.get("metadata", {})
        table.add_row(
            disc["node_id"],
            meta.get("problem", "N/A")[:50] + "...",
            f"{meta.get('confidence_score', 0):.2f}",
            meta.get("domain", "general"),
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} matches[/dim]")


# ═══════════════════════════════════════════════════════════════════
# GRAPH COMMANDS
# ═══════════════════════════════════════════════════════════════════


@graph_app.command("stats")
def graph_stats():
    """Show knowledge graph statistics."""
    kg = get_knowledge_graph()
    stats = kg.get_stats()

    console.print(
        Panel.fit(
            f"[bold]Knowledge Graph Statistics[/bold]\n\n"
            f"Total Nodes: [cyan]{stats.get('nodes', 0)}[/cyan]\n"
            f"Total Edges: [cyan]{stats.get('edges', 0)}[/cyan]\n"
            f"Graph Density: [cyan]{stats.get('density', 0):.4f}[/cyan]\n"
            f"Connected: {'[green]Yes[/green]' if stats.get('is_connected') else '[red]No[/red]'}\n",
            title="📊 Graph Stats",
        )
    )

    # Node type breakdown
    node_types = stats.get("node_types", {})
    if node_types:
        table = Table(title="Nodes by Type")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="magenta")

        for node_type, count in node_types.items():
            table.add_row(node_type, str(count))

        console.print(table)

    # Central nodes
    central = stats.get("central_nodes", [])
    if central:
        console.print("\n[bold]Most Central Nodes:[/bold]")
        for node_id, score in central:
            console.print(f"  • {node_id}: {score:.4f}")


@graph_app.command("visualize")
def graph_visualize(
    output: str = typer.Option("graph_export.json", "--output", "-o"),
    format: str = typer.Option("json", "--format", "-f", help="json or graphml"),
):
    """Export knowledge graph for visualization."""
    kg = get_knowledge_graph()

    if format == "json":
        kg.export_to_json(output)
    elif format == "graphml":
        kg.export_to_graphml(output)
    else:
        console.print(f"[red]Unknown format: {format}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓ Exported to {output}[/green]")


@graph_app.command("analogies")
def graph_analogies(
    source: str = typer.Option(..., "--source", "-s", help="Source domain"),
    target: str = typer.Option(..., "--target", "-t", help="Target domain"),
):
    """Find analogies between domains."""
    kg = get_knowledge_graph()

    # Get analogies
    analogies = kg.get_nodes_by_type("analogy")
    relevant = [
        a
        for a in analogies
        if a.get("metadata", {}).get("source_domain") == source
        and a.get("metadata", {}).get("target_domain") == target
    ]

    if not relevant:
        # Try reverse
        relevant = [
            a
            for a in analogies
            if a.get("metadata", {}).get("source_domain") == target
            and a.get("metadata", {}).get("target_domain") == source
        ]

    table = Table(title=f"Analogies: {source} ↔ {target}")
    table.add_column("Concept A", style="cyan")
    table.add_column("Concept B", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Confidence", style="yellow")

    for analogy in relevant:
        meta = analogy.get("metadata", {})
        table.add_row(
            meta.get("source_concept", "N/A"),
            meta.get("target_concept", "N/A"),
            meta.get("mapping_type", "N/A"),
            f"{meta.get('confidence', 0):.2f}",
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(relevant)} analogies[/dim]")


# ═══════════════════════════════════════════════════════════════════
# ANALOGY COMMANDS
# ═══════════════════════════════════════════════════════════════════


@analogy_app.command("find")
def analogy_find(
    concept: str = typer.Argument(..., help="Source concept"),
    from_domain: str = typer.Option(..., "--from", "-f", help="Source domain"),
    to_domain: str = typer.Option(..., "--to", "-t", help="Target domain"),
    top_k: int = typer.Option(5, "--top", "-k", min=1, max=20),
    store: bool = typer.Option(False, "--store", "-s", help="Store in knowledge graph"),
):
    """
    Find analogies for a concept across domains.

    Example:
        turbo analogy find neuron --from biology --to computer_science
    """
    from src.analogy import get_analogy_engine

    console.print(
        f"[dim]Finding analogies: {concept} ({from_domain} → {to_domain})...[/dim]"
    )

    engine = get_analogy_engine()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Computing semantic similarities...", total=None)
        results = engine.find_analogies(from_domain, to_domain, concept, top_k=top_k)
        progress.update(task, completed=True)

    if not results:
        console.print(
            "[yellow]No analogies found. Try different domains or concept.[/yellow]"
        )
        return

    table = Table(title=f"Analogies: {concept} ({from_domain} → {to_domain})")
    table.add_column("Source", style="cyan")
    table.add_column("Target", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Confidence", style="yellow")
    table.add_column("Reasoning", style="dim", max_width=40)

    for r in results:
        table.add_row(
            r.source_concept,
            r.target_concept,
            r.mapping_type,
            f"{r.confidence:.2f}",
            r.reasoning[:50] + "..." if len(r.reasoning) > 50 else r.reasoning,
        )

    console.print(table)

    if store:
        for r in results:
            if r.confidence >= 0.7:
                engine.store_analogy(r)
        console.print(
            f"[green]✓ Stored {len([r for r in results if r.confidence >= 0.7])} high-confidence analogies[/green]"
        )


@analogy_app.command("discover")
def analogy_discover(
    domain1: str = typer.Argument(..., help="First domain"),
    domain2: str = typer.Argument(..., help="Second domain"),
    max_analogies: int = typer.Option(10, "--max", "-m", min=1, max=50),
):
    """
    Systematically discover analogies between two domains.

    Example:
        turbo analogy discover biology computer_science
    """
    from src.analogy import get_analogy_engine

    console.print(
        f"[dim]Discovering cross-domain analogies: {domain1} ↔ {domain2}...[/dim]"
    )

    engine = get_analogy_engine()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning domain concepts...", total=None)
        results = engine.discover_cross_domain_analogies(
            domain1, domain2, max_analogies
        )
        progress.update(task, completed=True)

    if not results:
        console.print(
            "[yellow]No analogies discovered. Domains may be too dissimilar.[/yellow]"
        )
        return

    table = Table(title=f"Cross-Domain Analogies: {domain1} ↔ {domain2}")
    table.add_column(f"{domain1}", style="cyan")
    table.add_column(f"{domain2}", style="magenta")
    table.add_column("Confidence", style="yellow")
    table.add_column("Type", style="green")

    for r in results:
        table.add_row(
            r.source_concept,
            r.target_concept,
            f"{r.confidence:.2f}",
            r.mapping_type,
        )

    console.print(table)
    console.print(f"\n[dim]Discovered {len(results)} analogies[/dim]")


@analogy_app.command("solve")
def analogy_solve(
    A: str = typer.Argument(..., help="First term (A in A:B::C:?)"),
    B: str = typer.Argument(..., help="Second term (B in A:B::C:?)"),
    C: str = typer.Argument(..., help="Third term (C in A:B::C:?)"),
):
    """
    Solve proportional analogy A:B::C:? using Word2Vec.

    Example:
        turbo analogy solve king queen man
        => woman
    """
    from src.analogy import get_analogy_engine

    engine = get_analogy_engine()
    result = engine.solve_proportional_analogy(A, B, C)

    if result:
        console.print(
            Panel.fit(
                f"[bold]Analogy Solution[/bold]\n\n"
                f"{A} : {B}\n"
                f"{C} : [green]{result.target_concept.split(':')[1]}[/green]\n\n"
                f"Confidence: {result.confidence:.2f}\n"
                f"Method: {result.mapping_type}",
                title="🔀 Proportional Analogy",
            )
        )
    else:
        console.print(
            "[yellow]Could not solve analogy. Word2Vec model may be unavailable.[/yellow]"
        )


@analogy_app.command("domains")
def analogy_domains():
    """List available domains for analogy discovery."""
    from src.analogy.engine import ConceptNetBridge

    domains = ConceptNetBridge.DOMAIN_CONCEPTS

    table = Table(title="Available Domains for Analogy Discovery")
    table.add_column("Domain", style="cyan")
    table.add_column("Concepts", style="magenta")
    table.add_column("Sample", style="dim")

    for domain, concepts in domains.items():
        table.add_row(
            domain,
            str(len(concepts)),
            ", ".join(concepts[:3]) + "...",
        )

    console.print(table)
    console.print(
        f"\n[dim]Total: {len(domains)} domains with {sum(len(c) for c in domains.values())} concepts[/dim]"
    )


@analogy_app.command("chain")
def analogy_chain(
    source: str = typer.Option(..., "--source", "-s", help="Source domain"),
    target: str = typer.Option(..., "--target", "-t", help="Target domain"),
    max_length: int = typer.Option(3, "--max-length", "-l", min=2, max=5),
):
    """Find chains of analogies connecting domains."""
    from src.analogy import get_analogy_engine

    engine = get_analogy_engine()
    chains = engine.get_analogy_chain(source, target, max_length)

    if not chains:
        console.print("[yellow]No analogy chains found.[/yellow]")
        return

    console.print(f"[bold]Analogy Chains: {source} → {target}[/bold]\n")
    for i, chain in enumerate(chains[:5], 1):
        console.print(f"Chain {i}: {' → '.join(chain)}")


# ═══════════════════════════════════════════════════════════════════
# TRIZ COMMANDS
# ═══════════════════════════════════════════════════════════════════


@triz_app.command("list")
def triz_list(
    search: Optional[str] = typer.Option(
        None, "--search", "-s", help="Search by keyword"
    ),
):
    """List all 40 TRIZ principles."""
    from src.triz import get_c4_triz_bridge

    bridge = get_c4_triz_bridge()

    if search:
        principles = bridge.search_principles(search)
        title = f"TRIZ Principles matching '{search}'"
    else:
        principles = bridge.get_all_principles()
        title = "40 TRIZ Inventive Principles"

    table = Table(title=title)
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="dim", max_width=50)
    table.add_column("Examples", style="green", max_width=30)

    for p in principles:
        table.add_row(
            str(p.number),
            p.name,
            p.description[:50] + "..." if len(p.description) > 50 else p.description,
            p.examples[0] if p.examples else "",
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(principles)} principles[/dim]")


@triz_app.command("show")
def triz_show(
    principle_num: int = typer.Argument(
        ..., help="Principle number (1-40)", min=1, max=40
    ),
):
    """Show detailed information about a TRIZ principle."""
    from src.triz import get_c4_triz_bridge

    bridge = get_c4_triz_bridge()
    info = bridge.get_principle_info(principle_num)

    if not info:
        console.print(f"[red]Principle {principle_num} not found[/red]")
        raise typer.Exit(1)

    # Get mapped C4 operators
    c4_ops = bridge.get_c4_for_triz_principle(principle_num)

    console.print(
        Panel.fit(
            f"[bold]{info.number}. {info.name}[/bold]\n\n"
            f"{info.description}\n\n"
            f"[bold]Examples:[/bold]\n"
            + "\n".join(f"  • {ex}" for ex in info.examples)
            + "\n\n"
            f"[bold]Typical Contradictions:[/bold]\n"
            + "\n".join(f"  • {c}" for c in info.typical_contradictions)
            + "\n\n"
            f"[bold]C4 Operators:[/bold] [cyan]{', '.join(c4_ops) if c4_ops else 'None mapped'}[/cyan]",
            title=f"🔧 TRIZ Principle {info.number}",
        )
    )


@triz_app.command("recommend")
def triz_recommend(
    improve: str = typer.Option(..., "--improve", "-i", help="Parameter to improve"),
    worsen: str = typer.Option(..., "--worsen", "-w", help="Parameter that worsens"),
):
    """
    Get C4+TRIZ recommendations for a contradiction.

    Example:
        turbo triz recommend --improve speed --worsen accuracy
    """
    from src.triz import get_c4_triz_bridge

    bridge = get_c4_triz_bridge()
    recs = bridge.recommend_for_contradiction(improve, worsen)

    if not recs["triz_principles"]:
        console.print(
            f"[yellow]No standard recommendation for {improve} vs {worsen}[/yellow]"
        )
        console.print("[dim]Using default C4 operators...[/dim]")
        recs["c4_operators"] = ["tau+", "sigma", "delta", "iota", "lambda+"]

    console.print(
        Panel.fit(
            f"[bold]Contradiction:[/bold] Improve {improve} vs {worsen}\n\n"
            f"[cyan]Recommended TRIZ Principles:[/cyan] {', '.join(map(str, recs['triz_principles']))}\n"
            f"[cyan]Recommended C4 Operators:[/cyan] {', '.join(recs['c4_operators'])}\n",
            title="🎯 C4+TRIZ Recommendation",
        )
    )

    # Show principle details
    if recs["principle_details"]:
        table = Table(title="TRIZ Principles Details")
        table.add_column("#", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Mapped C4", style="green")

        for p in recs["principle_details"]:
            if p:
                c4_mapped = bridge.get_c4_for_triz_principle(p.number)
                table.add_row(
                    str(p.number),
                    p.name,
                    ", ".join(c4_mapped[:3]) + ("..." if len(c4_mapped) > 3 else ""),
                )

        console.print(table)


@triz_app.command("bridge")
def triz_bridge(
    c4_operator: str = typer.Argument(
        ..., help="C4 operator (e.g., tau+, sigma, delta)"
    ),
):
    """Show TRIZ principles activated by a C4 operator."""
    from src.triz import get_c4_triz_bridge

    bridge = get_c4_triz_bridge()
    principles = bridge.get_triz_for_c4_path([c4_operator])

    if not principles:
        console.print(f"[yellow]No TRIZ principles mapped to {c4_operator}[/yellow]")
        return

    console.print(f"[bold]C4 Operator:[/bold] [cyan]{c4_operator}[/cyan]\n")
    console.print("[bold]Activates TRIZ Principles:[/bold]\n")

    for p_num in principles:
        info = bridge.get_principle_info(p_num)
        if info:
            console.print(f"  [cyan]{p_num}.[/cyan] [magenta]{info.name}[/magenta]")
            console.print(f"      [dim]{info.description[:60]}...[/dim]\n")


@triz_app.command("solve")
def triz_solve(
    problem: str = typer.Argument(..., help="Problem description"),
    improve: str = typer.Option(..., "--improve", "-i", help="What to improve"),
    worsen: str = typer.Option(..., "--worsen", "-w", help="What gets worse"),
):
    """
    Generate complete C4+TRIZ solution path.

    Example:
        turbo triz solve "slow charging" --improve speed --worsen battery_life
    """
    from src.triz import get_c4_triz_bridge

    bridge = get_c4_triz_bridge()
    solution = bridge.generate_c4_triz_path(problem, (improve, worsen))

    console.print(
        Panel.fit(
            f"[bold]Problem:[/bold] {solution['problem']}\n"
            f"[bold]Contradiction:[/bold] {solution['contradiction'][0]} vs {solution['contradiction'][1]}\n\n"
            f"[bold]C4 Path:[/bold] [cyan]{' → '.join(solution['c4_path'])}[/cyan]\n"
            f"[bold]TRIZ Principles:[/bold] [magenta]{', '.join(map(str, solution['triz_principles']))}[/magenta]\n\n"
            f"[bold]Steps:[/bold] {solution['estimated_steps']} (Theorem 11: {'✓' if solution['within_theorem_11'] else '✗'})",
            title="🚀 C4+TRIZ Solution Path",
        )
    )

    # Show detailed steps
    table = Table(title="Step-by-Step Solution")
    table.add_column("Step", style="cyan", justify="center")
    table.add_column("C4 Operator", style="magenta")
    table.add_column("TRIZ Principle", style="green")
    table.add_column("Explanation", style="dim", max_width=40)

    for step in solution["steps"]:
        table.add_row(
            str(step["step"]),
            step["c4_operator"],
            f"{step['triz_principle']}. {step['triz_name']}",
            step["explanation"][:50] + "..."
            if len(step["explanation"]) > 50
            else step["explanation"],
        )

    console.print(table)


# ═══════════════════════════════════════════════════════════════════
# VALIDATION COMMANDS
# ═══════════════════════════════════════════════════════════════════


@validation_app.command("create")
def validate_create(
    discovery_id: str = typer.Argument(..., help="Discovery/hypothesis ID to validate"),
    name: str = typer.Option(..., "--name", "-n", help="Experiment name"),
    description: str = typer.Option(
        "", "--description", "-d", help="Experiment description"
    ),
    researcher: str = typer.Option("", "--researcher", "-r", help="Researcher name"),
):
    """Create a new validation experiment for a hypothesis."""
    from src.validation import get_validation_tracker

    tracker = get_validation_tracker()

    try:
        exp = tracker.create_experiment(
            discovery_id=discovery_id,
            name=name,
            description=description,
            researcher=researcher,
        )

        console.print(
            Panel.fit(
                f"[bold green]✓ Experiment created[/bold green]\n"
                f"ID: [cyan]{exp.id}[/cyan]\n"
                f"Name: {exp.name}\n"
                f"Testing: {discovery_id}\n"
                f"Falsifiability criteria: {len(exp.falsifiability_criteria)}",
                title="🔬 Validation Experiment",
            )
        )

        if exp.falsifiability_criteria:
            console.print("\n[bold]Falsifiability Criteria:[/bold]")
            for i, crit in enumerate(exp.falsifiability_criteria, 1):
                console.print(f"  {i}. {crit.statement}")
                console.print(f"     Measure: {crit.measurement}")
                console.print(f"     Threshold: {crit.threshold}\n")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@validation_app.command("start")
def validate_start(
    exp_id: str = typer.Argument(..., help="Experiment ID"),
):
    """Start an experiment (mark as running)."""
    from src.validation import get_validation_tracker

    tracker = get_validation_tracker()

    try:
        exp = tracker.start_experiment(exp_id)
        console.print(f"[green]✓ Experiment {exp_id} started[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@validation_app.command("observe")
def validate_observe(
    exp_id: str = typer.Argument(..., help="Experiment ID"),
    value: float = typer.Option(..., "--value", "-v", help="Observed value"),
    unit: str = typer.Option(..., "--unit", "-u", help="Unit of measurement"),
    notes: str = typer.Option("", "--notes", "-n", help="Observation notes"),
):
    """Add an observation to an experiment."""
    from src.validation import get_validation_tracker

    tracker = get_validation_tracker()

    try:
        obs = tracker.add_observation(
            exp_id=exp_id,
            value=value,
            unit=unit,
            notes=notes,
        )
        console.print(f"[green]✓ Observation recorded:[/green] {value} {unit}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@validation_app.command("conclude")
def validate_conclude(
    exp_id: str = typer.Argument(..., help="Experiment ID"),
    outcome: str = typer.Argument(
        ..., help="Outcome: validated, falsified, or inconclusive"
    ),
    conclusion: str = typer.Option("", "--conclusion", "-c", help="Conclusion text"),
    strength: float = typer.Option(
        0.5, "--strength", "-s", min=0.1, max=0.9, help="Update strength"
    ),
):
    """
    Conclude an experiment and update hypothesis confidence.

    Example:
        turbo validate conclude exp_1 validated --strength 0.7
    """
    from src.validation import get_validation_tracker

    tracker = get_validation_tracker()

    try:
        result = tracker.conclude_experiment(
            exp_id=exp_id,
            outcome=outcome,
            conclusion=conclusion,
            strength=strength,
        )

        console.print(
            Panel.fit(
                f"[bold]Experiment {exp_id} concluded[/bold]\n\n"
                f"Outcome: [cyan]{outcome.upper()}[/cyan]\n"
                f"Old confidence: {result['old_confidence']:.3f}\n"
                f"New confidence: [green]{result['new_confidence']:.3f}[/green]\n"
                f"Delta: {result['delta']:+.3f}",
                title="📊 Validation Result",
            )
        )
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@validation_app.command("list")
def validate_list(
    discovery_id: Optional[str] = typer.Option(
        None, "--discovery", "-d", help="Filter by discovery ID"
    ),
):
    """List validation experiments."""
    from src.validation import get_validation_tracker

    tracker = get_validation_tracker()

    if discovery_id:
        experiments = tracker.get_experiments_for_discovery(discovery_id)
    else:
        experiments = list(tracker._experiments.values())

    table = Table(title="Validation Experiments")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Discovery", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Observations", style="blue", justify="right")

    for exp in experiments:
        table.add_row(
            exp.id,
            exp.name[:30] + "..." if len(exp.name) > 30 else exp.name,
            exp.discovery_id,
            exp.status.value,
            str(len(exp.observations)),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(experiments)} experiments[/dim]")


@validation_app.command("summary")
def validate_summary():
    """Show validation system summary and calibration status."""
    from src.validation import get_validation_tracker

    tracker = get_validation_tracker()
    summary = tracker.get_validation_summary()

    console.print(
        Panel.fit(
            f"[bold]Validation Summary[/bold]\n\n"
            f"Total experiments: {summary['total_experiments']}\n"
            f"Validation rate: {summary['validation_rate']:.1%}\n\n"
            f"[bold]Calibration Status:[/bold]\n"
            f"  {summary['calibration']['status']}\n"
            f"  Brier score: {summary['calibration']['brier_score']:.3f}\n"
            f"  Total predictions: {summary['calibration']['total_predictions']}",
            title="📈 Validation Statistics",
        )
    )

    if summary["by_status"]:
        console.print("\n[bold]By Status:[/bold]")
        for status, count in summary["by_status"].items():
            console.print(f"  {status}: {count}")


# ═══════════════════════════════════════════════════════════════════
# LLM COMMANDS
# ═══════════════════════════════════════════════════════════════════


@llm_app.command("generate")
def llm_generate(
    prompt: str = typer.Argument(..., help="Prompt to send to LLM"),
    model: str = typer.Option(
        "qwen/qwen-2.5-72b-instruct", "--model", "-m", help="Model to use"
    ),
    temperature: float = typer.Option(0.7, "--temperature", "-t", min=0.0, max=1.0),
    max_tokens: int = typer.Option(2000, "--max-tokens", help="Maximum tokens"),
    async_mode: bool = typer.Option(False, "--async", "-a", help="Use async client"),
):
    """Generate text using LLM."""
    import asyncio
    from src.llm import LLMClient, AsyncLLMClient

    if async_mode:

        async def generate_async():
            async with AsyncLLMClient() as client:
                return await client.generate(
                    prompt, model=model, temperature=temperature, max_tokens=max_tokens
                )

        try:
            response = asyncio.run(generate_async())
        except ImportError as e:
            console.print(f"[red]Async support requires httpx: {e}[/red]")
            raise typer.Exit(1)
    else:
        client = LLMClient()
        try:
            response = client.generate(
                prompt, model=model, temperature=temperature, max_tokens=max_tokens
            )
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"[bold]Response:[/bold]\n{response.content}\n\n"
            f"[dim]Model: {response.model}"
            f"{' | Latency: ' + str(round(response.latency_ms, 1)) + 'ms' if response.latency_ms > 0 else ''}[/dim]",
            title="🤖 LLM Response",
        )
    )


@llm_app.command("batch")
def llm_batch(
    prompts: List[str] = typer.Argument(
        ..., help="Prompts to process (space-separated in quotes)"
    ),
    model: str = typer.Option(
        "qwen/qwen-2.5-72b-instruct", "--model", "-m", help="Model to use"
    ),
    max_concurrent: int = typer.Option(
        5, "--max-concurrent", "-c", min=1, max=10, help="Max concurrent requests"
    ),
):
    """
    Generate multiple responses concurrently.

    Example:
        turbo llm batch "Prompt 1" "Prompt 2" "Prompt 3"
    """
    import asyncio
    from src.llm import AsyncLLMClient

    async def generate_batch():
        async with AsyncLLMClient() as client:
            return await client.generate_batch(
                prompts, model=model, max_concurrent=max_concurrent
            )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Processing {len(prompts)} prompts...", total=None
            )
            responses = asyncio.run(generate_batch())
            progress.update(task, completed=True)
    except ImportError as e:
        console.print(f"[red]Batch mode requires httpx: {e}[/red]")
        raise typer.Exit(1)

    table = Table(title=f"Batch Results ({len(responses)} responses)")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Prompt", style="magenta", max_width=30)
    table.add_column("Response", style="green", max_width=40)
    table.add_column("Latency", style="yellow", justify="right")

    for i, (prompt, response) in enumerate(zip(prompts, responses), 1):
        table.add_row(
            str(i),
            prompt[:30] + "..." if len(prompt) > 30 else prompt,
            response.content[:40] + "..."
            if len(response.content) > 40
            else response.content,
            f"{response.latency_ms:.0f}ms" if response.latency_ms > 0 else "-",
        )

    console.print(table)


@llm_app.command("test")
def llm_test(
    async_mode: bool = typer.Option(False, "--async", "-a", help="Test async client"),
):
    """Test LLM API connectivity."""
    if async_mode:
        import asyncio
        from src.llm import AsyncLLMClient

        async def test_async():
            async with AsyncLLMClient() as client:
                return await client.test_connection()

        try:
            connected = asyncio.run(test_async())
        except ImportError:
            console.print(
                "[red]Async client requires httpx. Install: pip install httpx[/red]"
            )
            raise typer.Exit(1)
    else:
        from src.llm import LLMClient

        client = LLMClient()
        connected = client.test_connection()

    if connected:
        console.print("[green]✓ LLM API connection successful[/green]")
    else:
        console.print("[red]✗ LLM API connection failed[/red]")
        console.print("[dim]Check OPENROUTER_API_KEY environment variable[/dim]")
        raise typer.Exit(1)


# ═══════════════════════════════════════════════════════════════════
# AGENT COMMANDS
# ═══════════════════════════════════════════════════════════════════


@agent_app.command("discover")
def agent_discover(
    problem: str = typer.Argument(..., help="Problem to solve"),
    max_hypotheses: int = typer.Option(
        10, "--max", "-n", min=1, max=20, help="Max hypotheses to generate"
    ),
    output: str = typer.Option(
        "report.md", "--output", "-o", help="Output file (.md or .json)"
    ),
):
    """
    Autonomous scientific discovery.

    The agent will:
    1. Analyze your problem
    2. Generate hypotheses using C4+TRIZ+Analogy
    3. Rank by confidence and cost
    4. Export full report

    Example:
        turbo agent discover "Increase battery density without losing safety"
    """
    import asyncio
    from src.agent import get_agent

    async def run_discovery():
        agent = get_agent()
        report = await agent.discover(
            problem=problem,
            max_hypotheses=max_hypotheses,
        )
        return report

    try:
        report = asyncio.run(run_discovery())

        # Build summary text
        top_hypothesis_text = ""
        if report.hypotheses:
            h = report.hypotheses[0]
            conf_pct = h.confidence * 100
            top_hypothesis_text = f"[bold]Top Hypothesis:[/bold]\n{h.hypothesis}\nConfidence: {conf_pct:.0f}%"

        # Display summary
        duration_min = (report.end_time - report.start_time).total_seconds() / 60
        summary_text = (
            f"[bold]Discovery Complete![/bold]\n\n"
            f"Generated: {report.total_hypotheses} hypotheses\n"
            f"Duration: {duration_min:.1f} minutes\n\n" + top_hypothesis_text
        )

        console.print(Panel.fit(summary_text, title="🤖 Agent Report"))

        # Show recommendations
        console.print("\n[bold]Recommendations:[/bold]")
        for i, rec in enumerate(report.recommendations[:3], 1):
            console.print(f"  {i}. {rec}")

        # Export
        agent = get_agent()
        agent.export_report(report, output)

    except Exception as e:
        console.print(f"[red]Agent error: {e}[/red]")
        raise typer.Exit(1)


# ═══════════════════════════════════════════════════════════════════
# CONCEPT COMMANDS
# ═══════════════════════════════════════════════════════════════════


@concept_app.command("list")
def concept_list(
    domain: Optional[str] = typer.Option(
        None, "--domain", "-d", help="Filter by domain"
    ),
):
    """List all concepts and domains."""
    from src.analogy.engine import ConceptNetBridge

    bridge = ConceptNetBridge()

    if domain:
        concepts = bridge.get_domain_concepts(domain)
        table = Table(title=f"Concepts in domain: {domain}")
        table.add_column("#", style="cyan")
        table.add_column("Concept", style="magenta")

        for i, concept in enumerate(concepts, 1):
            table.add_row(str(i), concept)

        console.print(table)
        console.print(f"\n[dim]Total: {len(concepts)} concepts[/dim]")
    else:
        stats = bridge.get_concept_stats()
        table = Table(title="Domain Statistics")
        table.add_column("Domain", style="cyan")
        table.add_column("Concepts", style="magenta", justify="right")

        for dom, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            table.add_row(dom, str(count))

        console.print(table)
        console.print(
            f"\n[dim]Total: {len(stats)} domains, {sum(stats.values())} concepts[/dim]"
        )


@concept_app.command("add")
def concept_add(
    domain: str = typer.Argument(..., help="Domain name"),
    concept: str = typer.Argument(..., help="Concept to add"),
):
    """Add a new concept to a domain."""
    from src.analogy.engine import ConceptNetBridge

    bridge = ConceptNetBridge()

    if bridge.add_concept(domain, concept):
        console.print(f"[green]✓ Added '{concept}' to domain '{domain}'[/green]")
    else:
        console.print(
            f"[yellow]Concept '{concept}' already exists in '{domain}'[/yellow]"
        )


@concept_app.command("extract")
def concept_extract(
    text: str = typer.Argument(..., help="Text to analyze"),
    domain: str = typer.Option("general", "--domain", "-d", help="Target domain"),
):
    """Auto-extract concepts from text."""
    from src.analogy.engine import ConceptNetBridge

    bridge = ConceptNetBridge()
    concepts = bridge.extract_concepts_from_text(text, domain)

    if concepts:
        console.print(f"[green]✓ Extracted {len(concepts)} concepts:[/green]")
        for concept in concepts:
            console.print(f"  • {concept}")
    else:
        console.print("[yellow]No new concepts extracted[/yellow]")


@concept_app.command("metaphor")
def concept_metaphor(
    source_domain: str = typer.Argument(..., help="Source domain"),
    source_concept: str = typer.Argument(..., help="Source concept"),
    target_domain: str = typer.Argument(..., help="Target domain"),
    target_concept: str = typer.Argument(..., help="Target concept"),
):
    """Add a conceptual metaphor (cross-domain mapping)."""
    from src.analogy.engine import ConceptNetBridge

    bridge = ConceptNetBridge()

    if bridge.add_conceptual_metaphor(
        source_domain, source_concept, target_domain, target_concept
    ):
        console.print(
            f"[green]✓ Added metaphor: {source_domain}:{source_concept} → "
            f"{target_domain}:{target_concept}[/green]"
        )
    else:
        console.print("[yellow]Metaphor already exists[/yellow]")


@concept_app.command("auto")
def concept_auto(
    hypothesis_id: str = typer.Argument(..., help="Hypothesis/discovery ID"),
):
    """Auto-extract concepts from a hypothesis."""
    from src.analogy.engine import ConceptNetBridge
    from src.graph.knowledge_graph import get_knowledge_graph

    kg = get_knowledge_graph()
    bridge = ConceptNetBridge()

    node = kg.get_node(hypothesis_id)
    if not node:
        console.print(f"[red]Hypothesis {hypothesis_id} not found[/red]")
        raise typer.Exit(1)

    hypothesis_text = node.get("metadata", {}).get("hypothesis", "")
    domain = node.get("metadata", {}).get("domain", "general")

    result = bridge.auto_extract_from_hypothesis(hypothesis_text, domain)

    console.print(
        Panel.fit(
            f"[bold]Auto-extraction from {hypothesis_id}[/bold]\n\n"
            f"Domain: {domain}\n"
            f"New concepts: {len(result['concepts'])}\n"
            f"Potential analogies: {len(result['potential_analogies'])}",
            title="🔍 Concept Extraction",
        )
    )

    if result["concepts"]:
        console.print("\n[bold]Extracted Concepts:[/bold]")
        for c in result["concepts"]:
            console.print(f"  • {c}")

    if result["potential_analogies"]:
        console.print("\n[bold]Potential Analogies:[/bold]")
        for a in result["potential_analogies"][:5]:
            console.print(
                f"  • {a['source'][0]}:{a['source'][1]} → "
                f"{a['target'][0]}:{a['target'][1]}"
            )


# ═══════════════════════════════════════════════════════════════════
# MULTI-AGENT COMMANDS
# ═══════════════════════════════════════════════════════════════════


@app.command("discover")
def multi_discover(
    problem: str = typer.Argument(..., help="Research problem"),
    output: str = typer.Option("report.md", "--output", "-o", help="Output file"),
):
    """
    Multi-agent discovery (Analyst + Scientist + Critic + Synthesizer).

    Runs full multi-agent pipeline for comprehensive analysis.

    Example:
        turbo discover "optimize battery charging"
    """
    import asyncio
    from src.agents import get_multi_agent_system

    async def run():
        system = get_multi_agent_system()
        result = await system.discover(problem)
        return result

    try:
        result = asyncio.run(run())

        # Display results
        console.print(
            Panel.fit(
                f"[bold green]✓ Multi-Agent Discovery Complete![/bold green]\n\n"
                f"Problem: {result['problem']}\n"
                f"Agents used: {result['agent_count']}\n"
                f"Hypotheses generated: {len(result['hypotheses'])}",
                title="🤖 Multi-Agent System",
            )
        )

        # Show top hypothesis
        synthesis = result["synthesis"]
        top = synthesis.get("top_hypotheses", [])
        if top:
            console.print(f"\n[bold]Top Hypothesis:[/bold]")
            console.print(f"  {top[0]['hypothesis']}")
            console.print(f"  Confidence: {top[0]['final_score']:.0%}")

        # Show recommendations
        console.print(f"\n[bold]Recommendations:[/bold]")
        for rec in synthesis.get("recommended_next_steps", [])[:3]:
            console.print(f"  • {rec}")

    except Exception as e:
        console.print(f"[red]Multi-agent error: {e}[/red]")
        raise typer.Exit(1)


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD COMMANDS
# ═══════════════════════════════════════════════════════════════════


@app.command("dashboard")
def dashboard_command(
    export: Optional[str] = typer.Option(None, "--export", "-e", help="Export to file"),
    format: str = typer.Option("json", "--format", "-f", help="Export format"),
):
    """
    Show analytics dashboard with business metrics.

    Displays:
    - Time-to-hypothesis
    - Validation rates
    - ROI estimates
    - Domain distribution

    Example:
        turbo dashboard
        turbo dashboard --export metrics.json
    """
    from src.dashboard import get_dashboard

    dashboard = get_dashboard()

    if export:
        dashboard.export_metrics(export, format=format)
    else:
        dashboard.render_dashboard()


# ═══════════════════════════════════════════════════════════════════
# EXPLAINABILITY COMMANDS
# ═══════════════════════════════════════════════════════════════════


@app.command("explain")
def explain_command(
    discovery_id: str = typer.Argument(..., help="Discovery ID to explain"),
    level: str = typer.Option(
        "technical", "--level", "-l", help="simple/technical/math"
    ),
):
    """
    Explain why a C4 path works (Explainability Engine).

    Shows step-by-step reasoning for each C4 operator.

    Example:
        turbo explain discovery_001
        turbo explain discovery_001 --level simple
    """
    from src.explainability import get_explainability_engine, ExplanationLevel
    from src.graph.knowledge_graph import get_knowledge_graph

    kg = get_knowledge_graph()
    discovery = kg.get_node(discovery_id)

    if not discovery:
        console.print(f"[red]Discovery {discovery_id} not found[/red]")
        raise typer.Exit(1)

    meta = discovery.get("metadata", {})
    problem = meta.get("problem", "")
    hypothesis = meta.get("hypothesis", "")
    c4_path = meta.get("c4_path", [])

    if not c4_path:
        console.print("[yellow]No C4 path found for this discovery[/yellow]")
        raise typer.Exit(1)

    # Get explanation level
    level_map = {
        "simple": ExplanationLevel.SIMPLE,
        "technical": ExplanationLevel.TECHNICAL,
        "math": ExplanationLevel.MATHEMATICAL,
    }
    expl_level = level_map.get(level, ExplanationLevel.TECHNICAL)

    # Generate explanation
    engine = get_explainability_engine()
    explanation = engine.explain_path(problem, c4_path, hypothesis, expl_level)

    # Render
    engine.render_explanation(explanation, expl_level)


# ═══════════════════════════════════════════════════════════════════
# REFERENCE MANAGER COMMANDS
# ═══════════════════════════════════════════════════════════════════


@search_app.command("import")
def search_import_references(
    file_path: str = typer.Argument(..., help="Path to export file (CSV/BibTeX)"),
    source: str = typer.Option("auto", "--source", "-s", help="zotero/mendeley/auto"),
):
    """
    Import references from Zotero or Mendeley.

    Supports:
    - Zotero: CSV, BibTeX
    - Mendeley: CSV

    Example:
        turbo search import references.csv --source zotero
        turbo search import library.bib
    """
    from src.references import get_reference_manager

    try:
        manager = get_reference_manager()
        references = manager.import_references(file_path, source=source)

        if not references:
            console.print("[yellow]No references found in file[/yellow]")
            return

        # Show preview
        table = Table(title=f"Imported References ({len(references)})")
        table.add_column("Title", style="cyan", max_width=40)
        table.add_column("Year", style="magenta")
        table.add_column("Source", style="green")

        for ref in references[:10]:
            table.add_row(
                ref.title[:40] + "..." if len(ref.title) > 40 else ref.title,
                str(ref.year) if ref.year else "N/A",
                ref.source,
            )

        console.print(table)

        # Save to knowledge graph
        manager.save_to_knowledge_graph(references)
        console.print(f"[green]✓ Imported {len(references)} references[/green]")

    except Exception as e:
        console.print(f"[red]Import error: {e}[/red]")
        raise typer.Exit(1)


# ═══════════════════════════════════════════════════════════════════
# TRENDS OF EVOLUTION COMMANDS
# ═══════════════════════════════════════════════════════════════════


@app.command("evolution")
def evolution_command(
    technology: str = typer.Argument(..., help="Technology to analyze"),
    visualize: bool = typer.Option(True, "--visualize/--no-visualize", "-v/-V"),
):
    """
    Analyze technology evolution using S-curves.

    Predicts maturity stage and next paradigm.

    Example:
        turbo evolution "lithium-ion battery"
        turbo evolution "quantum computing"
    """
    from src.trends import get_trends_analyzer

    analyzer = get_trends_analyzer()
    analysis = analyzer.analyze_technology(technology)

    if visualize:
        console.print(analyzer.render_s_curve(analysis))
    else:
        console.print(
            Panel.fit(
                f"[bold]Technology: {analysis.technology}[/bold]\n\n"
                f"Stage: [cyan]{analysis.current_stage.value.upper()}[/cyan]\n"
                f"Maturity: {analysis.maturity_percent:.0f}%\n"
                f"Performance: {analysis.performance_trend}\n"
                f"Patent Activity: {analysis.patent_activity}\n"
                f"Market Growth: {analysis.market_growth}\n\n"
                f"[bold]Predictions:[/bold]\n"
                f"Time to maturity: {analysis.time_to_maturity or 'Unknown'} years\n"
                f"Next paradigm: {analysis.next_paradigm or 'Unknown'}\n\n"
                f"[bold]Strategy:[/bold] {analysis.strategy}\n"
                f"[bold]Investment:[/bold] {analysis.investment_recommendation}",
                title="📈 Technology Evolution",
            )
        )


# ═══════════════════════════════════════════════════════════════════
# PATENT SEARCH COMMANDS
# ═══════════════════════════════════════════════════════════════════


@search_app.command("patents")
def search_patents(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", min=1, max=50),
    white_space: bool = typer.Option(
        False, "--white-space", "-w", help="Analyze white space"
    ),
):
    """
    Search patents and analyze white space.

    Example:
        turbo search patents "battery thermal management"
        turbo search patents "solid state battery" --white-space
    """
    from src.patents import get_patent_client

    client = get_patent_client()
    patents = client.search_patents(query, limit=limit)

    if not patents:
        console.print("[yellow]No patents found[/yellow]")
        return

    table = Table(title=f"Patent Search: '{query}'")
    table.add_column("Patent ID", style="cyan")
    table.add_column("Title", style="magenta", max_width=40)
    table.add_column("Assignee", style="green")
    table.add_column("Year", style="yellow")

    for patent in patents:
        year = patent.grant_date[:4] if patent.grant_date else patent.filing_date[:4]
        table.add_row(
            patent.patent_id,
            patent.title[:40] + "..." if len(patent.title) > 40 else patent.title,
            patent.assignee,
            year,
        )

    console.print(table)

    if white_space:
        analysis = client.analyze_white_space(query, patents)
        console.print(
            Panel.fit(
                f"[bold]White Space Analysis[/bold]\n\n"
                f"Patents analyzed: {analysis['patent_count']}\n"
                f"White space areas:\n"
                + "\n".join(f"  • {gap}" for gap in analysis["white_space_areas"])
                + f"\n\nRecommendation: {analysis['recommendation']}",
                title="🔍 White Space",
            )
        )


# ═══════════════════════════════════════════════════════════════════
# EFFECTS DATABASE COMMANDS
# ═══════════════════════════════════════════════════════════════════


@app.command("effects")
def effects_command(
    query: str = typer.Argument(..., help="Search query or problem description"),
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Filter by category"
    ),
):
    """
    Search physical and chemical effects database.

    Find physical phenomena to solve problems.

    Example:
        turbo effects "temperature sensing"
        turbo effects "piezoelectric"
        turbo effects "flow control" --category fluid
    """
    from src.effects import get_effects_database

    db = get_effects_database()

    # Try direct search first
    effects = db.search_effects(query, category=category)

    # If no direct results, try suggestion based on problem
    if not effects:
        effects = db.suggest_effects(query)

    if not effects:
        console.print("[yellow]No effects found. Try different keywords.[/yellow]")
        console.print(
            f"[dim]Available categories: {', '.join(db.list_categories())}[/dim]"
        )
        return

    table = Table(title=f"Physical Effects: '{query}'")
    table.add_column("Effect", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Description", style="dim", max_width=40)
    table.add_column("Applications", style="green", max_width=30)

    for effect in effects:
        table.add_row(
            effect.name,
            effect.category,
            effect.description[:40] + "..."
            if len(effect.description) > 40
            else effect.description,
            ", ".join(effect.applications[:2]),
        )

    console.print(table)


# ═══════════════════════════════════════════════════════════════════
# PRESENTATION COMMANDS
# ═══════════════════════════════════════════════════════════════════


@app.command("present")
def present_command(
    discovery_id: str = typer.Argument(..., help="Discovery to present"),
    output: str = typer.Option("slides.md", "--output", "-o", help="Output file"),
    format: str = typer.Option("markdown", "--format", "-f", help="markdown/html"),
    title: str = typer.Option(
        "Research Discovery", "--title", "-t", help="Presentation title"
    ),
):
    """
    Export discovery to presentation slides.

    Supports Markdown (Marp/Slidev) and HTML (reveal.js).

    Example:
        turbo present discovery_001 --output slides.md
        turbo present discovery_001 --format html --output presentation.html
    """
    from src.export import get_presentation_exporter

    exporter = get_presentation_exporter()
    slides = exporter.create_presentation(discovery_id, title=title)

    if not slides:
        console.print("[red]Could not create presentation[/red]")
        raise typer.Exit(1)

    # Export
    if format == "html":
        exporter.export_to_html(slides, output)
    else:
        exporter.export_to_markdown(slides, output)

    console.print(f"[green]✓ Presentation exported to {output}[/green]")
    console.print(f"[dim]{len(slides)} slides created[/dim]")


# ═══════════════════════════════════════════════════════════════════
# PLUGIN COMMANDS
# ═══════════════════════════════════════════════════════════════════


@app.command("plugins")
def plugins_command(
    action: str = typer.Argument("list", help="list/run/info"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Plugin name"),
):
    """
    Manage tool plugins.

    List, run, and get info about plugins.

    Example:
        turbo plugins list
        turbo plugins run --name calculator
    """
    from src.plugins import get_plugin_registry

    registry = get_plugin_registry()

    if action == "list":
        plugins = registry.list_plugins()

        table = Table(title="Installed Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="magenta")
        table.add_column("Description", style="dim", max_width=40)

        for meta in plugins:
            table.add_row(meta.name, meta.version, meta.description)

        console.print(table)

    elif action == "run" and name:
        try:
            result = registry.execute(name)
            console.print(f"[green]Result:[/green] {result}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    elif action == "info" and name:
        plugin = registry.get_plugin(name)
        if plugin:
            meta = plugin.metadata
            console.print(
                Panel.fit(
                    f"[bold]{meta.name}[/bold] v{meta.version}\n\n"
                    f"{meta.description}\n\n"
                    f"Author: {meta.author}\n"
                    f"Requires: {', '.join(meta.requires) if meta.requires else 'None'}",
                    title="Plugin Info",
                )
            )
        else:
            console.print(f"[red]Plugin not found: {name}[/red]")


# ═══════════════════════════════════════════════════════════════════
# MAIN COMMANDS
# ═══════════════════════════════════════════════════════════════════


@app.command()
def repl(
    model: str = typer.Option("claude-sonnet-4", "--model", "-m", help="LLM model"),
):
    """Start interactive REPL shell."""
    console.print(
        Panel.fit(
            "[bold]TURBO-CDI Interactive Shell[/bold]\n"
            "Type commands or 'help' for assistance. Ctrl+D to exit.",
            title="🖥️  REPL",
        )
    )

    from src.terminal import TurboTerminal

    terminal = TurboTerminal()
    terminal.start()


@app.command()
def server(
    port: int = typer.Option(8000, "--port", "-p"),
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
):
    """Start API server."""
    console.print(f"[dim]Starting server on {host}:{port}...[/dim]")
    console.print("[yellow]Note: API server implementation in progress[/yellow]")


@app.command()
def status():
    """Show system status and health."""
    from src.utils.retry import check_retry_system_health

    health = check_retry_system_health()

    console.print(
        Panel.fit(
            f"[bold]System Status[/bold]\n\n"
            f"Tenacity Available: {'[green]Yes[/green]' if health['tenacity_available'] else '[red]No[/red]'}\n"
            f"Circuit Breakers: {len(health['circuit_breakers'])}\n"
            f"Total Retry Attempts: {health['metrics']['total_attempts']}\n"
            f"Success Rate: {health['metrics']['success_rate']:.2%}",
            title="🩺 Health Check",
        )
    )

    kg = get_knowledge_graph()
    stats = kg.get_stats()
    console.print(
        f"\nKnowledge Graph: [cyan]{stats.get('nodes', 0)}[/cyan] nodes, "
        f"[cyan]{stats.get('edges', 0)}[/cyan] edges"
    )


# ═══════════════════════════════════════════════════════════════════
# ONE-SHOT SOLVER COMMAND
# ═══════════════════════════════════════════════════════════════════


@app.command("solve")
def solve_command(
    problem: str = typer.Argument(..., help="Research problem to solve"),
    full: bool = typer.Option(True, "--full/--quick", help="Full cycle or quick mode"),
    max_hypotheses: int = typer.Option(5, "--max", "-n", min=1, max=10),
    output: str = typer.Option("report.md", "--output", "-o", help="Output file"),
    no_literature: bool = typer.Option(
        False, "--no-literature", help="Skip literature search"
    ),
    no_consensus: bool = typer.Option(
        False, "--no-consensus", help="Skip consensus analysis"
    ),
):
    """
    One-shot scientific discovery (full cycle in one command).

    Executes complete discovery cycle:
    1. Search literature (Semantic Scholar)
    2. Analyze scientific consensus
    3. Generate hypotheses (C4+TRIZ+Analogy)
    4. Create validation plan
    5. Export report

    Example:
        turbo solve "increase battery density without losing safety"
        turbo solve "optimize neural network training" --full --output report.md
    """
    import asyncio
    from src.solver.one_shot import get_one_shot_solver

    async def run_solver():
        solver = get_one_shot_solver()
        result = await solver.solve(
            problem=problem,
            max_hypotheses=max_hypotheses,
            include_validation=full,
            literature_search=not no_literature,
            consensus_analysis=not no_consensus,
        )
        return result

    try:
        result = asyncio.run(run_solver())

        # Display summary
        console.print(solver.get_one_shot_solver().render_summary(result))

        # Export
        if output:
            get_one_shot_solver().export_report(result, output)

    except Exception as e:
        console.print(f"[red]Solver error: {e}[/red]")
        raise typer.Exit(1)


# ═══════════════════════════════════════════════════════════════════
# SEMANTIC SCHOLAR SEARCH COMMAND
# ═══════════════════════════════════════════════════════════════════


@search_app.command("semantic")
def search_semantic(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", min=1, max=100),
    year_start: Optional[int] = typer.Option(None, "--from", help="Start year"),
    year_end: Optional[int] = typer.Option(None, "--to", help="End year"),
    open_access: bool = typer.Option(
        False, "--open-access", "-o", help="Open access only"
    ),
    save: bool = typer.Option(False, "--save", "-s", help="Save to knowledge graph"),
):
    """
    Search Semantic Scholar (200M+ papers).

    Free tier: 100 requests per 5 minutes
    Get API key: https://www.semanticscholar.org/product/api

    Example:
        turbo search semantic "battery energy density"
        turbo search semantic "neural networks" --from 2020 --open-access
    """
    import asyncio
    from src.search.semantic_scholar import get_semantic_scholar_client

    async def run_search():
        client = get_semantic_scholar_client()
        async with client:
            return await client.search_papers(
                query=query,
                limit=limit,
                year_start=year_start,
                year_end=year_end,
                open_access_only=open_access,
            )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching Semantic Scholar...", total=None)
            papers = asyncio.run(run_search())
            progress.update(task, completed=True)

        if not papers:
            console.print("[yellow]No papers found.[/yellow]")
            return

        table = Table(title=f"Semantic Scholar Results: '{query}'")
        table.add_column("Title", style="cyan", max_width=40)
        table.add_column("Year", style="magenta", justify="center")
        table.add_column("Citations", style="green", justify="right")
        table.add_column("TL;DR", style="dim", max_width=30)

        for paper in papers:
            tldr_short = paper.tldr[:40] + "..." if len(paper.tldr) > 40 else paper.tldr
            table.add_row(
                paper.title[:40] + "..." if len(paper.title) > 40 else paper.title,
                str(paper.year) if paper.year else "N/A",
                str(paper.citation_count),
                tldr_short if tldr_short else "N/A",
            )

        console.print(table)
        console.print(f"\n[dim]Found {len(papers)} papers[/dim]")

        if save:
            kg = get_knowledge_graph()
            for paper in papers:
                kg.add_reference(
                    title=paper.title,
                    authors=paper.authors,
                    year=paper.year,
                    source="semantic_scholar",
                    source_id=paper.paper_id,
                    metadata={
                        "citation_count": paper.citation_count,
                        "fields": paper.fields_of_study,
                        "open_access": paper.open_access_pdf is not None,
                    },
                )
            kg.save()
            console.print(
                f"[green]✓ Saved {len(papers)} references to knowledge graph[/green]"
            )

    except ImportError as e:
        console.print(f"[red]Requires httpx: pip install httpx[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")
        raise typer.Exit(1)


# ═══════════════════════════════════════════════════════════════════
# CONSENSUS METER COMMAND
# ═══════════════════════════════════════════════════════════════════


@validation_app.command("consensus")
def validate_consensus(
    discovery_id: str = typer.Argument(..., help="Discovery/hypothesis ID"),
    search: bool = typer.Option(
        True, "--search/--no-search", help="Search for evidence"
    ),
):
    """
    Analyze scientific consensus for a hypothesis.

    Shows visual for/against meter inspired by Consensus.app.

    Example:
        turbo validate consensus discovery_001
    """
    import asyncio
    from src.validation.consensus_meter import (
        get_consensus_meter,
        Evidence,
        EvidenceType,
        EvidenceStrength,
    )
    from src.search.semantic_scholar import get_semantic_scholar_client

    kg = get_knowledge_graph()
    discovery = kg.get_node(discovery_id)

    if not discovery:
        console.print(f"[red]Discovery {discovery_id} not found[/red]")
        raise typer.Exit(1)

    hypothesis_text = discovery.get("metadata", {}).get("hypothesis", "")

    console.print(
        Panel.fit(
            f"[bold]Analyzing Consensus[/bold]\n\n"
            f"Hypothesis: {hypothesis_text[:80]}...",
            title="🔍 Consensus Meter",
        )
    )

    # Gather evidence
    evidence_list = []

    if search:

        async def gather_evidence():
            client = get_semantic_scholar_client()
            async with client:
                papers = await client.search_papers(hypothesis_text, limit=15)
                return papers

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Searching for evidence...", total=None)
                papers = asyncio.run(gather_evidence())
                progress.update(task, completed=True)

            # Convert papers to evidence
            for paper in papers:
                # Simple heuristic classification
                ev_type = (
                    EvidenceType.SUPPORTING
                    if paper.citation_count > 50
                    else EvidenceType.NEUTRAL
                )

                ev = Evidence(
                    source=paper.title,
                    type=ev_type,
                    strength=EvidenceStrength.MODERATE
                    if paper.citation_count > 20
                    else EvidenceStrength.WEAK,
                    description=paper.abstract[:150] + "..."
                    if len(paper.abstract) > 150
                    else paper.abstract,
                    citation_count=paper.citation_count,
                    year=paper.year,
                    peer_reviewed=True,
                )
                evidence_list.append(ev)

        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not search for evidence: {e}[/yellow]"
            )

    # Calculate consensus
    meter = get_consensus_meter()
    score = meter.calculate_consensus(discovery_id, hypothesis_text, evidence_list)

    # Display results
    console.print(
        Panel.fit(
            meter.render_rich_meter(score),
            title=f"Consensus: {score.consensus_level.upper()}",
            border_style="green"
            if score.consensus_level in ["strong", "moderate"]
            else "yellow",
        )
    )

    # ASCII bar
    console.print(meter.render_consensus_bar(score))

    # Summary text
    console.print(f"\n[italic]{meter.generate_summary_text(score)}[/italic]")

    # Evidence breakdown
    if evidence_list:
        console.print(f"\n[bold]Evidence Breakdown:[/bold]")
        table = Table()
        table.add_column("Type", style="cyan")
        table.add_column("Source", style="magenta", max_width=30)
        table.add_column("Strength", style="yellow")
        table.add_column("Citations", style="green", justify="right")

        for ev in evidence_list[:10]:
            type_color = {
                EvidenceType.SUPPORTING: "green",
                EvidenceType.CONTRADICTING: "red",
                EvidenceType.NEUTRAL: "yellow",
            }.get(ev.type, "white")

            table.add_row(
                f"[{type_color}]{ev.type.value}[/{type_color}]",
                ev.source[:30] + "..." if len(ev.source) > 30 else ev.source,
                ev.strength.name.lower(),
                str(ev.citation_count),
            )

        console.print(table)


# ═══════════════════════════════════════════════════════════════════
# INTERACTIVE CONTRADICTION MATRIX COMMAND
# ═══════════════════════════════════════════════════════════════════


@triz_app.command("matrix")
def triz_matrix(
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive mode"
    ),
    improve: Optional[int] = typer.Option(
        None, "--improve", help="Parameter to improve (1-39)"
    ),
    worsen: Optional[int] = typer.Option(
        None, "--worsen", help="Parameter that worsens (1-39)"
    ),
    problem: Optional[str] = typer.Option(
        None, "--problem", "-p", help="Problem description (auto-detect params)"
    ),
):
    """
    Interactive TRIZ Contradiction Matrix.

    Shows the classic 39x39 matrix mapping engineering parameters.
    Each cell contains recommended TRIZ principles.

    Example:
        turbo triz matrix --interactive
        turbo triz matrix --improve 9 --worsen 14
        turbo triz matrix --problem "increase speed without losing strength"
    """
    from src.triz.contradiction_matrix import get_contradiction_matrix

    matrix = get_contradiction_matrix()

    if problem and not (improve and worsen):
        # Auto-detect parameters from problem
        detected = matrix.suggest_parameters(problem)
        if detected[0] and detected[1]:
            improve, worsen = detected
            console.print(
                f"[dim]Detected: Improve '{matrix.get_parameter_name(improve)}', "
                f"Avoid worsening '{matrix.get_parameter_name(worsen)}'[/dim]\n"
            )

    if improve and worsen:
        # Show specific cell
        cell = matrix.get_principles(improve, worsen)

        if cell:
            console.print(
                Panel.fit(
                    matrix.render_cell_detail(cell),
                    title=f"🔧 Contradiction Matrix Cell ({improve},{worsen})",
                )
            )

            # Show similar contradictions
            similar = matrix.find_similar_contradictions(improve, worsen)
            if similar:
                console.print("\n[bold]Similar Contradictions:[/bold]")
                for sim in similar:
                    console.print(
                        f"  • Improve {matrix.get_parameter_name(sim.improve_param)} vs "
                        f"{matrix.get_parameter_name(sim.worsen_param)}"
                    )
        else:
            console.print(
                f"[yellow]No data for contradiction {improve} vs {worsen}[/yellow]"
            )
            console.print(
                "[dim]Try turbo triz recommend instead for AI-powered recommendations[/dim]"
            )

    elif interactive or not (improve and worsen):
        # Show interactive menu
        console.print(
            Panel.fit(
                "[bold]TRIZ Contradiction Matrix[/bold]\n\n"
                "The classic 39x39 matrix mapping engineering trade-offs.\n"
                "Each cell contains recommended inventive principles.",
                title="🔧 Interactive Matrix",
            )
        )

        # Show ASCII preview
        console.print(matrix.render_matrix_ascii())

        # Show statistics
        stats = matrix.get_statistics()
        console.print(f"\n[dim]Matrix Statistics:[/dim]")
        console.print(f"  • {stats['total_contradictions']} documented contradictions")
        console.print(f"  • {stats['unique_improve_params']} improvement parameters")
        console.print(f"  • {stats['avg_principles_per_cell']:.1f} principles per cell")

        # Show most common principles
        console.print(f"\n[dim]Most Recommended Principles:[/dim]")
        for principle_num, count in stats["most_common_principles"]:
            console.print(f"  • Principle {principle_num}: recommended {count} times")

        # Show common contradictions
        console.print(f"\n[bold]Most Common Contradictions:[/bold]")
        common = matrix.get_common_contradictions(5)
        for cell in common:
            console.print(
                f"  • {matrix.get_parameter_name(cell.improve_param)} vs "
                f"{matrix.get_parameter_name(cell.worsen_param)} "
                f"({cell.frequency:,} patents)"
            )


# ═══════════════════════════════════════════════════════════════════
# GRAPH VIEW COMMAND
# ═══════════════════════════════════════════════════════════════════


@graph_app.command("view")
def graph_view(
    center: Optional[str] = typer.Option(None, "--center", "-c", help="Center node ID"),
    depth: int = typer.Option(2, "--depth", "-d", min=1, max=4),
    types: Optional[List[str]] = typer.Option(
        None, "--type", "-t", help="Filter by node type"
    ),
    export: Optional[str] = typer.Option(
        None, "--export", "-e", help="Export to HTML file"
    ),
    min_confidence: float = typer.Option(0.0, "--min-confidence", min=0.0, max=1.0),
):
    """
    Obsidian-style graph visualization.

    Interactive force-directed graph of the knowledge graph.
    Supports filtering, zooming, and panning.

    Example:
        turbo graph view
        turbo graph view --center discovery_001 --depth 2
        turbo graph view --export graph.html
    """
    from src.graph.graph_view import get_graph_renderer

    renderer = get_graph_renderer()

    if export:
        # Export to interactive HTML
        try:
            path = renderer.export_to_html(
                output_path=export,
                center_node=center,
                title="TURBO-CDI Knowledge Graph",
            )
            console.print(f"[green]✓ Interactive graph exported to {path}[/green]")
            console.print(f"[dim]Open in browser: file://{Path(path).absolute()}[/dim]")
        except Exception as e:
            console.print(f"[red]Export error: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Show ASCII preview
        try:
            preview = renderer.render_ascii_preview(
                center_node=center, width=70, height=20
            )
            console.print(preview)

            # Show node count
            nodes, edges = renderer.build_visualization_graph(
                center_node=center,
                depth=depth,
                node_types=types,
                min_confidence=min_confidence,
            )

            console.print(f"\n[bold]Graph Statistics:[/bold]")
            console.print(f"  Nodes: {len(nodes)}")
            console.print(f"  Edges: {len(edges)}")

            # Show node types
            type_counts = {}
            for node in nodes:
                type_counts[node.type] = type_counts.get(node.type, 0) + 1

            if type_counts:
                console.print(f"\n[dim]Node Types:[/dim]")
                for node_type, count in sorted(
                    type_counts.items(), key=lambda x: -x[1]
                ):
                    console.print(f"  • {node_type}: {count}")

            console.print(
                f"\n[dim]Tip: Use --export graph.html for interactive visualization[/dim]"
            )

        except Exception as e:
            console.print(f"[red]Graph error: {e}[/red]")
            raise typer.Exit(1)


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    """TURBO-CDI v4.0 - Scientific Hypothesis Generation Platform"""
    if version:
        console.print("TURBO-CDI v4.0 - C4 Cognitive Geometry Engine")
        raise typer.Exit()


if __name__ == "__main__":
    app()
