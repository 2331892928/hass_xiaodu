import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, CONF_BAIDUID_COOKIE
from .api.XiaoDuAPI import XiaoDuAPI

_LOGGER = logging.getLogger(__name__)


class XiaoduConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    def __init__(self):
        self.cookie = None
        self._home_id_list = None
        self.home_id = None

    async def async_step_user(self, user_input=None):
        # logging.info("进入主页面")
        form = self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BAIDUID_COOKIE): str,
                }
            ),
            description_placeholders={
                "BAIDU_COOKIE_hint": "app login BAIDU_COOKIE",
            },
            errors={},
        )

        if user_input is not None:
            self.cookie = user_input["BAIDUID_COOKIE"]
            session = async_get_clientsession(self.hass)
            xiaoduApi = XiaoDuAPI(self.cookie, session)
            loginFlag = await xiaoduApi.checkSession()
            _LOGGER.info("校验结果: %s", loginFlag)
            if not loginFlag[0]:
                form['errors']['base'] = loginFlag[1]
                return form
            self._home_id_list = await xiaoduApi.get_home_id_list()

            logging.info("通过，下一个页面")
            return await self.async_step_home()
        return form

    async def async_step_home(self, user_input=None):
        errors = {}

        if user_input is not None:
            houseId = user_input["houseId"]
            self.home_id = houseId
            session = async_get_clientsession(self.hass)
            xiaoduApi = XiaoDuAPI(self.cookie, session)
            self._device_wifi_id_dict = await xiaoduApi.get_device_wifi_id_dict(houseId)
            return await self.async_step_device()
        return self.async_show_form(
            step_id="home",
            data_schema=vol.Schema(
                {vol.Required("houseId"): vol.In(self._home_id_list)}
            ),
            errors=errors,
        )

    async def async_step_device(self, user_input=None):
        if user_input is not None:
            applianceIds = user_input["device_ids"]
            devices = []
            for i in applianceIds:
                devices.append(
                    {"applianceId": i,
                     "houseId": self.home_id,
                     "cookie": self.cookie
                     }
                )
            home_name = self._home_id_list[self.home_id]
            # 这里的cookie都是通用的 一个家庭 找出所选设备的信息 将设备类型传入
            session = async_get_clientsession(self.hass)
            xiaoduApi = XiaoDuAPI(cookie=self.cookie, session=session)
            detail = await xiaoduApi.get_details(self.home_id, applianceIds)
            _LOGGER.info(detail)
            applianceTypes = detail['appliances']
            return self.async_create_entry(
                title=f"XiaoDu：{home_name}",
                data={"devices": devices, "applianceTypes": applianceTypes}
            )

        data_schema = vol.Schema(
            {
                vol.Required("device_ids"): cv.multi_select(
                    self._device_wifi_id_dict
                ),
            }
        )
        return self.async_show_form(step_id="device", data_schema=data_schema)
