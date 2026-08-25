"""Reporting and evidence export."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ccm.models import ControlCatalog, ScanResult


def generate_markdown_report(
    result: ScanResult, catalog: ControlCatalog, output_file: Optional[Path] = None
) -> str:
    """Generate markdown report.
    
    Args:
        result: Scan result
        catalog: Control catalog
        output_file: Optional output file path
        
    Returns:
        Markdown report content
    """
    control_map = {c.id: c for c in catalog.controls}
    
    lines = [
        "# Continuous Control Monitoring Report",
        "",
        f"**Generated:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## Summary",
        "",
        f"- **Total Controls:** {result.summary['total']}",
        f"- **Passed:** {result.summary['pass']}",
        f"- **Failed:** {result.summary['fail']}",
        f"- **Errors:** {result.summary['error']}",
        f"- **Excepted:** {result.summary['excepted']}",
        "",
        "## Control Results",
        "",
    ]
    
    for check in result.checks:
        control = control_map.get(check.control_id)
        if control:
            status_icon = {
                "pass": "✅",
                "fail": "❌",
                "error": "⚠️",
                "excepted": "🔶",
            }.get(check.status, "❓")
            
            lines.extend([
                f"### {status_icon} {control.id}: {control.title}",
                "",
                f"**Status:** {check.status.upper()}",
                f"**Severity:** {control.severity.value.upper()}",
                f"**Category:** {control.category}",
                "",
                f"**Intent:** {control.intent}",
                "",
                f"**Details:** {check.details}",
                "",
            ])
            
            if check.exception_id:
                lines.extend([
                    f"**Exception ID:** {check.exception_id}",
                    "",
                ])
            
            frameworks = ", ".join(
                f"{fm.framework} ({', '.join(fm.controls)})"
                for fm in control.frameworks
            )
            lines.extend([
                f"**Frameworks:** {frameworks}",
                "",
                "---",
                "",
            ])
    
    report = "\n".join(lines)
    
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(report)
    
    return report


def generate_html_report(
    result: ScanResult, catalog: ControlCatalog, output_file: Optional[Path] = None
) -> str:
    """Generate HTML report.
    
    Args:
        result: Scan result
        catalog: Control catalog
        output_file: Optional output file path
        
    Returns:
        HTML report content
    """
    control_map = {c.id: c for c in catalog.controls}
    
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CCM Report - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            text-transform: uppercase;
            color: #666;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            margin: 0;
        }}
        .pass {{ color: #10b981; }}
        .fail {{ color: #ef4444; }}
        .error {{ color: #f59e0b; }}
        .excepted {{ color: #8b5cf6; }}
        .control {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #ddd;
        }}
        .control.pass {{ border-left-color: #10b981; }}
        .control.fail {{ border-left-color: #ef4444; }}
        .control.error {{ border-left-color: #f59e0b; }}
        .control.excepted {{ border-left-color: #8b5cf6; }}
        .control-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }}
        .control-title {{
            flex: 1;
        }}
        .control-title h2 {{
            margin: 0 0 5px 0;
            font-size: 18px;
        }}
        .control-id {{
            color: #666;
            font-size: 14px;
        }}
        .status-badge {{
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-badge.pass {{ background: #d1fae5; color: #065f46; }}
        .status-badge.fail {{ background: #fee2e2; color: #991b1b; }}
        .status-badge.error {{ background: #fef3c7; color: #92400e; }}
        .status-badge.excepted {{ background: #ede9fe; color: #5b21b6; }}
        .control-meta {{
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            font-size: 14px;
        }}
        .control-meta span {{
            background: #f3f4f6;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        .severity-critical {{ background: #fee2e2; color: #991b1b; font-weight: bold; }}
        .severity-high {{ background: #fed7aa; color: #9a3412; font-weight: bold; }}
        .severity-medium {{ background: #fef3c7; color: #92400e; }}
        .severity-low {{ background: #d1fae5; color: #065f46; }}
        .control-details {{
            margin-top: 15px;
        }}
        .control-details p {{
            margin: 8px 0;
        }}
        .frameworks {{
            margin-top: 10px;
            font-size: 13px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Continuous Control Monitoring Report</h1>
        <p>Generated: {timestamp}</p>
    </div>
    
    <div class="summary">
        <div class="summary-card">
            <h3>Total Controls</h3>
            <p class="value">{total}</p>
        </div>
        <div class="summary-card">
            <h3>Passed</h3>
            <p class="value pass">{passed}</p>
        </div>
        <div class="summary-card">
            <h3>Failed</h3>
            <p class="value fail">{failed}</p>
        </div>
        <div class="summary-card">
            <h3>Errors</h3>
            <p class="value error">{errors}</p>
        </div>
        <div class="summary-card">
            <h3>Excepted</h3>
            <p class="value excepted">{excepted}</p>
        </div>
    </div>
    
    <div class="controls">
        {controls_html}
    </div>
</body>
</html>"""
    
    controls_html_parts = []
    
    for check in result.checks:
        control = control_map.get(check.control_id)
        if control:
            severity_class = f"severity-{control.severity.value}"
            frameworks_text = ", ".join(
                f"{fm.framework} ({', '.join(fm.controls)})"
                for fm in control.frameworks
            )
            
            exception_html = ""
            if check.exception_id:
                exception_html = f'<p><strong>Exception ID:</strong> {check.exception_id}</p>'
            
            control_html = f"""
        <div class="control {check.status}">
            <div class="control-header">
                <div class="control-title">
                    <h2>{control.title}</h2>
                    <div class="control-id">{control.id}</div>
                </div>
                <span class="status-badge {check.status}">{check.status}</span>
            </div>
            <div class="control-meta">
                <span class="{severity_class}">Severity: {control.severity.value.upper()}</span>
                <span>Category: {control.category}</span>
            </div>
            <div class="control-details">
                <p><strong>Intent:</strong> {control.intent}</p>
                <p><strong>Details:</strong> {check.details}</p>
                {exception_html}
                <div class="frameworks">
                    <strong>Frameworks:</strong> {frameworks_text}
                </div>
            </div>
        </div>"""
            
            controls_html_parts.append(control_html)
    
    html = html_template.format(
        timestamp=result.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
        total=result.summary["total"],
        passed=result.summary["pass"],
        failed=result.summary["fail"],
        errors=result.summary["error"],
        excepted=result.summary["excepted"],
        controls_html="\n".join(controls_html_parts),
    )
    
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(html)
    
    return html


def export_evidence(result: ScanResult, output_file: Path) -> None:
    """Export evidence to JSON file.
    
    Args:
        result: Scan result
        output_file: Output file path
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(result.model_dump(mode="json"), f, indent=2, default=str)
