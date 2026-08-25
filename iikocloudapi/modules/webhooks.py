from collections.abc import Mapping
from typing import Any, Literal

import orjson
from pydantic import BaseModel, ConfigDict, Field

from iikocloudapi.client import Client
from iikocloudapi.helpers import BaseResponseModel


class WebHookShortFilter(BaseModel):
    """Webhook filter used by event types that only expose an updates flag."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    updates: bool


class WebHooksFilter(BaseModel):
    """Webhook filters returned by iiko.

    Non-stop-list filters stay as mappings so callers can read and write settings
    without losing fields introduced by newer iiko API versions.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    delivery_order_filter: dict[str, Any] | None = Field(default=None, alias="deliveryOrderFilter")
    table_order_filter: dict[str, Any] | None = Field(default=None, alias="tableOrderFilter")
    reserve_filter: dict[str, Any] | None = Field(default=None, alias="reserveFilter")
    stop_list_update_filter: WebHookShortFilter | None = Field(default=None, alias="stopListUpdateFilter")
    personal_shift_filter: WebHookShortFilter | None = Field(default=None, alias="personalShiftFilter")
    nomenclature_update_filter: WebHookShortFilter | None = Field(default=None, alias="nomenclatureUpdateFilter")
    business_hours_and_mapping_update_filter: WebHookShortFilter | None = Field(
        default=None,
        alias="businessHoursAndMappingUpdateFilter",
    )


class GetWebHookSettingsResponse(BaseResponseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    api_login_name: str | None = Field(alias="apiLoginName")
    web_hooks_uri: str | None = Field(alias="webHooksUri")
    auth_token: str | None = Field(default=None, alias="authToken")
    web_hooks_filter: WebHooksFilter | None = Field(default=None, alias="webHooksFilter")


class UpdateWebHookSettingsBody(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    organization_id: str = Field(alias="organizationId")
    web_hooks_uri: str = Field(alias="webHooksUri")
    auth_token: str | None = Field(default=None, alias="authToken")
    web_hooks_filter: WebHooksFilter | None = Field(default=None, alias="webHooksFilter")


class UpdateWebHookSettingsResponse(BaseResponseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class TerminalGroupStopListUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    is_full: bool = Field(alias="isFull")


class StopListUpdateEventInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    terminal_groups_stop_lists_updates: list[TerminalGroupStopListUpdate] = Field(
        alias="terminalGroupsStopListsUpdates"
    )


class StopListUpdateWebhookEvent(BaseModel):
    """Payload of an iiko `StopListUpdate` webhook event."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    event_type: Literal["StopListUpdate"] = Field(alias="eventType")
    event_time: str = Field(alias="eventTime")
    organization_id: str = Field(alias="organizationId")
    correlation_id: str = Field(alias="correlationId")
    event_info: StopListUpdateEventInfo = Field(alias="eventInfo")


class Webhooks:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def settings(
        self,
        organization_id: str,
        timeout: str | int | None = None,
    ) -> GetWebHookSettingsResponse:
        """Get webhook settings for the organization and authorized API login."""
        response = await self._client.request(
            "/api/1/webhooks/settings",
            data={"organizationId": organization_id},
            timeout=timeout,
        )
        return GetWebHookSettingsResponse(**orjson.loads(response.content))

    async def update_settings(
        self,
        organization_id: str,
        web_hooks_uri: str,
        auth_token: str | None = None,
        web_hooks_filter: WebHooksFilter | Mapping[str, Any] | None = None,
        timeout: str | int | None = None,
    ) -> UpdateWebHookSettingsResponse:
        """Add or update webhook settings for the authorized API login.

        Call `settings` first and merge the returned filters when changing only
        one event type: iiko treats this operation as an update of the complete
        webhook settings object.
        """
        normalized_filter = (
            WebHooksFilter.model_validate(dict(web_hooks_filter))
            if isinstance(web_hooks_filter, Mapping)
            else web_hooks_filter
        )
        body = UpdateWebHookSettingsBody.model_validate(
            {
                "organizationId": organization_id,
                "webHooksUri": web_hooks_uri,
                "authToken": auth_token,
                "webHooksFilter": normalized_filter,
            }
        )
        response = await self._client.request(
            "/api/1/webhooks/update_settings",
            data=body.model_dump(by_alias=True, exclude_none=True),
            timeout=timeout,
        )
        return UpdateWebHookSettingsResponse(**orjson.loads(response.content))
