import hashlib
import hmac
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from ecom_payments import Ecom, EcomAPIError


class Response:
    def __init__(self, body=None, status=200):
        self.status = status
        self._body = json.dumps(body).encode() if body is not None else b""

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class SDKTest(unittest.TestCase):
    def setUp(self):
        self.ecom = Ecom(
            api_token="pk_test_123",
            merchant_id="123456",
            environment="sandbox",
            webhook_secret="secret",
        )

    @patch("urllib.request.urlopen")
    def test_products_send_expected_requests(self, urlopen):
        urlopen.return_value = Response({"data": {"id": "ok"}})

        result = self.ecom.e_api.create_charge(
            {"amount": {"value": 10, "currency": "KWD"}, "options": {"mode": "INDIRECT"}}
        )
        self.ecom.e_api.get_charge("token/one")
        self.ecom.e_links.create_invoice({"language": "en"})
        self.ecom.e_links.list_invoices({"page": 2, "take": 25, "order": "ASC"})
        self.ecom.e_links.get_invoice("invoice/one")
        self.ecom.e_links.get_invoice_by_payment_token("payment/one")
        self.ecom.e_links.delete_invoice("invoice/one")
        self.ecom.e_links.send_invoice_reminder("invoice/one", {"sms": True})
        self.ecom.e_links.mark_invoice_as_paid("invoice/one", {"paymentMethod": "CASH"})
        self.ecom.refunds.create_refund({"amount": 5, "ecomId": "ecom-1"})
        self.ecom.refunds.list_refunds({"page": 1})
        self.ecom.refunds.get_refund("refund/one")

        self.assertEqual(result, {"id": "ok"})
        requests = [call.args[0] for call in urlopen.call_args_list]
        self.assertEqual(requests[0].full_url, "https://api-sandbox.ecom.io/eapi/v1/api/charges")
        self.assertEqual(requests[0].method, "POST")
        self.assertEqual(json.loads(requests[0].data), {
            "amount": {"value": 10, "currency": "KWD"}, "options": {"mode": "INDIRECT"}
        })
        self.assertEqual(requests[1].full_url, "https://api-sandbox.ecom.io/eapi/v1/api/charges/token%2Fone")
        self.assertEqual(requests[3].full_url, "https://api-sandbox.ecom.io/elinks/v1/api/invoices?page=2&take=25&order=ASC")
        self.assertEqual(requests[11].full_url, "https://api-sandbox.ecom.io/transaction/v1/api/refunds/refund%2Fone")
        self.assertEqual(requests[0].get_header("X-ecom-api-token"), "pk_test_123")
        self.assertEqual(requests[0].get_header("X-ecom-mid"), "123456")

    @patch("urllib.request.urlopen")
    def test_production_and_api_error(self, urlopen):
        error = urllib.error.HTTPError(
            "https://api-live.ecom.io/eapi/v1/api/charges/token",
            401,
            "Unauthorized",
            {},
            io.BytesIO(json.dumps({"error": "UNAUTHORIZED", "message": ["Invalid token"]}).encode()),
        )
        urlopen.side_effect = error
        client = Ecom(api_token="x", merchant_id="y", environment="production")

        with self.assertRaises(EcomAPIError) as caught:
            client.e_api.get_charge("token")

        self.assertEqual(caught.exception.status, 401)
        self.assertEqual(caught.exception.api_error, "UNAUTHORIZED")
        self.assertEqual(str(caught.exception), "Invalid token")
        self.assertEqual(urlopen.call_args.args[0].full_url, "https://api-live.ecom.io/eapi/v1/api/charges/token")

    def test_webhook_signatures(self):
        data = {
            "paymentStatus": "CAPTURED",
            "amount": "10.000",
            "ignored": None,
            "ecomId": "123",
        }
        expected = hmac.new(
            b"secret",
            b"amount=10.000&ecomId=123&paymentStatus=CAPTURED",
            hashlib.sha256,
        ).hexdigest()

        self.assertEqual(self.ecom.webhooks.generate_signature(data), expected)
        self.assertTrue(self.ecom.webhooks.verify_signature(data, expected))
        self.assertFalse(self.ecom.webhooks.verify_signature(data, "invalid"))

    def test_configuration_validation(self):
        with self.assertRaises(ValueError):
            Ecom(api_token="", merchant_id="123")
        with self.assertRaises(ValueError):
            Ecom(api_token="x", merchant_id="y", environment="other")


if __name__ == "__main__":
    unittest.main()
