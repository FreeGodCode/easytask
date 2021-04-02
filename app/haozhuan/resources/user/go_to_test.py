from flask_restplus import Resource, reqparse
from utils.mysql_cli import MysqlSearch
from utils.short_link import get_short_link
from flask import redirect, g, url_for,current_app
from utils.constants import MEMBERS_TABLE, ET_GLOBAL_CONFIG
from utils.http_status import HttpStatus

class GoToTView(Resource):
    def get(self):
        # 查询iiuv邀请码
        fx = MysqlSearch().get_one(f"SELECT domains FROM {ET_GLOBAL_CONFIG}")
        ym = fx['domains'].split(',')[0]
        print(fx)
        return {'data': ym}, HttpStatus.OK.value
