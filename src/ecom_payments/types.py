from __future__ import annotations

from typing import Dict, List, Literal, TypedDict, Union

Environment = Literal["sandbox", "production"]
Language = Literal["en", "ar"]
SortOrder = Literal["ASC", "DESC"]
Product = Literal["E_API", "E_LINKS"]
PaymentStatus = Literal[
    "INITIATED", "CAPTURED", "TIMED_OUT", "HOST_TIMEOUT", "DECLINED",
    "FAILURE", "UNKNOWN", "CANCELED", "NOT_CAPTURED", "REFUNDED",
]


class Amount(TypedDict):
    value: Union[int, float]
    currency: Literal["KWD"]


class Customer(TypedDict, total=False):
    fullName: str
    phoneCode: str
    phoneNumber: str
    email: str


class _ChargeOptionsOptional(TypedDict, total=False):
    paymentMethod: Literal["KNET", "CREDIT_CARD", "APPLE_PAY"]
    templateId: str


class ChargeOptions(_ChargeOptionsOptional):
    mode: Literal["DIRECT", "INDIRECT"]


class _ChargeRequestOptional(TypedDict, total=False):
    urls: Dict[str, str]
    customer: Customer
    references: Dict[str, str]
    description: str
    order: Dict[str, object]
    language: Language
    metadata: Dict[str, str]
    vendors: List[Dict[str, Union[str, int, float]]]


class ChargeRequest(_ChargeRequestOptional):
    amount: Amount
    options: ChargeOptions


class Pagination(TypedDict, total=False):
    page: int
    take: int
    order: SortOrder


class _RefundRequestOptional(TypedDict, total=False):
    merchantReference: str
    description: str


class RefundRequest(_RefundRequestOptional):
    amount: Union[int, float]
    ecomId: str


class TransactionWebhookData(TypedDict, total=False):
    ecomId: str
    paymentStatus: PaymentStatus
    product: Product
    amount: Union[str, int, float]
    currency: str
    merchantReference: str
    ecomReference: str
    productPaymentToken: str
    paymentMethod: str


class RefundWebhookData(TypedDict):
    refundId: str
    status: Literal["REFUNDED", "REJECTED"]
    product: Product
    amount: Union[str, int, float]
    currency: str
    originalEcomId: str
