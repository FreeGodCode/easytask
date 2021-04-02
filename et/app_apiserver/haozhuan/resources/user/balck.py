from flask_restplus import Resource
from flask import current_app, g
from utils.mysql_cli import MysqlSearch
from utils.constants import ET_GLOBAL_CONFIG
import json

class BalckListView(Resource):
    """获取公告与封禁用户"""
    def get(self):
        # 获取公告数据
        rc = current_app.redis_cli
        system_list = list()
        balck_list_json = list()
        # 获取公告数据列表
        list_len = rc.llen("system_logging")
        if list_len < 10:
            system_log = rc.lrange("system_logging",0, -1)
        else:
            system_log =rc.lrange("system_logging", (list_len - 10), -1)
        # json_data = json.loads(system_log)
        # print(json_data)  
        # 获取封禁用户数据列表
        balck_len = rc.llen("balck_list")
        if balck_len < 10:
            balck_list = rc.lrange("balck_list", 0, -1)
        else:
            balck_list = rc.lrange("balck_list", (balck_len - 10), -1)
        for i in system_log:
            dic = {
                "system": json.loads(i.decode())
            }
            system_list.append(dic)
        for k in balck_list:
            l = k.decode()
            mobile = l[7:]
            dic2 = {
                "balck_mobile": '*******' + mobile
            }
            balck_list_json.append(dic2)
        data = {
            "system_list": system_list,
            "balck_mobile": balck_list_json
        }
        return {"data":data}, 200





