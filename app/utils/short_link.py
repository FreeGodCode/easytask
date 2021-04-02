import requests
import json

from haozhuan.config import global_config
from utils.mysql_cli import MysqlSearch
from utils.constants import MEMBERS_TABLE, ET_GLOBAL_CONFIG
from flask import g, current_app

def get_short_link(iiuv):
    host = 'https://dwz.cn'
    path = '/admin/v2/create'
    url = host + path
    method = 'POST'
    content_type = 'application/json'

    # 设置Token
    token = global_config.getRaw('baidu', 'BAIDU_SHORT_LINK_TOKEN')


    # 设置待创建的长网址 # TODO 生成短链接地址是跳转到301的地址
    bodys = {'Url': global_config.getRaw('baidu', 'SHORT_URL') + f"?iiuv={iiuv}", 'TermOfValidity': 'long-term'}

    # 配置headers
    headers = {'Content-Type': content_type, 'Token': token}
    # headers = {'Token': token}

    # 发起请求
    response = requests.post(url=url, data=json.dumps(bodys), headers=headers)

    # 读取响应
    res = response.text

    return json.loads(res)["ShortUrl"]
