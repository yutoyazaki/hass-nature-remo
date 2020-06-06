"""Support for Nature Remo E energy sensor."""
import logging

import requests
import voluptuous as vol

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
    DEVICE_CLASS_POWER,
)

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Nature Remo E sensor."""
    if discovery_info is None:
        return
    _LOGGER.info("Start setup platform")
    api = hass.data[DOMAIN]["api"]
    appliances = hass.data[DOMAIN]["appliances"]
    add_entities(
        [
            NatureRemoE(api, appliance)
            for appliance in appliances
            if appliance["type"] == "EL_SMART_METER"
        ]
    )


class NatureRemoE(Entity):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, api, appliance):
        self._api = api
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
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_POWER

    def update(self):
        """Get the latest data, update state."""
        appliance = self._api.get_appliance_list(self._appliance_id)
        smart_meter = appliance["smart_meter"]
        for echonetlite_properties in smart_meter["echonetlite_properties"]:
            epc = echonetlite_properties["epc"]
            val = echonetlite_properties["val"]
            if epc == 211:
                coefficient = int(val)
            elif epc == 215:
                cumulative_electric_energy_effective_digits = int(val)
            elif epc == 224:
                normal_direction_cumulative_electric_energy = int(val)
            elif epc == 225:
                cumulative_electric_energy_unit = int(val)
            elif epc == 227:
                reverse_direction_cumulative_electric_energy = int(val)
            elif epc == 231:
                measured_instantaneous = val
                _LOGGER.info("Success to fetch: %sW", measured_instantaneous)
                self._state = measured_instantaneous
