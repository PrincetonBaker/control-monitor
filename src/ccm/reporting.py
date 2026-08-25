"""Report generation for scan results."""

from datetime import datetime
from pathlib import Path

from jinja2 import Template

from ccm.catalog import CatalogManager
from ccm.models import CheckStatus, ScanResult


class ReportGenerator:
    """Generate reports from scan results."""

    def __init__(self, catalog_path: str = "controls.yaml"):
        self.catalog_manager = CatalogManager(catalog_path)
        self.catalog_manager.load_catalog()

    def generate_markdown(self, scan_result: ScanResult, output_file: str | None = None) -> str:
        """Generate Markdown report."""
        lines = []
        lines.append("# CCM Control Scan Report\n")
        lines.append(f"**Generated:** {scan_result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

        lines.append("## Summary\n")
        summary = scan_result.summary
        lines.append(f"- **Total Controls:** {summary['total']}")
        lines.append(f"- **Passed:** {summary['pass']} ✓")
        lines.append(f"- **Failed:** {summary['fail']} ✗")
        lines.append(f"- **Accepted (Exception):** {summary['accepted']} ⚠")
        lines.append(f"- **Errors:** {summary['error']} ⚡")
        lines.append("")

        if scan_result.exceptions_applied:
            lines.append(f"**Exceptions Applied:** {len(scan_result.exceptions_applied)}\n")

        lines.append("## Control Results\n")

        evidence_by_status = {
            CheckStatus.FAIL: [],
            CheckStatus.ACCEPTED: [],
            CheckStatus.ERROR: [],
            CheckStatus.PASS: [],
        }

        for evidence in scan_result.evidence:
            evidence_by_status[evidence.status].append(evidence)

        for status, status_evidence in evidence_by_status.items():
            if not status_evidence:
                continue

            icon = {
                CheckStatus.PASS: "✓",
                CheckStatus.FAIL: "✗",
                CheckStatus.ACCEPTED: "⚠",
                CheckStatus.ERROR: "⚡",
            }[status]

            lines.append(f"### {status.value.upper()} {icon}\n")

            for evidence in status_evidence:
                control = self.catalog_manager.get_control(evidence.control_id)
                lines.append(f"#### {evidence.control_id}: {control.title if control else 'Unknown'}")
                lines.append(f"- **Status:** {status.value}")
                lines.append(f"- **Message:** {evidence.message}")
                lines.append(f"- **Collector:** {evidence.collector}")
                lines.append(f"- **Timestamp:** {evidence.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

                if evidence.error:
                    lines.append(f"- **Error:** {evidence.error}")

                if control:
                    lines.append(f"- **Severity:** {control.severity}")
                    lines.append(f"- **Category:** {control.category}")

                    frameworks = ", ".join([f.name for f in control.frameworks])
                    lines.append(f"- **Frameworks:** {frameworks}")

                lines.append("")

        report = "\n".join(lines)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)

        return report

    def generate_html(self, scan_result: ScanResult, output_file: str | None = None) -> str:
        """Generate HTML report."""
        template = Template(
            """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CCM Control Scan Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0 0 10px 0;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }
        .summary-card .value {
            font-size: 32px;
            font-weight: bold;
        }
        .summary-card.pass .value { color: #27ae60; }
        .summary-card.fail .value { color: #e74c3c; }
        .summary-card.accepted .value { color: #f39c12; }
        .summary-card.error .value { color: #95a5a6; }
        .control {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border-left: 4px solid #ccc;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .control.pass { border-left-color: #27ae60; }
        .control.fail { border-left-color: #e74c3c; }
        .control.accepted { border-left-color: #f39c12; }
        .control.error { border-left-color: #95a5a6; }
        .control h3 {
            margin: 0 0 10px 0;
        }
        .control .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .status.pass { background: #27ae60; color: white; }
        .status.fail { background: #e74c3c; color: white; }
        .status.accepted { background: #f39c12; color: white; }
        .status.error { background: #95a5a6; color: white; }
        .control-meta {
            color: #666;
            font-size: 14px;
        }
        .control-meta span {
            margin-right: 15px;
        }
        .message {
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .error-message {
            background: #fee;
            color: #c00;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }
        .section-header {
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #ccc;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>CCM Control Scan Report</h1>
        <p>Generated: {{ timestamp }}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <h3>Total Controls</h3>
            <div class="value">{{ summary.total }}</div>
        </div>
        <div class="summary-card pass">
            <h3>Passed</h3>
            <div class="value">{{ summary.pass }}</div>
        </div>
        <div class="summary-card fail">
            <h3>Failed</h3>
            <div class="value">{{ summary.fail }}</div>
        </div>
        <div class="summary-card accepted">
            <h3>Accepted</h3>
            <div class="value">{{ summary.accepted }}</div>
        </div>
        <div class="summary-card error">
            <h3>Errors</h3>
            <div class="value">{{ summary.error }}</div>
        </div>
    </div>

    {% if exceptions_count > 0 %}
    <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 30px;">
        <strong>⚠ {{ exceptions_count }} exception(s) applied during this scan</strong>
    </div>
    {% endif %}

    {% for status_name, status_evidence in evidence_by_status.items() %}
    {% if status_evidence %}
    <div class="section-header">
        <h2>{{ status_name }} ({{ status_evidence|length }})</h2>
    </div>

    {% for evidence in status_evidence %}
    <div class="control {{ evidence.status }}">
        <h3>{{ evidence.control_id }}: {{ evidence.control_title }}</h3>
        <span class="status {{ evidence.status }}">{{ evidence.status }}</span>

        <div class="control-meta">
            <span><strong>Collector:</strong> {{ evidence.collector }}</span>
            <span><strong>Severity:</strong> {{ evidence.severity }}</span>
            <span><strong>Category:</strong> {{ evidence.category }}</span>
        </div>

        <div class="message">
            {{ evidence.message }}
        </div>

        {% if evidence.error %}
        <div class="error-message">
            <strong>Error:</strong> {{ evidence.error }}
        </div>
        {% endif %}

        <div class="control-meta">
            <span><strong>Frameworks:</strong> {{ evidence.frameworks }}</span>
        </div>
    </div>
    {% endfor %}
    {% endif %}
    {% endfor %}

</body>
</html>
"""
        )

        evidence_by_status = {
            "FAILED": [],
            "ACCEPTED": [],
            "ERRORS": [],
            "PASSED": [],
        }

        for evidence in scan_result.evidence:
            control = self.catalog_manager.get_control(evidence.control_id)

            evidence_data = {
                "control_id": evidence.control_id,
                "control_title": control.title if control else "Unknown",
                "status": evidence.status.value,
                "collector": evidence.collector,
                "message": evidence.message,
                "error": evidence.error,
                "severity": control.severity if control else "unknown",
                "category": control.category if control else "unknown",
                "frameworks": ", ".join([f.name for f in control.frameworks]) if control else "",
            }

            if evidence.status == CheckStatus.FAIL:
                evidence_by_status["FAILED"].append(evidence_data)
            elif evidence.status == CheckStatus.ACCEPTED:
                evidence_by_status["ACCEPTED"].append(evidence_data)
            elif evidence.status == CheckStatus.ERROR:
                evidence_by_status["ERRORS"].append(evidence_data)
            else:
                evidence_by_status["PASSED"].append(evidence_data)

        html = template.render(
            timestamp=scan_result.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            summary=scan_result.summary,
            exceptions_count=len(scan_result.exceptions_applied),
            evidence_by_status=evidence_by_status,
        )

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(html)

        return html
