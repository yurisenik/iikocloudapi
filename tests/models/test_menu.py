import asyncio

import orjson
from httpx import Response

from iikocloudapi.modules.menu import (
    ComboCalculateResponse,
    ComboResponse,
    Compound,
    CompoundOrderItemComponent,
    Menu,
    MenuByIdResponse,
    MenuResponse,
    Product,
    StopListsCheckResponse,
    StopListsResponse,
)

menu_json = """{
  "correlationId": "48fb4cd3-2ef6-4479-bea1-7c92721b988c",
  "externalMenus": [
    {
      "id": "string",
      "name": "string"
    }
  ],
  "priceCategories": [
    {
      "id": "string",
      "name": "string"
    }
  ]
}"""


menu_by_id_json = """{
  "id": 0,
  "name": "string",
  "description": "string",
  "itemCategories": [
    {
      "items": [
        {
          "itemSizes": [
            {
              "prices": [
                {
                  "organizationId": "string",
                  "price": 20.5
                }
              ],
              "itemModifierGroups": [
                {
                  "items": [
                    {
                      "prices": [
                        {
                          "organizationId": "string",
                          "price": 20.5
                        }
                      ],
                      "sku": "string",
                      "name": "string",
                      "description": "string",
                      "buttonImage": "string",
                      "restrictions": {
                        "minQuantity": 0,
                        "maxQuantity": 0,
                        "freeQuantity": 0,
                        "byDefault": 0
                      },
                      "allergenGroups": [
                        {
                          "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
                          "code": "string",
                          "name": "string"
                        }
                      ],
                      "nutritionPerHundredGrams": {},
                      "portionWeightGrams": 0,
                      "tags": [
                        {
                          "id": "string",
                          "name": "string"
                        }
                      ],
                      "itemId": "f11b669d-7201-4c21-88af-d85092f0c005"
                    }
                  ],
                  "name": "string",
                  "description": "string",
                  "restrictions": {
                    "minQuantity": 0,
                    "maxQuantity": 0,
                    "freeQuantity": 0,
                    "byDefault": 0
                  },
                  "canBeDivided": true,
                  "itemGroupId": "dafef977-3bc5-4162-979f-d665700eac84",
                  "childModifiersHaveMinMaxRestrictions": true,
                  "sku": "string"
                }
              ],
              "sku": "string",
              "sizeCode": "string",
              "sizeName": "string",
              "isDefault": true,
              "portionWeightGrams": 0,
              "sizeId": "f98600f7-1d0f-4a64-936e-93e133055658",
              "nutritionPerHundredGrams": {},
              "buttonImageUrl": "https://102922.selcdn.ru/ecomm/someimage.png",
              "buttonImageCroppedUrl": [
                "https://102922.selcdn.ru/ecomm/someimage.png"
              ]
            }
          ],
          "sku": "002345-35cm",
          "name": "Chicken Parmegiano",
          "description": "Delicate taste, juicy chicken fillet, mushrooms, Cheddar cheese and Mozzarella cheese, oregano, Parmegiano sauce",
          "allergenGroups": [
            {
              "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
              "code": "string",
              "name": "string"
            }
          ],
          "itemId": "f11b669d-7201-4c21-88af-d85092f0c005",
          "modifierSchemaId": "51a77930-ad82-4138-b68f-0d444ed97b5f",
          "taxCategory": {
            "id": "string",
            "name": "string",
            "percentage": 0
          },
          "orderItemType": "Product"
        }
      ],
      "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
      "name": "string",
      "description": "string",
      "buttonImageUrl": "https://102922.selcdn.ru/ecomm/someimage.png",
      "headerImageUrl": "string"
    }
  ]
}"""


stop_lists_json = """{
  "correlationId": "48fb4cd3-2ef6-4479-bea1-7c92721b988c",
  "terminalGroupStopLists": [
    {
      "organizationId": "7bc05553-4b68-44e8-b7bc-37be63c6d9e9",
      "items": [
        {
          "terminalGroupId": "4fab19a5-203c-4bf5-94eb-f572aa8b117b",
          "items": [
            {
              "balance": 0,
              "productId": "dcd53ddb-8104-4e48-8cc0-5df1088c6113",
              "sizeId": null,
              "sku": "string",
              "dateAdd": "2019-08-24 14:15:22.123"
            }
          ]
        }
      ]
    }
  ]
}"""

stop_lists_check_json = """{
  "correlationId": "48fb4cd3-2ef6-4479-bea1-7c92721b988c",
  "rejectedItems": [
    {
      "balance": 0,
      "productId": "dcd53ddb-8104-4e48-8cc0-5df1088c6113",
      "sizeId": null,
      "sku": "string",
      "dateAdd": "2019-08-24 14:15:22.123"
    }
  ]
}"""

