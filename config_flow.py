"""Config flow for Run Command integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_COMMAND,
    CONF_NAME,
    CONF_RESULT_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_VALUE_TEMPLATE,
    DEFAULT_NAME,
    DEFAULT_RESULT_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RESULT_TYPE_JSON,
    RESULT_TYPE_TEXT,
)

_LOGGER = logging.getLogger(__name__)


def validate_attribute_templates(value: str) -> dict[str, str]:
    """Validate attribute templates JSON format."""
    if not value:
        return {}
    try:
        templates = json.loads(value)
        if not isinstance(templates, dict):
            raise vol.Invalid("속성 템플릿은 JSON 객체여야 합니다")
        for key, val in templates.items():
            if not isinstance(key, str) or not isinstance(val, str):
                raise vol.Invalid("속성 이름과 값은 문자열이어야 합니다")
        return templates
    except json.JSONDecodeError as err:
        raise vol.Invalid(f"유효하지 않은 JSON 형식: {err}")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Run Command."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # 속성 템플릿 유효성 검사
                if CONF_ATTRIBUTE_TEMPLATES in user_input:
                    user_input[CONF_ATTRIBUTE_TEMPLATES] = validate_attribute_templates(
                        user_input[CONF_ATTRIBUTE_TEMPLATES]
                    )

                # 고유한 ID 생성
                await self.async_set_unique_id(user_input[CONF_NAME])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            except vol.Invalid as err:
                errors["base"] = str(err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_COMMAND): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Optional(CONF_RESULT_TYPE, default=DEFAULT_RESULT_TYPE): vol.In(
                    [RESULT_TYPE_TEXT, RESULT_TYPE_JSON]
                ),
                vol.Optional(CONF_VALUE_TEMPLATE, default=""): str,
                vol.Optional(CONF_ATTRIBUTE_TEMPLATES, default=""): str,
            }
        )

        placeholders = {
            "attribute_example": '{"temperature": "{{ value | regex_findall(\\"temp: (\\\\d+)\\") | first }}", "status": "{{ json.status if json else \\"unknown\\" }}"}'
        }

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders=placeholders,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
