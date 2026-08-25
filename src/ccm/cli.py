"""Command-line interface for CCM."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ccm.catalog import load_catalog
from ccm.exceptions import ExceptionManager
from ccm.reporting import export_evidence, generate_html_report, generate_markdown_report
from ccm.scanner import Scanner

app = typer.Typer(
    name="ccm",
    help="Continuous Control Monitoring - YAML control catalog mapped to compliance frameworks",
    add_completion=False,
)
console = Console()


@app.command()
def scan(
    framework: Optional[str] = typer.Option(
        None, "--framework", "-f", help="Filter by framework (SOC2, ISO27001, PCI-DSS, HIPAA)"
    ),
    control_id: Optional[str] = typer.Option(
        None, "--control", "-c", help="Scan specific control ID"
    ),
    output: str = typer.Option(
        "console", "--output", "-o", help="Output format: console, json, markdown, html"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output-file", help="Output file path (required for json, markdown, html)"
    ),
    exit_on_fail: bool = typer.Option(
        True, "--exit-on-fail/--no-exit-on-fail", help="Exit with code 1 on failures"
    ),
) -> None:
    """Scan controls and generate compliance report."""
    catalog = load_catalog()
    scanner = Scanner(catalog=catalog, use_fixtures=True)
    
    if control_id:
        console.print(f"[cyan]Scanning control {control_id}...[/cyan]")
        result = scanner.scan_control(control_id)
    elif framework:
        console.print(f"[cyan]Scanning {framework} controls...[/cyan]")
        result = scanner.scan_by_framework(framework)
    else:
        console.print("[cyan]Scanning all controls...[/cyan]")
        result = scanner.scan_all()
    
    if output == "console":
        _print_console_report(result, catalog)
    elif output == "json":
        if not output_file:
            console.print("[red]Error: --output-file required for json output[/red]")
            raise typer.Exit(1)
        export_evidence(result, Path(output_file))
        console.print(f"[green]Evidence exported to {output_file}[/green]")
    elif output == "markdown":
        if not output_file:
            console.print("[red]Error: --output-file required for markdown output[/red]")
            raise typer.Exit(1)
        generate_markdown_report(result, catalog, Path(output_file))
        console.print(f"[green]Markdown report saved to {output_file}[/green]")
    elif output == "html":
        if not output_file:
            output_file = f"ccm-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
        generate_html_report(result, catalog, Path(output_file))
        console.print(f"[green]HTML report saved to {output_file}[/green]")
    else:
        console.print(f"[red]Unknown output format: {output}[/red]")
        raise typer.Exit(1)
    
    if exit_on_fail and result.has_critical_or_high_failures(catalog):
        console.print("\n[red]❌ Critical or high severity failures detected[/red]")
        raise typer.Exit(1)
    elif exit_on_fail and result.has_failures():
        console.print("\n[yellow]⚠️  Some controls failed[/yellow]")
        raise typer.Exit(1)
    else:
        console.print("\n[green]✅ All controls passed or excepted[/green]")


def _print_console_report(result, catalog):
    """Print report to console."""
    control_map = {c.id: c for c in catalog.controls}
    
    console.print("\n[bold]Summary[/bold]")
    summary_table = Table()
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", style="magenta")
    
    summary_table.add_row("Total", str(result.summary["total"]))
    summary_table.add_row("✅ Passed", str(result.summary["pass"]))
    summary_table.add_row("❌ Failed", str(result.summary["fail"]))
    summary_table.add_row("⚠️  Errors", str(result.summary["error"]))
    summary_table.add_row("🔶 Excepted", str(result.summary["excepted"]))
    
    console.print(summary_table)
    
    console.print("\n[bold]Control Results[/bold]")
    results_table = Table()
    results_table.add_column("Control ID", style="cyan")
    results_table.add_column("Title", style="white")
    results_table.add_column("Status", style="magenta")
    results_table.add_column("Severity", style="yellow")
    results_table.add_column("Details", style="white", overflow="fold")
    
    for check in result.checks:
        control = control_map.get(check.control_id)
        if control:
            status_icon = {
                "pass": "✅",
                "fail": "❌",
                "error": "⚠️",
                "excepted": "🔶",
            }.get(check.status, "❓")
            
            results_table.add_row(
                control.id,
                control.title[:40] + "..." if len(control.title) > 40 else control.title,
                f"{status_icon} {check.status}",
                control.severity.value.upper(),
                check.details[:60] + "..." if len(check.details) > 60 else check.details,
            )
    
    console.print(results_table)


@app.command()
def report(
    input_file: str = typer.Argument(..., help="Input JSON evidence file"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, html"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Generate report from evidence file."""
    import json
    from ccm.models import ScanResult
    
    catalog = load_catalog()
    
    with open(input_file, "r") as f:
        data = json.load(f)
    
    result = ScanResult(**data)
    
    if format == "markdown":
        if not output_file:
            output_file = input_file.replace(".json", ".md")
        generate_markdown_report(result, catalog, Path(output_file))
        console.print(f"[green]Markdown report saved to {output_file}[/green]")
    elif format == "html":
        if not output_file:
            output_file = input_file.replace(".json", ".html")
        generate_html_report(result, catalog, Path(output_file))
        console.print(f"[green]HTML report saved to {output_file}[/green]")
    else:
        console.print(f"[red]Unknown format: {format}[/red]")
        raise typer.Exit(1)


