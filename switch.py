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
    loop = hass.loop
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
        self._state = False
        await self._get_signal()

    async def async_added_to_hass(self) -> None:
        """Set up a switch."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self._update_callback)
        )

    # @property
    # def state(self):
    #     """Return the state of the switch."""
    #     return self._state

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self._state

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        _LOGGER.debug("Set state: ON")
        # signal_list = await self._get_signal()
        signal_list = asyncio.run_coroutine_threadsafe(self._get_signal(), self._coordinator).result()
        # find on signal
        for signal in signal_list:
            _LOGGER.debug("~~~~~~~~~~", signal, "~~~~~~~~~~")
            if signal['name'] == "on":
                self._post(signal['id'])
                self._state = True
                return
        _LOGGER.debug("Cannot find on signal")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the switch."""
        _LOGGER.debug("Set state: OFF")
        # signal_list = await self._get_signal()
        signal_list = asyncio.run_coroutine_threadsafe(self._get_signal(), self._coordinator).result()
        # find off signal
        _LOGGER.debug("===== Check =====")
        for signal in signal_list:
            _LOGGER.debug("~~~~~~~~~~", signal, "~~~~~~~~~~")
            if signal['name'] == "off":
                self._post(signal['id'])
                self._state = False
                return
        _LOGGER.debug("Cannot find off signal")

    async def _get_signal(self):
        _LOGGER.debug("Get Signals from aplications: %s", self._appliance_id)
        response = self._api.getany(
            f"/appliances/{self._appliance_id}/signals"
        )
        self._update(response)
        self.async_write_ha_state()
        # await self._coordinator.async_request_refresh()
        # return response

    async def _post(self, signal_id):
        _LOGGER.debug("Send Signals using signal: %s", signal_id)
        response = await self._api.post(
            f"/signals/{signal_id}/send"
        )
        # self._update(response)
        self.async_write_ha_state()

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

    @callback
    def _update_callback(self):
        self._update(
            self._coordinator.data["appliances"][self._appliance_id]["settings"],
            self._coordinator.data["devices"][self._device["id"]],
        )
        self.async_write_ha_state()

    def _update(self, sw_settings, device=None):
        # hold this to determin the ac mode while it's turned-off
        self._remo_mode = sw_settings["mode"]

        _LOGGER.debug(sw_settings)
