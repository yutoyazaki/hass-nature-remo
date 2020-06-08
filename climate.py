"""Support for Nature Remo AC."""
import logging

from homeassistant.core import callback
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from . import DOMAIN, CONF_COOL_TEMP, CONF_HEAT_TEMP

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE

MODE_HA_TO_REMO = {
    HVAC_MODE_AUTO: "auto",
    HVAC_MODE_FAN_ONLY: "blow",
    HVAC_MODE_COOL: "cool",
    HVAC_MODE_DRY: "dry",
    HVAC_MODE_HEAT: "warm",
    HVAC_MODE_OFF: "power-off",
}

MODE_REMO_TO_HA = {
    "auto": HVAC_MODE_AUTO,
    "blow": HVAC_MODE_FAN_ONLY,
    "cool": HVAC_MODE_COOL,
    "dry": HVAC_MODE_DRY,
    "warm": HVAC_MODE_HEAT,
    "power-off": HVAC_MODE_OFF,
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo AC."""
    if discovery_info is None:
        return
    _LOGGER.info("Start setup platform")
    coordinator = hass.data[DOMAIN]["coordinator"]
    api = hass.data[DOMAIN]["api"]
    config = hass.data[DOMAIN]["config"]
    appliances = coordinator.data
    async_add_entities(
        [
            NatureRemoAC(coordinator, api, appliance, config)
            for appliance in appliances.values()
            if appliance["type"] == "AC"
        ]
    )


class NatureRemoAC(ClimateEntity):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, coordinator, api, appliance, config):
        self._coordinator = coordinator
        self._api = api
        self._default_temp = {
            HVAC_MODE_COOL: config[CONF_COOL_TEMP],
            HVAC_MODE_HEAT: config[CONF_HEAT_TEMP],
        }
        self._name = f"Nature Remo {appliance['nickname']}"
        self._appliance_id = appliance["id"]
        self._modes = appliance["aircon"]["range"]["modes"]
        self._hvac_mode = None
        self._target_temperature = None
        self._remo_mode = None
        self._fan_mode = None
        self._swing_mode = None
        self._update(appliance["settings"])

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
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        temp_range = self._current_mode_temp_range()
        if len(temp_range) == 0:
            return DEFAULT_MIN_TEMP
        return min(temp_range)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        temp_range = self._current_mode_temp_range()
        if len(temp_range) == 0:
            return DEFAULT_MAX_TEMP
        return max(temp_range)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return list(MODE_HA_TO_REMO.keys())

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._fan_mode

    @property
    def fan_modes(self):
        """List of available fan modes."""
        return self._modes[self._remo_mode]["vol"]

    @property
    def swing_mode(self):
        """Return the swing setting."""
        return self._swing_mode

    @property
    def swing_modes(self):
        """List of available swing modes."""
        return self._modes[self._remo_mode]["dir"]

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return
        target_temp = int(target_temp)
        _LOGGER.info("Set temperature %d", target_temp)
        await self._post({"temperature": f"{target_temp}"})

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        mode = MODE_HA_TO_REMO[hvac_mode]
        _LOGGER.info("Set mode %s", mode)
        if mode == MODE_HA_TO_REMO[HVAC_MODE_OFF]:
            await self._post({"button": mode})
        else:
            await self._post(
                {
                    "operation_mode": mode,
                    "temperature": self._default_temp.get(hvac_mode),
                }
            )

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        await self._post({"air_volume": fan_mode})

    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        await self._post({"air_direction": swing_mode})

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self._update_callback)
        )

    async def async_update(self):
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()

    def _update(self, ac_settings):
        # hold this to determin the ac mode while it's turned-off
        self._remo_mode = ac_settings["mode"]
        try:
            self._target_temperature = float(ac_settings["temp"])
        except:
            self._target_temperature = None

        if ac_settings["button"] == MODE_HA_TO_REMO[HVAC_MODE_OFF]:
            self._hvac_mode = HVAC_MODE_OFF
        else:
            self._hvac_mode = MODE_REMO_TO_HA[self._remo_mode]

        self._fan_mode = ac_settings["vol"] or None
        self._swing_mode = ac_settings["dir"] or None

    @callback
    def _update_callback(self):
        self._update(self._coordinator.data[self._appliance_id]["settings"])
        self.async_write_ha_state()

    async def _post(self, data):
        response = await self._api.post(
            f"/appliances/{self._appliance_id}/aircon_settings", data
        )
        self._update(response)
        self.async_write_ha_state()

    def _current_mode_temp_range(self):
        temp_range = self._modes[self._remo_mode]["temp"]
        return list(map(int, filter(None, temp_range)))
