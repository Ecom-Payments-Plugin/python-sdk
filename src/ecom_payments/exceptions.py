from __future__ import annotations

from typing import Any, Optional


class EcomAPIError(RuntimeError):
    """An unsuccessful or malformed response from Ecom."""

    def __init__(
        self,
        status: int,
        body: Any,
        api_error: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        super().__init__(message or f"Ecom API request failed with status {status}")
        self.status = status
        self.body = body
        self.api_error = api_error
