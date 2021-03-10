"""Support for Nature Remo Light."""
import logging
from enum import Enum

import voluptuous as vol
from homeassistant.components.light import (
    LightEntity,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR_TEMP,
)
from homeassistant.helpers import config_validation as cv, entity_platform
from . import DOMAIN, NatureRemoBase

_LOGGER = logging.getLogger(__name__)

SERVICE_PRESS_LIGHT_BUTTON = "press_light_button"
SERVICE_PRESS_CUSTOM_BUTTON = "press_custom_button"

ATTR_IS_NIGHT = "is_night"


class LightButton(Enum):
    on = "on"
    max = "on-100"
    favorite = "on-favorite"
    on_off = "onoff"
    night = "night"
    bright_up = "bright-up"
    bright_down = "bright-down"
    color_temp_up = "colortemp-up"
    color_temp_down = "colortemp-down"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo Light."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up light platform.")
    coordinator = hass.data[DOMAIN]["coordinator"]
    api = hass.data[DOMAIN]["api"]
    config = hass.data[DOMAIN]["config"]
    appliances = coordinator.data["appliances"]
    async_add_entities(
        [
            NatureRemoLight(coordinator, api, appliance, config)
            for appliance in appliances.values()
            if appliance["type"] == "LIGHT"
        ]
    )
    platform = entity_platform.current_platform.get()
    _LOGGER.debug("Registering light entity services.")
    platform.async_register_entity_service(
        SERVICE_PRESS_LIGHT_BUTTON,
        {vol.Required("button_name"): cv.enum(LightButton)},
        NatureRemoLight.async_press_light_button,
    )
    platform.async_register_entity_service(
        SERVICE_PRESS_CUSTOM_BUTTON,
        {vol.Required("button_name"): cv.string},
        NatureRemoLight.async_press_custom_button,
    )


class NatureRemoLight(NatureRemoBase, LightEntity):
    """Implementation of a Nature Remo Light component."""

    def __init__(self, coordinator, api, appliance, config):
        super().__init__(coordinator, appliance)
        self._api = api
        self._buttons = [b["name"] for b in appliance["light"]["buttons"]]
        self._signals = {s["name"]: s["id"] for s in appliance["signals"]}
        self._is_on = False
        self._is_night = False

    # Entity methods

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the entity."""
        # Remo does return light.state however it doesn't seem to be correct
        # in my experience.
        return True

    # ToggleEntity methods

    @property
    def is_on(self):
        """Return True if entity is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self._post({"button": "on"})
        self._set_on(True)

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        await self._post({"button": "onoff"})
        self._set_on(False)

    # LightEntity methods

    @property
    def supported_features(self):
        """Flag supported features."""
        # Even though the IR remote of the light may support adjusting
        # the brightness and color temperature, it's only ever by 1 grade
        # and we don't know how many grades there are, so we can't even
        # map the grades into anything useful.
        return 0

    @property
    def state_attributes(self):
        """Return state attributes."""
        if not self.is_on:
            return None

        return {ATTR_IS_NIGHT: self._is_night}

    # own methods

    async def _post(self, data):
        await self._api.post(f"/appliances/{self._appliance_id}/light", data)

    def _set_on(self, is_on, is_night = False):
        self._is_on = is_on
        self._is_night = is_night
        self.async_write_ha_state()

    async def async_press_light_button(self, service_call):
        button = LightButton(service_call.data["button_name"])
        await self._post({"button": button.value})
        if button == LightButton.on_off and self._is_on \
                or button == LightButton.night and self._is_night:
            self._set_on(False)
        else:
            self._set_on(True, button == LightButton.night)

    async def async_press_custom_button(self, service_call):
        signal_name = service_call.data["button_name"]
        signal_id = self._signals.get(signal_name)
        if signal_id is None:
            _LOGGER.error(f"Invalid signal name: {signal_name}")
            return
        await self._api.post(f"/signals/{signal_id}/send", None)
        self._set_on(True)
