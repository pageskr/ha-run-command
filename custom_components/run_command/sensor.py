"""Sensor platform for Run Command integration."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import Template

from .const import (
    CONF_ATTRIBUTE_TEMPLATES,
    CONF_COMMAND,
    CONF_NAME,
    CONF_RESULT_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_VALUE_TEMPLATE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RESULT_TYPE_JSON,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Run Command sensor from a config entry."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities(
        [RunCommandSensor(hass, config_entry.entry_id, config)], update_before_add=True
    )


class RunCommandSensor(SensorEntity):
    """Representation of a Run Command sensor."""

    def __init__(self, hass: HomeAssistant, entry_id: str, config: dict[str, Any]) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._config = config
        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = f"{DOMAIN}_{entry_id}"
        self._command_template = Template(config[CONF_COMMAND], hass)
        self._value_template = None
        if config.get(CONF_VALUE_TEMPLATE):
            self._value_template = Template(config[CONF_VALUE_TEMPLATE], hass)
        self._attribute_templates: dict[str, Template] = {}
        if config.get(CONF_ATTRIBUTE_TEMPLATES):
            for attr_name, attr_template in config[CONF_ATTRIBUTE_TEMPLATES].items():
                self._attribute_templates[attr_name] = Template(attr_template, hass)
        
        self._scan_interval = timedelta(
            seconds=config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        self._result_type = config.get(CONF_RESULT_TYPE)
        self._state: Any = None
        self._attributes: dict[str, Any] = {}
        self._raw_value: str | None = None
        self._json_value: dict | list | None = None

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state."""
        return True

    @property
    def update_method(self) -> str:
        """Return the polling update method."""
        return "async_update"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._attributes

    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # 명령어 템플릿 렌더링
            command = self._command_template.async_render()
            
            # 명령어 실행
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                _LOGGER.error(
                    "명령어 실행 실패 (코드 %s): %s", proc.returncode, stderr.decode()
                )
                self._state = None
                return
            
            # 결과 처리
            self._raw_value = stdout.decode().strip()
            self._json_value = None
            
            # JSON 파싱 시도
            if self._result_type == RESULT_TYPE_JSON and self._raw_value:
                try:
                    self._json_value = json.loads(self._raw_value)
                except json.JSONDecodeError:
                    _LOGGER.warning("JSON 파싱 실패: %s", self._raw_value)
            
            # 템플릿 변수 준비
            template_vars = {
                "value": self._raw_value,
                "json": self._json_value,
            }
            
            # 값 템플릿 처리
            if self._value_template:
                try:
                    self._state = self._value_template.async_render(template_vars)
                except TemplateError as err:
                    _LOGGER.error("값 템플릿 렌더링 오류: %s", err)
                    self._state = None
            else:
                self._state = self._raw_value
            
            # 속성 템플릿 처리
            self._attributes = {}
            for attr_name, attr_template in self._attribute_templates.items():
                try:
                    self._attributes[attr_name] = attr_template.async_render(template_vars)
                except TemplateError as err:
                    _LOGGER.error("속성 템플릿 '%s' 렌더링 오류: %s", attr_name, err)
                    self._attributes[attr_name] = None
            
            # JSON 값만 속성에 추가 (raw_value는 제거)
            if self._json_value is not None:
                self._attributes["json_value"] = self._json_value
                
        except Exception as err:
            _LOGGER.error("센서 업데이트 중 오류: %s", err)
            self._state = None

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        return self._state

    @property
    def scan_interval(self) -> timedelta:
        """Return the polling interval."""
        return self._scan_interval
