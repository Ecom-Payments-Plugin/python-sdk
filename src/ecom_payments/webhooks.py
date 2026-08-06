from __future__ import annotations

import hashlib
import hmac
from typing import Any, Mapping, Optional


class Webhooks:
    def __init__(self, secret: Optional[str] = None) -> None:
        self._secret = secret

    def generate_signature(
        self, data: Mapping[str, Any], secret: Optional[str] = None
    ) -> str:
        key = secret or self._secret
        if not key:
            raise ValueError("webhook secret is required")
        payload = "&".join(
            f"{name}={self._value(value)}"
            for name, value in sorted(data.items(), key=lambda item: item[0].lower())
            if value is not None
        )
        return hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def verify_signature(
        self,
        data: Mapping[str, Any],
        signature: str,
        secret: Optional[str] = None,
    ) -> bool:
        if len(signature) != 64:
            return False
        try:
            bytes.fromhex(signature)
        except ValueError:
            return False
        return hmac.compare_digest(
            self.generate_signature(data, secret), signature.lower()
        )

    @staticmethod
    def _value(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)
