"""Evidence storage and retrieval."""

import json
from datetime import datetime
from pathlib import Path

from ccm.models import Evidence


class EvidenceStore:
    """Store and retrieve evidence artifacts."""

    def __init__(self, evidence_dir: str = "evidence"):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def _get_evidence_path(self, control_id: str, timestamp: datetime) -> Path:
        """Generate evidence file path."""
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{control_id}_{ts_str}.evidence.json"
        return self.evidence_dir / filename

    def store_evidence(self, evidence: Evidence) -> Path:
        """Store evidence to disk and return file path."""
        file_path = self._get_evidence_path(evidence.control_id, evidence.timestamp)
        with open(file_path, "w") as f:
            json.dump(evidence.model_dump(mode="json"), f, indent=2)
        return file_path

    def store_batch(self, evidence_list: list[Evidence]) -> list[Path]:
        """Store multiple evidence artifacts."""
        return [self.store_evidence(e) for e in evidence_list]

    def get_latest_evidence(self, control_id: str) -> Evidence | None:
        """Get most recent evidence for a control."""
        pattern = f"{control_id}_*.evidence.json"
        files = sorted(self.evidence_dir.glob(pattern), reverse=True)

        if not files:
            return None

        with open(files[0]) as f:
            data = json.load(f)
            return Evidence(**data)

    def get_evidence_history(
        self, control_id: str, limit: int | None = None
    ) -> list[Evidence]:
        """Get evidence history for a control."""
        pattern = f"{control_id}_*.evidence.json"
        files = sorted(self.evidence_dir.glob(pattern), reverse=True)

        if limit:
            files = files[:limit]

        results = []
        for file_path in files:
            with open(file_path) as f:
                data = json.load(f)
                results.append(Evidence(**data))

        return results

    def export_evidence(self, output_file: str) -> Path:
        """Export all evidence to a single JSON file."""
        output_path = Path(output_file)
        all_evidence = []

        for file_path in sorted(self.evidence_dir.glob("*.evidence.json")):
            with open(file_path) as f:
                all_evidence.append(json.load(f))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(all_evidence, f, indent=2)

        return output_path
