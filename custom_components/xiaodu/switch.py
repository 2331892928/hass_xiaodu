import json
import random

from homeassistant import core
from homeassistant.components.switch import SwitchEntity
from . import XiaoDuAPI, ApplianceTypes
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
        if not A.is_switch(applianceTypes):
            continue
        # 防止某些不是switch设备冒充switch设备，导致所有的switch设备注册失败，此bug由wx用户：rocky** 若** 提供
        try:
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
                    if p['title'] == "功能控制":
                        panels = detail['appliance']['panels'][i]['list']
                        break
                for panel in panels:
                    payload = None
                    headerNameOn = None
                    headerNameOff = None
                    TypeStr = panel['name']
                    TypeValue = panel['value']
                    switchName = panel['label']
                    # 更新的时候传状态
                    if_on = False
                    for i, p in enumerate(panel['actions']):
                        if 'payload' in p:
                            payload = json.dumps(p['payload'])
                        if i == 0:
                            headerNameOn = p['headerName']
                        if i == 1:
                            headerNameOff = p['headerName']
                    entities.append(
                        XiaoduSwitch(api[device_id], name + "_" + switchName, if_on, group_name, bot_name, TypeStr,
                                     TypeValue, headerNameOn, headerNameOff, payload))
            else:
                if_onS = str(detail['appliance']['stateSetting']['turnOnState']['value']).lower()
                if if_onS == "on":
                    if_on = True
                else:
                    if_on = False
                entities.append(XiaoduSwitch(api[device_id], name, if_on, group_name, bot_name))
        except Exception as e:
            _LOGGER.error(e)
            continue
    async_add_entities(entities, True)


class XiaoduSwitch(SwitchEntity):
    def __init__(self, api: XiaoDuAPI, name: str, if_on: bool, groupName: str, botName: str, switchType: str = "switch", typeValue: str = None, headerNameOn: str = None, headerNameOff: str = None, payloadObject: str = None):
        self._api = api
        #  重复实体的 uid 会重复 来一个独一无二的
        if switchType != "switch":
            self._attr_unique_id = f"{api.applianceId}_switch_{switchType}_{typeValue}"
        else:
            self._attr_unique_id = f"{api.applianceId}_switch"
        self._is_on = if_on
        # self._attr_is_on = if_on
        self._name = name
        self._group_name = botName
        self.switchType = switchType
        self.typeValue = typeValue
        self.headerNameOn = headerNameOn
        self.headerNameOff = headerNameOff
        self.payloadObject = payloadObject
        if if_on:
            self._attr_icon = "mdi:toggle-switch-variant"
        else:
            self._attr_icon = "mdi:toggle-switch-variant-off"


    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._api.applianceId)},
            "name": self._name,
            "manufacturer": self._group_name,
        }

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self):
        if self.switchType == "switch":
            flag = await self._api.switch_on()
        else:
            flag = await self._api.switch_panel_on(self.switchType, self.typeValue, self.headerNameOn, self.headerNameOff, self.payloadObject)
        self._is_on = True
        self._attr_icon = "mdi:toggle-switch-variant"
        # await self.async_update()
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self):
        if self.switchType == "switch":
            flag = await self._api.switch_off()
        else:
            flag = await self._api.switch_panel_off(self.switchType, self.typeValue, self.headerNameOn, self.headerNameOff, self.payloadObject)
        self._is_on = False
        self._attr_icon = "mdi:toggle-switch-variant-off"
        # await self.async_update()
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        if self.switchType == "switch":
            self._is_on = await self._api.switch_status()
        else:
            # 单个
            self._is_on = await self._api.switch_panel_status(self.switchType, self.typeValue, self.headerNameOn, self.headerNameOff, self.payloadObject)

    async def async_added_to_hass(self):
        await self.async_update()
