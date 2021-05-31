"""Support for Nature Remo E energy sensor."""
import logging

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
    DEVICE_CLASS_POWER,
    TEMP_CELSIUS,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    DEVICE_CLASS_HUMIDITY,
    LIGHT_LUX,
    DEVICE_CLASS_ILLUMINANCE,
)
from . import DOMAIN, NatureRemoBase, NatureRemoDeviceBase

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo E sensor."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up sensor platform.")
    coordinator = hass.data[DOMAIN]["coordinator"]
    appliances = coordinator.data["appliances"]
    devices = coordinator.data["devices"]
    entities = [
        NatureRemoE(coordinator, appliance)
        for appliance in appliances.values()
        if appliance["type"] == "EL_SMART_METER"
    ]
    for device in devices.values():
        entities.append(NatureRemoTemperatureSensor(coordinator, device))
        entities.append(NatureRemoHumiditySensor(coordinator, device))
        entities.append(NatureRemoIlluminanceSensor(coordinator, device))
    async_add_entities(entities)


class NatureRemoE(NatureRemoBase):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._unit_of_measurement = POWER_WATT

    @property
    def state(self):
        """Return the state of the sensor."""
        appliance = self._coordinator.data["appliances"][self._appliance_id]
        smart_meter = appliance["smart_meter"]
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


class NatureRemoTemperatureSensor(NatureRemoDeviceBase):
    """Implementation of a Nature Remo sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._name = self._name.strip() + " Temperature"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._device["id"] + "-te"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return TEMP_CELSIUS

    @property
    def state(self):
        """Return the state of the sensor."""
        device = self._coordinator.data["devices"][self._device["id"]]
        return device["newest_events"]["te"]["val"]

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_TEMPERATURE


class NatureRemoHumiditySensor(NatureRemoDeviceBase):
    """Implementation of a Nature Remo sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._name = self._name.strip() + " Humidity"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._device["id"] + "-hu"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return PERCENTAGE

    @property
    def state(self):
        """Return the state of the sensor."""
        device = self._coordinator.data["devices"][self._device["id"]]
        return device["newest_events"]["hu"]["val"]

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_HUMIDITY


class NatureRemoIlluminanceSensor(NatureRemoDeviceBase):
    """Implementation of a Nature Remo sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._name = self._name.strip() + " Illuminance"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._device["id"] + "-il"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return LIGHT_LUX

    @property
    def state(self):
        """Return the state of the sensor."""
        device = self._coordinator.data["devices"][self._device["id"]]
        return device["newest_events"]["il"]["val"]

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_ILLUMINANCE 
