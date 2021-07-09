"""Support for Nature Remo AC."""
import logging
import asyncio

from homeassistant.core import callback
from homeassistant.components.switch import SwitchEntity
# from homeassistant.components.switch.const import (
#     SERVICE_TOGGLE,
#     SERVICE_TURN_OFF,
#     SERVICE_TURN_ON,
#     STATE_ON,
# )
from . import DOMAIN, NatureRemoBase

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:
    """Set up the Nature Remo IR."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up IR platform.")
    coordinator = hass.data[DOMAIN]["coordinator"]
    api = hass.data[DOMAIN]["api"]
    config = hass.data[DOMAIN]["config"]
    appliances = coordinator.data["appliances"]
    async_add_entities(
        [
            NatureRemoIR(coordinator, api, appliance, config)
            for appliance in appliances.values()
            if appliance["type"] == "IR"
        ]
    )

class NatureRemoIR(NatureRemoBase, SwitchEntity):
    """Implementation of a Nature Remo IR."""

    def __init__(self, coordinator, api, appliance, config) -> None:
        super().__init__(coordinator, appliance)
        self._api = api
        self._signals = {s["name"]: s["id"] for s in appliance["signals"]}
        self._is_on = False

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the entity."""
        # Remo does return light.state however it doesn't seem to be correct
        # in my experience.
        return True

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self._is_on
    
    def _set_on(self, is_on: bool) -> None:
        self._is_on = is_on
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        _LOGGER.debug(self._signals)
        _LOGGER.debug("Set state: ON")
        await self._post(self._signals['on'])
        self._set_on(True)
        _LOGGER.debug("Cannot find on signal")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the switch."""
        _LOGGER.debug("Set state: OFF")
        await self._post(self._signals['off'])
        self._set_on(False)
        _LOGGER.debug("Cannot find off signal")

    # async def _get_signal(self):
    #     _LOGGER.debug("Get Signals from aplications: %s", self._appliance_id)
    #     response = self._api.getany(
    #         f"/appliances/{self._appliance_id}/signals"
    #     )
    #     self._update(response)
    #     self.async_write_ha_state()
    #     # await self._coordinator.async_request_refresh()
    #     # return response

    async def _post(self, signal_id):
        _LOGGER.debug("Send Signals using signal: %s", signal_id)
        response = await self._api.post(f"/signals/{signal_id}/send", None)
        # self._update(response)
        self.async_write_ha_state()

    # async def async_added_to_hass(self):
    #     """Subscribe to updates."""
    #     self.async_on_remove(
    #         self._coordinator.async_add_listener(self.async_write_ha_state)
    #     )

    # async def async_update(self):
    #     """Update the entity.
    #     Only used by the generic entity update service.
    #     """
    #     await self._coordinator.async_request_refresh()

    # @callback
    # def _update_callback(self):
    #     self._update(
    #         self._coordinator.data["appliances"][self._appliance_id]["settings"],
    #         self._coordinator.data["devices"][self._device["id"]],
    #     )
    #     self.async_write_ha_state()

    # def _update(self, sw_settings, device=None):
    #     # hold this to determin the ac mode while it's turned-off
    #     self._remo_mode = sw_settings["mode"]
    #     _LOGGER.debug(sw_settings)
