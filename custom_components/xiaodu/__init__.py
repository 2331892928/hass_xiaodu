import asyncio
import logging

from homeassistant import core, config_entries
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .ApplianceTypes import ApplianceTypes
from .api.XiaoDuAPI import XiaoDuAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Platform
PLATFORMS = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.COVER,
    Platform.CLIMATE,
    Platform.BUTTON,
    Platform.LOCK,
]


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
    # 更新配置 由async_update_entry触发
    if not entry.update_listeners:
        entry.add_update_listener(async_update_options)
        # entry.async_on_unload()
    # async_create_task 被弃用 2025.6
    # 要放在最外边 不然会重复注册导致出错

    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )
    # for i in ('light', 'switch'):
    #     await hass.config_entries.async_forward_entry_setup(
    #         entry, i
    #     )

    return True


# 注册后 要取消注册 才可以进行配置更新 但是只能重新配置一次 再次配置需要重启 不过也够了 cookie 180天
# 距我的观察 卸载重新创建后 async_setup_entry 没有进入 没有 执行 entry.add_update_listener(async_update_options)的导致
# 更新配置 async_update_entry 确实不会用
async def async_unload_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    # if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
    #     hass.data[DOMAIN].pop(entry.entry_id)
    # return unload_ok
    _LOGGER.info("卸载")
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, sd)
                for sd in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_update_options(hass: core.HomeAssistant, entry: config_entries.ConfigEntry):
    # hass.config_entries.async_schedule_reload(config_entry.entry_id)
    entry1 = {**entry.data, **entry.options}
    _LOGGER.info("更新啦:%s", entry1)
    await hass.config_entries.async_reload(entry.entry_id)
