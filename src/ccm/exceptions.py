"""Risk exception management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from ccm.models import RiskException


class ExceptionManager:
    """Manage risk acceptance exceptions."""

    def __init__(self, exceptions_file: Path):
        """Initialize exception manager.
        
        Args:
            exceptions_file: Path to exceptions JSON file
        """
        self.exceptions_file = exceptions_file
        self._exceptions: dict[str, RiskException] = {}
        self._load()

    def _load(self) -> None:
        """Load exceptions from file."""
        if self.exceptions_file.exists():
            try:
                with open(self.exceptions_file, "r") as f:
                    content = f.read().strip()
                    if not content:
                        self._exceptions = {}
                        return
                    data = json.loads(content)
                    self._exceptions = {}
                    for exc_id, exc_data in data.items():
                        if isinstance(exc_data.get("expiry_date"), str):
                            exc_data["expiry_date"] = datetime.fromisoformat(
                                exc_data["expiry_date"].replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                        if isinstance(exc_data.get("created_at"), str):
                            exc_data["created_at"] = datetime.fromisoformat(
                                exc_data["created_at"].replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                        self._exceptions[exc_id] = RiskException(**exc_data)
            except (json.JSONDecodeError, ValueError):
                self._exceptions = {}

    def _save(self) -> None:
        """Save exceptions to file."""
        self.exceptions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.exceptions_file, "w") as f:
            data = {
                exc_id: exc.model_dump(mode="json")
                for exc_id, exc in self._exceptions.items()
            }
            json.dump(data, f, indent=2, default=str)

    def add_exception(
        self,
        control_id: str,
        reason: str,
        compensating_control: str,
        expiry_date: datetime,
        approver: str,
    ) -> RiskException:
        """Add a new risk exception.
        
        Args:
            control_id: Control identifier
            reason: Reason for exception
            compensating_control: Description of compensating control
            expiry_date: When exception expires
            approver: Who approved the exception
            
        Returns:
            Created exception
        """
        exception_id = str(uuid4())
        exception = RiskException(
            id=exception_id,
            control_id=control_id,
            reason=reason,
            compensating_control=compensating_control,
            expiry_date=expiry_date,
            approver=approver,
        )
        self._exceptions[exception_id] = exception
        self._save()
        return exception

    def get_exception(self, exception_id: str) -> Optional[RiskException]:
        """Get exception by ID.
        
        Args:
            exception_id: Exception identifier
            
        Returns:
            Exception if found, None otherwise
        """
        return self._exceptions.get(exception_id)

    def get_exceptions_for_control(self, control_id: str) -> list[RiskException]:
        """Get all exceptions for a control.
        
        Args:
            control_id: Control identifier
            
        Returns:
            List of exceptions for the control
        """
        return [
            exc for exc in self._exceptions.values()
            if exc.control_id == control_id
        ]

    def get_valid_exception_for_control(self, control_id: str) -> Optional[RiskException]:
        """Get valid (non-expired) exception for a control.
        
        Args:
            control_id: Control identifier
            
        Returns:
            Valid exception if found, None otherwise
        """
        exceptions = self.get_exceptions_for_control(control_id)
        for exc in exceptions:
            if exc.is_valid():
                return exc
        return None

    def list_all(self) -> list[RiskException]:
        """List all exceptions.
        
        Returns:
            List of all exceptions
        """
        return list(self._exceptions.values())

    def list_expired(self) -> list[RiskException]:
        """List expired exceptions.
        
        Returns:
            List of expired exceptions
        """
        return [exc for exc in self._exceptions.values() if exc.is_expired()]

    def list_valid(self) -> list[RiskException]:
        """List valid (non-expired) exceptions.
        
        Returns:
            List of valid exceptions
        """
        return [exc for exc in self._exceptions.values() if exc.is_valid()]
