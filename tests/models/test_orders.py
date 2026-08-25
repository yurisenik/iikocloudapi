import asyncio

import orjson
import pytest
from httpx import Response

from iikocloudapi.modules.orders import (
    OrderAddItemsBody,
    OrderByIdBody,
    OrderByTableBody,
    OrderChangePaymentsBody,
    OrderCloseBody,
    OrderCloseResponse,
    OrderCreateBody,
    OrderCreateResponse,
    OrderPaymentAdditionalData,
    OrderPaymentItem,
    OrderQueryResponse,
    Orders,
)

order_create_response_json = """{
  "correlationId": "11111111-2222-3333-4444-555555555555",
  "orderInfo": {
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "externalNumber": "42",
    "organizationId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": 1700000000,
    "creationStatus": "Success",
    "errorInfo": null,
    "order": {
      "tableIds": ["770e8400-e29b-41d4-a716-446655440099"],
      "customer": null,
      "phone": "",
      "status": "New",
      "sum": 199.5,
      "number": 7,
      "items": [],
      "terminalGroupId": "660e8400-e29b-41d4-a716-446655440001",
      "comment": null
    }
  }
}"""


def test_order_create_response_parses():
    parsed = OrderCreateResponse(**orjson.loads(order_create_response_json))
    assert parsed.correlation_id == "11111111-2222-3333-4444-555555555555"
    assert parsed.order_info.id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert parsed.order_info.creation_status == "Success"
    assert parsed.order_info.order["sum"] == 199.5
    assert parsed.order_info.order["number"] == 7


