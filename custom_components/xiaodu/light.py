import logging

from homeassistant import core
from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, \
    ATTR_COLOR_TEMP_KELVIN, LightEntityFeature, ATTR_EFFECT
from . import XiaoDuAPI, ApplianceTypes

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, config_entry, async_add_entities):
    api = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    A = ApplianceTypes()
    for device_id in api:
        aapi: XiaoDuAPI = api[device_id]
        # 判断是否是light设备
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
        entities.append(XiaoDuLight(api[device_id], name, if_on, detail['appliance']))
    async_add_entities(entities, update_before_add=True)


class XiaoDuLight(LightEntity):

    # def effect(self) -> str | None:
    #     return 'test'
    #
    # def effect_list(self) -> list[str] | None:
    #     return ['test']

    def __init__(self, api: XiaoDuAPI, name: str, if_on: bool, detail):
        self._api = api
        self._attr_unique_id = f"{api.applianceId}_light"
        # self._attr_is_on = if_on
        self._is_on = if_on
        self._attr_name = name
        self._group_name = detail['groupName']
        self.pColorMode = None
        self.effectList = {}
        if if_on:
            self._attr_icon = "mdi:lightbulb"
        else:
            self._attr_icon = "mdi:lightbulb-off"

        # 新的集成必须同时实现color_mode和supported_color_modes。如果集成升级以支持颜色模式，则应同时实现color_mode和。supported_color_modes
        # self._attr_color_mode = ColorMode.COLOR_TEMP
        # 如果支持亮度控制 并且支持色温 有色温的应该都支持模式 不必判断
        if 'brightness' in detail['stateSetting'] and 'colorTemperatureInKelvin' in detail['stateSetting']:
            self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self.pColorMode = ColorMode.COLOR_TEMP
            brightness = detail['stateSetting']['brightness']['value']
            self._brightness = round(brightness / 100 * 255)
            # 没有色温 只有亮度
        if 'brightness' in detail['stateSetting'] and 'colorTemperatureInKelvin' not in detail['stateSetting']:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self.pColorMode = ColorMode.BRIGHTNESS
            brightness = detail['stateSetting']['brightness']['value']
            self._brightness = round(brightness / 100 * 255)
        if 'mode' in detail['stateSetting']:
            self._attr_supported_features = LightEntityFeature(
                LightEntityFeature.EFFECT)
            effect_list = []
            valueRangeMap = detail['stateSetting']['mode']['valueRangeMap']
            for i in valueRangeMap:
                effect_list.append(valueRangeMap[i])
            self._attr_effect_list = effect_list
            if 'value' not in detail['stateSetting']['mode']:
                mode = "NIGHT_UP"
            else:
                mode = detail['stateSetting']['mode']['value']
            self._attr_effect = valueRangeMap[mode]

        # 最基础的只有开和关 没有模式 色温 亮度控制
        if 'mode' not in detail['stateSetting'] and 'brightness' not in detail['stateSetting'] and 'colorTemperatureInKelvin' not in detail['stateSetting']:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF
            self.pColorMode = ColorMode.ONOFF

    @property
    def brightness(self):
        return self._brightness

    @property
    def color_temp_kelvin(self) -> int | None:
        return self._color_temp_kelvin

    async def async_turn_on(self, **kwargs):
        # 如果kwargs为空就直接开 否则控制亮度
        # {'brightness': 145} 1-255
        # _LOGGER.info(kwargs)
        # 开
        if kwargs == {}:
            flag = await self._api.switch_on()
        # 控制亮度 计算亮度 1-255
        if 'brightness' in kwargs:
            brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
            attributeValue = round(brightness / 255 * 100)
            self._brightness = brightness
            flag = await self._api.brightness(attributeValue)
        if 'color_temp_kelvin' in kwargs:
            # 无传则居中
            color_temp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN, 4614)
            color_temp = kwargs.get(ATTR_COLOR_TEMP, 261)
            self._attr_color_temp_kelvin = color_temp_kelvin
            # 将色温换算成比例
            # (比例 / 100 * 差值)+最小=真实色温
            mddile = self.max_color_temp_kelvin - self.min_color_temp_kelvin
            attributeValue = round((color_temp_kelvin - self.min_color_temp_kelvin) / mddile * 100)
            flag = await self._api.colorTemperatureInKelvin(attributeValue)
        if 'effect' in kwargs:
            effect = kwargs.get(ATTR_EFFECT, "读写")
            mode = "READING"
            for i in self.effectList:
                if self.effectList[i] == effect:
                    mode = i
            flag = await self._api.light_set_mode(mode)
        self._is_on = True
        self._attr_icon = "mdi:lightbulb"
        # await self.async_update()
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self, **kwargs):
        flag = await self._api.switch_off()
        self._is_on = False
        self._attr_icon = "mdi:lightbulb-off"
        # await self.async_update()
        self.async_schedule_update_ha_state(True)
        # 如果状态错误 回退
        if not flag:
            self._is_on = True
            self._attr_icon = "mdi:lightbulb"
            self.async_schedule_update_ha_state(True)

    async def async_update(self):
        self._is_on = await self._api.switch_status()
        detail = await self._api.get_detail()
        detail = detail['appliance']
        self.effectList = detail['stateSetting']['mode']['valueRangeMap']
        if self.pColorMode == ColorMode.BRIGHTNESS:
            # 更新亮度
            brightness = detail['stateSetting']['brightness']['value']
            self._brightness = round(brightness / 100 * 255)
            # self._attr_brightness = brightness
        elif self.pColorMode == ColorMode.COLOR_TEMP:
            # 更新亮度
            brightness = detail['stateSetting']['brightness']['value']
            self._brightness = round(brightness / 100 * 255)
            # 更新色温和色温范围 得到的色温是比例
            colorTemperatureInKelvin = detail['stateSetting']['colorTemperatureInKelvin']['value']
            # 换算色温比例
            colorTemperatureInKelvinMin = detail['stateSetting']['colorTemperatureInKelvin']['valueKelvinRangeMap']['min']
            colorTemperatureInKelvinMax = detail['stateSetting']['colorTemperatureInKelvin']['valueKelvinRangeMap']['max']
            self._attr_min_color_temp_kelvin = colorTemperatureInKelvinMin
            self._attr_min_mireds = colorTemperatureInKelvinMin
            self._attr_max_color_temp_kelvin = colorTemperatureInKelvinMax
            self._attr_max_mireds = colorTemperatureInKelvinMax
            mddile = colorTemperatureInKelvinMax - colorTemperatureInKelvinMin
            # (比例 / 100 * 差值)+最小=真实色温
            colorTemperatureInKelvin = round(colorTemperatureInKelvin / 100 * mddile) + colorTemperatureInKelvinMin
            self._attr_color_temp_kelvin = colorTemperatureInKelvin
            self._color_temp_kelvin = colorTemperatureInKelvin
            # 模式
            # self._attr_effect_list = ['test']