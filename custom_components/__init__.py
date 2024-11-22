import asyncio

from dev.xiaodu.custom_components.xiaodu import ApplianceTypes
from xiaodu.api.XiaoDuAPI import XiaoDuAPI
import tracemalloc
# async def main():
#     X = XiaoDuAPI(“”,s)
#     print(X.checkSession())
import aiohttp

if __name__ == "__main__":
    # s = aiohttp.ClientSession()
    # a = asyncio.run(main())
    # print(a)
    # asyncio.run(main())
    # print("主程序结束")
    A = ApplianceTypes()
    print(A.is_light(['LIGHT','DESK_LAMP']))

