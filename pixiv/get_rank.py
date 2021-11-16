import importlib
import sys
import time
import traceback
from urllib.parse import urlparse

from pixivpy3 import *


def get_rank(mode, a, page):
    _REFRESH_TOKEN = "SKT8S-NkBrEX5F3_ayVvMLv62tDWT33ge-oWPylBaiI"
    importlib.reload(sys)
    sys.dont_write_bytecode = True
    api = ByPassSniApi()
    api.require_appapi_hosts(hostname="public-api.secure.pixiv.net")
    api.set_accept_language('zh')
    api.auth(refresh_token=_REFRESH_TOKEN)

    data_Qur = []
    offset = None
    _Index = 0
    while True:
        time.sleep(1)
        _Index += 1
        if mode == 2:
            rfirst = api.illust_ranking(mode=a, offset=offset)
        elif mode == 1:
            rfirst = api.user_illusts(user_id=a, offset=offset)
        print(f"Query Rank {a} with Offset:{offset};I={_Index}")
        data_Qur += rfirst['illusts']
        if (next_url := rfirst.get('next_url')) is not None:
            try:
                for param in urlparse(next_url).query.split('&'):  # type:str
                    if param.startswith('offset'):
                        offset = param.split('=')[1]
            except:
                traceback.print_exc()
                break
            time.sleep(2)
        else:
            break
        if _Index == page:
            break
    return(data_Qur)