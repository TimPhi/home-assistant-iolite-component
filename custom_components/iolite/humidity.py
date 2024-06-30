"""Support for IOLITE heating."""

import asyncio
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from iolite_client.client import Client
from iolite_client.entity import HumiditySensor, Room

from . import IoliteDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup from config entry."""

    coordinator: IoliteDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    devices = []
    for room in coordinator.data.values():
        for device in room.devices.values():
            if isinstance(device, HumiditySensor):
                devices.append(
                    HumidityEntity(coordinator, device, room, coordinator.client)
                )

    for device in devices:
        _LOGGER.info(f"Adding {device}")

    async_add_entities(devices)


# Failed to call service climate/set_temperature. asyncio.run() cannot be called from a running event loop


class HumidityEntity(CoordinatorEntity, SensorEntity):

    def __init__(self, coordinator, sensor: HumiditySensor, room: Room, client: Client):
        super().__init__(coordinator)
        self.sensor = sensor
        self.client = client
        self._attr_unique_id = sensor.identifier
        self._attr_name = f"{self.sensor.name} ({room.name})"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._attr_name,
            "manufacturer": self.sensor.manufacturer,
        }
        self.attr_device_class = SensorDeviceClass.HUMIDITY
        self._update_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state()
        self.async_write_ha_state()

    @property
    def room(self) -> Room:
        """Return device data object from coordinator."""
        return self.coordinator.data[self.sensor.place_identifier]

    def _update_state(self):
        sensor: HumiditySensor = self.room.devices[self.sensor.identifier]
        self._attr_native_value = sensor.humidity_level
