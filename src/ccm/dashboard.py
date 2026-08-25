"""FastAPI dashboard for CCM."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ccm.catalog import load_catalog
from ccm.exceptions import ExceptionManager
from ccm.models import ScanResult
from ccm.scanner import Scanner

app = FastAPI(
    title="CCM Dashboard",
    description="Continuous Control Monitoring Dashboard",
    version="0.1.0",
)


class ScanRequest(BaseModel):
    """Scan request model."""

    framework: Optional[str] = None
    control_id: Optional[str] = None


class ExceptionRequest(BaseModel):
    """Exception creation request."""

    control_id: str
    reason: str
    compensating_control: str
    expiry_date: str
    approver: str


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Render dashboard homepage."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CCM Dashboard</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                background: white;
                padding: 30px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .header h1 {
                margin: 0 0 10px 0;
                color: #667eea;
            }
            .header p {
                margin: 0;
                color: #666;
            }
            .card {
                background: white;
                padding: 25px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .card h2 {
                margin: 0 0 15px 0;
                color: #333;
            }
            .endpoints {
                list-style: none;
                padding: 0;
            }
            .endpoints li {
                padding: 10px;
                margin: 5px 0;
                background: #f5f5f5;
                border-radius: 4px;
                font-family: monospace;
            }
            .endpoints li code {
                color: #667eea;
                font-weight: bold;
            }
            .button {
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-right: 10px;
            }
            .button:hover {
                background: #5568d3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Continuous Control Monitoring Dashboard</h1>
                <p>Real-time compliance monitoring for SOC 2, ISO 27001, PCI-DSS, and HIPAA</p>
            </div>
            
            <div class="card">
                <h2>Quick Actions</h2>
                <a href="/scan?format=html" class="button">Run Full Scan</a>
                <a href="/controls" class="button">View Controls</a>
                <a href="/exceptions" class="button">View Exceptions</a>
            </div>
            
            <div class="card">
                <h2>API Endpoints</h2>
                <ul class="endpoints">
                    <li><code>GET /scan</code> - Run control scan</li>
                    <li><code>GET /controls</code> - List all controls</li>
                    <li><code>GET /controls/{control_id}</code> - Get specific control</li>
                    <li><code>GET /exceptions</code> - List risk exceptions</li>
                    <li><code>POST /exceptions</code> - Create risk exception</li>
                    <li><code>GET /health</code> - Health check</li>
                    <li><code>GET /docs</code> - Interactive API documentation</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/scan")
async def scan(
    framework: Optional[str] = Query(None, description="Filter by framework"),
    control_id: Optional[str] = Query(None, description="Scan specific control"),
    format: str = Query("json", description="Output format: json or html"),
):
    """Run control scan."""
    catalog = load_catalog()
    scanner = Scanner(catalog=catalog, use_fixtures=True)
    
    if control_id:
        result = scanner.scan_control(control_id)
    elif framework:
        result = scanner.scan_by_framework(framework)
    else:
        result = scanner.scan_all()
    
    if format == "html":
        from ccm.reporting import generate_html_report
        
        html = generate_html_report(result, catalog)
        return HTMLResponse(content=html)
    else:
        return result.model_dump(mode="json")


@app.get("/controls")
async def list_controls(
    framework: Optional[str] = Query(None, description="Filter by framework"),
):
    """List all controls."""
    from ccm.catalog import filter_by_framework
    
    catalog = load_catalog()
    
    if framework:
        controls = filter_by_framework(catalog, framework)
    else:
        controls = catalog.controls
    
    return {
        "controls": [c.model_dump() for c in controls],
        "count": len(controls),
    }


@app.get("/controls/{control_id}")
async def get_control(control_id: str):
    """Get specific control by ID."""
    from ccm.catalog import get_control_by_id
    
    catalog = load_catalog()
    control = get_control_by_id(catalog, control_id)
    
    if not control:
        raise HTTPException(status_code=404, detail=f"Control {control_id} not found")
    
    return control.model_dump()


@app.get("/exceptions")
async def list_exceptions(
    show_expired: bool = Query(False, description="Include expired exceptions"),
):
    """List risk exceptions."""
    exceptions_file = Path.cwd() / "exceptions.json"
    manager = ExceptionManager(exceptions_file)
    
    if show_expired:
        exceptions = manager.list_all()
    else:
        exceptions = manager.list_valid()
    
    return {
        "exceptions": [e.model_dump(mode="json") for e in exceptions],
        "count": len(exceptions),
    }


@app.post("/exceptions")
async def create_exception(request: ExceptionRequest):
    """Create a risk exception."""
    exceptions_file = Path.cwd() / "exceptions.json"
    manager = ExceptionManager(exceptions_file)
    
    try:
        expiry_date = datetime.strptime(request.expiry_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid expiry_date format. Use YYYY-MM-DD"
        )
    
    exception = manager.add_exception(
        control_id=request.control_id,
        reason=request.reason,
        compensating_control=request.compensating_control,
        expiry_date=expiry_date,
        approver=request.approver,
    )
    
    return exception.model_dump(mode="json")


@app.get("/latest-evidence")
async def get_latest_evidence():
    """Get latest scan evidence if available."""
    evidence_file = Path.cwd() / "evidence.json"
    
    if not evidence_file.exists():
        return {"message": "No evidence file found. Run a scan first."}
    
    with open(evidence_file, "r") as f:
        data = json.load(f)
    
    return data


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
