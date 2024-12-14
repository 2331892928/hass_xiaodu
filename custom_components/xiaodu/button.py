import json

from . import XiaoDuAPI, ApplianceTypes
from homeassistant import core
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    A = ApplianceTypes()
    for device_id in api:
        aapi: XiaoDuAPI = api[device_id]
        # 判断是否是switch设备
        applianceTypes = aapi.applianceTypes
        if not A.is_button(applianceTypes):
            continue
        detail = await aapi.get_detail()
        if detail == []:
            continue
        name = detail['appliance']['friendlyName']
        group_name = detail['appliance']['groupName']
        bot_name = detail['appliance']['botName']
        # 如果是晾衣架 需要 多模式 所以需要重复注册实体
        if 'CLOTHES_RACK' in detail['appliance']['applianceTypes']:
            # 0是 上下 1是功能 确保兼容 还是遍历一下
            panels = []
            for i, p in enumerate(detail['appliance']['panels']):
                if p['title'] == "上下控制":
                    panels = detail['appliance']['panels'][i]['list']
                    break
            for panel in panels:
                TypeStr = panel['name']
                TypeValue = panel['value']
                switchName = panel['label']
                headerName = None
                for i, p in enumerate(panel['actions']):
                    headerName = p['headerName']
                    break
                entities.append(
                    XiaoduButton(api[device_id], name + "_" + switchName, group_name, bot_name, TypeStr, TypeValue, headerName))
    async_add_entities(entities, True)


class XiaoduButton(ButtonEntity):
    def __init__(self, api: XiaoDuAPI, name: str, group_name: str, bot_name: str, switchType: str, typeValue: str, headerName:str):
        self._api = api
        #  重复实体的 uid 会重复 来一个独一无二的
        if switchType != "switch":
            self._attr_unique_id = f"{api.applianceId}_switch_{switchType}_{typeValue}"
        else:
            self._attr_unique_id = f"{api.applianceId}_switch"
        self._attr_name = name
        self._group_name = bot_name
        self._attr_device_class = ButtonDeviceClass.IDENTIFY
        self._attr_icon = "mdi:gesture-tap-button"
        self.switchType = switchType
        self.typeValue = typeValue
        self.headerName = headerName

    async def async_press(self) -> None:
        """Handle the button press."""
        flag = await self._api.button_panel(self.switchType, self.typeValue, self.headerName)
        self.async_schedule_update_ha_state(True)
