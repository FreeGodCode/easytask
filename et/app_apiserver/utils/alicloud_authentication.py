import json
import urllib.parse
import urllib.request
import ssl
from flask import current_app

def ali_authentication(idNo, name):
    """阿里云实名认证工具"""
    try:
        host = current_app.config['ALIHOST']
        path = current_app.config['ALIPATH']
        appcode = current_app.config['ALIAPPCODE']
        bodys = {}
        url = host + path
        bodys['idNo'] = idNo
        bodys['name'] = name
        post_data = urllib.parse.urlencode(bodys).encode()
        requests = urllib.request.Request(url, post_data)
        requests.add_header('Authorization', 'APPCODE ' + appcode)
        # 根据API的要求，定义相对应的Content-Type
        requests.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urllib.request.urlopen(requests, context=ctx)
        content = response.read().decode()
        if (content):
            mes = json.loads(content)
            return mes
    except Exception as e:
        return False
