from qiniu import Auth
from flask import current_app
from haozhuan.config import global_config


def generate_token():
    # 需要填写你的 Access Key 和 Secret Key
    access_key = global_config.getRaw('qiniu', 'QINIU_ACCESS_KEY')
    secret_key = global_config.getRaw('qiniu', 'QINIU_SECRET_KEY')
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = global_config.getRaw('qiniu', 'QINIU_BUCKET_NAME')
    key = None
    # 生成上传 Token，可以指定过期时间等
    # 3600为token过期时间，秒为单位。3600等于一小时
    token = q.upload_token(bucket_name, key, 3600)
    return token
