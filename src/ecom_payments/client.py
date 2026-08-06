from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Mapping, Optional

from .exceptions import EcomAPIError
from .types import ChargeRequest, Environment, Pagination, RefundRequest
from .webhooks import Webhooks

_HOSTS = {
    "sandbox": "https://api-sandbox.ecom.io",
    "production": "https://api-live.ecom.io",
}


class _HTTPClient:
    def __init__(
        self, api_token: str, merchant_id: str, environment: Environment
    ) -> None:
        self._api_token = api_token
        self._merchant_id = merchant_id
        self._host = _HOSTS[environment]

    def request(
        self,
        method: str,
        service: str,
        path: str,
        body: Optional[Mapping[str, Any]] = None,
        query: Optional[Mapping[str, Any]] = None,
        unwrap: bool = True,
    ) -> Any:
        url = f"{self._host}/{service}{path}"
        if query:
            values = {key: value for key, value in query.items() if value is not None}
            if values:
                url = f"{url}?{urllib.parse.urlencode(values)}"
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "X-Ecom-Api-Token": self._api_token,
                "X-Ecom-Mid": self._merchant_id,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
                raw = response.read().decode()
        except urllib.error.HTTPError as error:
            status = error.code
            raw = error.read().decode(errors="replace")
        except urllib.error.URLError as error:
            raise EcomAPIError(0, str(error.reason), message=f"Ecom connection failed: {error.reason}") from error

        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError as error:
            raise EcomAPIError(status, raw, message="Ecom API returned invalid JSON") from error
        if not 200 <= status < 300:
            message = parsed.get("message") if isinstance(parsed, dict) else None
            if isinstance(message, list):
                message = ", ".join(map(str, message))
            raise EcomAPIError(
                status,
                parsed if parsed is not None else raw,
                str(parsed["error"]) if isinstance(parsed, dict) and "error" in parsed else None,
                message,
            )
        if not unwrap:
            return None
        if not isinstance(parsed, dict) or "data" not in parsed:
            raise EcomAPIError(status, parsed, message="Ecom API response is missing data")
        return parsed["data"]


class EAPI:
    def __init__(self, http: _HTTPClient) -> None:
        self._http = http

    def create_charge(self, request: ChargeRequest) -> Dict[str, Any]:
        return self._http.request("POST", "eapi", "/v1/api/charges", request)

    def get_charge(self, payment_token: str) -> Dict[str, Any]:
        return self._http.request(
            "GET", "eapi", f"/v1/api/charges/{urllib.parse.quote(payment_token, safe='')}"
        )


class ELinks:
    def __init__(self, http: _HTTPClient) -> None:
        self._http = http

    def create_invoice(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        return self._http.request("POST", "elinks", "/v1/api/invoices", request)

    def list_invoices(self, query: Optional[Pagination] = None) -> Dict[str, Any]:
        return self._http.request("GET", "elinks", "/v1/api/invoices", query=query)

    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        return self._http.request("GET", "elinks", f"/v1/api/invoices/{urllib.parse.quote(invoice_id, safe='')}")

    def get_invoice_by_payment_token(self, payment_token: str) -> Dict[str, Any]:
        return self._http.request("GET", "elinks", f"/v1/api/invoices/payment-token/{urllib.parse.quote(payment_token, safe='')}")

    def delete_invoice(self, invoice_id: str) -> None:
        self._http.request("DELETE", "elinks", f"/v1/api/invoices/{urllib.parse.quote(invoice_id, safe='')}", unwrap=False)

    def send_invoice_reminder(self, invoice_id: str, request: Mapping[str, Any]) -> None:
        self._http.request("POST", "elinks", f"/v1/api/invoices/{urllib.parse.quote(invoice_id, safe='')}/reminder", request, unwrap=False)

    def mark_invoice_as_paid(self, invoice_id: str, request: Mapping[str, Any]) -> None:
        self._http.request("PATCH", "elinks", f"/v1/api/invoices/{urllib.parse.quote(invoice_id, safe='')}/mark-as-paid", request, unwrap=False)


class Refunds:
    def __init__(self, http: _HTTPClient) -> None:
        self._http = http

    def create_refund(self, request: RefundRequest) -> Dict[str, Any]:
        return self._http.request("POST", "transaction", "/v1/api/refunds", request)

    def list_refunds(self, query: Optional[Pagination] = None) -> Dict[str, Any]:
        return self._http.request("GET", "transaction", "/v1/api/refunds", query=query)

    def get_refund(self, refund_id: str) -> Dict[str, Any]:
        return self._http.request("GET", "transaction", f"/v1/api/refunds/{urllib.parse.quote(refund_id, safe='')}")


class Ecom:
    def __init__(
        self,
        *,
        api_token: str,
        merchant_id: str,
        environment: Environment = "sandbox",
        webhook_secret: Optional[str] = None,
    ) -> None:
        if not api_token or not merchant_id:
            raise ValueError("api_token and merchant_id are required")
        if environment not in _HOSTS:
            raise ValueError("environment must be sandbox or production")
        http = _HTTPClient(api_token, merchant_id, environment)
        self.e_api = EAPI(http)
        self.e_links = ELinks(http)
        self.refunds = Refunds(http)
        self.webhooks = Webhooks(webhook_secret)
