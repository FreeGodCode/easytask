import json
from flask_restplus import Resource, reqparse
from utils.decorators import login_required
from utils.mysql_cli import MysqlWrite
from utils.constants import ET_MEMBER_EXTEND
from flask import g

class AppEquipmentView(Resource):
    method_decorators = [
        login_required
    ]
    def post(self):
        """用户设备信息"""
        parser = reqparse.RequestParser()
        parser.add_argument('json_data', type=dict, required=True, location='json')
        args = parser.parse_args()
        new_data = json.dumps(args.json_data).replace("'", '"')
        # 入库
        res = MysqlWrite().write(f"UPDATE {ET_MEMBER_EXTEND} SET equipment='{new_data}' WHERE member_id='{g.user_id}'")
        if res == 1:
            return 200
        else:
            return {'code': 4003, 'msg': '参数异常'}, 200
