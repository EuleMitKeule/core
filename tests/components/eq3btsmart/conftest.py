"""Fixtures for eq3btsmart tests."""

import asyncio
from collections.abc import Callable, Generator
from datetime import timedelta
from unittest.mock import AsyncMock, create_autospec, patch

from bleak.backends.scanner import AdvertisementData
from eq3btsmart import Thermostat
from eq3btsmart.adapter.eq3_duration import Eq3Duration
from eq3btsmart.adapter.eq3_serial import Eq3Serial
from eq3btsmart.adapter.eq3_temperature import Eq3Temperature
from eq3btsmart.adapter.eq3_temperature_offset import Eq3TemperatureOffset
from eq3btsmart.const import OperationMode
from eq3btsmart.models import DeviceData, Presets, Status
import pytest

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.eq3btsmart.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from .const import DEVICE_SERIAL, FIRMWARE_VERSION, MAC, RSSI

from tests.common import MockConfigEntry
from tests.components.bluetooth import BLEDevice, generate_ble_device


@pytest.fixture(autouse=True)
def mock_bluetooth(enable_bluetooth: None) -> None:
    """Auto mock bluetooth."""


@pytest.fixture
def fake_service_info() -> BluetoothServiceInfoBleak:
    """Return a BluetoothServiceInfoBleak for use in testing."""
    return BluetoothServiceInfoBleak(
        name="CC-RT-BLE",
        address=MAC,
        rssi=RSSI,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        source="local",
        connectable=True,
        time=0,
        device=generate_ble_device(address=MAC, name="CC-RT-BLE", rssi=0),
        advertisement=AdvertisementData(
            local_name="CC-RT-BLE",
            manufacturer_data={},
            service_data={},
            service_uuids=[],
            rssi=RSSI,
            tx_power=-127,
            platform_data=(),
        ),
        tx_power=-127,
    )


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""

    return MockConfigEntry(
        domain=DOMAIN,
        title=slugify(MAC),
        unique_id=MAC,
    )


@pytest.fixture
def mock_ble_device(
    fake_service_info: BluetoothServiceInfoBleak,
) -> Generator[BLEDevice]:
    """Mock a BLEDevice."""

    # this should patch the bluetooth.async_ble_device_from_address function in the eq3btsmart component to return a mock BLEDevice
    with patch(
        "homeassistant.components.eq3btsmart.bluetooth.async_ble_device_from_address",
        return_value=fake_service_info.device,
    ):
        yield fake_service_info.device


@pytest.fixture
def mock_status() -> Status:
    """Mock a Status object."""

    class MockStatus:
        def __init__(self) -> None:
            """Initialize the mock status."""

            self.valve = 1
            self.target_temperature = Eq3Temperature(20.0)
            self._operation_mode = OperationMode.AUTO
            self.is_away = False
            self.is_boost = False
            self.is_dst = False
            self.is_window_open = False
            self.is_locked = False
            self.is_low_battery = False
            self.away_until = None
            self.presets = Presets(
                window_open_temperature=Eq3Temperature(5.0),
                window_open_time=Eq3Duration(timedelta(seconds=15)),
                comfort_temperature=Eq3Temperature(21.0),
                eco_temperature=Eq3Temperature(16.0),
                offset_temperature=Eq3TemperatureOffset(0),
            )

        @property
        def operation_mode(self):
            return self._operation_mode

        @operation_mode.setter
        def operation_mode(self, value):
            self._operation_mode = value

    return MockStatus()


@pytest.fixture
def mock_device_data() -> DeviceData:
    """Mock a DeviceData object."""
    return DeviceData(
        firmware_version=FIRMWARE_VERSION, device_serial=Eq3Serial(DEVICE_SERIAL)
    )


@pytest.fixture(autouse=True)
def mock_thermostat(
    mock_status: Status, mock_device_data: DeviceData
) -> Generator[AsyncMock]:
    """Mock a BleakClient client."""

    mock_thermostat = create_autospec(Thermostat, instance=True)
    update_callback: Callable[[], None] = None
    connection_callback: Callable[[], bool] = None

    def register_update_callback(callback: Callable[[], None]):
        nonlocal update_callback
        update_callback = callback

    def unregister_update_callback(callback: Callable[[], None]):
        nonlocal update_callback
        update_callback = None

    def register_connection_callback(callback: Callable[[], None]):
        nonlocal connection_callback
        connection_callback = callback

    def unregister_connection_callback(callback: Callable[[], None]):
        nonlocal connection_callback
        connection_callback = None

    async def async_get_status():
        await asyncio.sleep(0.1)
        update_callback()

    async def async_connect():
        await asyncio.sleep(0.1)
        mock_thermostat.is_connected = True
        connection_callback(True)

    async def async_disconnect():
        await asyncio.sleep(0.1)
        mock_thermostat.is_connected = False
        connection_callback(False)

    mock_thermostat.async_connect = AsyncMock()
    mock_thermostat.async_get_status = AsyncMock()
    mock_thermostat.register_update_callback.side_effect = register_update_callback
    mock_thermostat.unregister_update_callback.side_effect = unregister_update_callback
    mock_thermostat.register_connection_callback.side_effect = (
        register_connection_callback
    )
    mock_thermostat.unregister_connection_callback.side_effect = (
        unregister_connection_callback
    )
    mock_thermostat.is_connected = False
    mock_thermostat.async_connect.side_effect = async_connect
    mock_thermostat.async_disconnect.side_effect = async_disconnect
    mock_thermostat.async_get_status.side_effect = async_get_status
    mock_thermostat.status = mock_status
    mock_thermostat.device_data = mock_device_data

    with (
        patch(
            "homeassistant.components.eq3btsmart.Thermostat",
            return_value=mock_thermostat,
        ),
        patch(
            "homeassistant.components.eq3btsmart.coordinator.Thermostat",
            return_value=mock_thermostat,
        ),
    ):
        yield mock_thermostat


@pytest.fixture
async def setup_config_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_ble_device: BLEDevice,
    mock_thermostat: AsyncMock,
) -> AsyncMock:
    """Set up a config entry."""

    async def setup_entry() -> MockConfigEntry:
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        return mock_config_entry

    return setup_entry
