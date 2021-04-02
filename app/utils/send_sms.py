#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""易盾短信发送接口python示例代码
接口文档: http://dun.163.com/api.html
python版本：python2.7
运行:
    1. 修改 SECRET_ID,SECRET_KEY,BUSINESS_ID 为对应申请到的值
    2. $ python smssend.py
"""


__author__ = 'yidun-dev'
__version__ = '0.1-dev'

import hashlib
import json
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime
from haozhuan.config import global_config


class SmsSendAPIDemo(object):
    """易盾短信发送接口示例代码"""
    API_URL = global_config.getRaw('wangyi', 'API_URL')
    VERSION = global_config.getRaw('wangyi', 'VERSION')

    def __init__(self):
        """
        Args:
            secret_id (str) 产品密钥ID，产品标识
            secret_key (str) 产品私有密钥，服务端生成签名信息使用
            business_id (str) 业务ID，易盾根据产品业务特点分配
        """
        self.secret_id = global_config.getRaw('wangyi', 'WI_SECRET_ID')
        self.secret_key = global_config.getRaw('wangyi', 'WI_SECRET_KEY')
        self.business_id = global_config.getRaw('wangyi', 'WI_BUSINESS_ID')

    def gen_signature(self, params=None):
        """生成签名信息
        Args:
            params (object) 请求参数
        Returns:
            参数签名md5值
        """
        buff = ""
        for k in sorted(params.keys()):
            buff += str(k) + str(params[k])
        buff += self.secret_key
        return hashlib.md5(buff.encode('utf-8')).hexdigest()

    def send(self,params):
        """请求易盾接口
        Args:
            params (object) 请求参数
        Returns:
            请求结果，json格式
        """
        params["secretId"] = self.secret_id
        params["businessId"] = self.business_id
        params["version"] = self.VERSION
        params["timestamp"] = int(time.time() * 1000)
        params["nonce"] = int(random.random() * 100000000)
        params["signature"] = self.gen_signature(params)

        try:
            params = urllib.parse.urlencode(params).encode()
            requests = urllib.request.Request(self.API_URL, params)
            # 根据API的要求，定义相对应的Content-Type
            requests.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
            content = urllib.request.urlopen(requests, timeout=1).read()
            return json.loads(content)
        except Exception as e:
            print("调用API接口失败:{}".format(e))

class SendSMS(object):
    def send(self,mobile,code):
        time_now = datetime.now().strftime("%Y-%m-%d-%H-%S-%M")
        params = {
            "mobile": mobile,
            "templateId": "10848",
            "paramType": "json",
            "params": {"code":code,"time":time_now},
        }
        ret = SmsSendAPIDemo().send(params)
