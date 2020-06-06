"""The Nature Remo integration."""
import logging
import requests
import voluptuous as vol

from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.const import CONF_ACCESS_TOKEN

_LOGGER = logging.getLogger(__name__)
_RESOURCE = "https://api.nature.global/1/"

DOMAIN = "nature_remo"

CONF_COOL_TEMP = "cool_temperature"
CONF_HEAT_TEMP = "heat_temperature"
DEFAULT_COOL_TEMP = 28
DEFAULT_HEAT_TEMP = 20

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ACCESS_TOKEN): cv.string,
                vol.Optional(CONF_COOL_TEMP, default=DEFAULT_COOL_TEMP): vol.Coerce(int),
                vol.Optional(CONF_HEAT_TEMP, default=DEFAULT_HEAT_TEMP): vol.Coerce(int),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up Nature Remo component."""
    access_token = config[DOMAIN][CONF_ACCESS_TOKEN]
    api = NatureRemoAPI(access_token)
    appliances = api.get_appliance_list()
    hass.data[DOMAIN] = {
        "api": api,
        "appliances": appliances,
        "config": config[DOMAIN]
    }

    discovery.load_platform(hass, 'sensor', DOMAIN, {}, config)
    discovery.load_platform(hass, 'climate', DOMAIN, {}, config)
    return True

class NatureRemoAPI:
  def __init__(self, access_token):
      self._access_token = access_token
  
  def get_appliance_list(self, appliance_id=None):
    headers = {"Authorization": f"Bearer {self._access_token}"}
    response = requests.get(f"{_RESOURCE}/appliances", headers=headers).json()
    if appliance_id:
      return next(appliance for appliance in response if appliance["id"] == appliance_id)
    else:
      return response

  def post(self, path, data):
    headers = {"Authorization": f"Bearer {self._access_token}"}
    return requests.post(f"{_RESOURCE}{path}", data=data, headers=headers).json()