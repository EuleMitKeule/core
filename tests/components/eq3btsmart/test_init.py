"""Test the eq3btsmart setup."""

from unittest.mock import AsyncMock

from syrupy.assertion import SnapshotAssertion

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import MAC

from tests.common import MockConfigEntry
from tests.components.bluetooth import BLEDevice


async def test_setup(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
    mock_ble_device: BLEDevice,
    mock_thermostat: AsyncMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test setup creates expected devices."""

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_thermostat.async_connect.assert_called_once()
    assert mock_thermostat.async_get_status.call_count == 2

    assert mock_config_entry.state is ConfigEntryState.LOADED

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_BLUETOOTH, MAC)}
    )

    assert device_entry is not None


async def test_setup_retry_connect(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_ble_device: BLEDevice,
    mock_thermostat: AsyncMock,
) -> None:
    """Test setup creates expected devices."""

    mock_thermostat.async_connect.reset_mock(side_effect=True)
    mock_thermostat.status = None
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_fail_no_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setup creates expected devices."""

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_ble_device: BLEDevice,
    mock_thermostat: AsyncMock,
) -> None:
    """Test unloading the eq3btsmart entry."""

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_thermostat.unregister_connection_callback.call_count == 0

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_thermostat.unregister_connection_callback.call_count == 1


async def test_update_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_ble_device: BLEDevice,
    mock_thermostat: AsyncMock,
) -> None:
    """Test updating the eq3btsmart entry."""

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_thermostat.async_get_status.call_count == 2

    hass.config_entries.async_update_entry(mock_config_entry, title="new_title")
    await hass.async_block_till_done()

    assert mock_thermostat.async_get_status.call_count == 4
