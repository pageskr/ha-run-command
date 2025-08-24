"""Constants for the Run Command integration."""
from typing import Final

DOMAIN: Final = "run_command"

# Configuration keys
CONF_COMMAND: Final = "command"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_VALUE_TEMPLATE: Final = "value_template"
CONF_ATTRIBUTE_TEMPLATES: Final = "attribute_templates"
CONF_NAME: Final = "name"
CONF_TIMEOUT: Final = "timeout"
CONF_UNIT_OF_MEASUREMENT: Final = "unit_of_measurement"
CONF_KEEP_LAST_VALUE: Final = "keep_last_value"
CONF_REMOVE_UNIT: Final = "remove_unit"



# Default values
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_NAME: Final = "Run Command Sensor"
DEFAULT_TIMEOUT: Final = 60
MAX_TIMEOUT: Final = 600

# Attribute names
ATTR_LAST_UPDATE: Final = "last_update"
ATTR_LAST_ERROR: Final = "last_error"