@app.command()
def export_evidence_cmd(
    framework: Optional[str] = typer.Option(None, "--framework", "-f", help="Filter by framework"),
    control_id: Optional[str] = typer.Option(None, "--control", "-c", help="Specific control ID"),
    output_file: str = typer.Option(
        "evidence.json", "--output", "-o", help="Output file path"
    ),
) -> None:
    """Export evidence to JSON file."""
    catalog = load_catalog()
    scanner = Scanner(catalog=catalog, use_fixtures=True)
    
    if control_id:
        result = scanner.scan_control(control_id)
    elif framework:
        result = scanner.scan_by_framework(framework)
    else:
        result = scanner.scan_all()
    
    export_evidence(result, Path(output_file))
    console.print(f"[green]Evidence exported to {output_file}[/green]")


@app.command()
def exception(
    action: str = typer.Argument(..., help="Action: list, add"),
    control_id: Optional[str] = typer.Option(None, "--control", "-c", help="Control ID"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Exception reason"),
    compensating: Optional[str] = typer.Option(
        None, "--compensating", help="Compensating control description"
    ),
    expiry: Optional[str] = typer.Option(None, "--expiry", "-e", help="Expiry date (YYYY-MM-DD)"),
    approver: Optional[str] = typer.Option(None, "--approver", "-a", help="Approver name"),
    show_expired: bool = typer.Option(False, "--show-expired", help="Show expired exceptions"),
) -> None:
    """Manage risk acceptance exceptions."""
    exceptions_file = Path.cwd() / "exceptions.json"
    manager = ExceptionManager(exceptions_file)
    
    if action == "list":
        if show_expired:
            exceptions = manager.list_expired()
            console.print("[yellow]Expired Exceptions[/yellow]")
        else:
            exceptions = manager.list_valid()
            console.print("[green]Valid Exceptions[/green]")
        
        if not exceptions:
            console.print("No exceptions found.")
            return
        
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Control", style="magenta")
        table.add_column("Reason", style="white")
        table.add_column("Compensating", style="white")
        table.add_column("Expiry", style="yellow")
        table.add_column("Approver", style="green")
        
        for exc in exceptions:
            table.add_row(
                exc.id[:8],
                exc.control_id,
                exc.reason[:40] + "..." if len(exc.reason) > 40 else exc.reason,
                exc.compensating_control[:40] + "..."
                if len(exc.compensating_control) > 40
                else exc.compensating_control,
                exc.expiry_date.strftime("%Y-%m-%d"),
                exc.approver,
            )
        
        console.print(table)
    
    elif action == "add":
        if not all([control_id, reason, compensating, expiry, approver]):
            console.print(
                "[red]Error: --control, --reason, --compensating, --expiry, and --approver "
                "are required for 'add' action[/red]"
            )
            raise typer.Exit(1)
        
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
        except ValueError:
            console.print("[red]Error: Invalid expiry date format. Use YYYY-MM-DD[/red]")
            raise typer.Exit(1)
        
        exception = manager.add_exception(
            control_id=control_id,
            reason=reason,
            compensating_control=compensating,
            expiry_date=expiry_date,
            approver=approver,
        )
        
        console.print(f"[green]Exception added: {exception.id}[/green]")
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        raise typer.Exit(1)


@app.command()
def list_controls(
    framework: Optional[str] = typer.Option(None, "--framework", "-f", help="Filter by framework"),
) -> None:
    """List all controls in the catalog."""
    from ccm.catalog import filter_by_framework
    
    catalog = load_catalog()
    
    if framework:
        controls = filter_by_framework(catalog, framework)
        console.print(f"[cyan]Controls for {framework}[/cyan]\n")
    else:
        controls = catalog.controls
        console.print("[cyan]All Controls[/cyan]\n")
    
    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Severity", style="yellow")
    table.add_column("Category", style="magenta")
    table.add_column("Frameworks", style="green")
    
    for control in controls:
        frameworks = ", ".join(fm.framework for fm in control.frameworks)
        table.add_row(
            control.id,
            control.title[:50] + "..." if len(control.title) > 50 else control.title,
            control.severity.value.upper(),
            control.category,
            frameworks,
        )
    
    console.print(table)
    console.print(f"\n[green]Total: {len(controls)} controls[/green]")


if __name__ == "__main__":
    app()
