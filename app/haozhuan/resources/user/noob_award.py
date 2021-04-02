import json

from flask_restplus import Resource
from utils.decorators import verify_required, login_required
from utils.mysql_cli import MysqlWrite,MysqlSearch
from utils.constants import ET_TASK_ORDERS
from utils.http_status import HttpStatus
from flask import g

class NoobAwardView(Resource):
    method_decorators = [
        verify_required, login_required
    ]

    def get(self):
        task_order = MysqlSearch().get_one(f"SELECT member_id FROM {ET_TASK_ORDERS} WHERE member_id={g.user_id}")
        if task_order:
            return {'data': '次任务只能领取一次'}
        data = {
            "新手任务": 1
        }
        user_submit = json.dumps(data)
        res = MysqlWrite().write(f"INSERT INTO {ET_TASK_ORDERS} (user_submit,task_id,member_id) value ('{user_submit}',1,'{g.user_id}')")
        if res == 1:
            return {'data': "新手任务发放成功"}, HttpStatus.OK.value
