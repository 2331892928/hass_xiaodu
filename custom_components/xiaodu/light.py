import logging

from homeassistant import core
from . import XiaoDuAPI, ApplianceTypes

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    A = ApplianceTypes()
    for device_id in api:
        aapi: XiaoDuAPI = api[device_id]
        # 判断是否是switch设备
        applianceTypes = aapi.applianceTypes
        if not A.is_light(applianceTypes):
            continue
        detail = await aapi.get_detail()
        name = detail['appliance']['friendlyName']
        if_onS = str(detail['appliance']['stateSetting']['turnOnState']['value']).lower()
        if if_onS == "on":
            if_on = True
        else:
            if_on = False
        group_name = detail['appliance']['groupName']
        bot_name = detail['appliance']['botName']
        # entities.append(XiaoDuLight(api[device_id], name, if_on, group_name, bot_name))
    # async_add_entities(entities, True)



class XiaoDuLight:
    def __init__(self, api: XiaoDuAPI, name: str, if_on: bool, groupName: str, botName: str):
        self._api = api
        self._attr_unique_id = f"{api.applianceId}_light"
        self._is_on = if_on
        self._name = name
        self._group_name = groupName
        self._bot_ame = botName
        self._attr_icon = "mdi:lightbulb"

    def turn_on(self, **kwargs):
        pass

    def turn_off(self, **kwargs):
        pass
