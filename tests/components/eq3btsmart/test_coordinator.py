"""Tests for the eq3btsmart coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock

from eq3btsmart.exceptions import Eq3Exception

from homeassistant.components.eq3btsmart.const import SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow

from tests.common import async_fire_time_changed


async def test_auto_reconnect(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test auto reconnect."""

    await setup_config_entry()
    assert mock_thermostat.async_connect.call_count == 1
    await mock_thermostat.async_disconnect()

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=SCAN_INTERVAL + 1))
    await hass.async_block_till_done()

    assert mock_thermostat.async_connect.call_count == 2


async def test_update_exception(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test update exception."""

    await setup_config_entry()
    assert mock_thermostat.async_connect.call_count == 1
    mock_thermostat.async_get_status.side_effect = Eq3Exception

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=SCAN_INTERVAL + 1))
    await hass.async_block_till_done()

    # entities should be unavailable now


async def test_connection_error(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test connection error."""

    mock_thermostat.async_connect.side_effect = Eq3Exception
    entry = await setup_config_entry()
    assert entry.state is ConfigEntryState.SETUP_RETRY
