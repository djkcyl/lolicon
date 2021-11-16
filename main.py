import time
import uvicorn

from apscheduler.schedulers.background import BackgroundScheduler
from peewee import IntegerField, CharField, Model, fn
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pixiv.database.operating import database


schedulers = BackgroundScheduler()


class BaseModel(Model):
    class Meta:
        database = database


class ImageIn(BaseModel):
    Id = IntegerField()
    name = CharField()
    sanity_level = IntegerField()
    tags = CharField(max_length=512)
    unlike = IntegerField()
    user_id = IntegerField()
    user_name = CharField()

    class Meta:
        table_name = "image_info"


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    print("startup")


@app.get("/")
async def get(san: Optional[int] = 4, only: Optional[bool] = False):
    """
    随机返回一张图
    """
    if san not in [2, 4, 6]:
        return {"code": 500, "msg": "参数错误，san仅可为 2|4|6"}
    if only:
        whe = ImageIn.sanity_level == san
    else:
        whe = ImageIn.sanity_level <= san

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
    return {
        "code": 200,
        "url": f"https://pic.a60.one:8443/{data.Id}.jpg",
        "pic": data.Id,
        "name": data.name,
        "userid": data.user_id,
        "username": data.user_name,
        "sanity_level": data.sanity_level,
        "time": str(round(times * 1000)) + "ms",
    }


@app.get("/get/userid/{userid}")
def get_userid(userid: int):
    try:
        data = ImageIn.select().where(ImageIn.user_id == userid)
    except Exception:
        return {"code": 501, "error": "数据库查询失败"}
    else:
        data_num = len(data)
        if data_num > 1:
            info_list = []
            for info in data:
                info_list.append(
                    {
                        "url": f"https://pic.a60.one:8443/{data.Id}.jpg",
                        "pic": info.Id,
                        "name": info.name,
                        "sanity_level": info.sanity_level,
                    }
                )
            return {
                "code": 200,
                "data": {
                    "userid": data[0].user_id,
                    "username": data[0].user_name,
                    "pic_num": data_num,
                    "pic_list": info_list,
                },
            }
        else:
            return {"code": 404, "error": "未找到相应作者的图片"}


@app.get("/get/tags/{tags}")
def get_tags(
    tags: str,
    num: Optional[int] = 5,
    san: Optional[int] = 4,
    only: Optional[bool] = False,
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
    try:
        data = (
            ImageIn.select()
            .where(ImageIn.unlike == 0)
            .where(whe)
            .where(fn.Lower(ImageIn.tags).contains(tags.lower()))
            .order_by(fn.Random())
            .limit(num)
        )
    except Exception:
        return {"code": 501, "error": "数据库查询失败"}
    else:
        data_num = len(data)
        if data_num > 0:
            info_list = []
            for info in data:
                info_list.append(
                    {
                        "userid": info.user_id,
                        "username": info.user_name,
                        "url": f"https://pic.a60.one:8443/{info.Id}.jpg",
                        "pic": info.Id,
                        "name": info.name,
                        "sanity_level": info.sanity_level,
                    }
                )
            times = time.time() - tf
            return {
                "code": 200,
                "data": {"tags": tags, "pic_list": info_list},
                "time": str(round(times * 1000)) + "ms",
            }
        else:
            return {"code": 404, "error": "未找到相应tag的图片"}


if __name__ == "__main__":

    uvicorn.run("main:app", host="0.0.0.0", port=404, debug=True, reload=True)
