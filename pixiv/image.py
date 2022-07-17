import os

from PIL import Image

from .logger import logger


IMAGE_PATH = "images"
if not os.path.exists(IMAGE_PATH):
    os.makedirs(IMAGE_PATH)
if not os.path.exists(f"{IMAGE_PATH}/comp/mosaic"):
    os.makedirs(f"{IMAGE_PATH}/comp/mosaic")
if not os.path.exists(f"{IMAGE_PATH}/error"):
    os.makedirs(f"{IMAGE_PATH}/error")


def image_mosaic(name):
    img = Image.open(f"{IMAGE_PATH}/comp/{name}")
    img_x, img_y = img.size
    imgsize = img.size
    img_ratio = img_x / img_y
    img_resolution = (20, int(20 / img_ratio))
    img = img.resize(img_resolution)
    img = img.resize(imgsize, resample=Image.BOX)
    img.save(f"{IMAGE_PATH}/comp/mosaic/{name}", quality=50)


def image_compression(name, san):
    imgsize = os.path.getsize(f"{IMAGE_PATH}/{name}")
    try:
        img = Image.open(f"{IMAGE_PATH}/{name}").convert("RGB")
    except Exception:
        return [1]
    img_x, img_y = img.size
    logger.info(f"原图分辨率为 {str(img_x)}x{str(img_y)}")

    if img_x > 1500 or img_y > 1500:
        logger.info("分辨率大于 1500 ，正在缩放")
        img.thumbnail((1500, 1500), Image.ANTIALIAS)
        img_x, img_y = img.size
        logger.info(f"缩放后分辨率为 {img_x}x{img_y}")

    img.save(f"{IMAGE_PATH}/comp/{name}", quality=85)
    finlsize = os.path.getsize(f"{IMAGE_PATH}/comp/{name}")
    logger.info(f"压缩完成 {int(finlsize / 1024)}kb / {int(imgsize / 1024)}kb")
    logger.info(name)

    # 单独打码存放。应该用不上吧。。。。
    # if san == 6:
    #     image_mosaic(name)

    return [
        0,
        f"{str(img_x)}x{str(img_y)}",
        f"{int(finlsize / 1000)}kb / {int(imgsize / 1000)}kb",
    ]
