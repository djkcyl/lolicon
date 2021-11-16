import importlib
import sys
import time

from logger import logger
from func_timeout import func_set_timeout
from pixivpy3 import *


_REFRESH_TOKEN = "SKT8S-NkBrEX5F3_ayVvMLv62tDWT33ge-oWPylBaiI"
importlib.reload(sys)
sys.dont_write_bytecode = True
api = ByPassSniApi()
api.require_appapi_hosts(hostname="public-api.secure.pixiv.net")
api.set_accept_language('zh')
logger.info("正在等待pixiv认证")
api.auth(refresh_token=_REFRESH_TOKEN)
logger.info("认证完成")




@func_set_timeout(15)
def get_id(id):
    for _ in range(3):
        try:
            rfirst = api.illust_detail(illust_id=id)
            return rfirst
        except:
            time.sleep(3)
            logger.warning('详情获取错误，正在重试')
    logger.error('重试三次后仍然出错，请检查')
    exit()