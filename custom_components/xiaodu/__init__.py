import logging

from homeassistant import core, config_entries
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api.XiaoDu import XiaoDuAC
from .const import DOMAIN
_LOGGER = logging.getLogger(__name__)
async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the xiaodu component."""
    # @TODO: Add setup code.
    return True


async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    session = async_get_clientsession(hass)
    # Setup devices based on the selected devices from the config flow
    for device_info in entry.data["devices"]:
        applianceId = device_info["applianceId"]
        cookie = device_info["cookie"]
        hass.data[DOMAIN][entry.entry_id][applianceId] = XiaoDuAC(
            applianceId=applianceId,
            cookie=cookie,
            session=session
        )
        # async_create_task 被弃用 2025.6
        await hass.config_entries.async_forward_entry_setup(
            entry, Platform.SWITCH
        )

    return True