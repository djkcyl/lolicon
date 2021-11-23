import time
import base64
import uvicorn

from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from peewee import IntegerField, CharField, Model, fn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse

from pixiv.database.operating import database
from pixiv.lolicon import start_spider


schedulers = BackgroundScheduler()
schedulers.add_job(start_spider, "interval", hours=1)
schedulers.start()


class BaseModel(Model):
    class Meta:
        database = database


class ImageIn(BaseModel):
    num = IntegerField()
    Id = IntegerField()
    name = CharField()
    sanity_level = IntegerField()
    tags = CharField()
    unlike = IntegerField()
    user_id = IntegerField()
    user_name = CharField()
    image_urls = CharField()

    class Meta:
        table_name = "image_info"


description = (
    "san为图片等级：三个等级分别对应R-12 R-16 R-18。\n"
    "only为等级锁定：False为不锁定，即可以搜索到符合该等级及该等级以下的图片。True为锁定，即仅可搜索到符合该等级的图片。\n"
    "bytes为返回图片本体：设置为True后会返回图片本体。\n"
    "redirect为重定向：设置为True后会跳转到图片地址。该选项与bytes不可同时使用\n"
    "original为原图：设置为True后会返回原始图片的地址，请自行准备代理使用。该选项与bytes不可同时使用。"
)


app = FastAPI(title="A60 - LoliconMirror API", description=description, version="1.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def str_to_base64(string: str) -> str:
    return base64.b64encode(string.encode("utf-8")).decode("utf-8")


@app.get("/", status_code=200)
async def get(
    san: Optional[int] = 4,
    only: Optional[bool] = False,
    redirect: Optional[bool] = False,
    bytes: Optional[bool] = False,
    original: Optional[bool] = False,
):
    """
    随机返回一张图
    """
    if san not in [2, 4, 6]:
        return JSONResponse({"code": 400, "msg": "参数错误，san仅可为 2|4|6"}, status_code=400)
    if only:
        whe = ImageIn.sanity_level == san
    else:
        whe = ImageIn.sanity_level <= san

    if bytes and redirect:
        return JSONResponse(
            {"code": 400, "msg": "参数错误，bytes和redirect不能同时为True"}, status_code=400
        )
    if bytes and original:
        return JSONResponse(
            {"code": 400, "msg": "参数错误，original和bytes不能同时为True"}, status_code=400
        )

    ft = time.time()

    imgId = (
        ImageIn.select(ImageIn.Id)
        .where(whe)
        .where(ImageIn.unlike == 0)
        .order_by(fn.Random())
        .limit(1)
    )
    datanum = imgId[0]
    data = ImageIn.select().where(ImageIn.Id == datanum.Id)[0]

    tt = time.time()
    times = tt - ft
    if redirect:
        return RedirectResponse(
            url=data.image_urls
            if original
            else f"https://pic.a60.one:8443/{data.Id}.jpg",
            status_code=302,
        )
    elif bytes:
        return FileResponse(
            Path(f"images/comp/{data.Id}.jpg"),
            headers={"Pic-NAME-Base64": str_to_base64(data.name)},
            media_type="image/jpeg",
        )
    else:
        return JSONResponse(
            {
                "code": 200,
                "id": data.num,
                "pic": data.Id,
                "name": data.name,
                "tags": data.tags,
                "userid": data.user_id,
                "username": data.user_name,
                "sanity_level": data.sanity_level,
                "url": data.image_urls
                if original
                else f"https://pic.a60.one:8443/{data.Id}.jpg",
                "time": str(round(times * 1000)) + "ms",
            }
        )


# @app.get("/get/userid/{userid}")
def get_userid(userid: int):
    ft = time.time()
    data = ImageIn.select().where(ImageIn.user_id == userid)
    data_num = len(data)
    if data_num > 1:
        info_list = []
        for info in data:
            info_list.append(
                {
                    "id": info.num,
                    "pic": info.Id,
                    "name": info.name,
                    "tags": info.tags,
                    "sanity_level": info.sanity_level,
                    "url": f"https://pic.a60.one:8443/{data.Id}.jpg",
                }
            )
        tt = time.time()
        times = tt - ft
        return JSONResponse(
            {
                "code": 200,
                "data": {
                    "userid": data[0].user_id,
                    "username": data[0].user_name,
                    "pic_num": data_num,
                    "pic_list": info_list,
                },
                "time": str(round(times * 1000)) + "ms",
            }
        )
    else:
        return JSONResponse({"code": 404, "error": "未找到相应作者的图片"}, status_code=404)


@app.get("/get/tags/{tags}")
def get_tags(
    tags: str,
    num: Optional[int] = 5,
    san: Optional[int] = 4,
    only: Optional[bool] = False,
    original: Optional[bool] = False,
):
    if san not in [2, 4, 6]:
        return {"code": 500, "msg": "参数错误，san仅可为 2|4|6"}
    if only:
        whe = ImageIn.sanity_level == san
    else:
        whe = ImageIn.sanity_level <= san

    tf = time.time()
    if num > 20:
        return {"code": 511, "error": "操作有误，num最大值为20"}

    data = (
        ImageIn.select()
        .where(ImageIn.unlike == 0)
        .where(whe)
        .where(fn.Lower(ImageIn.tags).contains(tags.lower()))
        .order_by(fn.Random())
        .limit(num)
    )

    data_num = len(data)
    if data_num > 0:
        info_list = []
        for info in data:
            info_list.append(
                {
                    "id": info.num,
                    "pic": info.Id,
                    "name": info.name,
                    "tags": info.tags,
                    "userid": info.user_id,
                    "username": info.user_name,
                    "sanity_level": info.sanity_level,
                    "url": info.image_urls
                    if original
                    else f"https://pic.a60.one:8443/{info.Id}.jpg",
                }
            )
        times = time.time() - tf
        return JSONResponse(
            {
                "code": 200,
                "data": {"tags": tags, "pic_list": info_list},
                "time": str(round(times * 1000)) + "ms",
            }
        )
    else:
        return JSONResponse({"code": 404, "error": "未找到相应tag的图片"}, status_code=404)


if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=404)
