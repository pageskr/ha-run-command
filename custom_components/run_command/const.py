"""Constants for the Run Command integration."""
from typing import Final

DOMAIN: Final = "run_command"

# Configuration keys
CONF_COMMAND: Final = "command"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_RESULT_TYPE: Final = "result_type"
CONF_VALUE_TEMPLATE: Final = "value_template"
CONF_ATTRIBUTE_TEMPLATES: Final = "attribute_templates"
CONF_NAME: Final = "name"

# Result types
RESULT_TYPE_TEXT: Final = "text"
RESULT_TYPE_JSON: Final = "json"

# Default values
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_RESULT_TYPE: Final = RESULT_TYPE_TEXT
DEFAULT_NAME: Final = "Run Command Sensor"
