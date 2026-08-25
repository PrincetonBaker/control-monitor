"""Command-line interface for CCM."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import typer
from dateutil import parser

from ccm.catalog import CatalogManager
from ccm.evidence import EvidenceStore
from ccm.exceptions import ExceptionManager
from ccm.models import CheckStatus
from ccm.reporting import ReportGenerator
from ccm.scanner import Scanner

app = typer.Typer(
    name="ccm",
    help="Continuous Control Monitoring - Compliance automation platform",
    add_completion=False,
)


@app.command()
def scan(
    framework: str | None = typer.Option(None, "--framework", "-f", help="Scan specific framework"),
    control: str | None = typer.Option(None, "--control", "-c", help="Scan specific control"),
    category: str | None = typer.Option(None, "--category", help="Scan controls by category"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output format (json|markdown|html)"),
    fail_on_error: bool = typer.Option(True, "--fail-on-error", help="Exit with error code on failures"),
):
    """Run control scans."""
    typer.echo("🔍 CCM Control Scanner\n")

    scanner = Scanner()

    try:
        if control:
            typer.echo(f"Scanning control: {control}")
            result = scanner.scan_control(control)
        elif framework:
            typer.echo(f"Scanning framework: {framework}")
            result = scanner.scan_framework(framework)
        elif category:
            typer.echo(f"Scanning category: {category}")
            result = scanner.scan_category(category)
        else:
            typer.echo("Scanning all controls...")
            result = scanner.scan_all()

        typer.echo("\n" + "=" * 60)
        typer.echo("SCAN SUMMARY")
        typer.echo("=" * 60)
        typer.echo(f"Total:    {result.summary['total']}")
        typer.echo(f"✓ Passed:   {result.summary['pass']}")
        typer.echo(f"✗ Failed:   {result.summary['fail']}")
        typer.echo(f"⚠ Accepted: {result.summary['accepted']}")
        typer.echo(f"⚡ Errors:   {result.summary['error']}")

        if result.exceptions_applied:
            typer.echo(f"\n⚠ {len(result.exceptions_applied)} exception(s) applied")

        report_gen = ReportGenerator()
        if output == "markdown" or output == "md":
            report_path = f"reports/scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
            report_gen.generate_markdown(result, report_path)
            typer.echo(f"\n📄 Markdown report: {report_path}")
        elif output == "html":
            report_path = f"reports/scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html"
            report_gen.generate_html(result, report_path)
            typer.echo(f"\n📄 HTML report: {report_path}")

        typer.echo(f"\n💾 Evidence stored in: evidence/")

        if fail_on_error and result.summary["fail"] > 0:
            typer.echo("\n❌ Scan failed: unaccepted control failures detected")
            raise typer.Exit(code=1)

        typer.echo("\n✅ Scan completed successfully")
        raise typer.Exit(code=0)

    except Exception as e:
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def report(
    format: str = typer.Argument("markdown", help="Report format (markdown|html)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate a report from the most recent scan."""
    typer.echo("📊 Generating report...\n")

    try:
        evidence_store = EvidenceStore()
        evidence_dir = Path("evidence")

        if not evidence_dir.exists() or not list(evidence_dir.glob("*.evidence.json")):
            typer.echo("❌ No evidence found. Run a scan first.", err=True)
            raise typer.Exit(code=1)

        from ccm.models import ScanResult

        evidence_files = sorted(evidence_dir.glob("*.evidence.json"))
        latest_timestamp = None
        latest_evidence = []

        for file_path in evidence_files:
            evidence = evidence_store.get_latest_evidence(file_path.stem.split("_")[0])
            if evidence:
                if not latest_timestamp or evidence.timestamp > latest_timestamp:
                    latest_timestamp = evidence.timestamp
                if not latest_evidence or evidence.timestamp == latest_evidence[0].timestamp:
                    latest_evidence.append(evidence)

        result = ScanResult(evidence=latest_evidence)
        report_gen = ReportGenerator()

        if not output:
            output = f"reports/report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"

        if format == "markdown" or format == "md":
            report_gen.generate_markdown(result, output)
        elif format == "html":
            report_gen.generate_html(result, output)
        else:
            typer.echo(f"❌ Unknown format: {format}", err=True)
            raise typer.Exit(code=1)

        typer.echo(f"✅ Report generated: {output}")

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def export_evidence(
    output: str = typer.Option("evidence_export.json", "--output", "-o", help="Output file"),
):
    """Export all evidence to a single JSON file."""
    typer.echo("📦 Exporting evidence...\n")

    try:
        evidence_store = EvidenceStore()
        output_path = evidence_store.export_evidence(output)
        typer.echo(f"✅ Evidence exported: {output_path}")

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


