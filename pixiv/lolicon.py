import func_timeout
import importlib
import requests
import time
import json
import sys
import os

from pathlib import Path
from pixivpy3 import AppPixivAPI
from func_timeout import func_set_timeout

from .logger import logger
from .database.operating import add_new, exists
from .image import IMAGE_PATH, image_compression


_REFRESH_TOKEN = Path("refresh_token.txt").read_text()
if _REFRESH_TOKEN == "":
    logger.error("refresh_token.txt 为空，请检查")
    exit()

proxies = {"http": "http://127.0.0.1:10811", "https": "http://127.0.0.1:10811"}


def download_image(url, pid, num, info):
    headers = {"referer": "https://www.pixiv.net/"}
    image_pid = f"{str(pid)}_p{str(num)}"
    for retry in range(5):
        try:
            if os.path.exists(f"{IMAGE_PATH}/comp/{image_pid}.jpg"):
                logger.info("图片已下载完成")
            else:
                logger.info(f"正在下载：{url}")
                r = requests.get(url=url, headers=headers, proxies=proxies)
                image_fcontent = r.content
                with open(f"{IMAGE_PATH}/{image_pid}.jpg", "wb") as f:
                    f.write(image_fcontent)
                logger.info("下载完成")
                time.sleep(0.1)
                image_comp = image_compression(
                    f"{image_pid}.jpg", int(info["sanity_level"])
                )
                if image_comp[0] == 0:
                    add_new(
                        image_pid,
                        info["title"],
                        info["user"]["id"],
                        info["user"]["name"],
                        info["tags"],
                        info["sanity_level"],
                        url,
                    )
                    logger.info("保存完成")
                    return
                else:
                    logger.error("保存失败，正在重试")
        except Exception as e:
            logger.error(f"下载错误，正在重试 {retry} {e}")
            time.sleep(3)
    logger.error("重试五次后仍保存失败，请检查")
    os.system(f"cp {IMAGE_PATH}/{image_pid}.jpg {IMAGE_PATH}/error/")
    os.remove(f"{IMAGE_PATH}/{image_pid}.jpg")
    exit()


@func_set_timeout(10)
def get_id(api, id):
    for _ in range(3):
        try:
            return api.illust_detail(illust_id=id)
        except Exception as e:
            time.sleep(3)
            logger.warning("详情获取错误，正在重试")
            logger.warning(f"{type(e)} {str(e)}")
    logger.error("重试三次后仍然出错，请检查")
    exit()


def lolicon_update(api, offset=None):
    print("========================================================================")
    times = str(int(time.time() * 1000) - 100000000)
    if offset is None:
        data = {
            "size": "original",
            "r18": 2,
            "num": 100,
            "dateAfter": times,
        }
    else:
        datea = (13300 + offset) * 100000000 - 1000
        dateb = (13301 + offset) * 100000000
        data = {
            "size": "original",
            "r18": 2,
            "num": 100,
            "dateAfter": datea,
            "dateBefore": dateb,
        }
        date = datea / 1000
        times = f"{time.gmtime(date).tm_year}-{time.gmtime(date).tm_mon}-{time.gmtime(date).tm_mday}"
        logger.info(f"[{offset}] - [{times}]")

    illustlist = requests.get(
        url="https://api.lolicon.app/setu/v2",
        params=data,
        proxies=proxies,
    ).json()
    ranknum = len(illustlist["data"])
    logger.info(f"已获取lolicon总计 {ranknum} 个")
    for i, image_info in enumerate(illustlist["data"], start=1):
        print("========================================================================")
        image_pid = image_info["pid"]
        image_p = image_info["p"]
        logger.info(f"[{i} / {ranknum}] 作品ID：{image_pid}-{image_p}")
        if not exists(f"{str(image_pid)}_p0"):
            time.sleep(0.3)
            for _ in range(3):
                try:
                    logger.info("正在获取详细信息")
                    image_info_raw = get_id(api, image_pid)
                    break
                except func_timeout.exceptions.FunctionTimedOut:
                    logger.warning("获取详细信息超时，正在重试")
                    time.sleep(2)
            try:
                image_info = image_info_raw["illust"]
                image_id = image_info["id"]
                image_title = image_info["title"]
                logger.info(f"作品标题: {image_title}")
            except KeyError:
                if "error" in image_info_raw:
                    logger.error(image_info_raw["error"])
                    if image_info_raw["error"]["message"] == "Rate Limit":
                        logger.error("已超过最大请求限制，等待十分钟后继续运行")
                        return 2
                    elif image_info_raw["error"]["user_message"] == "该作品已被删除，或作品ID不存在。":
                        logger.warning("该作品已被删除，或作品ID不存在。")
                    elif (
                        image_info_raw["error"]["message"]
                        == "Error occurred at the OAuth process. Please check your Access Token to fix this. Error Message: invalid_grant"
                    ):
                        logger.error("认证已超时，正在重启")
                        return 1
                    else:
                        print(json.dumps(image_info_raw, indent=2, ensure_ascii=False))
                        logger.error("未知错误")
                        exit()
                else:
                    print(json.dumps(image_info_raw, indent=2, ensure_ascii=False))
                    exit()
            else:
                if image_info["type"] == "illust":
                    if image_info["page_count"] < 2:
                        logger.info("单图")
                        image_url = image_info["meta_single_page"].get(
                            "original_image_url"
                        )
                        download_image(
                            image_url,
                            image_id,
                            "0",
                            image_info,
                        )
                    else:
                        logger.info(f"多图({image_info['page_count']})")
                        for image_num, image_mpages in enumerate(
                            image_info["meta_pages"]
                        ):
                            image_url = image_mpages["image_urls"]["original"]
                            download_image(image_url, image_id, image_num, image_info)
                else:
                    logger.info("类型不为 illust 已跳过")
        else:
            logger.info("图片已存在")


def start_spider(first=False):
    offset = 0 if first else None
    while True:
        try:
            importlib.reload(sys)
            sys.dont_write_bytecode = True
            api = AppPixivAPI()
            api.requests.proxies.update(proxies)
            api.set_accept_language("zh")
            logger.info("正在等待pixiv认证")
            api.auth(refresh_token=_REFRESH_TOKEN)
            logger.info("认证完成")
            logger.info("正在开始爬lolicon API")
            if first:
                while True:
                    restarts = lolicon_update(api, offset=offset)
                    if restarts:
                        break
                    offset += 1
            else:
                restarts = lolicon_update(api)
                break
        except Exception as e:
            logger.error(e)
        try:
            if restarts == 1:
                tloop = 1
            elif restarts == 2:
                tloop = 60
        except UnboundLocalError:
            tloop = 10

        logger.info("正在等待重启")
        offset = offset - 4
        for i in range(tloop):
            i = tloop - i
            logger.info(f"还剩 {i * 10} 秒")
            time.sleep(10)
        logger.info("正在重启")
