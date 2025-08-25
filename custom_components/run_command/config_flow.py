"""Config flow for Run Command integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from .const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_COMMAND,
    CONF_KEEP_LAST_VALUE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
    CONF_REMOVE_UNIT,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_TIMEOUT,
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
                # 템플릿 선택자는 문자열을 반환하므로 변환 필요 없음
                # CONF_COMMAND는 문자열로 저장
                # CONF_VALUE_TEMPLATE는 문자열로 저장
                
                # 속성 템플릿 유효성 검사 (JSON 문자열을 딕셔너리로 변환)
                if CONF_ATTRIBUTE_TEMPLATES in user_input and user_input[CONF_ATTRIBUTE_TEMPLATES]:
                    user_input[CONF_ATTRIBUTE_TEMPLATES] = validate_attribute_templates(
                        user_input[CONF_ATTRIBUTE_TEMPLATES]
                    )
                else:
                    user_input[CONF_ATTRIBUTE_TEMPLATES] = {}

                # 측정 단위가 빈 문자열이면 None으로 변환
                if user_input.get(CONF_UNIT_OF_MEASUREMENT) == "":
                    user_input[CONF_UNIT_OF_MEASUREMENT] = None

                # REMOVE_UNIT 체크박스 제거
                user_input.pop(CONF_REMOVE_UNIT, None)

                # 중복 이름 확인 및 고유 ID 생성
                base_name = user_input[CONF_NAME]
                entries = self._async_current_entries()
                existing_names = {entry.data.get(CONF_NAME) for entry in entries}
                
                # 동일한 이름이 있으면 숫자를 붙여서 고유하게 만들기
                unique_name = base_name
                counter = 2
                while unique_name in existing_names:
                    unique_name = f"{base_name} {counter}"
                    counter += 1
                
                if unique_name != base_name:
                    user_input[CONF_NAME] = unique_name
                    _LOGGER.info(f"센서 이름이 '{base_name}'에서 '{unique_name}'으로 변경되었습니다")

                # 고유한 ID 설정 (이름 기반)
                await self.async_set_unique_id(unique_name)
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
                vol.Required(CONF_COMMAND): selector.TemplateSelector(),
                vol.Optional(
                    CONF_TIMEOUT, default=DEFAULT_TIMEOUT
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_TIMEOUT)),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Optional(CONF_VALUE_TEMPLATE, default=""): selector.TemplateSelector(),
                vol.Optional(CONF_ATTRIBUTE_TEMPLATES, default=""): selector.TemplateSelector(),
                vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): str,
                vol.Optional(CONF_REMOVE_UNIT, default=False): bool,
                vol.Optional(CONF_KEEP_LAST_VALUE, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Run Command."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # 속성 템플릿 유효성 검사 (JSON 문자열을 딕셔너리로 변환)
                if CONF_ATTRIBUTE_TEMPLATES in user_input and user_input[CONF_ATTRIBUTE_TEMPLATES]:
                    user_input[CONF_ATTRIBUTE_TEMPLATES] = validate_attribute_templates(
                        user_input[CONF_ATTRIBUTE_TEMPLATES]
                    )
                else:
                    user_input[CONF_ATTRIBUTE_TEMPLATES] = {}

                # 측정 단위 제거 처리
                if user_input.get(CONF_REMOVE_UNIT, False):
                    user_input[CONF_UNIT_OF_MEASUREMENT] = None
                    user_input.pop(CONF_REMOVE_UNIT, None)  # 체크박스 값은 제거
                elif CONF_REMOVE_UNIT in user_input:
                    user_input.pop(CONF_REMOVE_UNIT)  # 체크박스 값은 제거
                    # 빈 문자열일 경우 None으로 변환
                    if user_input.get(CONF_UNIT_OF_MEASUREMENT) == "":
                        user_input[CONF_UNIT_OF_MEASUREMENT] = None
                
                # 기존 데이터와 병합
                new_data = {**self.config_entry.data, **user_input}
                
                # 이름이 변경된 경우 고유 ID 업데이트
                if user_input.get(CONF_NAME) != self.config_entry.data.get(CONF_NAME):
                    # 중복 이름 확인
                    entries = self.hass.config_entries.async_entries(DOMAIN)
                    existing_names = {
                        entry.data.get(CONF_NAME) 
                        for entry in entries 
                        if entry.entry_id != self.config_entry.entry_id
                    }
                    
                    base_name = user_input[CONF_NAME]
                    unique_name = base_name
                    counter = 2
                    while unique_name in existing_names:
                        unique_name = f"{base_name} {counter}"
                        counter += 1
                    
                    new_data[CONF_NAME] = unique_name

                # 설정 업데이트
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=new_data,
                    title=new_data[CONF_NAME],
                )
                
                return self.async_create_entry(title="", data={})
                
            except vol.Invalid as err:
                errors["base"] = str(err)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # 현재 설정값을 기본값으로 사용
        current_data = self.config_entry.data
        
        # 속성 템플릿을 JSON 문자열로 변환 (멀티라인 유지)
        attr_templates_str = ""
        if current_data.get(CONF_ATTRIBUTE_TEMPLATES):
            try:
                attr_templates_str = json.dumps(
                    current_data[CONF_ATTRIBUTE_TEMPLATES], 
                    ensure_ascii=False,
                    indent=2  # 들여쓰기로 멀티라인 유지
                )
            except Exception:
                attr_templates_str = ""

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, 
                    default=current_data.get(CONF_NAME, DEFAULT_NAME)
                ): str,
                vol.Required(
                    CONF_COMMAND,
                    default=current_data.get(CONF_COMMAND, "")
                ): selector.TemplateSelector(),
                vol.Optional(
                    CONF_TIMEOUT,
                    default=current_data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_TIMEOUT)),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Optional(
                    CONF_VALUE_TEMPLATE,
                    default=current_data.get(CONF_VALUE_TEMPLATE, "")
                ): selector.TemplateSelector(),
                vol.Optional(
                    CONF_ATTRIBUTE_TEMPLATES,
                    default=attr_templates_str
                ): selector.TemplateSelector(),
                vol.Optional(
                    CONF_UNIT_OF_MEASUREMENT,
                    default=current_data.get(CONF_UNIT_OF_MEASUREMENT, "") or ""
                ): str,
                vol.Optional(
                    CONF_REMOVE_UNIT,
                    default=False
                ): bool,
                vol.Optional(
                    CONF_KEEP_LAST_VALUE,
                    default=current_data.get(CONF_KEEP_LAST_VALUE, False)
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
