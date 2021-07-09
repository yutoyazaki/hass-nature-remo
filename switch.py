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
        # self._signals = {s["name"]: s["id"] for s in appliance["signals"]}
        self._signals = appliance["signals"]
        self._is_on = False

    @property
    def assumed_state(self) -> bool:
        """Return True if unable to access real state of the entity."""
        # Remo does return light.state however it doesn't seem to be correct
        # in my experience.
        return True

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return self._is_on
    
    def _set_on(self, is_on: bool) -> None:
        self._is_on = is_on
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        _LOGGER.debug("Set state: ON")
        try:
            await self._post_icon([
                "ico_on",
                "ico_io",
            ])
            self._set_on(True)
        except:
            _LOGGER.debug("Cannot find on signal")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the switch."""
        _LOGGER.debug("Set state: OFF")
        try:
            await self._post_icon([
                "ico_off",
                "ico_io",
            ])
            self._set_on(False)
        except:
            _LOGGER.debug("Cannot find off signal")

    async def _post_icon(self, names: [str]) -> None:
        images = [x.get("image") for x in self._signals]
        for name in names:
            if name in images:
                await self._post(self._signals[images.index(name)]["id"])
                break

    async def _post(self, signal: str) -> None:
        _LOGGER.debug("Send Signals using signal: %s, signal")
        response = await self._api.post(f"/signals/{signal}/send", None)
        self.async_write_ha_state()
