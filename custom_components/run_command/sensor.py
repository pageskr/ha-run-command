"""Sensor platform for Run Command integration."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

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
    RESULT_TYPE_TEXT,
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
        self._result_type = config.get(CONF_RESULT_TYPE, RESULT_TYPE_TEXT)
        self._state: Any = None
        self._attributes: dict[str, Any] = {}
        self._last_update: datetime | None = None

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
                self._attributes["last_error"] = stderr.decode().strip()
                self._last_update = dt_util.now()
                self._attributes["last_update"] = self._last_update.isoformat()
                return
            
            # 업데이트 시간 기록
            self._last_update = dt_util.now()
            
            # 결과 처리
            raw_result = stdout.decode().strip()
            
            # 템플릿 변수 준비
            template_vars = {}
            
            if self._result_type == RESULT_TYPE_JSON:
                # JSON 형식인 경우
                try:
                    json_data = json.loads(raw_result)
                    template_vars["json"] = json_data
                    template_vars["value"] = raw_result  # JSON 문자열도 value에 포함
                except json.JSONDecodeError:
                    _LOGGER.warning("JSON 파싱 실패, 텍스트로 처리: %s", raw_result)
                    template_vars["value"] = raw_result
                    template_vars["json"] = None
            else:
                # 텍스트 형식인 경우
                template_vars["value"] = raw_result
                template_vars["json"] = None
            
            # 값 템플릿 처리
            if self._value_template:
                try:
                    self._state = self._value_template.async_render(template_vars)
                except TemplateError as err:
                    _LOGGER.error("값 템플릿 렌더링 오류: %s", err)
                    self._state = None
                    self._attributes["template_error"] = str(err)
            else:
                # 템플릿이 없으면 기본값 설정
                if self._result_type == RESULT_TYPE_JSON and "json" in template_vars and template_vars["json"] is not None:
                    self._state = json.dumps(template_vars["json"], ensure_ascii=False)
                else:
                    self._state = template_vars["value"]
            
            # 속성 초기화
            self._attributes = {}
            
            # 속성 템플릿 처리
            for attr_name, attr_template in self._attribute_templates.items():
                try:
                    self._attributes[attr_name] = attr_template.async_render(template_vars)
                except TemplateError as err:
                    _LOGGER.error("속성 템플릿 '%s' 렌더링 오류: %s", attr_name, err)
                    self._attributes[attr_name] = None
            
            # 마지막 업데이트 시간 추가
            self._attributes["last_update"] = self._last_update.isoformat()
            
            # 에러 속성 제거 (성공 시)
            if "last_error" in self._attributes:
                del self._attributes["last_error"]
            if "template_error" in self._attributes:
                del self._attributes["template_error"]
                
        except Exception as err:
            _LOGGER.error("센서 업데이트 중 오류: %s", err)
            self._state = None
            self._attributes["last_error"] = str(err)
            self._last_update = dt_util.now()
            self._attributes["last_update"] = self._last_update.isoformat()

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        return self._state

    @property
    def scan_interval(self) -> timedelta:
        """Return the polling interval."""
        return self._scan_interval
