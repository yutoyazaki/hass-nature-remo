"""The Nature Remo integration."""
import logging
import requests
import voluptuous as vol

from datetime import timedelta
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import CONF_ACCESS_TOKEN

_LOGGER = logging.getLogger(__name__)
_RESOURCE = "https://api.nature.global/1/"

DOMAIN = "nature_remo"

CONF_COOL_TEMP = "cool_temperature"
CONF_HEAT_TEMP = "heat_temperature"
DEFAULT_COOL_TEMP = 28
DEFAULT_HEAT_TEMP = 20
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=60)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ACCESS_TOKEN): cv.string,
                vol.Optional(CONF_COOL_TEMP, default=DEFAULT_COOL_TEMP): vol.Coerce(
                    int
                ),
                vol.Optional(CONF_HEAT_TEMP, default=DEFAULT_HEAT_TEMP): vol.Coerce(
                    int
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up Nature Remo component."""
    access_token = config[DOMAIN][CONF_ACCESS_TOKEN]
    session = async_get_clientsession(hass)
    api = NatureRemoAPI(access_token, session)
    coordinator = hass.data[DOMAIN] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Nature Remo update",
        update_method=api.get,
        update_interval=DEFAULT_UPDATE_INTERVAL,
    )
    await coordinator.async_refresh()
    hass.data[DOMAIN] = {
        "api": api,
        "coordinator": coordinator,
        "config": config[DOMAIN],
    }

    await discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    await discovery.async_load_platform(hass, "climate", DOMAIN, {}, config)
    return True


class NatureRemoAPI:
    """Nature Remo API client"""

    def __init__(self, access_token, session):
        """Init API client"""
        self._access_token = access_token
        self._session = session

    async def get(self):
        """Get appliance list"""
        headers = {"Authorization": f"Bearer {self._access_token}"}
        response = await self._session.get(f"{_RESOURCE}/appliances", headers=headers)
        return {x["id"]: x for x in await response.json()}

    async def post(self, path, data):
        """Post any request"""
        headers = {"Authorization": f"Bearer {self._access_token}"}
        response = await self._session.post(
            f"{_RESOURCE}{path}", data=data, headers=headers
        )
        return await response.json()
