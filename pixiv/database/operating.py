from peewee import SqliteDatabase, Model, IntegerField, CharField, DateField, AutoField
from datetime import date
import random

database = SqliteDatabase("pixiv.db")


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

    class Meta:
        table_name = "image_info"


database.create_tables([ImageIn], safe=True)


def add_new(pid, name, user_id, user_name, tags, sanity_level, image_urls):
    tag = ""
    for i in tags:
        tag += i["name"] + ","
        if i["translated_name"] is not None:
            tag += i["translated_name"] + ","
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
    )
    p.save()


def exists(pid):
    p = ImageIn.select().where(ImageIn.Id == pid)
    if p.exists():
        return True
    else:
        return False


def unlike(type, pid):
    if type == 1:
        p = ImageIn.select().where(ImageIn.Id == pid)
        if not p.exists():
            return 0
        else:
            try:
                q = ImageIn.update({ImageIn.unlike: 1}).where(ImageIn.Id == pid)
                q.execute()
                return 1
            except Exception:
                return 2
    elif type == 2:
        p = ImageIn.select().where(ImageIn.user_id == int(pid))
        if not p.exists():
            return 0
        else:
            try:
                q = ImageIn.update({ImageIn.unlike: 1}).where(
                    ImageIn.user_id == int(pid)
                )
                q.execute()
                return 1
            except Exception:
                return 2
    elif type == 3:
        p = ImageIn.select().where(ImageIn.user_id == int(pid))
        if not p.exists():
            return 0
        else:
            try:
                q = ImageIn.update({ImageIn.unlike: 1}).where(
                    ImageIn.user_id == int(pid)
                )
                q.execute()
                return 1
            except Exception:
                return 2


def search(type, value):
    if type == "san":
        try:
            data = random.choice(
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