exception_app = typer.Typer(help="Manage risk exceptions")
app.add_typer(exception_app, name="exception")


@exception_app.command("list")
def exception_list(
    control: str | None = typer.Option(None, "--control", "-c", help="Filter by control ID"),
    include_expired: bool = typer.Option(False, "--include-expired", help="Include expired exceptions"),
):
    """List risk exceptions."""
    manager = ExceptionManager()
    exceptions = manager.list_exceptions(control_id=control, include_expired=include_expired)

    if not exceptions:
        typer.echo("No exceptions found.")
        return

    typer.echo(f"\n📋 Risk Exceptions ({len(exceptions)})\n")

    for exc in exceptions:
        status = "EXPIRED" if exc.is_expired() else "ACTIVE" if exc.is_active else "INACTIVE"
        status_icon = "❌" if status == "EXPIRED" else "✓" if status == "ACTIVE" else "○"

        typer.echo(f"{status_icon} Exception {exc.id} [{status}]")
        typer.echo(f"  Control:     {exc.control_id}")
        typer.echo(f"  Reason:      {exc.reason}")
        typer.echo(f"  Compensating: {exc.compensating_control}")
        typer.echo(f"  Expires:     {exc.expiry_date.strftime('%Y-%m-%d')}")
        typer.echo(f"  Approver:    {exc.approver}")
        typer.echo()


@exception_app.command("add")
def exception_add(
    control_id: str = typer.Argument(..., help="Control ID"),
    reason: str = typer.Option(..., "--reason", "-r", help="Reason for exception"),
    compensating: str = typer.Option(..., "--compensating", "-c", help="Compensating control"),
    expires: str = typer.Option(..., "--expires", "-e", help="Expiry date (YYYY-MM-DD)"),
    approver: str = typer.Option(..., "--approver", "-a", help="Approver name"),
):
    """Add a new risk exception."""
    try:
        expiry_date = parser.parse(expires)
        if expiry_date <= datetime.utcnow():
            typer.echo("❌ Expiry date must be in the future", err=True)
            raise typer.Exit(code=1)

        manager = ExceptionManager()
        exception = manager.add_exception(
            control_id=control_id,
            reason=reason,
            compensating_control=compensating,
            expiry_date=expiry_date,
            approver=approver,
        )

        typer.echo(f"\n✅ Exception {exception.id} created")
        typer.echo(f"  Control:     {exception.control_id}")
        typer.echo(f"  Expires:     {exception.expiry_date.strftime('%Y-%m-%d')}")

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def list_controls(
    framework: str | None = typer.Option(None, "--framework", "-f", help="Filter by framework"),
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
):
    """List all controls in the catalog."""
    catalog = CatalogManager()
    catalog.load_catalog()

    if framework:
        controls = catalog.get_controls_by_framework(framework)
        typer.echo(f"\n📋 Controls for framework: {framework}\n")
    elif category:
        controls = catalog.get_controls_by_category(category)
        typer.echo(f"\n📋 Controls for category: {category}\n")
    else:
        controls = catalog.list_all_controls()
        typer.echo("\n📋 All Controls\n")

    for control in controls:
        typer.echo(f"[{control.severity.upper()}] {control.id}: {control.title}")
        typer.echo(f"  Category: {control.category}")
        frameworks = ", ".join([f.name for f in control.frameworks])
        typer.echo(f"  Frameworks: {frameworks}")
        typer.echo()


@app.command()
def version():
    """Show version information."""
    from ccm import __version__

    typer.echo(f"CCM version {__version__}")


if __name__ == "__main__":
    app()
