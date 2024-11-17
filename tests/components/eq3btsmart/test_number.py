"""Tests for the eq3btsmart climate platform."""

from unittest.mock import AsyncMock

from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from .const import MAC


async def test_set_native_value(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test set native value for number."""

    await setup_config_entry()

    entity_id = f"{NUMBER_DOMAIN}.{slugify(MAC)}_comfort_temperature"

    await hass.services.async_call(
        NUMBER_DOMAIN,
        "set_value",
        {"value": 21.5},
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    mock_thermostat.async_configure_comfort_temperature.assert_called_once_with(21.5)
