"""Support for EQ3 devices."""

import asyncio
import logging

from eq3btsmart import Thermostat
from eq3btsmart.exceptions import Eq3Exception
from eq3btsmart.thermostat_config import ThermostatConfig

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_CURRENT_TEMP_SELECTOR,
    CONF_EXTERNAL_TEMP_SENSOR,
    CONF_MAC_ADDRESS,
    CONF_TARGET_TEMP_SELECTOR,
    DEFAULT_CURRENT_TEMP_SELECTOR,
    DEFAULT_TARGET_TEMP_SELECTOR,
    SCAN_INTERVAL,
    SIGNAL_THERMOSTAT_CONNECTED,
    SIGNAL_THERMOSTAT_DISCONNECTED,
)
from .models import Eq3ConfigEntryData

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]

_LOGGER = logging.getLogger(__name__)


type Eq3ConfigEntry = ConfigEntry[Eq3ConfigEntryData]


async def async_setup_entry(hass: HomeAssistant, entry: Eq3ConfigEntry) -> bool:
    """Handle config entry setup."""

    mac_address: str = entry.data.get(CONF_MAC_ADDRESS, entry.unique_id)

    device = bluetooth.async_ble_device_from_address(
        hass, mac_address.upper(), connectable=True
    )

    if device is None:
        raise ConfigEntryNotReady(f"[{mac_address}] Device could not be found")

    thermostat = Thermostat(
        thermostat_config=ThermostatConfig(
            mac_address=mac_address,
        ),
        ble_device=device,
    )

    entry.runtime_data = Eq3ConfigEntryData(thermostat=thermostat)

    if not entry.data:
        hass.config_entries.async_update_entry(
            entry,
            data={CONF_MAC_ADDRESS: mac_address},
        )

    if not entry.options:
        hass.config_entries.async_update_entry(
            entry,
            options={
                CONF_CURRENT_TEMP_SELECTOR: DEFAULT_CURRENT_TEMP_SELECTOR,
                CONF_TARGET_TEMP_SELECTOR: DEFAULT_TARGET_TEMP_SELECTOR,
                CONF_EXTERNAL_TEMP_SENSOR: None,
            },
        )

    entry.runtime_data = Eq3ConfigEntryData(thermostat=thermostat)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_create_background_task(
        hass, _async_run_thermostat(hass, entry, mac_address), entry.entry_id
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: Eq3ConfigEntry) -> bool:
    """Handle config entry unload."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.thermostat.async_disconnect()

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: Eq3ConfigEntry) -> None:
    """Handle config entry update."""

    await hass.config_entries.async_reload(entry.entry_id)


async def _async_run_thermostat(
    hass: HomeAssistant, entry: Eq3ConfigEntry, mac_address: str
) -> None:
    """Run the thermostat."""

    thermostat = entry.runtime_data.thermostat

    await _async_reconnect_thermostat(hass, entry, mac_address)

    while True:
        try:
            await thermostat.async_get_status()
        except Eq3Exception as e:
            if not thermostat.is_connected:
                _LOGGER.error(
                    "[%s] eQ-3 device disconnected",
                    mac_address,
                )
                async_dispatcher_send(
                    hass,
                    f"{SIGNAL_THERMOSTAT_DISCONNECTED}_{mac_address}",
                )
                await _async_reconnect_thermostat(hass, entry, mac_address)
                continue

            _LOGGER.error(
                "[%s] Error updating eQ-3 device: %s",
                mac_address,
                e,
            )

        await asyncio.sleep(SCAN_INTERVAL)


async def _async_reconnect_thermostat(
    hass: HomeAssistant, entry: Eq3ConfigEntry, mac_address: str
) -> None:
    """Reconnect the thermostat."""

    thermostat = entry.runtime_data.thermostat

    while True:
        try:
            await thermostat.async_connect()
        except Eq3Exception:
            await asyncio.sleep(SCAN_INTERVAL)
            continue

        _LOGGER.debug(
            "[%s] eQ-3 device connected",
            mac_address,
        )

        async_dispatcher_send(
            hass,
            f"{SIGNAL_THERMOSTAT_CONNECTED}_{mac_address}",
        )

        return
