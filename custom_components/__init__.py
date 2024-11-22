import asyncio

from xiaodu.api.XiaoDu import XiaoDu
import tracemalloc
async def main():
    s = aiohttp.ClientSession()
    print(s.close())
import aiohttp
if __name__ == "__main__":
    # X = XiaoDu("RQd2dNYjJYY1E5bFpJbjljb0xyQ2RBWEdFY21wbGc4ZThTRlFuYkNXSGx6R0puQUFBQUFBPT0AAAAAAAAAAJXkgoDxAmFfsKGwoUG1xLnKysIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOU~O2c8S8ZTeV")
    # a = asyncio.run(X.checkSession())
    # print(X.get_home_id_list())
    # print(a)
    asyncio.run(main())
    print("主程序结束")
