"""Exception management for control failures."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ccm.models import Exception as ControlException


class ExceptionManager:
    """Manage risk exceptions for control failures."""

    def __init__(self, exceptions_file: str = "exceptions.json"):
        self.exceptions_file = Path(exceptions_file)
        self.exceptions: dict[str, ControlException] = {}
        self._load_exceptions()

    def _load_exceptions(self) -> None:
        """Load exceptions from file."""
        if self.exceptions_file.exists():
            with open(self.exceptions_file) as f:
                content = f.read().strip()
                if not content:
                    return
                data = json.loads(content)
                for exc_data in data:
                    exc = ControlException(**exc_data)
                    self.exceptions[exc.id] = exc

    def _save_exceptions(self) -> None:
        """Save exceptions to file."""
        self.exceptions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.exceptions_file, "w") as f:
            data = [exc.model_dump(mode="json") for exc in self.exceptions.values()]
            json.dump(data, f, indent=2)

    def add_exception(
        self,
        control_id: str,
        reason: str,
        compensating_control: str,
        expiry_date: datetime,
        approver: str,
    ) -> ControlException:
        """Add a new exception."""
        exc_id = str(uuid.uuid4())[:8]
        exception = ControlException(
            id=exc_id,
            control_id=control_id,
            reason=reason,
            compensating_control=compensating_control,
            expiry_date=expiry_date,
            approver=approver,
        )
        self.exceptions[exc_id] = exception
        self._save_exceptions()
        return exception

    def get_exception_for_control(self, control_id: str) -> Optional[ControlException]:
        """Get valid exception for a control, if one exists."""
        for exception in self.exceptions.values():
            if exception.control_id == control_id and exception.is_valid():
                return exception
        return None

    def list_exceptions(
        self, control_id: Optional[str] = None, include_expired: bool = False
    ) -> list[ControlException]:
        """List all exceptions, optionally filtered."""
        results = list(self.exceptions.values())

        if control_id:
            results = [e for e in results if e.control_id == control_id]

        if not include_expired:
            results = [e for e in results if not e.is_expired()]

        return sorted(results, key=lambda e: e.created_date, reverse=True)

    def deactivate_exception(self, exception_id: str) -> bool:
        """Deactivate an exception."""
        if exception_id in self.exceptions:
            self.exceptions[exception_id].is_active = False
            self._save_exceptions()
            return True
        return False

    def get_expired_exceptions(self) -> list[ControlException]:
        """Get all expired but still active exceptions."""
        return [e for e in self.exceptions.values() if e.is_expired() and e.is_active]
