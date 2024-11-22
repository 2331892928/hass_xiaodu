import logging

from homeassistant import core, config_entries
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .ApplianceTypes import ApplianceTypes
from .api.XiaoDuAPI import XiaoDuAPI
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
    applianceTypes = entry.data["applianceTypes"]
    # Setup devices based on the selected devices from the config flow
    for i, device_info in enumerate(entry.data["devices"]):
        applianceId = device_info["applianceId"]
        houseId = device_info["houseId"]
        cookie = device_info["cookie"]
        hass.data[DOMAIN][entry.entry_id][applianceId] = XiaoDuAPI(
            applianceId=applianceId,
            houseId=houseId,
            cookie=cookie,
            session=session,
            applianceTypes=applianceTypes[i]['applianceTypes']
        )
        # async_create_task 被弃用 2025.6
    # 要放在最外边 不然会重复注册导致出错
    # Platform
    PLATFORMS = [
        Platform.LIGHT,
        Platform.SWITCH,
    ]
    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )
    # for i in ('light', 'switch'):
    #     await hass.config_entries.async_forward_entry_setup(
    #         entry, i
    #     )

    return True



