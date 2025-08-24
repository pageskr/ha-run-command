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
    CONF_KEEP_LAST_VALUE,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
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
        
        # 측정 단위 설정
        unit = config.get(CONF_UNIT_OF_MEASUREMENT)
        if unit is None or unit == "":
            # None이거나 빈 문자열일 경우 속성 제거
            self._attr_unit_of_measurement = None
        else:
            self._attr_unit_of_measurement = unit
        
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
        self._timeout = config.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self._keep_last_value = config.get(CONF_KEEP_LAST_VALUE, False)
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
        # 이전 상태 저장 (기존값 유지 옵션용)
        previous_state = self._state
        command_failed = False
        template_failed = False
        
        try:
            # 명령어 템플릿 렌더링
            command = self._command_template.async_render()
            
            # 명령어 실행 (타임아웃 설정)
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), 
                    timeout=self._timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                _LOGGER.error(
                    "명령어 실행 시간 초과 (%s초): %s", self._timeout, command
                )
                command_failed = True
                self._attributes["last_error"] = f"Command timeout after {self._timeout} seconds"
                self._last_update = dt_util.now()
                self._attributes["last_update"] = self._last_update.isoformat()
                
                if self._keep_last_value:
                    self._state = previous_state
                else:
                    self._state = None
                return
            
            if proc.returncode != 0:
                _LOGGER.error(
                    "명령어 실행 실패 (코드 %s): %s", proc.returncode, stderr.decode()
                )
                command_failed = True
                self._attributes["last_error"] = stderr.decode().strip()
                self._last_update = dt_util.now()
                self._attributes["last_update"] = self._last_update.isoformat()
                
                if self._keep_last_value:
                    self._state = previous_state
                else:
                    self._state = None
                return
            
            # 업데이트 시간 기록
            self._last_update = dt_util.now()
            
            # 결과 처리 - value는 항상 텍스트 문자열로 저장
            raw_result = stdout.decode().strip()
            
            # 템플릿 변수 준비 - value는 항상 문자열 그대로
            template_vars = {
                "value": raw_result  # 원본 텍스트 그대로 유지
            }
            
            # JSON 파싱 시도 - value_json에만 파싱된 값 저장
            try:
                json_data = json.loads(raw_result)
                template_vars["value_json"] = json_data
            except json.JSONDecodeError:
                template_vars["value_json"] = None
            
            # 값 템플릿 처리
            if self._value_template:
                try:
                    rendered_value = self._value_template.async_render(template_vars)
                    
                    # 기존값 유지 옵션이 켜져있고, 특정 값들인 경우 이전 상태 유지
                    if self._keep_last_value and str(rendered_value).lower() in ["false", "none", "unknown", "unavailable"]:
                        self._state = previous_state
                        self._attributes["template_result"] = str(rendered_value)
                    else:
                        self._state = rendered_value
                        
                except TemplateError as err:
                    _LOGGER.error("값 템플릿 렌더링 오류: %s", err)
                    template_failed = True
                    self._attributes["template_error"] = str(err)
                    
                    if self._keep_last_value:
                        self._state = previous_state
                    else:
                        self._state = None
            else:
                self._state = raw_result
            
            # 속성 초기화
            new_attributes = {}
            
            # 속성 템플릿 처리
            for attr_name, attr_template in self._attribute_templates.items():
                try:
                    new_attributes[attr_name] = attr_template.async_render(template_vars)
                except TemplateError as err:
                    _LOGGER.error("속성 템플릿 '%s' 렌더링 오류: %s", attr_name, err)
                    new_attributes[attr_name] = None
            
            # 속성 업데이트
            self._attributes = new_attributes
            
            # 마지막 업데이트 시간 추가
            self._attributes["last_update"] = self._last_update.isoformat()
            
            # 에러 속성 관리
            if not command_failed and "last_error" in self._attributes:
                del self._attributes["last_error"]
            if not template_failed and "template_error" in self._attributes:
                del self._attributes["template_error"]
            if not template_failed and "template_result" in self._attributes:
                del self._attributes["template_result"]
                
        except Exception as err:
            _LOGGER.error("센서 업데이트 중 오류: %s", err)
            self._attributes["last_error"] = str(err)
            self._last_update = dt_util.now()
            self._attributes["last_update"] = self._last_update.isoformat()
            
            if self._keep_last_value:
                self._state = previous_state
            else:
                self._state = None

    @property
    def state(self) -> Any:
        """Return the state of the sensor."""
        return self._state

    @property
    def scan_interval(self) -> timedelta:
        """Return the polling interval."""
        return self._scan_interval