def test_order_create_body_serializes_and_keeps_extra_on_order():
    body = OrderCreateBody.model_validate(
        {
            "organizationId": "550e8400-e29b-41d4-a716-446655440000",
            "terminalGroupId": "660e8400-e29b-41d4-a716-446655440001",
            "order": {
                "tableIds": ["770e8400-e29b-41d4-a716-446655440099"],
                "items": [
                    {"productId": "880e8400-e29b-41d4-a716-446655440012", "amount": 2},
                    {
                        "productId": "990e8400-e29b-41d4-a716-446655440013",
                        "amount": 1,
                        "type": "Product",
                        "modifiers": [{"productId": "aa0e8400-e29b-41d4-a716-446655440014", "amount": 1}],
                    },
                ],
                "guestsInfo": {"count": 1, "splitBetweenPersons": False},
                "guests": {"count": 2},
            },
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert dumped["organizationId"] == "550e8400-e29b-41d4-a716-446655440000"
    assert dumped["terminalGroupId"] == "660e8400-e29b-41d4-a716-446655440001"
    assert dumped["order"]["tableIds"] == ["770e8400-e29b-41d4-a716-446655440099"]
    assert dumped["order"]["guestsInfo"]["count"] == 1
    assert dumped["order"]["guestsInfo"]["splitBetweenPersons"] is False
    assert dumped["order"]["guests"]["count"] == 2
    assert len(dumped["order"]["items"]) == 2
    assert dumped["order"]["items"][1]["modifiers"][0]["productId"] == "aa0e8400-e29b-41d4-a716-446655440014"


def test_order_create_item_optional_type_omitted_from_payload_when_none():
    body = OrderCreateBody.model_validate(
        {
            "organizationId": "org",
            "terminalGroupId": "tg",
            "order": {"items": [{"productId": "pid", "amount": 1.0}]},
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert "type" not in dumped["order"]["items"][0]


def test_order_create_with_external_payment_pay_first():
    """Pay-first flow: order arrives already paid via external acquiring (e.g. T-Bank)."""
    body = OrderCreateBody.model_validate(
        {
            "organizationId": "org",
            "terminalGroupId": "tg",
            "order": {
                "tableIds": ["table-uuid"],
                "items": [{"productId": "pid", "amount": 1, "type": "Product"}],
                "payments": [
                    {
                        "paymentTypeKind": "External",
                        "sum": 199.5,
                        "paymentTypeId": "external-payment-type-uuid",
                        "isProcessedExternally": True,
                        "paymentAdditionalData": {
                            "type": "External",
                            "customData": "provider-payment-reference-123",
                        },
                        "isFiscalizedExternally": False,
                    }
                ],
            },
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    payment = dumped["order"]["payments"][0]
    assert payment["paymentTypeKind"] == "External"
    assert payment["isProcessedExternally"] is True
    assert payment["paymentAdditionalData"] == {
        "type": "External",
        "customData": "provider-payment-reference-123",
    }
    assert payment["sum"] == 199.5


def test_external_payment_additional_data_requires_openapi_custom_data():
    with pytest.raises(ValueError, match="customData is required"):
        OrderPaymentAdditionalData.model_validate({"type": "External"})


def test_external_payment_additional_data_rejects_legacy_credentials():
    with pytest.raises(ValueError, match="credentials"):
        OrderPaymentAdditionalData.model_validate(
            {
                "type": "External",
                "customData": "provider-reference",
                "credentials": "legacy-invalid-field",
            }
        )


def test_payment_type_kind_matches_openapi_discriminator():
    payment = OrderPaymentItem.model_validate(
        {
            "paymentTypeKind": "LoyaltyCard",
            "sum": 10,
            "paymentTypeId": "loyalty-payment-type",
        }
    )
    assert payment.payment_type_kind == "LoyaltyCard"

    with pytest.raises(ValueError, match="paymentTypeKind"):
        OrderPaymentItem.model_validate(
            {
                "paymentTypeKind": "IikoCard",
                "sum": 10,
                "paymentTypeId": "legacy-payment-type",
            }
        )


def test_order_close_body_minimal():
    body = OrderCloseBody.model_validate({"organizationId": "org", "orderId": "ord"})
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert dumped == {"organizationId": "org", "orderId": "ord"}


def test_order_close_body_with_cheque_info():
    body = OrderCloseBody.model_validate(
        {
            "organizationId": "org",
            "orderId": "ord",
            "chequeAdditionalInfo": {"email": "guest@example.com"},
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert dumped["chequeAdditionalInfo"]["email"] == "guest@example.com"


def test_order_close_response_parses_minimal():
    parsed = OrderCloseResponse(**orjson.loads('{"correlationId": "corr-1"}'))
    assert parsed.correlation_id == "corr-1"


def test_order_change_payments_body_serializes_payments_list():
    body = OrderChangePaymentsBody.model_validate(
        {
            "organizationId": "org",
            "orderId": "ord",
            "payments": [
                {
                    "paymentTypeKind": "External",
                    "sum": 500.0,
                    "paymentTypeId": "ext-pt",
                    "isProcessedExternally": True,
                }
            ],
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert "revision" not in dumped
    assert dumped["payments"][0]["paymentTypeKind"] == "External"
    assert dumped["payments"][0]["isProcessedExternally"] is True
    assert dumped["payments"][0]["sum"] == 500.0


def test_order_change_payments_rejects_non_openapi_revision():
    with pytest.raises(ValueError, match="revision"):
        OrderChangePaymentsBody.model_validate(
            {
                "organizationId": "org",
                "orderId": "ord",
                "revision": 12,
                "payments": [],
            }
        )


def test_order_add_items_body_round_trips_items():
    body = OrderAddItemsBody.model_validate(
        {
            "organizationId": "org",
            "orderId": "ord",
            "items": [{"productId": "pid", "amount": 2, "price": 99.5, "type": "Product"}],
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert dumped["items"][0]["productId"] == "pid"
    assert dumped["items"][0]["amount"] == 2
    assert dumped["items"][0]["type"] == "Product"


def test_order_add_items_body_accepts_openapi_compound_item_without_product_id():
    body = OrderAddItemsBody.model_validate(
        {
            "organizationId": "org",
            "orderId": "ord",
            "items": [
                {
                    "type": "Compound",
                    "amount": 1,
                    "primaryComponent": {
                        "productId": "primary-product",
                        "price": 120,
                        "modifiers": [{"productId": "modifier", "amount": 1}],
                    },
                    "secondaryComponent": {"productId": "secondary-product"},
                }
            ],
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert dumped["items"][0] == {
        "type": "Compound",
        "amount": 1.0,
        "primaryComponent": {
            "productId": "primary-product",
            "modifiers": [{"productId": "modifier", "amount": 1.0}],
            "price": 120.0,
        },
        "secondaryComponent": {"productId": "secondary-product"},
    }


def test_order_by_id_body_serializes():
    body = OrderByIdBody.model_validate({"organizationIds": ["o1"], "orderIds": ["ord1", "ord2"]})
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert dumped == {"organizationIds": ["o1"], "orderIds": ["ord1", "ord2"]}


def test_order_by_id_body_accepts_pos_ids_and_external_data_keys():
    body = OrderByIdBody.model_validate(
        {
            "organizationIds": ["o1"],
            "posOrderIds": ["pos-1"],
            "returnExternalDataKeys": ["source-reference"],
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert dumped == {
        "organizationIds": ["o1"],
        "posOrderIds": ["pos-1"],
        "returnExternalDataKeys": ["source-reference"],
    }


@pytest.mark.parametrize(
    ("order_ids", "pos_order_ids"),
    [
        (None, None),
        (["order-1"], ["pos-1"]),
    ],
)
def test_order_by_id_body_requires_exactly_one_id_kind(order_ids, pos_order_ids):
    with pytest.raises(ValueError, match="exactly one"):
        OrderByIdBody.model_validate(
            {
                "organizationIds": ["o1"],
                "orderIds": order_ids,
                "posOrderIds": pos_order_ids,
            }
        )


def test_order_by_table_body_with_statuses_filter():
    body = OrderByTableBody.model_validate(
        {
            "organizationIds": ["o1"],
            "tableIds": ["t1"],
            "statuses": ["New", "Bill"],
        }
    )
    dumped = body.model_dump(by_alias=True, exclude_none=True)
    assert dumped["statuses"] == ["New", "Bill"]


def test_order_query_response_keeps_orders_as_dicts():
    payload = """{
      "correlationId": "c",
      "orders": [
        {"id": "ord-1", "status": "New", "sum": 100, "payments": []}
      ]
    }"""
    parsed = OrderQueryResponse(**orjson.loads(payload))
    assert parsed.orders[0]["id"] == "ord-1"
    assert parsed.orders[0]["status"] == "New"


class RecordingClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def request(self, path: str, data: dict, timeout=None) -> Response:
        self.calls.append({"path": path, "data": data, "timeout": timeout})
        return Response(200, content=orjson.dumps({"correlationId": "c", "orders": []}))


def test_orders_by_table_calls_expected_endpoint_with_wire_payload():
    client = RecordingClient()
    response = asyncio.run(
        Orders(client).by_table(  # type: ignore[arg-type]
            organization_ids=["organization-id"],
            table_ids=["table-id"],
            statuses=["New", "Bill"],
            date_from="2026-08-25 09:00:00.000",
            timeout=25,
        )
    )

    assert response.orders == []
    assert client.calls == [
        {
            "path": "/api/1/order/by_table",
            "data": {
                "organizationIds": ["organization-id"],
                "tableIds": ["table-id"],
                "statuses": ["New", "Bill"],
                "dateFrom": "2026-08-25 09:00:00.000",
            },
            "timeout": 25,
        }
    ]


def test_orders_by_id_calls_endpoint_with_pos_ids_and_external_keys():
    client = RecordingClient()
    response = asyncio.run(
        Orders(client).by_id(  # type: ignore[arg-type]
            organization_ids=["organization-id"],
            pos_order_ids=["pos-order-id"],
            return_external_data_keys=["source-reference"],
            timeout=30,
        )
    )

    assert response.orders == []
    assert client.calls == [
        {
            "path": "/api/1/order/by_id",
            "data": {
                "organizationIds": ["organization-id"],
                "posOrderIds": ["pos-order-id"],
                "returnExternalDataKeys": ["source-reference"],
            },
            "timeout": 30,
        }
    ]


def test_orders_add_items_calls_endpoint_with_compound_wire_payload():
    client = RecordingClient()
    response = asyncio.run(
        Orders(client).add_items(  # type: ignore[arg-type]
            organization_id="organization-id",
            order_id="order-id",
            items=[
                {
                    "type": "Compound",
                    "amount": 1,
                    "primaryComponent": {"productId": "primary-product", "price": 120},
                }
            ],
            timeout=35,
        )
    )

    assert response.correlation_id == "c"
    assert client.calls == [
        {
            "path": "/api/1/order/add_items",
            "data": {
                "organizationId": "organization-id",
                "orderId": "order-id",
                "items": [
                    {
                        "type": "Compound",
                        "amount": 1.0,
                        "primaryComponent": {"productId": "primary-product", "price": 120.0},
                    }
                ],
            },
            "timeout": 35,
        }
    ]
