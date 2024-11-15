"""Models for eq3btsmart integration."""

from dataclasses import dataclass

from eq3btsmart.thermostat import Thermostat


@dataclass(slots=True)
class Eq3ConfigEntryData:
    """Config entry for a single eQ-3 device."""

    thermostat: Thermostat
