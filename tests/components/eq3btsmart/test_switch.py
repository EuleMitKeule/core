"""Tests for the eq3btsmart climate platform."""

from unittest.mock import AsyncMock

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from .const import MAC


async def test_turn_on(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test turn on for switch."""

    await setup_config_entry()

    entity_id = f"{SWITCH_DOMAIN}.{slugify(MAC)}_boost"

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    mock_thermostat.async_set_boost.assert_called_once_with(True)


async def test_turn_off(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test turn off for switch."""

    await setup_config_entry()

    entity_id = f"{SWITCH_DOMAIN}.{slugify(MAC)}_boost"

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    mock_thermostat.async_set_boost.assert_called_once_with(False)
