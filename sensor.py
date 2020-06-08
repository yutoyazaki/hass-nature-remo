"""Support for Nature Remo E energy sensor."""
import logging

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
    DEVICE_CLASS_POWER,
)
from homeassistant.helpers.entity import Entity
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo E sensor."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up sensor platform.")
    coordinator = hass.data[DOMAIN]["coordinator"]
    appliances = coordinator.data
    async_add_entities(
        [
            NatureRemoE(coordinator, appliance)
            for appliance in appliances.values()
            if appliance["type"] == "EL_SMART_METER"
        ]
    )


class NatureRemoE(Entity):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, coordinator, appliance):
        self._coordinator = coordinator
        self._name = f"Nature Remo {appliance['nickname']}"
        self._state = None
        self._unit_of_measurement = POWER_WATT
        self._appliance_id = appliance["id"]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._appliance_id

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        smart_meter = self._coordinator.data[self._appliance_id]["smart_meter"]
        echonetlite_properties = smart_meter["echonetlite_properties"]
        measured_instantaneous = next(
            value["val"] for value in echonetlite_properties if value["epc"] == 231
        )
        _LOGGER.debug("Current state: %sW", measured_instantaneous)
        return measured_instantaneous

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_POWER

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()
