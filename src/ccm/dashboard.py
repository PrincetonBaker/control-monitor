"""FastAPI dashboard for CCM."""

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from ccm.catalog import CatalogManager
from ccm.evidence import EvidenceStore
from ccm.exceptions import ExceptionManager
from ccm.models import CheckStatus
from ccm.scanner import Scanner

app = FastAPI(
    title="CCM Dashboard",
    description="Continuous Control Monitoring Dashboard",
    version="0.1.0",
)

catalog_manager = CatalogManager()
evidence_store = EvidenceStore()
exception_manager = ExceptionManager()


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Main dashboard page."""
    catalog_manager.load_catalog()

    evidence_dir = Path("evidence")
    if not evidence_dir.exists():
        evidence_dir.mkdir(parents=True, exist_ok=True)

    control_status = {}
    for control in catalog_manager.list_all_controls():
        latest = evidence_store.get_latest_evidence(control.id)
        control_status[control.id] = {
            "control": control,
            "evidence": latest,
        }

    exceptions = exception_manager.list_exceptions(include_expired=False)

    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CCM Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 32px; margin-bottom: 10px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .stat-card h3 {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        .stat-card .value {
            font-size: 36px;
            font-weight: bold;
        }
        .stat-card.pass .value { color: #10b981; }
        .stat-card.fail .value { color: #ef4444; }
        .stat-card.accepted .value { color: #f59e0b; }
        .controls {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        .controls-header {
            padding: 24px;
            border-bottom: 1px solid #e5e7eb;
        }
        .controls-header h2 { font-size: 20px; }
        .control-item {
            padding: 20px 24px;
            border-bottom: 1px solid #e5e7eb;
            display: grid;
            grid-template-columns: auto 1fr auto auto;
            gap: 20px;
            align-items: center;
        }
        .control-item:last-child { border-bottom: none; }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        .status-indicator.pass { background: #10b981; }
        .status-indicator.fail { background: #ef4444; }
        .status-indicator.accepted { background: #f59e0b; }
        .status-indicator.unknown { background: #9ca3af; }
        .control-info h4 {
            font-size: 14px;
            margin-bottom: 4px;
        }
        .control-info p {
            font-size: 12px;
            color: #6b7280;
        }
        .badge {
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge.critical { background: #fee2e2; color: #991b1b; }
        .badge.high { background: #fed7aa; color: #9a3412; }
        .badge.medium { background: #fef3c7; color: #92400e; }
        .timestamp {
            font-size: 12px;
            color: #9ca3af;
        }
        .exceptions-section {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            padding: 24px;
            margin-bottom: 30px;
        }
        .exceptions-section h2 {
            font-size: 20px;
            margin-bottom: 20px;
        }
        .exception-item {
            padding: 16px;
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            border-radius: 6px;
            margin-bottom: 12px;
        }
        .exception-item h4 {
            font-size: 14px;
            margin-bottom: 8px;
        }
        .exception-item p {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 4px;
        }
        .actions {
            margin-top: 30px;
            text-align: center;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            margin: 0 8px;
            font-weight: 500;
        }
        .btn:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ CCM Dashboard</h1>
        <p>Continuous Control Monitoring</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <h3>Total Controls</h3>
            <div class="value">{{ total_controls }}</div>
        </div>
        <div class="stat-card pass">
            <h3>Passed</h3>
            <div class="value">{{ passed_count }}</div>
        </div>
        <div class="stat-card fail">
            <h3>Failed</h3>
            <div class="value">{{ failed_count }}</div>
        </div>
        <div class="stat-card accepted">
            <h3>Exceptions</h3>
            <div class="value">{{ exceptions_count }}</div>
        </div>
    </div>

    {% if exceptions %}
    <div class="exceptions-section">
        <h2>⚠️ Active Risk Exceptions</h2>
        {% for exc in exceptions %}
        <div class="exception-item">
            <h4>{{ exc.control_id }} - Exception {{ exc.id }}</h4>
            <p><strong>Reason:</strong> {{ exc.reason }}</p>
            <p><strong>Compensating Control:</strong> {{ exc.compensating_control }}</p>
            <p><strong>Expires:</strong> {{ exc.expiry_date.strftime('%Y-%m-%d') }} | <strong>Approver:</strong> {{ exc.approver }}</p>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="controls">
        <div class="controls-header">
            <h2>Control Status</h2>
        </div>
        {% for control_id, data in control_status.items() %}
        <div class="control-item">
            <div class="status-indicator {{ data.evidence.status if data.evidence else 'unknown' }}"></div>
            <div class="control-info">
                <h4>{{ control_id }}: {{ data.control.title }}</h4>
                <p>{{ data.control.category }} | {{ ", ".join([f.name for f in data.control.frameworks]) }}</p>
            </div>
            <span class="badge {{ data.control.severity }}">{{ data.control.severity }}</span>
            <span class="timestamp">
                {% if data.evidence %}
                {{ data.evidence.timestamp.strftime('%Y-%m-%d %H:%M') }}
                {% else %}
                Never checked
                {% endif %}
            </span>
        </div>
        {% endfor %}
    </div>

    <div class="actions">
        <a href="/api/scan" class="btn">Run Scan</a>
        <a href="/api/controls" class="btn">View Controls</a>
        <a href="/api/exceptions" class="btn">View Exceptions</a>
    </div>
</body>
</html>
"""

    from jinja2 import Template

    total_controls = len(control_status)
    passed_count = sum(
        1 for d in control_status.values() if d["evidence"] and d["evidence"].status == CheckStatus.PASS
    )
    failed_count = sum(
        1 for d in control_status.values() if d["evidence"] and d["evidence"].status == CheckStatus.FAIL
    )

    template = Template(html_template)
    html = template.render(
        control_status=control_status,
        exceptions=exceptions,
        total_controls=total_controls,
        passed_count=passed_count,
        failed_count=failed_count,
        exceptions_count=len(exceptions),
    )

    return HTMLResponse(content=html)


@app.get("/api/controls")
def get_controls():
    """Get all controls."""
    catalog_manager.load_catalog()
    controls = catalog_manager.list_all_controls()
    return [c.model_dump() for c in controls]


@app.get("/api/controls/{control_id}")
def get_control(control_id: str):
    """Get a specific control."""
    catalog_manager.load_catalog()
    control = catalog_manager.get_control(control_id)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control.model_dump()


@app.get("/api/evidence/{control_id}")
def get_evidence(control_id: str, limit: int = 10):
    """Get evidence history for a control."""
    history = evidence_store.get_evidence_history(control_id, limit=limit)
    return [e.model_dump(mode="json") for e in history]


@app.get("/api/exceptions")
def get_exceptions():
    """Get all active exceptions."""
    exceptions = exception_manager.list_exceptions(include_expired=False)
    return [e.model_dump(mode="json") for e in exceptions]


@app.post("/api/scan")
def run_scan():
    """Trigger a full scan."""
    scanner = Scanner()
    result = scanner.scan_all()
    return result.model_dump(mode="json")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
