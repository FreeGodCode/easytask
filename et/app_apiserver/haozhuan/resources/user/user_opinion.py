import json
from flask import current_app, g
from flask_restplus import Resource, reqparse
from utils.decorators import login_required
from utils.mysql_cli import MysqlWrite, MysqlSearch
from utils.constants import ET_FEEDBACKS
from utils.http_status import HttpStatus

class UserOpinionView(Resource):
    method_decorators = [
        login_required
    ]
    def post(self):
        """用户意见提交"""
        parser = reqparse.RequestParser()
        parser.add_argument('json_data', type=dict, required=True, location='json')
        args = parser.parse_args()
        # 要json数据入库, 接收的类型必须是dict然后转str, 不然会一直报错.可能需要flask的json,
        new_data = json.dumps(args.json_data).replace("'", '"')
        m = MysqlWrite().write(f"INSERT INTO {ET_FEEDBACKS} (member_id,feedback) VALUE ('{g.user_id}','{new_data}')")
        if m == 1:
            return {'data': '反馈成功'}, HttpStatus.OK.value
        else:
            return {'网络异常,请重试'}, HttpStatus.OK.value

    def get(self):
        """获取用户意见"""
        y = MysqlSearch().get_one(f"SELECT feedback,add_time FROM {ET_FEEDBACKS} WHERE member_id='{g.user_id}'")
        data = dict()
        data["feedback"] = y['feedback']
        data["add_time"] = y['add_time']
        return {'data': data}, HttpStatus.OK.value