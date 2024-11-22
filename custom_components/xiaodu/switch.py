from homeassistant import core
from homeassistant.components.switch import SwitchEntity
from . import XiaoDuAC
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    for device_id in api:
        aapi: XiaoDuAC = api[device_id]
        detail = await aapi.get_detail()
        name = detail['appliance']['friendlyName']
        if_onS = str(detail['appliance']['stateSetting']['turnOnState']['value']).lower()
        if if_onS == "on":
            if_on = True
        else:
            if_on = False
        group_name = detail['appliance']['groupName']
        bot_name = detail['appliance']['botName']
        entities.append(XiaoduSwitch(api[device_id], name, if_on, group_name, bot_name))
    async_add_entities(entities, True)


class XiaoduSwitch(SwitchEntity):
    def __init__(self, api: XiaoDuAC, name: str, if_on: bool, groupName: str, botName: str):
        self._api = api
        self._attr_unique_id = f"{api.applianceId}_screen"
        self._is_on = if_on
        self._name = name
        self._group_name = groupName
        self._bot_ame = botName
        self._attr_icon = "mdi:lightbulb"

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
        flag = await self._api.turn_on()
        self._is_on = True
        await self.async_update()
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self):
        await self._api.turn_off()
        self._is_on = False
        await self.async_update()
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        self._is_on = await self._api.switch_status()
