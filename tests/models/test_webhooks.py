import asyncio

import orjson
from httpx import Response

from iikocloudapi import iikoCloudApi
from iikocloudapi.modules.webhooks import (
    GetWebHookSettingsResponse,
    StopListUpdateWebhookEvent,
    Webhooks,
    WebHooksFilter,
)

TEST_AUTH_TOKEN = "redacted-test-token"


class RecordingClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    async def request(self, path: str, data: dict, timeout=None) -> Response:
        self.calls.append({"path": path, "data": data, "timeout": timeout})
        return Response(200, content=orjson.dumps(self.payload))


def test_iiko_cloud_api_exposes_webhooks_module():
    client = RecordingClient({"correlationId": "correlation-id"})
    api = iikoCloudApi(client)  # type: ignore[arg-type]
    assert isinstance(api.webhooks, Webhooks)


def test_get_settings_preserves_filters_and_auth_token():
    client = RecordingClient(
        {
            "correlationId": "correlation-id",
            "apiLoginName": "login-name",
            "webHooksUri": "https://example.invalid/iiko-webhook",
            "authToken": TEST_AUTH_TOKEN,
            "webHooksFilter": {
                "deliveryOrderFilter": {"orderStatuses": ["Closed"]},
                "stopListUpdateFilter": {"updates": True},
                "futureFilter": {"enabled": True},
            },
        }
    )

    response = asyncio.run(Webhooks(client).settings("organization-id", timeout=20))  # type: ignore[arg-type]

    assert isinstance(response, GetWebHookSettingsResponse)
    assert response.web_hooks_filter is not None
    assert response.web_hooks_filter.stop_list_update_filter is not None
    assert response.web_hooks_filter.stop_list_update_filter.updates is True
    assert response.web_hooks_filter.model_extra == {"futureFilter": {"enabled": True}}
    assert client.calls == [
        {
            "path": "/api/1/webhooks/settings",
            "data": {"organizationId": "organization-id"},
            "timeout": 20,
        }
    ]


def test_get_settings_accepts_empty_short_filter_from_openapi_readback():
    client = RecordingClient(
        {
            "correlationId": "correlation-id",
            "apiLoginName": "login-name",
            "webHooksUri": "https://example.invalid/iiko-webhook",
            "webHooksFilter": {"stopListUpdateFilter": {}},
        }
    )

    response = asyncio.run(Webhooks(client).settings("organization-id"))  # type: ignore[arg-type]

    assert response.web_hooks_filter is not None
    assert response.web_hooks_filter.stop_list_update_filter is not None
    assert response.web_hooks_filter.stop_list_update_filter.updates is None


def test_update_settings_sends_complete_filter_with_wire_aliases():
    client = RecordingClient({"correlationId": "correlation-id"})
    filters = WebHooksFilter.model_validate(
        {
            "deliveryOrderFilter": {"orderStatuses": ["Closed"]},
            "stopListUpdateFilter": {"updates": True},
            "futureFilter": {"enabled": True},
        }
    )

    response = asyncio.run(
        Webhooks(client).update_settings(  # type: ignore[arg-type]
            "organization-id",
            "https://example.invalid/iiko-webhook",
            auth_token=TEST_AUTH_TOKEN,
            web_hooks_filter=filters,
            timeout=30,
        )
    )

    assert response.correlation_id == "correlation-id"
    assert client.calls[0]["path"] == "/api/1/webhooks/update_settings"
    assert client.calls[0]["timeout"] == 30
    assert client.calls[0]["data"] == {
        "organizationId": "organization-id",
        "webHooksUri": "https://example.invalid/iiko-webhook",
        "authToken": TEST_AUTH_TOKEN,
        "webHooksFilter": {
            "deliveryOrderFilter": {"orderStatuses": ["Closed"]},
            "stopListUpdateFilter": {"updates": True},
            "futureFilter": {"enabled": True},
        },
    }


def test_stop_list_update_webhook_event_parses_terminal_group_signal():
    event = StopListUpdateWebhookEvent.model_validate(
        {
            "eventType": "StopListUpdate",
            "eventTime": "2026-08-25 19:00:00.000",
            "organizationId": "organization-id",
            "correlationId": "correlation-id",
            "eventInfo": {
                "terminalGroupsStopListsUpdates": [
                    {"id": "terminal-group-id", "isFull": False},
                ]
            },
        }
    )

    update = event.event_info.terminal_groups_stop_lists_updates[0]
    assert update.id == "terminal-group-id"
    assert update.is_full is False
