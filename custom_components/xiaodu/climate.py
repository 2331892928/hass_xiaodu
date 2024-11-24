import logging

from homeassistant import core
from . import ApplianceTypes, XiaoDuAPI
from .const import DOMAIN
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, FAN_LOW, FAN_MEDIUM, FAN_HIGH, \
    HVACMode, FAN_MIDDLE, FAN_FOCUS, FAN_DIFFUSE
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    A = ApplianceTypes()
    for device_id in api:
        aapi: XiaoDuAPI = api[device_id]
        # 判断是否是climate设备
        applianceTypes = aapi.applianceTypes
        if not A.is_climate(applianceTypes):
            continue
        detail = await aapi.get_detail()
        name = detail['appliance']['friendlyName']
        if_onS = str(detail['appliance']['stateSetting']['turnOnState']['value']).lower()
        if if_onS == "on":
            if_on = True
        else:
            if_on = False
        entities.append(XiaoDuClimate(api[device_id], name, if_on, detail['appliance']))
    async_add_entities(entities, update_before_add=True)


class XiaoDuClimate(ClimateEntity):
    def __init__(self, api: XiaoDuAPI, name: str, if_on: bool, detail):
        self._api = api
        self._attr_name = name
        self._attr_unique_id = f"{api.applianceId}_cover"
        # 支持的功能 小度 只能 开 关 温度 模式 风速
        self._attr_supported_features = (
                ClimateEntityFeature.TURN_ON |
                ClimateEntityFeature.TURN_OFF |
                ClimateEntityFeature.TARGET_TEMPERATURE |
                ClimateEntityFeature.FAN_MODE
        )
        # 根据平台的空调不同 有5档风的三挡的 兼容最低版本 统一 低中高
        self._attr_fan_modes = [
            FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_MIDDLE, FAN_FOCUS, FAN_DIFFUSE]
        # 模式 支持 制热 制冷 松风 自动 除湿
        self._attr_hvac_modes = [
            HVACMode.COOL, HVACMode.HEAT, HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.OFF, HVACMode.AUTO]
        # 把温度单位 为 摄氏度
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        # 设置最低和最大 小度返回的不准确 为兼容所有 设置为16-32
        self._attr_min_temp = 16
        self._attr_max_temp = 32
        # 设置每次设定步长
        self._attr_target_temperature_step = 1
        # 得初始化一些变量 但不用真的 真的去自动更新
        self._attr_hvac_mode = None
        self._attr_fan_mode = None
        # 内部
        self._fan_mode_lookup = {
            1: FAN_LOW,
            2: FAN_MEDIUM,
            3: FAN_HIGH,
            4: FAN_MIDDLE,
            5: FAN_FOCUS,
            6: FAN_DIFFUSE,
            7: FAN_DIFFUSE,
            8: FAN_DIFFUSE,
            9: FAN_DIFFUSE,
            10: FAN_DIFFUSE
        }
        self._ac_mode_lookup = {
            "dry": "dehumidification",
            "fan_only": "fan"
        }
        self._ac_mode_lookup2 = {
            "dehumidification": HVACMode.DRY,
            "fan": HVACMode.FAN_ONLY
        }
        self.detail = None

    async def async_turn_on(self):
        """Turn the entity on."""
        flag = await self._api.set_ac_on()
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self):
        """Turn the entity off."""
        flag = await self._api.set_ac_off()
        self.async_schedule_update_ha_state(True)

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        if fan_mode == FAN_LOW:
            await self._api.set_ac_fan_jian()
        if fan_mode == FAN_HIGH:
            await self._api.set_ac_fan_jia()
        if fan_mode == FAN_MEDIUM:
            pass

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature.温度"""
        temperature = kwargs.get(ATTR_TEMPERATURE, 26.0)
        # 当前设定的小于即将设定的 就是加 否则减 没办法 小度 方法集 有 setTemperature 但是不能api 只能 语音
        if self.target_temperature < temperature:
            num = int(temperature - self.target_temperature)
            for i in range(num):
                await self._api.set_ac_temperature_jia()
        else:
            num = int(self.target_temperature - temperature)
            for i in range(num):
                await self._api.set_ac_temperature_jian()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

        # 查出别名 没有查出就原样
        mode = self._ac_mode_lookup.get(hvac_mode, hvac_mode)
        if mode == "off":
            flag = await self._api.set_ac_off()
        else:
            # 先开机 如果是关机状态 这样设置模式就直接开机了
            detail = self.detail['appliance']
            turnOnState = detail['stateSetting']['turnOnState']['value']
            if turnOnState.lower() == "off":
                flag = await self._api.set_ac_on()
            flag = await self._api.set_ac_mode(mode)
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        self.detail = await self._api.get_detail()
        detail = self.detail['appliance']
        mode = detail['stateSetting']['mode']['value']
        fanSpeed = detail['stateSetting']['fanSpeed']['value']
        temperature = detail['stateSetting']['temperature']['value']
        turnOnState = detail['stateSetting']['turnOnState']['value']
        if turnOnState.lower() == 'on':
            # 如果没有这个值 要么设备不支持 要么获取失败
            if mode is not None:
                self._attr_hvac_mode = self._ac_mode_lookup2.get(str(mode).lower(), str(mode).lower())
        else:
            self._attr_hvac_mode = HVACMode.OFF

        self._attr_fan_mode = self._fan_mode_lookup.get(fanSpeed, FAN_MEDIUM)
        self._attr_target_temperature = temperature
