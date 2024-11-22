import logging

import aiohttp

HOST = 'https://xiaodu.baidu.com'
import logging

_LOGGER = logging.getLogger(__name__)


class XiaoDu:
    def __init__(self, cookie: str, session: aiohttp.ClientSession) -> None:
        self.cookie = cookie
        # self._device_dict = None
        self.Session = session
        self.Header = self._common_header()
        # self.Session = session
        # self.Session.verify = False
        # logging.captureWarnings(True)

    async def checkSession(self):
        submit = {"url": "dueros://smarthome.bot.dueros.ai/gateway/myspeaker"}
        try:
            res = await self.Session.post(HOST + "/appserver/gateway/app/v1", json=submit, headers=self.Header)
            json = await res.json()
            if json['status'] != 0:
                return [False, "invalid_auth"]
            return [True, None]
        except Exception as e:
            logging.error("检查cookie 请求小度出错")
            logging.error(str(e))
            return [False, "cannot_xiaodu"]

    async def auth(self) -> bool:
        return True

    # async def deviceList(self):
    #     return await self._hass.async_add_executor_job(self.doDeviceList)

    async def doDeviceList(self):
        api = "/saiya/smarthome/devicelist?from=h5_control&withscene=1&generalscene=3"
        try:
            res = await self.Session.get(HOST + api, headers=self.Header)
            # logging.info("request \n %s \n %s \n %s \t %s", HOST + api, '', res.status_code, res.json())

            json = await res.json()
            return json['data']['appliances']
        except Exception as e:
            logging.error("请求小度出错")
            return []

    async def switch_on(self, applianceId):
        return await self.switch_toggle(applianceId, True)

    async def switch_off(self, applianceId):
        return await self.switch_toggle(applianceId, False)

    async def switch_status(self, applianceId):
        detail = await self.get_detail(applianceId)
        # if 'attributes' in detail['appliance']:
        #     # 是插座，查找插座的状态
        #     turnOnState = str(detail['appliance']['attributes']['turnOnState']['value']).lower()
        #     if turnOnState == "on":
        #         return True
        #     return False
        # else:
        #     # 其他 如灯
        #     turnOnState = detail['appliance']['status']['turnOnState']['value']
        #     if turnOnState == "已关闭":
        #         return False
        #     return True
        turnOnState = str(detail['appliance']['stateSetting']['turnOnState']['value']).lower()
        if turnOnState == "on":
            return True
        return False

    async def get_detail(self, applianceId):
        api = "/saiya/smarthome/appliancedetails"
        submit = {"applianceId": applianceId, "version": 2, "from": "h5"}
        try:
            res = await self.Session.get(HOST + api, headers=self.Header, json=submit)
            # logging.info("request \n %s \n %s \n %s \t %s", HOST + api, '', res.status_code, res.json())

            json = await res.json()
            if json['status'] == 0:
                return json['data']
            return {}
        except Exception as e:
            logging.error("请求小度出错")
            return {}

    async def switch_toggle(self, applianceId: str, method: bool):
        methodS = "ON"
        methodS2 = "TurnOnRequest"
        if not method:
            methodS = "OFF"
            methodS2 = "TurnOffRequest"
        api = "/saiya/smarthome/directivesend?from=h5_control"
        submit = {
            "header": {"namespace": "DuerOS.ConnectedHome.Control", "name": methodS2, "payloadVersion": 3},
            "payload": {"applianceId": applianceId,
                        "parameters": {"attribute": "turnOnState", "attributeValue": methodS,
                                       "proxyConnectStatus": False},
                        "appliance": {"applianceId": [applianceId]}, "turnOnState": {"value": methodS}}}
        try:
            res = await self.Session.get(HOST + api, headers=self.Header, json=submit)
            # logging.info("request \n %s \n %s \n %s \t %s", HOST + api, '', res.status_code, res.json())

            json = await res.json()
            if json['status'] == 0:
                return [True, None]
            if json['msg'] == 'not login':
                return [False, "cookie失效喔，请及时更新"]
            return [False, json['msg']]
        except Exception as e:
            logging.error("请求小度出错")
            return [False, "请求小度出错"]

    # def exec_scene(self, unique_id):
    #     api = '/saiya/smarthome/unified'
    #     param = {"method": "triggerScene", "params": {"sceneId": unique_id}}
    #     response = self.post(HOST + api, headers=self._common_header(), json=param)
    #     # logging.info("request \n %s \n %s \n %s \t %s", HOST + api, param, response.status_code, response.json())
    #     return response.status_code == 200

    async def get_home_id_list(self):
        api = "/saiya/smarthome/multihouse"
        submit = {"method": "HOUSE_LIST"}
        try:
            res = await self.Session.post(HOST + api, json=submit, headers=self.Header)
            # logging.info("request \n %s \n %s \n %s \t %s", HOST + api, '', res.status, await res.json())

            json = await res.json()
            houseList = json['data']['houseList']
            houseList_2 = {}
            # ha的select需要json来显示用单列表不行
            for i in houseList:
                # houseList_2.append([i['houseId'],i['houseName']])
                houseList_2[i['houseId']] = i['houseName']
            return houseList_2
        except Exception as e:
            logging.error("获取房屋 请求小度出错")
            logging.error(str(e))
            return []

    async def get_device_wifi_id(self, houseId: str):
        api = "/saiya/smarthome/appliance"
        try:
            submit = {"method": "GET_USER_ALL_APPLIANCES",
                      "params": {"from": "h5_control", "withscene": 1, "generalscene": 3}}
            res = await self.Session.post(HOST + api, headers=self.Header, cookies={"HOUSE_ID": houseId}, json=submit)
            # logging.info("request \n %s \n %s \n %s \t %s", HOST + api, '', res.status, await res.json())

            json = await res.json()
            return json['data']['appliances']
        except Exception as e:
            logging.error("请求小度出错")
            logging.error(str(e))
            return []

    async def get_device_wifi_id_dict(self, houseId: str):
        devices = await self.get_device_wifi_id(houseId)
        device_dict = {}
        for i in devices:
            device_dict[i['applianceId']] = i['friendlyName']
        return device_dict

    def _common_header(self):
        return {
            "Cookie": f"BDUSS={self.cookie};BDUSS_BFESS={self.cookie}",
            "User-Agent": 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
            "content-type": "application/json",
            "device-id": "deviceid",
            "host": "xiaodu.baidu.com",
        }


class XiaoDuAC:
    def __init__(self, applianceId: str, cookie: str, session: aiohttp.ClientSession):
        self.applianceId = applianceId
        self.cookie = cookie
        self.Session = session
        self.XiaoDuApi = XiaoDu(cookie, session)

    async def turn_on(self):
        return await self.XiaoDuApi.switch_on(self.applianceId)

    async def turn_off(self):
        return await self.XiaoDuApi.switch_off(self.applianceId)

    async def switch_status(self):
        return await self.XiaoDuApi.switch_status(self.applianceId)

    async def get_name(self):
        detail = await self.XiaoDuApi.get_detail(self.applianceId)
        name = detail['appliance']['friendlyName']
        return name

    async def get_detail(self):
        return await self.XiaoDuApi.get_detail(self.applianceId)
