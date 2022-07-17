import json
import base64
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.ims.v20201229 import ims_client, models


def image_moderation(img):
    try:
        cred = credential.Credential(
            "xxx",
            "xxx",
        )
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ims.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = ims_client.ImsClient(cred, "ap-shanghai", clientProfile)

        req = models.ImageModerationRequest()
        params = (
            {"FileUrl": img}
            if type(img) == str
            else {"FileContent": bytes_to_base64(img)}
        )
        req.from_json_string(json.dumps(params))

        resp = client.ImageModeration(req)
        return json.loads(resp.to_json_string())

    except TencentCloudSDKException as err:
        return err


def bytes_to_base64(data):
    return base64.b64encode(data).decode("utf-8")
