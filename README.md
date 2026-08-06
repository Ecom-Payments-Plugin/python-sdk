# Ecom Payments Python SDK

Python SDK for E_API charges, E_LINKS invoices, refunds, and webhook signature
verification. It requires Python 3.10 or newer and has no runtime dependencies.

## Installation

```bash
pip install ecom-payments-sdk
```

## Configure

```python
import os
from ecom_payments import Ecom

ecom = Ecom(
    api_token=os.environ["ECOM_API_TOKEN"],
    merchant_id=os.environ["ECOM_MERCHANT_ID"],
    environment="sandbox",  # or "production"
    webhook_secret=os.environ.get("ECOM_WEBHOOK_SECRET"),
)
```

Keep the API token and webhook secret on the server. Do not expose them in
browser or mobile application code.

## E_API charges

```python
charge = ecom.e_api.create_charge({
    "amount": {"value": 10, "currency": "KWD"},
    "options": {"mode": "INDIRECT"},
    "urls": {
        "successUrl": "https://example.com/payment/success",
        "errorUrl": "https://example.com/payment/error",
    },
    "references": {"merchantReference": "order-123"},
    "customer": {"fullName": "Ali", "email": "ali@example.com"},
    "language": "en",
})

print(charge["paymentUrl"])

details = ecom.e_api.get_charge(charge["paymentToken"])
```

## E_LINKS invoices

```python
invoice = ecom.e_links.create_invoice({
    "amount": {"value": 25, "currency": "KWD"},
    "customer": {
        "fullName": "Ali",
        "phoneCode": "+965",
        "phoneNumber": "66778899",
    },
    "notification": {"email": True, "sms": True},
    "language": "en",
})

invoices = ecom.e_links.list_invoices({
    "page": 1,
    "take": 10,
    "order": "DESC",
})

invoice = ecom.e_links.get_invoice(invoice_id)
invoice = ecom.e_links.get_invoice_by_payment_token(payment_token)
ecom.e_links.send_invoice_reminder(invoice_id, {"email": True})
ecom.e_links.mark_invoice_as_paid(invoice_id, {"paymentMethod": "CASH"})
ecom.e_links.delete_invoice(invoice_id)
```

## Refunds

```python
refund = ecom.refunds.create_refund({
    "amount": 5,
    "ecomId": details["id"],
    "merchantReference": "refund-order-123",
})

refunds = ecom.refunds.list_refunds({"page": 1, "take": 10})
refund = ecom.refunds.get_refund(refund["id"])
```

## Webhooks

Verify the event's `data` object against the `X-Webhook-Signature` header before
processing it:

```python
def handle_webhook(event: dict, signature: str) -> None:
    if not ecom.webhooks.verify_signature(event["data"], signature):
        raise ValueError("Invalid Ecom webhook signature")

    if event["eventType"] == "TRANSACTION_STATUS_CHANGED":
        print(event["data"]["paymentStatus"])
    elif event["eventType"] == "REFUND_STATUS_CHANGED":
        print(event["data"]["status"])
```

## Errors

```python
from ecom_payments import EcomAPIError

try:
    charge = ecom.e_api.get_charge(payment_token)
except EcomAPIError as error:
    print(error.status, error.api_error, error.body)
```

`EcomAPIError` is raised for HTTP errors, connection failures, invalid JSON, and
successful responses that do not contain the documented `data` field.

## Development

```bash
python -m pip install --editable .
python -m unittest discover -s tests -v
python -m build
```
