"""Tests for the eq3btsmart climate platform."""

from typing import Any
from unittest.mock import AsyncMock

from eq3btsmart.adapter.eq3_temperature import Eq3Temperature
from eq3btsmart.const import EQ3BT_OFF_TEMP, Eq3Preset, OperationMode
from eq3btsmart.exceptions import Eq3Exception
import pytest

from homeassistant.components.climate import (
    ATTR_HVAC_ACTION,
    ATTR_PRESET_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    PRESET_NONE,
    HVACAction,
    HVACMode,
)
from homeassistant.components.eq3btsmart.const import Preset
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import slugify

from .const import MAC

from tests.common import MockConfigEntry


async def test_setup(hass: HomeAssistant, setup_config_entry: MockConfigEntry) -> None:
    """Test setup for climate."""

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"
    assert hass.states.get(entity_id).name == slugify(MAC)


async def test_disconnect_unavailable(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: MockConfigEntry
) -> None:
    """Test disconnect for climate."""

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"
    assert hass.states.get(entity_id).state != "unavailable"

    await mock_thermostat.async_disconnect()

    assert hass.states.get(entity_id).state == "unavailable"


@pytest.mark.parametrize(
    ("attribute", "value", "preset_mode"),
    [
        ("is_boost", True, Preset.BOOST),
        ("is_away", True, Preset.AWAY),
        ("is_window_open", True, Preset.WINDOW_OPEN),
        ("is_low_battery", True, Preset.LOW_BATTERY),
        ("operation_mode", OperationMode.ON, Preset.OPEN),
        ("target_temperature", Eq3Temperature(21), Preset.COMFORT),
        ("target_temperature", Eq3Temperature(16), Preset.ECO),
        ("presets", None, PRESET_NONE),
        ("", None, PRESET_NONE),
    ],
)
async def test_preset_modes(
    hass: HomeAssistant,
    mock_thermostat: AsyncMock,
    setup_config_entry: AsyncMock,
    attribute: str,
    value: Any,
    preset_mode: Preset | str,
) -> None:
    """Test preset modes for climate."""

    setattr(mock_thermostat.status, attribute, value)
    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_PRESET_MODE] is preset_mode


@pytest.mark.parametrize(
    ("attribute", "value", "hvac_action"),
    [
        ("operation_mode", OperationMode.OFF, HVACAction.OFF),
        ("valve", 0, HVACAction.IDLE),
        ("valve", 1, HVACAction.HEATING),
    ],
)
async def test_hvac_action(
    hass: HomeAssistant,
    mock_thermostat: AsyncMock,
    setup_config_entry: AsyncMock,
    attribute: str,
    value: Any,
    hvac_action: HVACAction,
) -> None:
    """Test hvac action for climate."""

    setattr(mock_thermostat.status, attribute, value)
    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"
    state = hass.states.get(entity_id)

    assert state.attributes[ATTR_HVAC_ACTION] is hvac_action


async def test_set_temperature(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test set temperature for climate."""

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_temperature",
        {"temperature": 12},
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    mock_thermostat.async_set_temperature.assert_called_once_with(12)


async def test_set_temperature_hvac_mode(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test set temperature for climate."""

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_temperature",
        {
            "temperature": 12,
            "hvac_mode": HVACMode.HEAT,
        },
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    mock_thermostat.async_set_temperature.assert_called_once_with(12)
    mock_thermostat.async_set_mode.assert_called_once_with(OperationMode.MANUAL)


async def test_set_temperature_fails_with_hvac_mode_off(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test set temperature for climate."""

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            "set_temperature",
            {
                "temperature": 12,
                "hvac_mode": HVACMode.OFF,
            },
            blocking=True,
            target={
                "entity_id": entity_id,
            },
        )

    mock_thermostat.async_set_temperature.assert_not_called()
    mock_thermostat.async_set_mode.assert_not_called()


async def test_set_temperature_fails_with_invalid_temperature(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test set temperature for climate."""

    mock_thermostat.async_set_temperature.side_effect = ValueError

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            "set_temperature",
            {
                "temperature": 15,
                "hvac_mode": HVACMode.AUTO,
            },
            blocking=True,
            target={
                "entity_id": entity_id,
            },
        )

    mock_thermostat.async_set_temperature.assert_called_once_with(15)
    mock_thermostat.async_set_mode.assert_called_once_with(OperationMode.AUTO)


async def test_set_hvac_mode(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test set hvac mode for climate."""

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {"hvac_mode": HVACMode.HEAT},
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    mock_thermostat.async_set_mode.assert_called_once_with(OperationMode.MANUAL)


async def test_set_hvac_mode_off(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test set hvac mode for climate."""

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {"hvac_mode": HVACMode.OFF},
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    mock_thermostat.async_set_mode.assert_called_once_with(OperationMode.OFF)
    mock_thermostat.async_set_temperature.assert_called_once_with(EQ3BT_OFF_TEMP)


async def test_set_hvac_mode_off_fails(
    hass: HomeAssistant, mock_thermostat: AsyncMock, setup_config_entry: AsyncMock
) -> None:
    """Test set hvac mode for climate."""

    mock_thermostat.async_set_mode.side_effect = Eq3Exception

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {"hvac_mode": HVACMode.HEAT},
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    mock_thermostat.async_set_mode.assert_called_once_with(OperationMode.MANUAL)


@pytest.mark.parametrize(
    ("preset_mode", "method", "argument"),
    [
        (Preset.BOOST, "async_set_boost", True),
        (Preset.AWAY, "async_set_away", True),
        (Preset.ECO, "async_set_preset", Eq3Preset.ECO),
        (Preset.COMFORT, "async_set_preset", Eq3Preset.COMFORT),
        (Preset.OPEN, "async_set_mode", OperationMode.ON),
    ],
)
async def test_set_preset_mode(
    hass: HomeAssistant,
    mock_thermostat: AsyncMock,
    setup_config_entry: AsyncMock,
    preset_mode: Preset,
    method: str,
    argument: Any,
) -> None:
    """Test set preset mode for climate."""

    await setup_config_entry()

    entity_id = f"{CLIMATE_DOMAIN}.{slugify(MAC)}"

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_preset_mode",
        {"preset_mode": preset_mode},
        blocking=True,
        target={
            "entity_id": entity_id,
        },
    )

    getattr(mock_thermostat, method).assert_called_once_with(argument)
