import logging

from homeassistant import core
from .const import DOMAIN
from . import XiaoDuAPI, ApplianceTypes
from homeassistant.components.cover import CoverEntity, CoverEntityFeature

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: core.HomeAssistant, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    A = ApplianceTypes()
    for device_id in api:
        aapi: XiaoDuAPI = api[device_id]
        # 判断是否是cover设备
        applianceTypes = aapi.applianceTypes
        if not A.is_cover(applianceTypes):
            continue
        detail = await aapi.get_detail()
        name = detail['appliance']['friendlyName']
        if_onS = str(detail['appliance']['stateSetting']['turnOnState']['value']).lower()
        if if_onS == "on":
            if_on = True
        else:
            if_on = False
        entities.append(XiaoDuCover(api[device_id], name, if_on, detail['appliance']))
    async_add_entities(entities, update_before_add=True)


class XiaoDuCover(CoverEntity):
    def __init__(self, api: XiaoDuAPI, name: str, if_on: bool, detail):
        self._api = api
        self._attr_name = name
        self._attr_unique_id = f"{api.applianceId}_cover"
        self._attr_supported_features = CoverEntityFeature(CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE |
                                                           CoverEntityFeature.STOP)
        self._attr_is_closed = not if_on
        if if_on:
            self._attr_icon = "mdi:curtains"
        else:
            self._attr_icon = "mdi:curtains-closed"

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        flag = await self._api.set_curtain_open()
        # await self.async_update()
        self.async_schedule_update_ha_state(True)

    async def async_close_cover(self, **kwargs):
        flag = await self._api.set_curtain_close()
        # await self.async_update()
        self.async_schedule_update_ha_state(True)

    async def async_stop_cover(self, **kwargs):
        flag = await self._api.set_curtain_stop()
        # await self.async_update()
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        if_on = await self._api.switch_status()
        self._attr_is_closed = if_on
        if if_on:
            self._attr_icon = "mdi:curtains"
        else:
            self._attr_icon = "mdi:curtains-closed"
