from peewee import SqliteDatabase, Model, IntegerField, CharField, DateField, AutoField
from datetime import date
from cms import image_moderation
from pathlib import Path
import random

from pixiv.logger import logger

database = SqliteDatabase("pixiv.db")
imagepath = Path("/data/pixiv/images/comp")
Suggestion = {"Pass": 0, "Review": 1, "Block": 2}
Label = {"Sexy": 1, "Porn": 2, "Illegal": 3, "Polity": 4}
SubLabel = {
    "ACGSexy": 1,
    "ACGPorn": 2,
    "SexyHigh": 3,
    "PornSum": 4,
    "PornHigh": 5,
    "SexySum": 6,
    "BedLive": 7,
    "CarLive": 8,
    "SM": 9,
    "JapanFlag": 10,
    "GermanyFlag": 11,
    "CPCEmblem": 12,
    "CPCFlag": 13,
    "ChineseNationalFlag": 14,
    "GongQingTuanFlag": 15,
    "ButtocksExposed": 16,
    "WomenSexyBack": 17,
    "WomenPrivatePart": 18,
    "Smoking": 19,
    "RMB": 20,
    "SexualSuggestion": 21,
    "ShaoXianDuiFlag": 22,
    "ChineseMap": 23,
    "SexyBehavior": 24,
}


class UnknownField(object):
    def __init__(self, *_, **__):
        pass


class BaseModel(Model):
    class Meta:
        database = database


class ImageIn(BaseModel):
    date = DateField()
    Id = IntegerField()
    image_urls = CharField()
    name = CharField()
    num = AutoField()
    sanity_level = IntegerField()
    tags = CharField(max_length=512)
    unlike = IntegerField()
    user_id = IntegerField()
    user_name = CharField()
    tencent_safe = IntegerField()
    isModeration = IntegerField()
    ModerationSuggestion = IntegerField()
    ModerationLabel = IntegerField()
    ModerationSubLabel = IntegerField()
    ModerationScore = IntegerField()

    class Meta:
        table_name = "image_info"


database.create_tables([ImageIn], safe=True)


def add_new(pid, name, user_id, user_name, tags, sanity_level, image_urls):
    tag = ""
    for i in tags:
        tag += i["name"] + ","
        if i["translated_name"] is not None:
            tag += i["translated_name"] + ","

    logger.info("正在审核图片")
    res = image_moderation(imagepath.joinpath(f"{pid}.jpg").read_bytes())

    txSuggestion = res["Suggestion"]
    txLabel = res["Label"]
    txSubLabel = res["SubLabel"]
    txScore = res["Score"]

    logger.info(f"图片审核完成 {txSuggestion} {txLabel} {txSubLabel} {txScore}")

    p = ImageIn(
        Id=pid,
        name=name,
        date=date.today(),
        user_id=user_id,
        user_name=user_name,
        tags=tag[:-1],
        sanity_level=sanity_level,
        unlike=False,
        image_urls=image_urls,
        tencent_safe=1 if txSuggestion == "Pass" else 0,
        ModerationSuggestion=Suggestion[txSuggestion],
        ModerationLabel=0 if txLabel == "Normal" else Label[txLabel],
        ModerationSubLabel=SubLabel[txSubLabel] if txSubLabel else 0,
        ModerationScore=txScore,
        isModeration=1,
    )
    p.save()


def exists(pid):
    p = ImageIn.select().where(ImageIn.Id == pid)
    return bool(p.exists())


def unlike(type, pid):
    if type == 1:
        p = ImageIn.select().where(ImageIn.Id == pid)
        if not p.exists():
            return 0
        try:
            q = ImageIn.update({ImageIn.unlike: 1}).where(ImageIn.Id == pid)
            q.execute()
            return 1
        except Exception:
            return 2
    elif type in [2, 3]:
        p = ImageIn.select().where(ImageIn.user_id == int(pid))
        if not p.exists():
            return 0
        try:
            q = ImageIn.update({ImageIn.unlike: 1}).where(ImageIn.user_id == int(pid))
            q.execute()
            return 1
        except Exception:
            return 2


def search(type, value):
    if type == "san":
        try:
            data: ImageIn = random.choice(
                ImageIn.select().where(
                    (ImageIn.unlike == 0) & (ImageIn.sanity_level == value)
                )
            )
            info = [data.Id, data.name, data.user_id, data.user_name, data.sanity_level]
            return (1, info)
        except Exception:
            return (0, None)
    if type == "random":
        data = random.choice(ImageIn.select().where(ImageIn.unlike == 0))
        info = [data.Id, data.name, data.user_id, data.user_name, data.sanity_level]
        return (1, info)
