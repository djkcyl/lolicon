import requests
import time
offset = 0
url = f"https://api.lolicon.app/setu/v2"
# while True:

#     datea = (13300 + offset) * 100000000 - 1000
#     dateb = ((13302 + offset) * 100000000)
#     data = {
#         "size": "original",
#         "r18": 2,
#         "num": 100,
#         "dateAfter": datea,
#         "dateBefore": dateb,
#     }
#     req = requests.get(url, params=data).json()
#     print(time.gmtime(datea / 1000).tm_year, time.gmtime(datea / 1000).tm_mon, time.gmtime(datea / 1000).tm_mday)
#     print(datea, dateb)
#     print(len(req["data"]))
#     offset += 2

from pixiv.lolicon import start_sp

start_sp()