combo_json = """{
  "comboSpecifications": [
    {
      "sourceActionId": "dbec69f1-f4e2-424c-ada3-e033c731a538",
      "categoryId": "337f5e5d-288b-40d5-be14-901cc3acacc0",
      "name": "string",
      "priceModificationType": 0,
      "priceModification": 0,
      "isActive": true,
      "startDate": "2019-08-24 14:15:22.123",
      "expirationDate": "2019-08-24 14:15:22.123",
      "lackingGroupsToSuggest": 0,
      "includeModifiers": true,
      "groups": [
        {
          "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
          "name": "string",
          "isMainGroup": true,
          "products": [
            {
              "productId": "dcd53ddb-8104-4e48-8cc0-5df1088c6113",
              "sizeName": "string",
              "sizeId": "f98600f7-1d0f-4a64-936e-93e133055658",
              "forbiddenModifiers": [
                "497f6eca-6276-4993-bfeb-53cbbbba6f08"
              ],
              "priceModificationAmount": 0
            }
          ]
        }
      ]
    }
  ],
  "comboCategories": [
    {
      "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
      "name": "string"
    }
  ],
  "Warnings": [
    {
      "Code": "string",
      "ErrorCode": "string",
      "Message": "string"
    }
  ]
}"""


combo_calculate_json = """{
  "price": 0,
  "incorrectlyFilledGroups": [
    "497f6eca-6276-4993-bfeb-53cbbbba6f08"
  ]
}"""


def test_menu_response():
    MenuResponse(**orjson.loads(menu_json))


def test_menu_by_id_response():
    MenuByIdResponse(**orjson.loads(menu_by_id_json))


def test_stop_lists_response():
    StopListsResponse(**orjson.loads(stop_lists_json))


def test_stop_lists_check_response():
    StopListsCheckResponse(**orjson.loads(stop_lists_check_json))


def test_stop_lists_check_response_allows_omitted_rejected_items():
    response = StopListsCheckResponse(correlationId="correlation-id")
    assert response.rejected_items is None


def test_stop_lists_check_rejected_item_allows_omitted_size():
    response = StopListsCheckResponse.model_validate(
        {
            "correlationId": "correlation-id",
            "rejectedItems": [{"productId": "product-id", "balance": 0}],
        }
    )
    assert response.rejected_items is not None
    assert response.rejected_items[0].size_id is None


def test_stop_lists_check_product_uses_wire_aliases():
    item = Product.model_validate(
        {
            "productId": "product-id",
            "productSizeId": "size-id",
            "amount": 2,
            "price": 199.5,
        }
    )
    assert item.model_dump(by_alias=True, exclude_none=True) == {
        "type": "Product",
        "amount": 2.0,
        "productSizeId": "size-id",
        "productId": "product-id",
        "price": 199.5,
    }


def test_stop_lists_check_compound_uses_wire_aliases():
    item = Compound.model_validate(
        {
            "amount": 1,
            "productSizeId": "size-id",
            "primaryComponent": CompoundOrderItemComponent.model_validate({"productId": "primary-id", "price": 250}),
        }
    )
    assert item.model_dump(by_alias=True, exclude_none=True) == {
        "type": "Compound",
        "amount": 1.0,
        "productSizeId": "size-id",
        "primaryComponent": {"productId": "primary-id", "price": 250.0},
    }


class RecordingClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def request(self, path: str, data: dict, timeout=None) -> Response:
        self.calls.append({"path": path, "data": data, "timeout": timeout})
        return Response(200, content=orjson.dumps({"correlationId": "c", "rejectedItems": []}))


def test_stop_lists_check_calls_expected_endpoint_with_wire_payload():
    client = RecordingClient()
    response = asyncio.run(
        Menu(client).stop_lists_check(  # type: ignore[arg-type]
            organization_id="organization-id",
            terminal_group_id="terminal-group-id",
            items=[
                Product.model_validate(
                    {
                        "productId": "product-id",
                        "productSizeId": "size-id",
                        "amount": 2,
                        "price": 199.5,
                    }
                )
            ],
            timeout=20,
        )
    )

    assert response.rejected_items == []
    assert client.calls == [
        {
            "path": "/api/1/stop_lists/check",
            "data": {
                "organizationId": "organization-id",
                "terminalGroupId": "terminal-group-id",
                "items": [
                    {
                        "type": "Product",
                        "amount": 2.0,
                        "productSizeId": "size-id",
                        "productId": "product-id",
                        "price": 199.5,
                    }
                ],
            },
            "timeout": 20,
        }
    ]


def test_combo_response():
    ComboResponse(**orjson.loads(combo_json))


def test_combo_calculate_response():
    ComboCalculateResponse(**orjson.loads(combo_calculate_json))
